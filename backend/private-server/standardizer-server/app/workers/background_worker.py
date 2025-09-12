"""
백그라운드 작업 처리 워커
"""
import os
import logging
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from ..services.dart_extractor import DartDocumentExtractor
from ..services.standardizer import StandardizerService
from ..services.file_manager import FileManager
from ..services.redis_client import RedisClient

logger = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self):
        self.standardizer_service = StandardizerService()
        self.file_manager = FileManager()
        self.redis_client = RedisClient()
        self.dart_extractor = None
        self.running = False
        
    async def initialize(self):
        """워커 초기화"""
        try:
            # 표준화 서비스 초기화
            await self.standardizer_service.initialize()
            
            # Redis 클라이언트 초기화
            await self.redis_client.initialize()
            
            # DART 추출기 초기화 (API 키가 있을 때만)
            dart_api_key = os.getenv('DART_API_KEY')
            if dart_api_key:
                self.dart_extractor = DartDocumentExtractor(dart_api_key)
                logger.info("DART extractor initialized in worker")
            else:
                logger.warning("DART_API_KEY not found in worker")
                
            self.running = True
            logger.info("Background worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}")
            raise
    
    async def start(self):
        """워커 시작"""
        if not self.running:
            await self.initialize()
        
        logger.info("Starting background job worker")
        while self.running:
            try:
                # Redis에서 대기 중인 작업 가져오기
                jobs = await self.redis_client.get_pending_jobs(count=1)
                
                if jobs:
                    for job in jobs:
                        await self.process_single_job(job['stream_id'], job['data'])
                else:
                    # 작업이 없으면 1초 대기
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)  # 에러 시 5초 대기
    
    async def stop(self):
        """워커 중지"""
        self.running = False
        logger.info("Background worker stopped")
    
    async def process_single_job(self, stream_id: str, job_data: dict):
        """개별 작업 처리"""
        job_id = job_data.get('job_id')
        
        try:
            logger.info(f"Processing job: {job_id}")
            
            # 1. 작업 상태를 진행 중으로 변경
            await self.redis_client.update_job_status(
                job_id, 
                "in_progress", 
                {
                    "stage": "dart_extraction",
                    "current_step": 0,
                    "total_steps": 8
                }
            )
            
            # 2. DART 문서 추출
            company_name = job_data.get('company_name')
            report_type = job_data.get('report_type', 'A')
            
            if not self.dart_extractor:
                raise Exception("DART extractor not available")
            
            rcp_no, report_nm, rcept_dt = self.dart_extractor.get_latest_report(
                company_name, report_type
            )
            
            if not rcp_no:
                raise Exception(f"No reports found for {company_name}")
            
            xml_text = self.dart_extractor.dart.document(rcp_no)
            if not xml_text:
                raise Exception("Failed to download document")
            
            soup = BeautifulSoup(xml_text, 'xml')
            subsections = self.dart_extractor.extract_business_subsections(soup)
            
            if not subsections:
                raise Exception("Failed to extract subsections")
            
            # 3. 메타데이터 및 원본 파일 저장
            metadata = {
                "job_id": job_id,
                "company_name": company_name,
                "report_name": report_nm,
                "report_date": rcept_dt,
                "receipt_no": rcp_no,
                "created_at": datetime.now().isoformat()
            }
            self.file_manager.save_metadata(job_id, metadata)
            
            raw_files = {}
            for i, (title, content) in enumerate(subsections.items(), 1):
                raw_files[f"개요{i}_{title.replace(' ', '_').replace('.', '')}.txt"] = content
            self.file_manager.save_raw_files(job_id, raw_files)
            
            # 4. 표준화 시작
            await self.redis_client.update_job_status(
                job_id, 
                "in_progress", 
                {
                    "stage": "standardization",
                    "current_step": 1,
                    "total_steps": 8,
                    "message": "DART extraction completed, starting standardization"
                }
            )
            
            # 5. 각 챕터별 분류 및 표준화
            total_chapters = len(subsections)
            
            for i, (title, content) in enumerate(subsections.items(), 1):
                logger.info(f"Classifying and standardizing chapter {i}/{total_chapters}: {title}")
                
                # 분류와 표준화를 동시에 수행
                category, standardized_content = await self.standardizer_service.classify_and_standardize(title, content)
                
                # 카테고리별 파일에 append
                self.file_manager.append_to_category_file(job_id, category, title, standardized_content)
                
                await self.redis_client.update_job_status(
                    job_id, 
                    "in_progress", 
                    {
                        "stage": "standardization",
                        "current_step": i + 1,
                        "total_steps": 8,
                        "current_chapter": title,
                        "category": category,
                        "message": f"Completed {i}/{total_chapters} chapters - {title} -> {category}"
                    }
                )
            
            # 6. 작업 완료 메타데이터 업데이트
            self.file_manager.update_job_stage(job_id, "categorization", "completed")
            
            # 7. Summary Server로 요약 요청 전송
            await self._send_summarization_request(job_id, company_name)
            
            # 8. 작업 완료
            await self.redis_client.update_job_status(
                job_id, 
                "completed", 
                {
                    "stage": "standardization_completed",
                    "current_step": 8,
                    "total_steps": 10,  # 요약 단계 추가
                    "message": "Standardization completed, summarization request sent",
                    "completed_at": datetime.now().isoformat()
                }
            )
            
            await self.redis_client.ack_job(stream_id)
            logger.info(f"Standardization job completed, summarization request sent: {job_id}")
            
        except Exception as e:
            logger.error(f"Job failed: {job_id}, error: {e}")
            
            await self.redis_client.update_job_status(
                job_id, 
                "failed", 
                {
                    "stage": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
            )
            
            await self.redis_client.ack_job(stream_id)
    
    async def _send_summarization_request(self, job_id: str, company_name: str):
        """
        Summary Server로 요약 요청 메시지 전송
        
        Args:
            job_id (str): 작업 ID
            company_name (str): 회사명
        """
        try:
            # 카테고리별 파일 경로 생성
            job_path = self.file_manager.get_job_path(job_id)
            standardized_path = job_path / "standardized"
            
            categories = {
                "business_overview": str(standardized_path / "business_overview.txt"),
                "products_services": str(standardized_path / "products_services.txt"),
                "revenue_orders": str(standardized_path / "revenue_orders.txt"),
                "contracts_rnd": str(standardized_path / "contracts_rnd.txt"),
                "other_references": str(standardized_path / "other_references.txt")
            }
            
            # 각 카테고리별로 개별 요약 요청 메시지 전송
            summary_stream_ids = []
            for category, file_path in categories.items():
                category_request = {
                    "job_id": job_id,
                    "stage": "category_summarization_request", 
                    "company_name": company_name,
                    "category": category,
                    "file_path": file_path,
                    "requested_at": datetime.now().isoformat(),
                    "source_service": "standardizer"
                }
                
                # Summary Server용 Redis Stream에 카테고리별 메시지 전송
                stream_id = await self.redis_client.submit_summarization_job(category_request)
                summary_stream_ids.append(stream_id)
                logger.info(f"Category summarization request sent: job_id={job_id}, category={category}, stream_id={stream_id}")
            
            logger.info(f"All category summarization requests sent: job_id={job_id}, total_categories={len(summary_stream_ids)}")
            
            # 메타데이터 업데이트
            metadata_update = {
                "summarization_requests": {
                    "sent_at": datetime.now().isoformat(),
                    "stream_ids": summary_stream_ids,
                    "categories": list(categories.keys()),
                    "total_categories": len(categories),
                    "status": "sent"
                }
            }
            self.file_manager.save_metadata(job_id, metadata_update)
            
        except Exception as e:
            logger.error(f"Failed to send summarization request for job {job_id}: {e}")
            # 실패해도 전체 작업은 성공으로 처리 (요약은 선택사항)
            pass