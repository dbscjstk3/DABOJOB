import asyncio
import logging
import json
from datetime import datetime
from bs4 import BeautifulSoup

from .services.redis_client import RedisClient
from .services.dart_extractor import DartDocumentExtractor
from .services.standardizer import StandardizerService
from .services.file_manager import FileManager

logger = logging.getLogger(__name__)

class StandardizationWorker:
    def __init__(self):
        """워커 초기화"""
        self.redis_client = RedisClient()
        self.standardizer_service = StandardizerService()
        self.file_manager = FileManager()
        self.dart_extractor = None
        self.running = False
    
    async def initialize(self):
        """워커 서비스 초기화"""
        try:
            # Redis 클라이언트 초기화
            await self.redis_client.initialize()
            
            # 표준화 서비스 초기화
            await self.standardizer_service.initialize()
            
            # DART 추출기 초기화
            import os
            dart_api_key = os.getenv('DART_API_KEY')
            if dart_api_key:
                self.dart_extractor = DartDocumentExtractor(dart_api_key)
                logger.info("Worker: DART extractor initialized")
            else:
                logger.error("Worker: DART_API_KEY not found")
                raise ValueError("DART_API_KEY is required")
            
            logger.info("Standardization worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}")
            raise
    
    async def process_job(self, stream_id: str, job_data: dict):
        """
        개별 작업 처리
        
        Args:
            stream_id (str): Redis Stream ID
            job_data (dict): 작업 데이터
        """
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
                    "total_steps": 8  # DART 추출 + 7개 챕터 표준화
                }
            )
            
            # 2. DART 문서 추출
            company_name = job_data.get('company_name')
            report_type = job_data.get('report_type', 'A')
            
            # 최신 보고서 조회
            rcp_no, report_nm, rcept_dt = self.dart_extractor.get_latest_report(
                company_name, report_type
            )
            
            if not rcp_no:
                raise Exception(f"No reports found for {company_name}")
            
            # XML 다운로드 및 파싱
            xml_text = self.dart_extractor.dart.document(rcp_no)
            if not xml_text:
                raise Exception("Failed to download document")
            
            soup = BeautifulSoup(xml_text, 'xml')
            subsections = self.dart_extractor.extract_business_subsections(soup)
            
            if not subsections:
                raise Exception("Failed to extract subsections")
            
            # 3. 메타데이터 저장
            metadata = {
                "job_id": job_id,
                "company_name": company_name,
                "report_name": report_nm,
                "report_date": rcept_dt,
                "receipt_no": rcp_no,
                "created_at": datetime.now().isoformat()
            }
            self.file_manager.save_metadata(job_id, metadata)
            
            # 4. 원본 파일들 저장
            raw_files = {}
            for i, (title, content) in enumerate(subsections.items(), 1):
                raw_files[f"개요{i}_{title.replace(' ', '_').replace('.', '')}.txt"] = content
            self.file_manager.save_raw_files(job_id, raw_files)
            
            # 5. DART 추출 완료
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
            
            # 6. 각 챕터별 표준화 (진행률 업데이트)
            standardized_chapters = {}
            total_chapters = len(subsections)
            
            for i, (title, content) in enumerate(subsections.items(), 1):
                logger.info(f"Standardizing chapter {i}/{total_chapters}: {title}")
                
                # 표준화 수행
                standardized_content = await self.standardizer_service.standardize_text(content)
                standardized_chapters[title] = standardized_content
                
                # 진행률 업데이트
                await self.redis_client.update_job_status(
                    job_id, 
                    "in_progress", 
                    {
                        "stage": "standardization",
                        "current_step": i + 1,
                        "total_steps": 8,
                        "current_chapter": title,
                        "message": f"Completed {i}/{total_chapters} chapters"
                    }
                )
            
            # 7. 표준화된 파일들 저장
            self.file_manager.save_standardized_files(job_id, standardized_chapters)
            
            # 8. 작업 완료
            await self.redis_client.update_job_status(
                job_id, 
                "completed", 
                {
                    "stage": "completed",
                    "current_step": 8,
                    "total_steps": 8,
                    "message": "All processing completed successfully",
                    "completed_at": datetime.now().isoformat()
                }
            )
            
            # 9. Redis Stream에서 작업 확인
            await self.redis_client.ack_job(stream_id)
            
            logger.info(f"Job completed successfully: {job_id}")
            
        except Exception as e:
            logger.error(f"Job failed: {job_id}, error: {e}")
            
            # 실패 상태 업데이트
            await self.redis_client.update_job_status(
                job_id, 
                "failed", 
                {
                    "stage": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
            )
            
            # Stream에서 확인 (실패한 작업도 확인해서 재처리 방지)
            await self.redis_client.ack_job(stream_id)
    
    async def run(self):
        """워커 실행 (메인 루프)"""
        self.running = True
        logger.info("Standardization worker started")
        
        try:
            while self.running:
                # 대기 중인 작업 가져오기
                jobs = await self.redis_client.get_pending_jobs(count=1)
                
                if jobs:
                    for job in jobs:
                        await self.process_job(job['stream_id'], job['data'])
                else:
                    # 작업이 없으면 잠시 대기
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            await self.redis_client.close()
            logger.info("Standardization worker stopped")
    
    def stop(self):
        """워커 중지"""
        self.running = False
        logger.info("Stopping standardization worker...")

# 메인 워커 실행 함수
async def main():
    """워커 메인 함수"""
    worker = StandardizationWorker()
    
    try:
        await worker.initialize()
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        worker.stop()
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())