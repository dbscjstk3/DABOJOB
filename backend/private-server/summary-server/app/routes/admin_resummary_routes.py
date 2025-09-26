"""
재요약 트리거 API - 단순 버전
POST /admin/resummary/trigger/{mapping_id} 하나만
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from ..services.resummary_service import ResummaryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/resummary", tags=["Admin Resummary"])

class ResummaryTriggerRequest(BaseModel):
    """재요약 요청 (선택사항)"""
    reason: Optional[str] = "Manual resummary request"
    requested_by: Optional[str] = "Admin"

@router.post("/trigger/{mapping_id}")
async def trigger_resummary(
    mapping_id: int,
    background_tasks: BackgroundTasks,
    request: Optional[ResummaryTriggerRequest] = None
):
    """재요약 수동 요청 - 핵심 기능만"""
    try:
        # request가 없으면 기본값 사용
        if request is None:
            request = ResummaryTriggerRequest()

        # 백그라운드에서 재요약 처리
        async def process_resummary():
            try:
                service = ResummaryService()
                await service.trigger_resummary(
                    mapping_id=mapping_id,
                    reason=request.reason,
                    requested_by=request.requested_by
                )
                logger.info(f"Resummary completed for mapping_id: {mapping_id}")
            except Exception as e:
                logger.error(f"Background resummary failed: {e}")

        # 백그라운드 태스크 추가
        background_tasks.add_task(process_resummary)

        # 즉시 응답 반환
        return {
            "success": True,
            "status": "queued",
            "mapping_id": mapping_id,
            "message": f"Re-summarization queued for mapping {mapping_id}"
        }

    except Exception as e:
        logger.error(f"Failed to trigger resummary: {e}")
        raise HTTPException(status_code=500, detail=str(e))