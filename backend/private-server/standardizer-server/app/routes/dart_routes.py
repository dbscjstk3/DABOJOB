"""
DART 문서 처리 관련 API 엔드포인트
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..models.dart_models import DartExtractRequest
from ..services.dart_extractor import DartDocumentExtractor
from ..services.redis_client import RedisClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dart", tags=["dart"])

# 서비스 인스턴스
dart_extractor = None
redis_client = RedisClient()


def get_dart_extractor():
    """DART Extractor 인스턴스 반환"""
    global dart_extractor
    if not dart_extractor:
        dart_api_key = os.getenv('DART_API_KEY')
        if dart_api_key:
            dart_extractor = DartDocumentExtractor(dart_api_key)
            logger.info("DART extractor initialized")
        else:
            logger.warning("DART_API_KEY not found - DART extraction features disabled")
    return dart_extractor


@router.post("/subsections-async")
async def extract_dart_subsections_async(request: DartExtractRequest) -> dict:
    """DART 문서를 소제목별로 구조화하여 추출 (비동기)"""
    extractor = get_dart_extractor()
    if not extractor:
        raise HTTPException(status_code=503, detail="DART extraction service not available")
    
    try:
        job_id = str(request.mapping_id)
        logger.info(f"Processing async DART extraction: mapping_id={job_id}, company={request.company_name}")
        
        # Redis에 작업 상태 초기화
        await redis_client.initialize()
        await redis_client.update_job_status(job_id, "pending")
        
        # 작업 데이터 준비
        job_data = {
            "job_id": job_id,
            "mapping_id": request.mapping_id,
            "company_name": request.company_name,
            "report_type": request.report_type,
            "submitted_at": datetime.now().isoformat()
        }
        
        # Redis Stream에 작업 제출
        stream_id = await redis_client.submit_job(job_data)
        
        logger.info(f"Async job submitted: {job_id}, stream_id: {stream_id}")
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job submitted successfully",
            "stream_id": stream_id
        }
        
    except Exception as e:
        logger.error(f"Failed to submit async job: {e}")
        raise HTTPException(status_code=500, detail=str(e))