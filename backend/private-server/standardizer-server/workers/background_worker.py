"""
백그라운드 워커 시스템
"""
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from services.base import BaseService
from services.text_processor import TextProcessor
from services.company_mapper import CompanyMappingService
from services.dart_extractor import DartExtractorService
from services.crawler import CrawlerService
from utils.redis_helper import redis_helper
from utils.exceptions import StandardizerException


class BackgroundWorker(BaseService):
    """백그라운드 작업 처리 워커"""

    def __init__(self):
        super().__init__("BackgroundWorker")
        self.text_processor: Optional[TextProcessor] = None
        self.company_mapper: Optional[CompanyMappingService] = None
        self.dart_extractor: Optional[DartExtractorService] = None
        self.crawler_service: Optional[CrawlerService] = None
        self.worker_tasks: Dict[str, asyncio.Task] = {}
        self.is_running: bool = False

    async def _setup(self) -> None:
        """워커 서비스들 초기화"""
        try:
            # 서비스 인스턴스 생성
            self.text_processor = TextProcessor()
            self.company_mapper = CompanyMappingService()
            self.dart_extractor = DartExtractorService()
            self.crawler_service = CrawlerService()

            # 서비스들 초기화
            await self.text_processor.initialize()
            await self.company_mapper.initialize()
            await self.dart_extractor.initialize()
            await self.crawler_service.initialize()

            self.logger.info("Background worker services initialized")

        except Exception as e:
            raise StandardizerException(f"Failed to initialize background worker: {e}")

    async def _cleanup(self) -> None:
        """워커 정리"""
        try:
            # 실행 중인 작업들 정리
            await self.stop_all_workers()

            # 서비스들 정리
            if self.text_processor:
                await self.text_processor.shutdown()
            if self.company_mapper:
                await self.company_mapper.shutdown()
            if self.dart_extractor:
                await self.dart_extractor.shutdown()
            if self.crawler_service:
                await self.crawler_service.shutdown()

        except Exception as e:
            self.logger.error(f"Error during worker cleanup: {e}")

    async def start_workers(self) -> None:
        """모든 워커 시작"""
        if self.is_running:
            self.logger.warning("Workers already running")
            return

        try:
            self.is_running = True

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

            self.logger.info("All background workers started")

        except Exception as e:
            self.is_running = False
            raise StandardizerException(f"Failed to start workers: {e}")

    async def stop_all_workers(self) -> None:
        """모든 워커 중지"""
        if not self.is_running:
            return

        try:
            self.is_running = False

            # 모든 태스크 취소
            for worker_name, task in self.worker_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        self.logger.info(f"Worker {worker_name} cancelled")

            self.worker_tasks.clear()
            self.logger.info("All workers stopped")

        except Exception as e:
            self.logger.error(f"Error stopping workers: {e}")

    async def _process_crawler_jobs(self) -> None:
        """크롤링 작업 처리"""
        while self.is_running:
            try:
                jobs = await redis_helper.get_pending_jobs("crawler_stream", count=1)

                for job_data in jobs:
                    await self._handle_crawler_job(job_data)

                await asyncio.sleep(5)  # 5초 대기

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in crawler worker: {e}")
                await asyncio.sleep(10)

    async def _process_mapping_jobs(self) -> None:
        """매핑 작업 처리"""
        while self.is_running:
            try:
                jobs = await redis_helper.get_pending_jobs("mapping_stream", count=1)

                for job_data in jobs:
                    await self._handle_mapping_job(job_data)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in mapping worker: {e}")
                await asyncio.sleep(10)

    async def _process_dart_extract_jobs(self) -> None:
        """DART 추출 작업 처리"""
        while self.is_running:
            try:
                jobs = await redis_helper.get_pending_jobs("dart_extract_stream", count=1)

                for job_data in jobs:
                    await self._handle_dart_extract_job(job_data)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in DART extract worker: {e}")
                await asyncio.sleep(10)

    async def _process_standardize_jobs(self) -> None:
        """표준화 작업 처리"""
        while self.is_running:
            try:
                jobs = await redis_helper.get_pending_jobs("standardize_stream", count=1)

                for job_data in jobs:
                    await self._handle_standardize_job(job_data)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in standardize worker: {e}")
                await asyncio.sleep(10)

    async def _handle_crawler_job(self, job_data: Dict[str, Any]) -> None:
        """크롤링 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            self.logger.info(f"Processing crawler job: {job_id}")

            max_pages = job_data.get("max_pages", 5)
            result = await self.crawler_service.start_saramin_crawling(max_pages)

            # 결과 저장
            await redis_helper.update_job_status(job_id, "completed", result)

        except Exception as e:
            self.logger.error(f"Failed to process crawler job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_mapping_job(self, job_data: Dict[str, Any]) -> None:
        """매핑 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            self.logger.info(f"Processing mapping job: {job_id}")

            limit = job_data.get("limit", 10)
            result = await self.company_mapper.batch_process_mappings(limit)

            await redis_helper.update_job_status(job_id, "completed", result)

        except Exception as e:
            self.logger.error(f"Failed to process mapping job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_dart_extract_job(self, job_data: Dict[str, Any]) -> None:
        """DART 추출 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            self.logger.info(f"Processing DART extract job: {job_id}")

            corp_code = job_data.get("corp_code")
            year = job_data.get("year")

            result = await self.dart_extractor.extract_company_annual_report(
                corp_code=corp_code,
                year=year
            )

            await redis_helper.update_job_status(job_id, "completed", result)

        except Exception as e:
            self.logger.error(f"Failed to process DART extract job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_standardize_job(self, job_data: Dict[str, Any]) -> None:
        """표준화 작업 처리"""
        job_id = job_data.get("job_id")
        try:
            self.logger.info(f"Processing standardize job: {job_id}")

            text_id = job_data.get("text_id")
            content = job_data.get("content", "")
            title = job_data.get("title", "")

            if content:
                # 분류 및 표준화 수행
                category, standardized_content = await self.text_processor.classify_and_standardize(
                    title=title,
                    content=content
                )

                result = {
                    "text_id": text_id,
                    "category": category,
                    "standardized_content": standardized_content,
                    "processing_time": datetime.now().isoformat()
                }

                await redis_helper.update_job_status(job_id, "completed", result)
            else:
                await redis_helper.update_job_status(job_id, "failed", {"error": "No content provided"})

        except Exception as e:
            self.logger.error(f"Failed to process standardize job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    def get_worker_status(self) -> Dict[str, Any]:
        """워커 상태 반환"""
        return {
            "is_running": self.is_running,
            "active_workers": list(self.worker_tasks.keys()),
            "worker_count": len(self.worker_tasks),
            "services": {
                "text_processor": self.text_processor.get_status() if self.text_processor else None,
                "company_mapper": self.company_mapper.get_status() if self.company_mapper else None,
                "dart_extractor": self.dart_extractor.get_status() if self.dart_extractor else None,
                "crawler_service": self.crawler_service.get_status() if self.crawler_service else None
            }
        }

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        base_status = super().get_status()
        base_status.update(self.get_worker_status())
        return base_status