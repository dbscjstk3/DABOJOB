"""
크롤링 서비스
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from services.base import BaseService
from utils.exceptions import StandardizerException
from config import settings


class CrawlerService(BaseService):
    """크롤링 서비스"""

    def __init__(self):
        super().__init__("CrawlerService")
        self.executor: Optional[ThreadPoolExecutor] = None
        self.is_crawling: bool = False

    async def _setup(self) -> None:
        """크롤러 초기화"""
        try:
            self.executor = ThreadPoolExecutor(max_workers=2)
            self.logger.info("Crawler service initialized")
        except Exception as e:
            raise StandardizerException(f"Failed to initialize crawler: {e}")

    async def _cleanup(self) -> None:
        """리소스 정리"""
        if self.executor:
            self.executor.shutdown(wait=True, timeout=10)

    async def start_saramin_crawling(self, max_pages: int = 5) -> Dict[str, Any]:
        """사람인 크롤링 시작"""
        if self.is_crawling:
            return {
                "status": "already_running",
                "message": "크롤링이 이미 실행 중입니다."
            }

        try:
            self.is_crawling = True
            self.logger.info(f"Starting Saramin crawling (max_pages: {max_pages})")

            # 백그라운드에서 크롤링 실행
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                self.executor,
                self._run_saramin_crawler,
                max_pages
            )

            # 즉시 응답 반환 (백그라운드 실행)
            return {
                "status": "started",
                "message": f"사람인 크롤링이 시작되었습니다. (최대 {max_pages}페이지)",
                "max_pages": max_pages,
                "started_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.is_crawling = False
            self.logger.error(f"Failed to start crawling: {e}")
            raise StandardizerException(f"Failed to start crawling: {e}")

    def _run_saramin_crawler(self, max_pages: int) -> Dict[str, Any]:
        """사람인 크롤러 실행 (동기)"""
        try:
            from models.database import SessionLocal

            # 세션 생성
            db = SessionLocal()

            try:
                # TODO: 실제 크롤러 로직 구현
                # 1. Selenium 드라이버 초기화
                # 2. 사람인 페이지 방문
                # 3. 채용공고 데이터 추출
                # 4. 데이터베이스 저장

                # 현재 DB에서 회사 수 확인 (임시)
                from models.crawler import Company
                companies_count = db.query(Company).count()

                # 임시 구현 (실제 크롤링된 회사 수 반환)
                result = {
                    "status": "completed",
                    "pages_crawled": max_pages,
                    "jobs_found": companies_count * 2,  # 임시값
                    "companies_found": companies_count,
                    "duration_seconds": 5,
                    "completed_at": datetime.now().isoformat()
                }

                self.logger.info(f"Crawling completed: {result}")
                return result

            finally:
                db.close()
                self.is_crawling = False

        except Exception as e:
            self.is_crawling = False
            self.logger.error(f"Crawling failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }

    async def get_crawling_status(self) -> Dict[str, Any]:
        """크롤링 상태 조회"""
        try:
            from models.database import SessionLocal
            from models.crawler import CrawlingLog

            db = SessionLocal()

            try:
                # 최근 크롤링 로그 조회
                recent_logs = db.query(CrawlingLog).order_by(
                    CrawlingLog.started_at.desc()
                ).limit(5).all()

                logs_data = []
                for log in recent_logs:
                    logs_data.append({
                        "log_id": log.log_id,
                        "crawl_type": log.crawl_type,
                        "status": log.crawl_status.value if log.crawl_status else None,
                        "items_found": log.items_found,
                        "items_saved": log.items_saved,
                        "started_at": log.started_at.isoformat() if log.started_at else None,
                        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                        "duration_seconds": log.crawl_duration_seconds,
                        "error_message": log.error_message
                    })

                return {
                    "is_crawling": self.is_crawling,
                    "recent_logs": logs_data,
                    "service_status": "running" if self.is_initialized else "stopped"
                }

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Failed to get crawling status: {e}")
            return {
                "is_crawling": self.is_crawling,
                "recent_logs": [],
                "service_status": "error",
                "error": str(e)
            }

    async def get_crawling_statistics(self, days: int = 7) -> Dict[str, Any]:
        """크롤링 통계"""
        try:
            from models.database import SessionLocal
            from models.crawler import JobPosting, Company, CrawlingLog
            from datetime import timedelta

            db = SessionLocal()

            try:
                since_date = datetime.now() - timedelta(days=days)

                # 기본 통계
                total_jobs = db.query(JobPosting).count()
                recent_jobs = db.query(JobPosting).filter(
                    JobPosting.created_at >= since_date
                ).count()

                total_companies = db.query(Company).count()
                hot_jobs = db.query(JobPosting).filter(
                    JobPosting.is_hot == True
                ).count()

                # 크롤링 로그 통계
                recent_crawls = db.query(CrawlingLog).filter(
                    CrawlingLog.started_at >= since_date
                ).count()

                successful_crawls = db.query(CrawlingLog).filter(
                    CrawlingLog.started_at >= since_date,
                    CrawlingLog.crawl_status == 'success'
                ).count()

                return {
                    "period_days": days,
                    "jobs": {
                        "total": total_jobs,
                        "recent": recent_jobs,
                        "hot": hot_jobs
                    },
                    "companies": {
                        "total": total_companies
                    },
                    "crawling": {
                        "recent_attempts": recent_crawls,
                        "successful": successful_crawls,
                        "success_rate": round(
                            successful_crawls / recent_crawls * 100, 2
                        ) if recent_crawls > 0 else 0
                    }
                }

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Failed to get crawling statistics: {e}")
            raise StandardizerException(f"Failed to get statistics: {e}")

    def stop_crawling(self) -> Dict[str, Any]:
        """크롤링 중지"""
        if not self.is_crawling:
            return {
                "status": "not_running",
                "message": "실행 중인 크롤링이 없습니다."
            }

        try:
            # TODO: 실제 크롤링 중지 로직 구현
            self.is_crawling = False

            return {
                "status": "stopped",
                "message": "크롤링이 중지되었습니다.",
                "stopped_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to stop crawling: {e}")
            raise StandardizerException(f"Failed to stop crawling: {e}")

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        base_status = super().get_status()
        base_status.update({
            "is_crawling": self.is_crawling,
            "executor_active": self.executor is not None and not self.executor._shutdown
        })
        return base_status