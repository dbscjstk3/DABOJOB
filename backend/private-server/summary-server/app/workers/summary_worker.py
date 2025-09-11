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
from ..utils import qwen_summarize_long
import ollama

logger = logging.getLogger(__name__)

class SummaryWorker:
    def __init__(self):
        self.redis_client = RedisClient()
        self.file_manager = FileManager()
        self.ollama_client = None
        self.model_name = os.getenv('SUMMARY_MODEL', 'qwen2.5:0.5b-instruct-fp16')
        self.running = False
        
        # 카테고리별 요약 설정
        self.category_configs = {
            "business_overview": {"max_length": 800, "description": "사업 개요"},
            "products_services": {"max_length": 700, "description": "주요 제품 및 서비스"},
            "revenue_orders": {"max_length": 600, "description": "매출 및 수주 현황"},
            "contracts_rnd": {"max_length": 600, "description": "주요 계약 및 연구개발"},
            "other_references": {"max_length": 500, "description": "기타 참고사항"}
        }
        
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
        """요약 작업 처리"""
        job_id = job_data.get('job_id')
        
        try:
            logger.info(f"Processing summarization job: {job_id}")
            
            # 1. 작업 시작 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "summarization_in_progress",
                {
                    "stage": "summarization",
                    "current_step": 9,
                    "total_steps": 10,
                    "message": "Starting summarization of categorized files"
                }
            )
            
            # 2. 카테고리별 파일 경로 가져오기
            categorized_files = job_data.get('categorized_files', {})
            company_name = job_data.get('company_name', 'Unknown')
            
            # 3. 병렬로 카테고리별 요약 수행
            await self._process_categories_parallel(job_id, categorized_files)
            
            # 4. 메타데이터 저장
            metadata = {
                "job_id": job_id,
                "company_name": company_name,
                "summarization_completed_at": datetime.now().isoformat(),
                "categories_processed": list(categorized_files.keys())
            }
            self.file_manager.save_metadata(job_id, metadata)
            
            # 5. 최종 완료 상태 업데이트
            await self.redis_client.update_job_status(
                job_id,
                "summarization_completed",
                {
                    "stage": "summarization_completed",
                    "current_step": 10,
                    "total_steps": 10,
                    "message": "All categories summarized successfully",
                    "completed_at": datetime.now().isoformat()
                }
            )
            
            await self.redis_client.ack_job(stream_id)
            logger.info(f"Summarization job completed successfully: {job_id}")
            
        except Exception as e:
            logger.error(f"Summarization job failed: {job_id}, error: {e}")
            
            await self.redis_client.update_job_status(
                job_id,
                "summarization_failed",
                {
                    "stage": "summarization_failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
            )
            
            await self.redis_client.ack_job(stream_id)
    
    async def _process_categories_parallel(self, job_id: str, categorized_files: Dict[str, str]):
        """카테고리별 파일을 병렬로 요약 처리"""
        try:
            # 병렬 처리를 위한 태스크 리스트
            tasks = []
            
            for category, file_path in categorized_files.items():
                if category in self.category_configs:
                    task = self._summarize_single_category(
                        job_id, category, file_path, 
                        self.category_configs[category]
                    )
                    tasks.append(task)
            
            # 모든 카테고리 병렬 처리
            logger.info(f"Starting parallel summarization of {len(tasks)} categories")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 확인
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Category summarization failed: {result}")
            
        except Exception as e:
            logger.error(f"Parallel summarization failed: {e}")
            raise
    
    async def _summarize_single_category(self, job_id: str, category: str, file_path: str, config: Dict):
        """단일 카테고리 파일 요약 처리"""
        try:
            logger.info(f"Summarizing {category}: {file_path}")
            
            # 파일 내용 읽기
            content = self.file_manager.read_categorized_file(file_path)
            if not content:
                logger.warning(f"No content found for {category}: {file_path}")
                return
            
            # ThreadPoolExecutor를 사용하여 CPU 집약적 작업을 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                summary = await loop.run_in_executor(
                    executor,
                    qwen_summarize_long,
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