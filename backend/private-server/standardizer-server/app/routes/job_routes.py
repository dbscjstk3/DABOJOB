"""
작업(Job) 관련 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException
from ..services.file_manager import FileManager
from ..services.redis_client import RedisClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

# 서비스 인스턴스
file_manager = FileManager()
redis_client = RedisClient()


@router.get("")
def list_jobs():
    """모든 작업 목록 조회"""
    try:
        jobs = file_manager.list_jobs()
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
def get_job_status(job_id: str):
    """특정 작업 상태 조회"""
    try:
        status = file_manager.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/status")
async def get_job_status_redis(job_id: str):
    """Redis에서 작업 상태 조회"""
    try:
        # Redis에서 상태 조회
        redis_status = await redis_client.get_job_status(job_id)
        
        # 파일 시스템에서 상태 조회
        file_status = file_manager.get_job_status(job_id)
        
        # 두 정보 병합
        combined_status = {
            "job_id": job_id,
            "redis_status": redis_status,
            "file_status": file_status
        }
        
        if not redis_status and not file_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return combined_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/raw")
def get_raw_data(job_id: str):
    """작업의 원본 데이터 조회 (파일 내용 포함)"""
    try:
        if not file_manager.job_exists(job_id):
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # raw 디렉토리의 모든 파일 내용 읽기
        job_path = file_manager.get_job_path(job_id)
        raw_path = job_path / "raw"
        
        if not raw_path.exists():
            return {"job_id": job_id, "raw_files": {}}
        
        raw_files = {}
        for file_path in raw_path.iterdir():
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    raw_files[file_path.name] = content
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    raw_files[file_path.name] = f"Error reading file: {e}"
        
        metadata = file_manager.load_metadata(job_id)
        
        return {
            "job_id": job_id,
            "metadata": metadata,
            "raw_files": raw_files,
            "file_count": len(raw_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/standardized")
def get_standardized_data(job_id: str):
    """작업의 표준화된 데이터 조회 (파일 내용 포함)"""
    try:
        if not file_manager.job_exists(job_id):
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # standardized 디렉토리의 모든 파일 내용 읽기
        job_path = file_manager.get_job_path(job_id)
        standardized_path = job_path / "standardized"
        
        if not standardized_path.exists():
            return {"job_id": job_id, "standardized_files": {}}
        
        standardized_files = {}
        for file_path in standardized_path.iterdir():
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    standardized_files[file_path.name] = content
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    standardized_files[file_path.name] = f"Error reading file: {e}"
        
        metadata = file_manager.load_metadata(job_id)
        
        return {
            "job_id": job_id,
            "metadata": metadata,
            "standardized_files": standardized_files,
            "file_count": len(standardized_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get standardized data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/categorized")
def get_categorized_data(job_id: str):
    """카테고리별로 분류된 데이터 조회"""
    try:
        if not file_manager.job_exists(job_id):
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # 카테고리별 파일 내용 조회
        categorized_files = file_manager.get_categorized_files(job_id)
        
        # 각 카테고리별 챕터 수와 크기 계산
        category_stats = {}
        for category, content in categorized_files.items():
            if content:
                # 챕터 구분자로 챕터 수 계산
                chapter_count = content.count('===') // 2  # 시작과 끝 === 쌍
                category_stats[category] = {
                    "chapters": chapter_count,
                    "size": len(content),
                    "exists": True
                }
            else:
                category_stats[category] = {
                    "chapters": 0,
                    "size": 0,
                    "exists": False
                }
        
        metadata = file_manager.load_metadata(job_id)
        
        return {
            "job_id": job_id,
            "metadata": metadata,
            "categorized_files": categorized_files,
            "category_stats": category_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get categorized data: {e}")
        raise HTTPException(status_code=500, detail=str(e))