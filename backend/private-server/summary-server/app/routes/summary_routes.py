"""
요약 관련 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import ollama
import os

from ..services.file_manager import FileManager
from ..services.hashtag_extractor import HashtagExtractor
from ..services.redis_publisher import RedisPublisher
from ..utils import qwen_summarize_long

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/summary", tags=["summary"])

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
        model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
        
        # 개선된 Qwen 모델을 사용한 긴 텍스트 요약 (async 함수 호출)
        summary = await qwen_summarize_long(
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

@router.get("/mapping/{mapping_id}")
def get_summaries_by_mapping_id(mapping_id: int):
    """mapping_id로 요약 결과 조회"""
    try:
        # mapping_id를 job_id로 사용 (파일명이 mapping_id로 저장됨)
        job_id = str(mapping_id)

        # 요약 결과 조회
        summaries = file_manager.get_summary_results(job_id)

        if not summaries:
            raise HTTPException(status_code=404, detail=f"No summaries found for mapping_id {mapping_id}")

        # 각 카테고리별 통계 계산
        summary_stats = {}
        for category, content in summaries.items():
            summary_stats[category] = {
                "length": len(content),
                "exists": bool(content),
                "preview": content[:100] + "..." if len(content) > 100 else content
            }

        return {
            "mapping_id": mapping_id,
            "summaries": summaries,
            "summary_stats": summary_stats,
            "total_categories": len(summaries)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summaries for mapping_id {mapping_id}: {e}")
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


class HashtagExtractionRequest(BaseModel):
    mapping_id: int
    reason: Optional[str] = "Manual hashtag extraction"


@router.post("/extract-hashtags")
async def extract_hashtags_only(request: HashtagExtractionRequest):
    """
    기존 요약에서 해시태그만 다시 추출하여 news-summary로 전송

    Args:
        mapping_id: 매핑 ID
        reason: 재추출 사유 (선택사항)

    Returns:
        추출된 해시태그 정보
    """
    try:
        mapping_id = request.mapping_id

        logger.info(f"="*50)
        logger.info(f"🏷️ HASHTAG EXTRACTION ONLY")
        logger.info(f"  - Mapping ID: {mapping_id}")
        logger.info(f"  - Reason: {request.reason}")
        logger.info(f"  - Time: {datetime.now().isoformat()}")
        logger.info(f"="*50)

        # 1. 기존 요약 파일 읽기
        logger.info(f"📁 Reading existing summary files for mapping_id: {mapping_id}...")
        summaries = file_manager.get_summary_results(str(mapping_id))

        if not summaries:
            logger.error(f"❌ No summaries found for mapping_id: {mapping_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No summaries found for mapping_id: {mapping_id}"
            )

        logger.info(f"✅ Found {len(summaries)} categories with summaries:")
        for category, content in summaries.items():
            logger.info(f"   - {category}: {len(content) if content else 0} chars")

        # 2. job_id 생성 (기존과 동일한 형식 사용)
        job_id = f"summary_{mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"📝 Generated job_id: {job_id}")

        # 3. Redis Publisher 및 HashtagExtractor 초기화
        logger.info(f"🔧 Initializing Redis Publisher...")
        publisher = RedisPublisher()
        logger.info(f"✅ Redis Publisher ready")

        # 4. Ollama 클라이언트 설정
        logger.info(f"🤖 Setting up Ollama client...")
        ollama_client = get_ollama_client()
        model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
        logger.info(f"✅ Ollama client ready, using model: {model_name}")

        extractor = HashtagExtractor(ollama_client, model_name)

        # 5. 해시태그 추출 및 news 스트림으로 전송
        logger.info(f"🏷️ Starting hashtag extraction and streaming...")
        hashtags = await extractor.extract_hashtags_streaming(job_id, summaries, publisher)

        total_hashtags = sum(len(tags) for tags in hashtags.values())
        logger.info(f"✅ Hashtag extraction completed:")
        logger.info(f"   - Total hashtags: {total_hashtags}")
        for category, tags in hashtags.items():
            if tags:
                logger.info(f"   - {category}: {tags}")

        # 6. 정리
        logger.info(f"🧹 Cleaning up resources...")
        extractor.cleanup()
        publisher.cleanup()
        logger.info(f"✅ Resources cleaned up")

        logger.info(f"="*50)
        logger.info(f"✅ HASHTAG EXTRACTION COMPLETED")
        logger.info(f"  - Mapping ID: {mapping_id}")
        logger.info(f"  - Job ID: {job_id}")
        logger.info(f"  - Total hashtags: {total_hashtags}")
        logger.info(f"="*50)

        return {
            "success": True,
            "mapping_id": mapping_id,
            "job_id": job_id,
            "hashtags": hashtags,
            "stats": {
                "total_hashtags": total_hashtags,
                "categories_processed": len(hashtags),
                "by_category": {cat: len(tags) for cat, tags in hashtags.items()}
            },
            "message": f"Successfully extracted {total_hashtags} hashtags and sent to news-summary server"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract hashtags for mapping_id {request.mapping_id}: {e}", exc_info=True)

        # 리소스 정리 시도
        try:
            if 'extractor' in locals():
                extractor.cleanup()
            if 'publisher' in locals():
                publisher.cleanup()
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Hashtag extraction failed: {str(e)}"
        )

@router.post("/jobs/{job_id}/re-summarize")
async def re_summarize_standardized(job_id: str, max_length: int = 800, extract_hashtags: bool = True):
    """standardized 데이터를 다시 요약하고 해시태그 추출"""
    try:
        logger.info(f"Re-summarizing standardized data for job {job_id}")
        
        # standardized 파일들 조회
        categorized_files = file_manager.get_categorized_files(job_id)
        
        if not categorized_files or not any(categorized_files.values()):
            raise HTTPException(status_code=404, detail=f"No standardized files found for job {job_id}")
        
        client = get_ollama_client()
        model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
        
        summaries = {}
        
        # 각 카테고리별로 요약 수행
        for category, content in categorized_files.items():
            if content and content.strip():
                logger.info(f"Re-summarizing category: {category} ({len(content)} chars)")
                
                summary = await qwen_summarize_long(
                    ollama_client=client,
                    model_name=model_name,
                    text=content,
                    max_length=max_length,
                    category=category
                )
                summaries[category] = summary
            else:
                summaries[category] = None
        
        # 새로운 요약 결과 저장
        file_manager.save_summary_files(job_id, {
            k: v for k, v in summaries.items() if v is not None
        })
        
        # 해시태그 추출 및 실시간 Redis 발행
        hashtags = {}
        if extract_hashtags and summaries:
            try:
                # Redis Publisher 초기화
                publisher = RedisPublisher()

                # 해시태그 스트리밍 추출 (완료되는 대로 즉시 전솨)
                extractor = HashtagExtractor(client, model_name)
                hashtags = await extractor.extract_hashtags_streaming(job_id, summaries, publisher)
                extractor.cleanup()
                publisher.cleanup()

                logger.info(f"Hashtag streaming completed for job {job_id}")

            except Exception as e:
                logger.error(f"Failed to extract/publish hashtags: {e}")
                # 해시태그 실패해도 요약은 성공으로 처리
        
        # 메타데이터 업데이트
        file_manager.update_job_stage(job_id, "re_summarization", "completed")
        
        logger.info(f"Re-summarization completed for job {job_id}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "summaries": summaries,
            "hashtags": hashtags if extract_hashtags else {},
            "summary_stats": {
                category: {
                    "length": len(summary) if summary else 0,
                    "exists": bool(summary),
                    "preview": summary[:100] + "..." if summary and len(summary) > 100 else summary
                } for category, summary in summaries.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Re-summarization failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))