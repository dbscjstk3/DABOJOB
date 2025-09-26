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

            # 1. 기존 요약 파일 확인
            logger.info(f"📁 Checking existing summary files for mapping_id: {mapping_id}...")
            summaries = self.file_manager.get_summary_results(str(mapping_id))
            if not summaries:
                logger.error(f"❌ No existing summaries found for mapping_id: {mapping_id}")
                raise Exception(f"No existing summaries found for mapping_id: {mapping_id}")

            logger.info(f"✅ Found {len(summaries)} summary categories:")
            for category, content in summaries.items():
                logger.info(f"   - {category}: {len(content) if content else 0} chars")

            # 2. 재요약 완료 후 해시태그 추출 및 news 전송
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