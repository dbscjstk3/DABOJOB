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
            logger.info(f"Starting resummary for mapping_id: {mapping_id}, reason: {reason}")

            # 1. 기존 요약 파일 확인
            summaries = self.file_manager.get_summary_results(str(mapping_id))
            if not summaries:
                raise Exception(f"No existing summaries found for mapping_id: {mapping_id}")

            # 2. 재요약 완료 후 해시태그 추출 및 news 전송
            await self._process_resummary_completion(mapping_id, summaries)

            logger.info(f"Resummary completed for mapping_id: {mapping_id}")

        except Exception as e:
            logger.error(f"Resummary failed for mapping_id {mapping_id}: {e}")
            raise

    async def _process_resummary_completion(self, mapping_id: int, summaries: dict):
        """재요약 완료 후 해시태그 추출 및 news 전송"""
        try:
            logger.info(f"Processing resummary completion for mapping_id: {mapping_id}")

            # job_id 생성
            job_id = f"summary_{mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_resummary"

            # Redis Publisher 및 HashtagExtractor 초기화
            publisher = RedisPublisher()

            # Ollama 클라이언트 설정
            import ollama
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama:11434')
            host = ollama_host if ollama_host.startswith('http') else f'http://{ollama_host}'
            ollama_client = ollama.Client(host=host)
            model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')

            extractor = HashtagExtractor(ollama_client, model_name)

            # 해시태그 추출 및 스트리밍 전송
            hashtags = await extractor.extract_hashtags_streaming(job_id, summaries, publisher)

            # 정리
            extractor.cleanup()
            publisher.cleanup()

            logger.info(f"Resummary completion finished for mapping_id: {mapping_id}, hashtags: {sum(len(tags) for tags in hashtags.values())}")

        except Exception as e:
            logger.error(f"Failed resummary completion for mapping_id {mapping_id}: {e}")
            raise