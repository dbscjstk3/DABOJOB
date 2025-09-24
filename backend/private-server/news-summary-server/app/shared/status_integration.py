"""
News-Summary Server 상태 통합 모듈
기존 로직을 건드리지 않고 상태 관리만 추가
"""
import logging
from typing import Dict, Any, Optional
from .status_manager import SharedStatusManager, JobStage, JobStatus

logger = logging.getLogger(__name__)

class NewsStatusIntegration:
    def __init__(self):
        self.status_manager = SharedStatusManager()
        self.initialized = False

    async def initialize(self):
        """초기화 (실패해도 메인 로직에 영향 없음)"""
        try:
            await self.status_manager.initialize()
            self.initialized = True
            logger.info("NewsStatusIntegration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize status integration: {e}")
            self.initialized = False

    async def update_news_status(
        self,
        mapping_id: int,
        status: JobStatus,
        articles_count: Optional[int] = None,
        hashtags_count: Optional[int] = None,
        s3_key: Optional[str] = None,
        error_message: Optional[str] = None,
        chapters_completed: Optional[int] = None
    ):
        """뉴스 상태 업데이트 (비동기, 실패해도 메인 로직 영향 없음)"""
        if not self.initialized:
            return

        try:
            data = {}
            if articles_count is not None:
                data["articles_count"] = articles_count
            if hashtags_count is not None:
                data["hashtags_count"] = hashtags_count
            if s3_key:
                data["s3_key"] = s3_key
                data["s3_uploaded"] = True
            if error_message:
                data["error_message"] = error_message
            if chapters_completed is not None:
                data["chapters_completed"] = chapters_completed
                data["total_chapters"] = 5
                data["progress_percent"] = (chapters_completed / 5) * 100

            await self.status_manager.update_job_status(
                mapping_id=mapping_id,
                stage=JobStage.NEWS,
                status=status,
                data=data,
                service_name="news_summary_server"
            )
        except Exception as e:
            logger.error(f"Failed to update news status (non-critical): {e}")

    async def get_job_status(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        if not self.initialized:
            return None

        try:
            return await self.status_manager.get_job_status(mapping_id)
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def close(self):
        """연결 종료"""
        try:
            await self.status_manager.close()
        except:
            pass

# 전역 인스턴스
news_status = NewsStatusIntegration()