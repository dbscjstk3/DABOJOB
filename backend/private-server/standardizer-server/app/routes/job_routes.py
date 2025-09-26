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


@router.get("/{job_id}/categorized")
async def get_categorized_files(job_id: str):
    """카테고리별 표준화된 파일 내용 조회"""
    try:
        from ..services.file_manager import FileManager

        file_manager = FileManager()
        categorized_files = file_manager.get_categorized_files(job_id)

        if not categorized_files:
            raise HTTPException(status_code=404, detail=f"No categorized files found for job {job_id}")

        # 각 카테고리별 통계 추가
        stats = {}
        for category, content in categorized_files.items():
            # content가 None일 경우 빈 문자열로 처리
            if content is None:
                content = ""
                categorized_files[category] = ""  # None을 빈 문자열로 교체

            stats[category] = {
                "length": len(content),
                "exists": bool(content),
                "preview": content[:200] + "..." if len(content) > 200 else content
            }

        return {
            "job_id": job_id,
            "categorized_files": categorized_files,
            "stats": stats,
            "total_categories": len([c for c in categorized_files.values() if c])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get categorized files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 기타 디버그용 API들은 제거됨 - 핵심 파이프라인에만 집중