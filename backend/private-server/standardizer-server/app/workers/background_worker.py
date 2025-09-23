"""
백그라운드 워커 시스템 - 완전한 파이프라인
크롤링 → 매핑 → DART 추출 → 표준화
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .. import config
from ..database import SessionLocal
from ..models.crawler_models import CompanyDartMapping, MappingStatus
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

                for job_item in jobs:
                    await self._handle_crawler_job(job_item)

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

                for job_item in jobs:
                    await self._handle_mapping_job(job_item)

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

                for job_item in jobs:
                    await self._handle_dart_extract_job(job_item)

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

                for job_item in jobs:
                    await self._handle_standardize_job(job_item)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in standardize worker: {e}")
                await asyncio.sleep(10)

    async def _handle_crawler_job(self, job_item: Dict[str, Any]) -> None:
        """크롤링 작업 처리"""
        job_data = job_item["data"]
        stream_id = job_item["stream_id"]
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
                    "limit": 1000,
                    "submitted_at": datetime.now().isoformat()
                }

                await redis_helper.add_job("mapping_stream", mapping_job_data)
                logger.info(f"✅ Auto-mapping job queued: auto_mapping_{job_id}")

            # 작업 완료 확인
            await redis_helper.ack_job(stream_id)

        except Exception as e:
            logger.error(f"Failed to process crawler job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_mapping_job(self, job_item: Dict[str, Any]) -> None:
        """매핑 작업 처리"""
        job_data = job_item["data"]
        stream_id = job_item["stream_id"]
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing mapping job: {job_id}")

            limit = job_data.get("limit", 1000)
            result = await self.company_mapper.batch_process_mappings(limit)

            await redis_helper.update_job_status(job_id, "completed", result)

            # 매핑 성공한 회사들에 대해 자동으로 DART 문서 추출 시작
            total_mapped = result.get("suggested", 0) + result.get("verified", 0)
            if total_mapped > 0:
                logger.info(f"🎯 {total_mapped} companies mapped successfully (verified: {result.get('verified', 0)}, suggested: {result.get('suggested', 0)}). Starting DART extraction...")

                # 성공적으로 매핑된 회사들 가져오기
                db = SessionLocal()
                try:
                    # 신뢰도 95% 이상 또는 verified 상태인 회사들만 자동 추출
                    high_confidence_mappings = db.query(CompanyDartMapping).filter(
                        CompanyDartMapping.mapping_status.in_([MappingStatus.suggested, MappingStatus.verified]),
                        CompanyDartMapping.confidence_score >= 95,
                        CompanyDartMapping.dart_corp_code.isnot(None)
                    ).all()

                    for mapping in high_confidence_mappings:
                        # DART 추출 작업 큐에 추가
                        dart_job_data = {
                            "job_id": f"dart_extract_{mapping.mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            "mapping_id": mapping.mapping_id,
                            "company_name": mapping.crawled_company_name,
                            "dart_corp_name": mapping.dart_corp_name,  # DART 정식 기업명 사용
                            "dart_corp_code": mapping.dart_corp_code,
                            "report_type": "annual",
                            "submitted_at": datetime.now().isoformat()
                        }

                        await redis_helper.add_job("dart_extract_stream", dart_job_data)
                        logger.info(f"📄 DART extraction queued for {mapping.crawled_company_name} → {mapping.dart_corp_name} (Code: {mapping.dart_corp_code})")

                finally:
                    db.close()

            # 작업 완료 확인
            await redis_helper.ack_job(stream_id)

        except Exception as e:
            logger.error(f"Failed to process mapping job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_dart_extract_job(self, job_item: Dict[str, Any]) -> None:
        """DART 추출 작업 처리"""
        job_data = job_item["data"]
        stream_id = job_item["stream_id"]
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing DART extract job: {job_id}")

            dart_corp_name = job_data.get("dart_corp_name")
            company_name = job_data.get("company_name")
            mapping_id = job_data.get("mapping_id")

            if not self.dart_extractor:
                raise Exception("DART extractor not available")

            if not dart_corp_name:
                raise Exception(f"No DART corp name provided for {company_name}")

            # 중복 방지: 이미 추출된 mapping_id인지 확인
            if mapping_id:
                existing_status = await redis_helper.get_job_status(f"dart_extract_{mapping_id}")
                if existing_status and existing_status.get("status") == "completed":
                    logger.info(f"⏭️ DART extraction already completed for mapping_id {mapping_id}, skipping")
                    await redis_helper.ack_job(stream_id)
                    return

            logger.info(f"🔍 Extracting DART report for: {dart_corp_name}")

            # DART extractor는 sync 메서드이므로 asyncio.to_thread 사용
            extracted_content = await asyncio.to_thread(
                self.dart_extractor.extract_company_report_to_text,
                dart_corp_name
            )

            result = {
                "status": "extracted" if extracted_content else "failed",
                "content": extracted_content,
                "dart_corp_name": dart_corp_name,
                "dart_corp_code": job_data.get("dart_corp_code"),
                "extracted_at": datetime.now().isoformat()
            }

            # 일반 job_id와 mapping_id 기반 상태 모두 저장
            await redis_helper.update_job_status(job_id, "completed", result)
            if mapping_id:
                await redis_helper.update_job_status(f"dart_extract_{mapping_id}", "completed", result)

            # DART 추출 성공 시 자동으로 표준화 작업 시작
            if extracted_content:
                logger.info(f"📄 DART extraction completed for {job_data.get('company_name')} ({len(extracted_content):,} chars). Starting standardization...")

                # 표준화 작업을 Redis 스트림에 추가
                standardize_job_data = {
                    "job_id": f"standardize_{job_data.get('mapping_id')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "mapping_id": job_data.get("mapping_id"),
                    "company_name": job_data.get("company_name"),
                    "dart_content": extracted_content,
                    "submitted_at": datetime.now().isoformat()
                }

                await redis_helper.add_job("standardize_stream", standardize_job_data)
                logger.info(f"📝 Standardization job queued for {job_data.get('company_name')}")
            else:
                logger.warning(f"❌ DART extraction failed for {job_data.get('company_name')} - no content extracted")

            # 작업 완료 확인
            await redis_helper.ack_job(stream_id)

        except Exception as e:
            logger.error(f"Failed to process DART extract job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    async def _handle_standardize_job(self, job_item: Dict[str, Any]) -> None:
        """표준화 작업 처리"""
        job_data = job_item["data"]
        stream_id = job_item["stream_id"]
        job_id = job_data.get("job_id")
        try:
            logger.info(f"Processing standardize job: {job_id}")

            content = job_data.get("dart_content", "")
            title = job_data.get("company_name", "")
            mapping_id = job_data.get("mapping_id")

            # 중복 방지: 이미 표준화된 mapping_id인지 확인
            if mapping_id:
                existing_status = await redis_helper.get_job_status(f"standardize_{mapping_id}")
                if existing_status and existing_status.get("status") == "completed":
                    logger.info(f"⏭️ Standardization already completed for mapping_id {mapping_id}, skipping")
                    await redis_helper.ack_job(stream_id)
                    return

            if content:
                # DART 문서 전체를 5개 카테고리로 분류 및 표준화
                categorized_sections = await self.standardizer_service.classify_and_standardize_all_sections(
                    company_name=title,
                    content=content
                )

                # 각 카테고리별로 파일 저장 및 Summary 서버 전송
                file_paths = {}
                mapping_id = job_data.get("mapping_id")

                for category, standardized_content in categorized_sections.items():
                    if standardized_content:  # 내용이 있는 카테고리만 처리
                        # 카테고리별 파일 저장
                        file_path = self._save_standardized_content(
                            job_id=job_id,
                            mapping_id=mapping_id,
                            company_name=title,
                            category=category,
                            content=standardized_content
                        )
                        file_paths[category] = file_path

                        logger.info(f"📁 Category '{category}' saved: {len(standardized_content)} chars to {file_path}")

                        # 각 카테고리별로 Summary 서버에 작업 전송
                        category_result = {
                            "mapping_id": mapping_id,
                            "category": category,
                            "standardized_content": standardized_content,
                            "file_path": file_path,
                            "processing_time": datetime.now().isoformat()
                        }
                        await self._trigger_summary_server(job_data, category_result)

                # 전체 작업 결과
                result = {
                    "mapping_id": mapping_id,
                    "categories_processed": ", ".join(file_paths.keys()),  # list를 문자열로 변환
                    "categories_count": len(file_paths),
                    "file_paths": ", ".join(f"{k}:{v}" for k, v in file_paths.items()),  # dict를 문자열로 변환
                    "processing_time": datetime.now().isoformat()
                }

                # 일반 job_id와 mapping_id 기반 상태 모두 저장
                await redis_helper.update_job_status(job_id, "completed", result)
                if mapping_id:
                    await redis_helper.update_job_status(f"standardize_{mapping_id}", "completed", result)
                logger.info(f"✅ Standardization completed for {title}: {len(file_paths)} categories processed")
            else:
                await redis_helper.update_job_status(job_id, "failed", {"error": "No content provided"})

            # 작업 완료 확인
            await redis_helper.ack_job(stream_id)

        except Exception as e:
            logger.error(f"Failed to process standardize job {job_id}: {e}")
            await redis_helper.update_job_status(job_id, "failed", {"error": str(e)})

    def _save_standardized_content(self, job_id: str, mapping_id: str, company_name: str, category: str, content: str) -> str:
        """
        표준화된 내용을 파일로 저장하고 경로 반환

        Args:
            job_id: 작업 ID
            mapping_id: 매핑 ID
            company_name: 회사명
            category: 카테고리
            content: 표준화된 내용

        Returns:
            str: 저장된 파일 경로
        """
        # FileManager에서 카테고리별 파일로 저장
        self.file_manager.append_to_category_file(
            job_id=f"mapping_{mapping_id}",  # mapping_id 기반 디렉토리 사용
            category=category,
            title=company_name,
            content=content
        )

        # 파일 경로 반환
        job_path = self.file_manager.get_job_path(f"mapping_{mapping_id}")
        standardized_path = job_path / "standardized"

        category_files = {
            'business_overview': 'business_overview.txt',
            'products_services': 'products_services.txt',
            'revenue_orders': 'revenue_orders.txt',
            'contracts_rnd': 'contracts_rnd.txt',
            'other_references': 'other_references.txt'
        }

        file_name = category_files.get(category, 'other_references.txt')
        file_path = str(standardized_path / file_name)

        return file_path

    async def _trigger_summary_server(self, job_data: Dict, standardization_result: Dict):
        """Summary 서버로 표준화 완료 데이터 전달"""
        try:
            summary_job_data = {
                "job_id": f"summary_{job_data.get('mapping_id')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "company_name": job_data.get("company_name"),
                "file_path": standardization_result.get("file_path"),  # file_path로 변경
                "category": standardization_result.get("category"),
                "mapping_id": job_data.get("mapping_id"),
                "submitted_at": datetime.now().isoformat()
            }

            # Summary 서버의 Redis 스트림에 작업 추가
            await redis_helper.add_job("stream:summary", summary_job_data)

            logger.info(f"📊 Summary job queued for {job_data.get('company_name')} with file: {standardization_result.get('file_path')}")
            logger.info(f"🎉 Complete pipeline finished: Crawling → Mapping → DART → Standardization → Summary")

        except Exception as e:
            logger.error(f"Failed to trigger summary server: {e}")
            # Summary 실패해도 표준화는 성공으로 처리

    def get_status(self) -> Dict[str, Any]:
        """워커 상태 반환"""
        return {
            "running": self.running,
            "active_workers": ", ".join(self.worker_tasks.keys()),
            "worker_count": len(self.worker_tasks),
            "services": {
                "standardizer": "initialized" if self.standardizer_service else "not_initialized",
                "dart_extractor": "initialized" if self.dart_extractor else "not_initialized",
                "company_mapper": "initialized" if self.company_mapper else "not_initialized",
                "crawler_service": "initialized" if self.crawler_service else "not_initialized"
            }
        }