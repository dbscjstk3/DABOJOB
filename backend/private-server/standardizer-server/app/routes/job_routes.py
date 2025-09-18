"""
작업(Job) 관련 API 엔드포인트
핵심 파이프라인에 필요한 API만 유지
"""
import logging
from fastapi import APIRouter, HTTPException
from ..utils.redis_helper import redis_helper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """작업 상태 조회 - 파이프라인 진행 상황 확인용"""
    try:
        status = await redis_helper.get_job_status(job_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {
            "job_id": job_id,
            "status": status.get("status", "unknown"),
            "current_step": status.get("current_step"),
            "total_steps": status.get("total_steps"),
            "updated_at": status.get("updated_at"),
            "error": status.get("error"),
            "details": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 기타 디버그용 API들은 제거됨 - 핵심 파이프라인에만 집중
# GET /jobs - 작업 목록 조회 (불필요)
# GET /jobs/{job_id} - 작업 상세 조회 (불필요)
# GET /jobs/{job_id}/raw - 원본 데이터 조회 (디버그용)
# GET /jobs/{job_id}/standardized - 표준화 데이터 조회 (디버그용)
# GET /jobs/{job_id}/categorized - 분류 데이터 조회 (디버그용)