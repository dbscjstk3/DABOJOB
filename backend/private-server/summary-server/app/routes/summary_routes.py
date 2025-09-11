"""
요약 관련 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import ollama

from ..services.file_manager import FileManager
from ..utils import qwen_summarize_long

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summary", tags=["summary"])

# 서비스 인스턴스
file_manager = FileManager()
ollama_client = None

class SummarizeRequest(BaseModel):
    mapping_id: int
    chapter: int
    content: str
    file_path: str = ""
    max_length: int = 500
    enable_chunking: Optional[bool] = True

class SummarizeResponse(BaseModel):
    mapping_id: int
    chapter: int
    summary: str
    status: str = "completed"

def get_ollama_client():
    """Ollama 클라이언트 반환"""
    global ollama_client
    if not ollama_client:
        import os
        ollama_host = os.getenv('OLLAMA_HOST', 'ollama:11434')
        host = ollama_host if ollama_host.startswith('http') else f'http://{ollama_host}'
        ollama_client = ollama.Client(host=host)
    return ollama_client

@router.post("/", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest) -> SummarizeResponse:
    """텍스트 요약 처리"""
    try:
        logger.info(f"Processing summary: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        client = get_ollama_client()
        model_name = os.getenv('SUMMARY_MODEL', 'qwen2.5:0.5b-instruct-fp16')
        
        # 개선된 Qwen 모델을 사용한 긴 텍스트 요약
        summary = qwen_summarize_long(
            ollama_client=client,
            model_name=model_name,
            text=request.content,
            max_length=request.max_length
        )
        
        logger.info(f"Summary completed: mapping_id={request.mapping_id}")
        
        return SummarizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}")
def get_job_summaries(job_id: str):
    """작업의 요약 결과 조회"""
    try:
        # 요약 결과 조회
        summaries = file_manager.get_summary_results(job_id)
        
        if not summaries:
            raise HTTPException(status_code=404, detail=f"No summaries found for job {job_id}")
        
        # 각 카테고리별 통계 계산
        summary_stats = {}
        for category, content in summaries.items():
            summary_stats[category] = {
                "length": len(content),
                "exists": bool(content),
                "preview": content[:100] + "..." if len(content) > 100 else content
            }
        
        return {
            "job_id": job_id,
            "summaries": summaries,
            "summary_stats": summary_stats,
            "total_categories": len(summaries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summaries for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))