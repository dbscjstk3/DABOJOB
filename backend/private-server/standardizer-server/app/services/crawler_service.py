"""
크롤링 서비스
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


class CrawlerService:
    """크롤링 서비스"""

    def __init__(self):
        self.executor: Optional[ThreadPoolExecutor] = None
        self.is_crawling: bool = False

    async def initialize(self) -> None:
        """크롤러 초기화"""
        try:
            self.executor = ThreadPoolExecutor(max_workers=2)
            logger.info("Crawler service initialized")
        except Exception as e:
            raise Exception(f"Failed to initialize crawler: {e}")

    async def shutdown(self) -> None:
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
            logger.info(f"Starting Saramin crawling (max_pages: {max_pages})")

            # SaraminCrawler를 사용한 실제 크롤링
            from ..crawlers.saramin_crawler import SaraminCrawler
            from ..database import SessionLocal

            db = SessionLocal()
            try:
                crawler = SaraminCrawler(db_session=db)
                result = crawler.crawl(max_pages=max_pages)

                if result:
                    return {
                        "status": "completed",
                        "companies_found": result.get("companies_saved", 0),
                        "jobs_found": result.get("jobs_saved", 0),
                        "message": f"크롤링 완료: {result.get('companies_saved', 0)}개 회사, {result.get('jobs_saved', 0)}개 공고",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "failed",
                        "message": "크롤링 실패",
                        "timestamp": datetime.now().isoformat()
                    }

            finally:
                db.close()
                self.is_crawling = False

        except Exception as e:
            self.is_crawling = False
            logger.error(f"Failed to start Saramin crawling: {e}")
            return {
                "status": "failed",
                "message": f"크롤링 오류: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        return {
            "service": "CrawlerService",
            "is_crawling": self.is_crawling,
            "executor_available": self.executor is not None
        }