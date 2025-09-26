"""
재요약 서비스 - 최소한의 기능만
"""
import logging
from datetime import datetime
import os

from .redis_publisher import RedisPublisher
from .hashtag_extractor import HashtagExtractor
from .file_manager import FileManager

logger = logging.getLogger(__name__)

class ResummaryService:
    """재요약 서비스 - 최소 버전"""

    def __init__(self):
        self.file_manager = FileManager()

    async def trigger_resummary(self, mapping_id: int, reason: str, requested_by: str) -> None:
        """재요약 실행 - 핵심 기능"""
        try:
            logger.info(f"="*50)
            logger.info(f"🔄 RESUMMARY START")
            logger.info(f"  - Mapping ID: {mapping_id}")
            logger.info(f"  - Reason: {reason}")
            logger.info(f"  - Requested by: {requested_by}")
            logger.info(f"  - Time: {datetime.now().isoformat()}")
            logger.info(f"="*50)

            # 1. standardizer의 원본 표준화 파일들 읽기
            logger.info(f"📁 Reading standardized files from standardizer for mapping_id: {mapping_id}...")
            standardized_files = self._get_standardized_files(mapping_id)
            if not standardized_files:
                logger.error(f"❌ No standardized files found for mapping_id: {mapping_id}")
                raise Exception(f"No standardized files found for mapping_id: {mapping_id}")

            logger.info(f"✅ Found {len(standardized_files)} standardized categories:")
            for category, content in standardized_files.items():
                logger.info(f"   - {category}: {len(content) if content else 0} chars")

            # 2. 원본 파일들을 다시 요약
            logger.info(f"🔄 Re-summarizing standardized content...")
            summaries = await self._perform_resummary(mapping_id, standardized_files)

            # 3. 새로운 요약 결과 저장
            logger.info(f"💾 Saving new summary results...")
            for category, summary in summaries.items():
                if summary:
                    self.file_manager.save_summary(f"summary_{mapping_id}_resummary", category, summary)

            # 4. 해시태그 추출 및 news 전송
            await self._process_resummary_completion(mapping_id, summaries)

            logger.info(f"="*50)
            logger.info(f"✅ RESUMMARY COMPLETED")
            logger.info(f"  - Mapping ID: {mapping_id}")
            logger.info(f"  - Time: {datetime.now().isoformat()}")
            logger.info(f"="*50)

        except Exception as e:
            logger.error(f"Resummary failed for mapping_id {mapping_id}: {e}")
            raise

    async def _process_resummary_completion(self, mapping_id: int, summaries: dict):
        """재요약 완료 후 해시태그 추출 및 news 전송"""
        try:
            logger.info(f"")
            logger.info(f"📋 Processing resummary completion for mapping_id: {mapping_id}")

            # job_id 생성
            job_id = f"summary_{mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_resummary"
            logger.info(f"📝 Generated job_id: {job_id}")

            # Redis Publisher 및 HashtagExtractor 초기화
            logger.info(f"🔧 Initializing Redis Publisher...")
            publisher = RedisPublisher()
            logger.info(f"✅ Redis Publisher ready")

            # Ollama 클라이언트 설정
            import ollama
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama:11434')
            host = ollama_host if ollama_host.startswith('http') else f'http://{ollama_host}'
            logger.info(f"🤖 Connecting to Ollama at {host}...")
            ollama_client = ollama.Client(host=host)
            model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
            logger.info(f"✅ Ollama connected, using model: {model_name}")

            extractor = HashtagExtractor(ollama_client, model_name)

            # 해시태그 추출 및 스트리밍 전송
            logger.info(f"🏷️ Starting hashtag extraction...")
            hashtags = await extractor.extract_hashtags_streaming(job_id, summaries, publisher)

            total_hashtags = sum(len(tags) for tags in hashtags.values())
            logger.info(f"✅ Hashtag extraction completed:")
            logger.info(f"   - Total hashtags: {total_hashtags}")
            for category, tags in hashtags.items():
                if tags:
                    logger.info(f"   - {category}: {len(tags)} hashtags")

            # 정리
            logger.info(f"🧹 Cleaning up resources...")
            extractor.cleanup()
            publisher.cleanup()
            logger.info(f"✅ Resources cleaned up")

            logger.info(f"")
            logger.info(f"📊 Resummary Stats:")
            logger.info(f"   - Mapping ID: {mapping_id}")
            logger.info(f"   - Job ID: {job_id}")
            logger.info(f"   - Categories: {len(summaries)}")
            logger.info(f"   - Total hashtags: {total_hashtags}")

        except Exception as e:
            logger.error(f"Failed resummary completion for mapping_id {mapping_id}: {e}")
            raise

    def _get_standardized_files(self, mapping_id: int) -> dict:
        """standardizer에서 표준화된 원본 파일들 읽기"""
        try:
            from pathlib import Path

            # standardizer의 데이터 경로 (동일한 볼륨 마운트 사용)
            standardized_path = Path(f"/app/data/mapping/{mapping_id}/standardized")

            if not standardized_path.exists():
                logger.error(f"Standardized path not found: {standardized_path}")
                return {}

            # 표준화된 파일들 읽기
            category_files = {
                'business_overview': 'business_overview.txt',
                'products_services': 'products_services.txt',
                'revenue_orders': 'revenue_orders.txt',
                'contracts_rnd': 'contracts_rnd.txt',
                'other_references': 'other_references.txt'
            }

            results = {}
            for category, filename in category_files.items():
                file_path = standardized_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip():  # 비어있지 않은 파일만 포함
                        results[category] = content
                        logger.info(f"   📄 Read {category}: {len(content)} chars")
                else:
                    logger.warning(f"   ❌ File not found: {filename}")

            return results

        except Exception as e:
            logger.error(f"Error reading standardized files: {e}")
            return {}

    async def _perform_resummary(self, mapping_id: int, standardized_files: dict) -> dict:
        """표준화된 파일들을 다시 요약"""
        try:
            # Ollama 클라이언트 설정
            import ollama
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama:11434')
            host = ollama_host if ollama_host.startswith('http') else f'http://{ollama_host}'
            ollama_client = ollama.Client(host=host)
            model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')

            # utils에서 요약 함수 가져오기
            from ..utils import qwen_summarize_long

            summaries = {}

            # 카테고리별 최대 길이 설정
            category_configs = {
                "business_overview": {"max_length": 800, "description": "사업 개요"},
                "products_services": {"max_length": 700, "description": "주요 제품 및 서비스"},
                "revenue_orders": {"max_length": 600, "description": "매출 및 수주 현황"},
                "contracts_rnd": {"max_length": 600, "description": "주요 계약 및 연구개발"},
                "other_references": {"max_length": 500, "description": "기타 참고사항"}
            }

            for category, content in standardized_files.items():
                if content and content.strip():
                    config = category_configs.get(category, {"max_length": 600})
                    logger.info(f"   🔄 Summarizing {category}...")

                    summary = await qwen_summarize_long(
                        ollama_client=ollama_client,
                        model_name=model_name,
                        text=content,
                        max_length=config['max_length']
                    )

                    summaries[category] = summary
                    logger.info(f"   ✅ {category}: {len(summary)} chars")
                else:
                    summaries[category] = None
                    logger.warning(f"   ⚠️ {category}: No content to summarize")

            return summaries

        except Exception as e:
            logger.error(f"Error performing resummary: {e}")
            return {}