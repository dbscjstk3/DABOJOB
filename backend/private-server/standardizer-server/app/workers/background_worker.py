"""
백그라운드 워커 시스템 - 완전한 파이프라인
크롤링 → 매핑 → DART 추출 → 표준화
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ..services.dart_extractor import DartDocumentExtractor
from ..services.standardizer import StandardizerService
from ..services.file_manager import FileManager
from ..utils.redis_helper import redis_helper

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """백그라운드 작업 처리 워커"""

    def __init__(self):
        self.standardizer_service = StandardizerService()
        self.file_manager = FileManager()
        self.dart_extractor: Optional[DartDocumentExtractor] = None
        self.company_mapper = None  # 나중에 초기화
        self.crawler_service = None  # 나중에 초기화
        self.worker_tasks: Dict[str, asyncio.Task] = {}
        self.running = False

    async def initialize(self):
        """워커 서비스들 초기화"""
        try:
            # 기본 서비스들 초기화
            await self.standardizer_service.initialize()

            # DART 추출기 초기화
            import os
            dart_api_key = os.getenv('DART_API_KEY')
            if dart_api_key:
                self.dart_extractor = DartDocumentExtractor(dart_api_key)
                logger.info("DART extractor initialized")
            else:
                logger.warning("DART_API_KEY not found")

            # Company Mapper 초기화
            from ..services.company_mapper import CompanyMappingService
            self.company_mapper = CompanyMappingService()
            await self.company_mapper.initialize()

            # Crawler Service 초기화
            from ..services.crawler_service import CrawlerService
            self.crawler_service = CrawlerService()
            await self.crawler_service.initialize()

            # Redis 스트림 및 Consumer Group 설정
            await redis_helper.setup_streams()

            logger.info("Background worker services initialized")

        except Exception as e:
            logger.error(f"Failed to initialize background worker: {e}")
            raise

    async def start(self):
        """모든 워커 시작"""
        if self.running:
            logger.warning("Workers already running")
            return

        try:
            await self.initialize()
            self.running = True

            # 각 스트림별 워커 시작
            self.worker_tasks["crawler"] = asyncio.create_task(
                self._process_crawler_jobs()
            )
            self.worker_tasks["mapping"] = asyncio.create_task(
                self._process_mapping_jobs()
            )
            self.worker_tasks["dart_extract"] = asyncio.create_task(
                self._process_dart_extract_jobs()
            )
            self.worker_tasks["standardize"] = asyncio.create_task(
                self._process_standardize_jobs()
            )

            logger.info("All background workers started")

        except Exception as e:
            self.running = False
            raise Exception(f"Failed to start workers: {e}")

    async def stop(self):
        """모든 워커 중지"""
        if not self.running:
            return

        try:
            self.running = False

            # 모든 태스크 취소
            for worker_name, task in self.worker_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(f"Worker {worker_name} cancelled")

            self.worker_tasks.clear()
            logger.info("All workers stopped")

        except Exception as e:
            logger.error(f"Error stopping workers: {e}")

    async def _process_crawler_jobs(self) -> None:
        """크롤링 작업 처리"""
        while self.running:
            try:
                jobs = await redis_helper.get_pending_jobs("crawler_stream", count=1)

                for job_data in jobs:
                    await self._handle_crawler_job(job_data)

                await asyncio.sleep(5)  # 5초 대기

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in crawler worker: {e}")
                await asyncio.sleep(10)

    async def _process_mapping_jobs(self) -> None:
        """매핑 작업 처리"""
        while self.running:
            try:
                jobs = await redis_helper.get_pending_jobs("mapping_stream", count=1)

                for job_data in jobs:
                    await self._handle_mapping_job(job_data)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in mapping worker: {e}")
                await asyncio.sleep(10)

    async def _process_dart_extract_jobs(self) -> None:
        """DART 추출 작업 처리"""
        while self.running:
            try:
                jobs = await redis_helper.get_pending_jobs("dart_extract_stream", count=1)

                for job_data in jobs:
                    await self._handle_dart_extract_job(job_data)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in DART extract worker: {e}")
                await asyncio.sleep(10)

    async def _process_standardize_jobs(self) -> None:
        """표준화 작업 처리"""
        while self.running:
            try:
                jobs = await redis_helper.get_pending_jobs("standardize_stream", count=1)

                for job_data in jobs:
                    await self._handle_standardize_job(job_data)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in standardize worker: {e}")
                await asyncio.sleep(10)

    async def _handle_crawler_job(self, job_data: Dict[str, Any]) -> None:
        """크롤링 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing crawler job: {job_id}")

            max_pages = job_data.get("max_pages", 5)
            result = await self.crawler_service.start_saramin_crawling(max_pages)

            # 결과 저장
            await redis_helper.update_job_status(job_id, "completed", result)

            # 크롤링 성공 시 자동으로 매핑 작업 시작
            if result.get("status") == "completed" and result.get("companies_found", 0) > 0:
                logger.info(f"🔗 Crawling completed with {result.get('companies_found')} companies. Starting auto-mapping...")

                # 매핑 작업을 Redis 스트림에 추가
                mapping_job_data = {
                    "job_id": f"auto_mapping_{job_id}",
                    "trigger": "post_crawling",
                    "limit": 20,
                    "submitted_at": datetime.now().isoformat()
                }

                await redis_helper.add_job("mapping_stream", mapping_job_data)
                logger.info(f"✅ Auto-mapping job queued: auto_mapping_{job_id}")

        except Exception as e:
            logger.error(f"Failed to process crawler job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_mapping_job(self, job_data: Dict[str, Any]) -> None:
        """매핑 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing mapping job: {job_id}")

            limit = job_data.get("limit", 10)
            result = await self.company_mapper.batch_process_mappings(limit)

            await redis_helper.update_job_status(job_id, "completed", result)

            # 매핑 성공한 회사들에 대해 자동으로 DART 문서 추출 시작
            if result.get("suggested", 0) > 0:
                logger.info(f"🎯 {result.get('suggested')} companies mapped successfully. Starting DART extraction...")

                # 성공적으로 매핑된 회사들 가져오기
                from ..database import SessionLocal
                from ..models.crawler_models import CompanyDartMapping, MappingStatus

                db = SessionLocal()
                try:
                    # 신뢰도 95% 이상만 자동 추출
                    high_confidence_mappings = db.query(CompanyDartMapping).filter(
                        CompanyDartMapping.mapping_status == MappingStatus.suggested,
                        CompanyDartMapping.confidence_score >= 95,
                        CompanyDartMapping.dart_corp_code.isnot(None)
                    ).all()

                    for mapping in high_confidence_mappings:
                        # DART 추출 작업 큐에 추가
                        dart_job_data = {
                            "job_id": f"dart_extract_{mapping.mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            "mapping_id": mapping.mapping_id,
                            "company_name": mapping.crawled_company_name,
                            "corp_code": mapping.dart_corp_code,
                            "report_type": "annual",
                            "submitted_at": datetime.now().isoformat()
                        }

                        await redis_helper.add_job("dart_extract_stream", dart_job_data)
                        logger.info(f"📄 DART extraction queued for {mapping.crawled_company_name} (Code: {mapping.dart_corp_code})")

                finally:
                    db.close()

        except Exception as e:
            logger.error(f"Failed to process mapping job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_dart_extract_job(self, job_data: Dict[str, Any]) -> None:
        """DART 추출 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing DART extract job: {job_id}")

            corp_code = job_data.get("corp_code")
            year = job_data.get("year")

            if not self.dart_extractor:
                raise Exception("DART extractor not available")

            result = await self.dart_extractor.extract_company_annual_report(
                corp_code=corp_code,
                year=year
            )

            await redis_helper.update_job_status(job_id, "completed", result)

            # DART 추출 성공 시 자동으로 표준화 작업 시작
            if result.get("status") == "extracted" and result.get("content"):
                logger.info(f"📄 DART extraction completed for {job_data.get('company_name')}. Starting standardization...")

                # 표준화 작업을 Redis 스트림에 추가
                standardize_job_data = {
                    "job_id": f"standardize_{job_data.get('mapping_id')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "mapping_id": job_data.get("mapping_id"),
                    "company_name": job_data.get("company_name"),
                    "dart_content": result.get("content"),
                    "submitted_at": datetime.now().isoformat()
                }

                await redis_helper.add_job("standardize_stream", standardize_job_data)
                logger.info(f"📝 Standardization job queued for {job_data.get('company_name')}")

        except Exception as e:
            logger.error(f"Failed to process DART extract job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_standardize_job(self, job_data: Dict[str, Any]) -> None:
        """표준화 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing standardize job: {job_id}")

            content = job_data.get("dart_content", "")
            title = job_data.get("company_name", "")

            if content:
                # 분류 및 표준화 수행
                category, standardized_content = await self.standardizer_service.classify_and_standardize(
                    title=title,
                    content=content
                )

                result = {
                    "mapping_id": job_data.get("mapping_id"),
                    "category": category,
                    "standardized_content": standardized_content,
                    "processing_time": datetime.now().isoformat()
                }

                await redis_helper.update_job_status(job_id, "completed", result)
                logger.info(f"✅ Standardization completed for {title}")
            else:
                await redis_helper.update_job_status(job_id, "failed", {"error": "No content provided"})

        except Exception as e:
            logger.error(f"Failed to process standardize job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    def get_status(self) -> Dict[str, Any]:
        """워커 상태 반환"""
        return {
            "running": self.running,
            "active_workers": list(self.worker_tasks.keys()),
            "worker_count": len(self.worker_tasks),
            "services": {
                "standardizer": "initialized" if self.standardizer_service else "not_initialized",
                "dart_extractor": "initialized" if self.dart_extractor else "not_initialized",
                "company_mapper": "initialized" if self.company_mapper else "not_initialized",
                "crawler_service": "initialized" if self.crawler_service else "not_initialized"
            }
        }