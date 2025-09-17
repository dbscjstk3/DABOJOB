"""
요약 처리 백그라운드 워커
"""
import os
import logging
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from ..services.redis_client import RedisClient
from ..services.file_manager import FileManager
from ..services.hashtag_extractor import HashtagExtractor
from ..services.redis_publisher import RedisPublisher
from ..utils import qwen_summarize_long
import ollama

logger = logging.getLogger(__name__)

class SummaryWorker:
    def __init__(self):
        self.redis_client = RedisClient()
        self.file_manager = FileManager()
        self.ollama_client = None
        self.model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
        self.running = False

        # 카테고리별 요약 설정
        self.category_configs = {
            "business_overview": {"max_length": 800, "description": "사업 개요"},
            "products_services": {"max_length": 700, "description": "주요 제품 및 서비스"},
            "revenue_orders": {"max_length": 600, "description": "매출 및 수주 현황"},
            "contracts_rnd": {"max_length": 600, "description": "주요 계약 및 연구개발"},
            "other_references": {"max_length": 500, "description": "기타 참고사항"}
        }

        # job별 카테고리 완료 추적
        self.job_completion_tracker = {}
        
    async def initialize(self):
        """워커 초기화"""
        try:
            # Redis 클라이언트 초기화
            await self.redis_client.initialize()
            
            # Ollama 클라이언트 초기화
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama:11434')
            host = ollama_host if ollama_host.startswith('http') else f'http://{ollama_host}'
            self.ollama_client = ollama.Client(host=host)
            
            # 연결 테스트
            models = self.ollama_client.list()
            logger.info(f"Connected to Ollama at {host}")
            logger.info(f"Using model: {self.model_name}")
            
            self.running = True
            logger.info("Summary worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize summary worker: {e}")
            raise
    
    async def start(self):
        """워커 시작"""
        if not self.running:
            await self.initialize()
        
        logger.info("Starting summary worker")
        while self.running:
            try:
                # Redis에서 대기 중인 요약 작업 가져오기
                jobs = await self.redis_client.get_pending_summarization_jobs(count=1)
                
                if jobs:
                    for job in jobs:
                        await self.process_summarization_job(job['stream_id'], job['data'])
                else:
                    # 작업이 없으면 30초 대기
                    await asyncio.sleep(30)
                    
            except Exception as e:
                logger.error(f"Summary worker error: {e}")
                await asyncio.sleep(30)
    
    async def stop(self):
        """워커 중지"""
        self.running = False
        logger.info("Summary worker stopped")
    
    async def process_summarization_job(self, stream_id: str, job_data: dict):
        """카테고리별 요약 작업 처리"""
        job_id = job_data.get('job_id')
        category = job_data.get('category')
        file_path = job_data.get('file_path')
        
        try:
            logger.info(f"Processing category summarization: job_id={job_id}, category={category}")
            
            # 1. 카테고리 요약 시작 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "category_summarization_in_progress",
                {
                    "stage": "category_summarization",
                    "category": category,
                    "message": f"Summarizing {category}"
                }
            )
            
            # 2. 단일 카테고리 요약 수행
            company_name = job_data.get('company_name', 'Unknown')
            config = self.category_configs.get(category, {"max_length": 500})
            
            await self._summarize_single_category(job_id, category, file_path, config)
            
            # 3. 카테고리 완료 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "category_summarization_completed",
                {
                    "stage": "category_summarization_completed",
                    "category": category,
                    "message": f"Category {category} summarized successfully",
                    "completed_at": datetime.now().isoformat()
                }
            )

            # 4. 완료된 카테고리 추적 및 모든 카테고리 완료 확인
            await self._track_category_completion(job_id, category)

            await self.redis_client.ack_job(stream_id)
            logger.info(f"Category summarization completed: job_id={job_id}, category={category}")
            
        except Exception as e:
            logger.error(f"Category summarization failed: job_id={job_id}, category={category}, error: {e}")
            
            await self.redis_client.update_job_status(
                job_id,
                "category_summarization_failed",
                {
                    "stage": "category_summarization_failed",
                    "category": category,
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
            )

            # 실패한 job도 추적에서 제거
            if job_id in self.job_completion_tracker:
                del self.job_completion_tracker[job_id]

            await self.redis_client.ack_job(stream_id)
    
    async def _summarize_single_category(self, job_id: str, category: str, file_path: str, config: Dict):
        """단일 카테고리 파일 요약 처리"""
        try:
            logger.info(f"Summarizing {category}: {file_path}")
            
            # 파일 내용 읽기
            content = self.file_manager.read_categorized_file(file_path)
            if not content:
                logger.warning(f"No content found for {category}: {file_path}")
                return
            
            # qwen_summarize_long이 이제 async 함수이므로 직접 호출
            summary = await qwen_summarize_long(
                self.ollama_client,
                self.model_name,
                content,
                config['max_length']
            )
            
            # 요약 결과 저장
            self.file_manager.save_summary(job_id, category, summary)
            
            logger.info(f"Category {category} summarized: {len(summary)} characters")
            
        except Exception as e:
            logger.error(f"Failed to summarize {category}: {e}")
            raise

    async def _track_category_completion(self, job_id: str, completed_category: str):
        """카테고리 완료 추적 및 모든 카테고리 완료 시 해시태그 추출 시작"""
        try:
            # job_id별 완료된 카테고리 추적
            if job_id not in self.job_completion_tracker:
                self.job_completion_tracker[job_id] = set()

            self.job_completion_tracker[job_id].add(completed_category)
            completed_categories = self.job_completion_tracker[job_id]

            logger.info(f"Job {job_id}: {len(completed_categories)}/{len(self.category_configs)} categories completed")

            # 모든 카테고리가 완료되었는지 확인
            if len(completed_categories) >= len(self.category_configs):
                logger.info(f"All categories completed for job {job_id}. Starting hashtag extraction...")

                # 자동 해시태그 추출 시작
                await self._start_automatic_hashtag_extraction(job_id)

                # 완료된 job 추적에서 제거
                del self.job_completion_tracker[job_id]

        except Exception as e:
            logger.error(f"Failed to track category completion for job {job_id}: {e}")

    async def _start_automatic_hashtag_extraction(self, job_id: str):
        """모든 카테고리 요약 완료 후 자동 해시태그 추출 시작"""
        try:
            logger.info(f"Starting automatic hashtag extraction for job {job_id}")

            # 1. 요약 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "hashtag_extraction_started",
                {
                    "stage": "hashtag_extraction",
                    "message": "Starting hashtag extraction from summaries",
                    "started_at": datetime.now().isoformat()
                }
            )

            # 2. 요약 결과 파일들 읽기
            summaries = self.file_manager.get_summary_results(job_id)

            if not summaries:
                logger.warning(f"No summary results found for job {job_id}")
                return

            # 3. Redis Publisher 초기화
            publisher = RedisPublisher()

            # 4. 해시태그 추출기 초기화 및 스트리밍 추출 시작
            extractor = HashtagExtractor(self.ollama_client, self.model_name)
            hashtags = await extractor.extract_hashtags_streaming(job_id, summaries, publisher)

            # 5. 정리
            extractor.cleanup()
            publisher.cleanup()

            # 6. 완료 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "hashtag_extraction_completed",
                {
                    "stage": "hashtag_extraction_completed",
                    "message": "Hashtag extraction completed and published to Redis",
                    "hashtag_count": sum(len(tags) for tags in hashtags.values()),
                    "categories_processed": len(hashtags),
                    "completed_at": datetime.now().isoformat()
                }
            )

            logger.info(f"Automatic hashtag extraction completed for job {job_id}")

        except Exception as e:
            logger.error(f"Failed automatic hashtag extraction for job {job_id}: {e}")

            # 실패 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "hashtag_extraction_failed",
                {
                    "stage": "hashtag_extraction_failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
            )