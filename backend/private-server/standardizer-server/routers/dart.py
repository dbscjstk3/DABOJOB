"""
DART 문서 처리 관련 API 라우터
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from utils.logger import get_logger
from utils.redis_helper import redis_helper

logger = get_logger(__name__)
router = APIRouter(prefix="/api/dart", tags=["DART Documents"])


class DartExtractRequest(BaseModel):
    """DART 추출 요청"""
    mapping_id: int
    company_name: str
    corp_code: str
    report_type: str = "annual"


@router.post("/extract")
async def extract_dart_document(
    request: DartExtractRequest,
    background_tasks: BackgroundTasks
):
    """DART 문서 추출 작업 시작"""
    try:
        job_id = f"dart_extract_{request.mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Redis에 작업 정보 추가
        job_data = {
            "job_id": job_id,
            "mapping_id": request.mapping_id,
            "company_name": request.company_name,
            "corp_code": request.corp_code,
            "report_type": request.report_type,
            "status": "pending",
            "submitted_at": datetime.now().isoformat()
        }

        await redis_helper.add_job("dart_extract_stream", job_data)

        return {
            "job_id": job_id,
            "status": "submitted",
            "message": f"{request.company_name} DART 문서 추출 작업이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to submit DART extraction job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_extraction_status(job_id: str):
    """DART 추출 작업 상태 조회"""
    try:
        # TODO: Redis에서 작업 상태 조회
        # status = await redis_helper.get_job_status(job_id)

        return {
            "job_id": job_id,
            "status": "pending",  # TODO: 실제 상태 조회
            "message": "작업 상태 조회 중...",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get extraction status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_extraction_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = None
):
    """DART 추출 작업 목록 조회"""
    try:
        # TODO: Redis/DB에서 작업 목록 조회
        jobs = await redis_helper.get_pending_jobs(limit)

        if status:
            jobs = [job for job in jobs if job.get("status") == status]

        return {
            "total": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Failed to get extraction jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/standardize")
async def standardize_text(
    text_id: int,
    background_tasks: BackgroundTasks
):
    """텍스트 표준화 작업 시작"""
    try:
        job_id = f"standardize_{text_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job_data = {
            "job_id": job_id,
            "text_id": text_id,
            "task_type": "standardize",
            "status": "pending",
            "submitted_at": datetime.now().isoformat()
        }

        await redis_helper.add_job("standardize_stream", job_data)

        return {
            "job_id": job_id,
            "status": "submitted",
            "message": "텍스트 표준화 작업이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to submit standardization job: {e}")
        raise HTTPException(status_code=500, detail=str(e))