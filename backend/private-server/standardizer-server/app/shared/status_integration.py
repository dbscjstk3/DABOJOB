"""
Standardizer Server 상태 통합 모듈
기존 로직을 건드리지 않고 상태 관리만 추가
"""
import logging
from typing import Dict, Any, Optional
from .status_manager import SharedStatusManager, JobStage, JobStatus

logger = logging.getLogger(__name__)

class StandardizerStatusIntegration:
    def __init__(self):
        self.status_manager = SharedStatusManager()
        self.initialized = False

    async def initialize(self):
        """초기화 (실패해도 메인 로직에 영향 없음)"""
        try:
            await self.status_manager.initialize()
            self.initialized = True
            logger.info("StandardizerStatusIntegration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize status integration: {e}")
            self.initialized = False

    async def update_mapping_status(
        self,
        mapping_id: int,
        status: JobStatus,
        confidence_score: Optional[int] = None,
        dart_corp_code: Optional[str] = None,
        dart_corp_name: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """매핑 상태 업데이트 (비동기, 실패해도 메인 로직 영향 없음)"""
        if not self.initialized:
            return

        try:
            data = {}
            if confidence_score is not None:
                data["confidence_score"] = confidence_score
            if dart_corp_code:
                data["dart_corp_code"] = dart_corp_code
            if dart_corp_name:
                data["dart_corp_name"] = dart_corp_name
            if error_message:
                data["error_message"] = error_message

            await self.status_manager.update_job_status(
                mapping_id=mapping_id,
                stage=JobStage.MAPPING,
                status=status,
                data=data,
                service_name="standardizer_server"
            )
        except Exception as e:
            logger.error(f"Failed to update mapping status (non-critical): {e}")

    async def get_job_status(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        if not self.initialized:
            return None

        try:
            return await self.status_manager.get_job_status(mapping_id)
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드 통계 조회"""
        if not self.initialized:
            return {"total": 0, "error": "Status manager not initialized"}

        try:
            return await self.status_manager.get_dashboard_stats()
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {"total": 0, "error": str(e)}

    async def close(self):
        """연결 종료"""
        try:
            await self.status_manager.close()
        except:
            pass

# 전역 인스턴스
standardizer_status = StandardizerStatusIntegration()