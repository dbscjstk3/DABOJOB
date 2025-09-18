import os
import logging
import asyncio
import time
import json
import boto3
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import ollama
from concurrent.futures import ThreadPoolExecutor
import threading

from .utils import qwen_summarize
from .services.redis_consumer import RedisConsumer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="news-summary-server")

# 환경변수에서 올바른 이름으로 가져오기
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'ollama:11434')
MODEL_NAME = os.getenv('NEWS_MODEL', 'qwen2.5:0.5b-instruct-fp16')

# Ollama 클라이언트
ollama_client = None
executor = None
request_semaphore = None
shutdown_event = threading.Event()
redis_consumer = None
consumer_thread = None

# S3 클라이언트
s3_client = None

class NewsSummarizeRequest(BaseModel):
    job_id: int
    chapter: str
    company_name: str
    hashtags: List[str]

class HashtagNewsResult(BaseModel):
    hashtag: str
    news_count: int
    news_summaries: List[str]

class NewsSummarizeResponse(BaseModel):
    job_id: int
    chapter: str
    company_name: str
    total_news_found: int
    hashtag_results: List[HashtagNewsResult]
    status: str = "completed"

class NewsItem(BaseModel):
    news_id: int
    title: str
    url: str
    published_date: Optional[str]
    summary: Optional[str]

class HashtagDetail(BaseModel):
    hashtag: str
    news_items: List[NewsItem]

class CategoryResult(BaseModel):
    category: str
    hashtags: List[HashtagDetail]
    total_news_count: int

class JobResult(BaseModel):
    job_id: int
    company_name: str
    categories: List[CategoryResult]
    total_hashtags: int
    total_news: int
    status: str

async def _save_and_get_hashtag_id(job_id: int, chapter: str, hashtag: str) -> int:
    """해시태그를 DB에 저장하고 ID 반환"""
    try:
        from .database import database

        # 이미 존재하는 해시태그인지 확인
        query_check = """
        SELECT hashtag_id FROM summary_hashtags
        WHERE job_id = %s AND chapter = %s AND hashtag = %s
        """

        async with database.get_connection() as cursor:
            await cursor.execute(query_check, (job_id, chapter, hashtag))
            result = await cursor.fetchone()

            if result:
                return result[0]

            # 새로운 해시태그 저장 (summary_id는 0으로 설정)
            query_insert = """
            INSERT INTO summary_hashtags (job_id, summary_id, chapter, hashtag)
            VALUES (%s, %s, %s, %s)
            """

            await cursor.execute(query_insert, (job_id, 0, chapter, hashtag))
            hashtag_id = cursor.lastrowid

            logger.info(f"Saved hashtag: {hashtag} with ID: {hashtag_id}")
            return hashtag_id

    except Exception as e:
        logger.error(f"Error saving hashtag {hashtag}: {e}")
        # 에러 시 해시태그 이름으로 고유 ID 생성
        return abs(hash(f"{job_id}_{chapter}_{hashtag}")) % 1000000

async def _get_news_summaries(job_id: int, hashtag_id: int) -> List[str]:
    """해당 해시태그의 뉴스 요약 내용들을 가져오기"""
    try:
        from .database import database

        query = """
        SELECT news_content
        FROM news_summaries
        WHERE job_id = %s AND hashtag_id = %s AND status = 'completed'
        AND news_content IS NOT NULL AND news_content != ''
        ORDER BY news_id DESC
        """

        async with database.get_connection() as cursor:
            await cursor.execute(query, (job_id, hashtag_id))
            results = await cursor.fetchall()

            summaries = []
            for row in results:
                content = row[0]
                if content and len(content.strip()) > 0:
                    # 간단한 정제 (HTML 태그나 불필요한 내용 제거)
                    clean_content = content.strip()
                    if len(clean_content) > 500:  # 너무 길면 잘라내기
                        clean_content = clean_content[:500] + "..."
                    summaries.append(clean_content)

            return summaries

    except Exception as e:
        logger.error(f"Error getting news summaries for job_id={job_id}, hashtag_id={hashtag_id}: {e}")
        return []

async def news_search_callback(job_id: str, category: str, hashtags: list):
    """해시태그 기반 뉴스 검색 콜백"""
    logger.info(f"News search for job {job_id}, category {category}: {hashtags}")
    # TODO: 실제 뉴스 API 호출 로직 구현
    # 예: news_api.search(hashtags)
    # 결과를 파일이나 DB에 저장

    # 임시 처리
    for hashtag in hashtags:
        logger.info(f"Searching news with hashtag: {hashtag}")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global ollama_client, executor, request_semaphore, redis_consumer, consumer_thread, s3_client
    
    try:
        host = OLLAMA_HOST if OLLAMA_HOST.startswith('http') else f'http://{OLLAMA_HOST}'
        ollama_client = ollama.Client(host=host)
        
        # 동시 처리 제한을 위한 설정
        max_workers = int(os.getenv('MAX_WORKERS', '2'))  # 동시 처리 수 제한
        executor = ThreadPoolExecutor(max_workers=max_workers)
        request_semaphore = asyncio.Semaphore(max_workers)  # 동시 요청 제한
        
        # Redis Consumer 시작
        if os.getenv('ENABLE_REDIS_CONSUMER', 'true').lower() == 'true':
            try:
                redis_consumer = RedisConsumer()
                redis_consumer.set_news_search_callback(news_search_callback)
                consumer_thread = redis_consumer.start_background_consumer()
                logger.info("Redis consumer started successfully")
            except Exception as e:
                logger.error(f"Failed to start Redis consumer: {e}")
                # Redis 실패해도 서버는 계속 동작
        
        # 연결 테스트
        models = ollama_client.list()
        logger.info(f"Connected to Ollama at {host}")
        logger.info(f"Available models: {[m['name'] for m in models['models']]}")
        logger.info(f"Using model: {MODEL_NAME}")
        logger.info(f"Max concurrent workers: {max_workers}")

        # S3 클라이언트 초기화
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
            )
            logger.info("S3 client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {e}")
            s3_client = None

    except Exception as e:
        logger.error(f"Failed to initialize Ollama client: {e}")
        raise

@app.get("/health")
def health_check() -> dict:
    """헬스체크 with 리소스 상태"""
    active_tasks = 0
    if request_semaphore:
        active_tasks = max_workers - request_semaphore._value if hasattr(request_semaphore, '_value') else 0
    
    redis_status = "not_enabled"
    pending_messages = 0
    if redis_consumer:
        try:
            pending_info = redis_consumer.get_pending_messages()
            pending_messages = pending_info.get('total', 0)
            redis_status = "connected"
        except:
            redis_status = "error"
    
    return {
        "status": "ok" if not shutdown_event.is_set() else "shutting_down", 
        "service": "news-summary",
        "model": MODEL_NAME,
        "ollama_host": OLLAMA_HOST,
        "active_tasks": active_tasks,
        "max_workers": int(os.getenv('MAX_WORKERS', '2')),
        "redis_consumer": redis_status,
        "pending_messages": pending_messages
    }

max_workers = int(os.getenv('MAX_WORKERS', '2'))

@app.post("/news-summarize", response_model=NewsSummarizeResponse)
async def news_summarize_content(request: NewsSummarizeRequest) -> NewsSummarizeResponse:
    """해시태그 기반 뉴스 검색 및 요약 처리"""

    # 서버 종료 중이면 요청 거부
    if shutdown_event.is_set():
        raise HTTPException(status_code=503, detail="Server is shutting down")

    # 세마포어로 동시 요청 수 제한
    if not request_semaphore:
        raise HTTPException(status_code=503, detail="Request semaphore not initialized")

    async with request_semaphore:
        try:
            logger.info(f"Processing hashtag-based news summary: job_id={request.job_id}, chapter={request.chapter}, company={request.company_name}, hashtags={request.hashtags}")

            # news_service import
            from .services.news_service import NewsService
            news_service = NewsService()

            total_news_found = 0
            hashtag_results = []

            # 각 해시태그별로 뉴스 검색 및 요약 수행
            for hashtag in request.hashtags:
                try:
                    # 해시태그를 DB에 저장하고 ID 가져오기
                    hashtag_id = await _save_and_get_hashtag_id(request.job_id, request.chapter, hashtag)

                    # 뉴스 검색 및 처리
                    news_count = await news_service.search_and_process_news(
                        job_id=request.job_id,
                        hashtag_id=hashtag_id,
                        summary_id=0,  # 임시
                        hashtag=hashtag,
                        company_name=request.company_name
                    )

                    # 처리된 뉴스 요약 내용 가져오기
                    news_summaries = await _get_news_summaries(request.job_id, hashtag_id)

                    hashtag_results.append(HashtagNewsResult(
                        hashtag=hashtag,
                        news_count=news_count,
                        news_summaries=news_summaries
                    ))

                    total_news_found += news_count

                    logger.info(f"Found {news_count} news for hashtag: {hashtag}")

                except Exception as e:
                    logger.error(f"Error processing hashtag {hashtag}: {e}")
                    # 에러 발생시에도 빈 결과라도 추가
                    hashtag_results.append(HashtagNewsResult(
                        hashtag=hashtag,
                        news_count=0,
                        news_summaries=[]
                    ))

            logger.info(f"News summary completed: job_id={request.job_id}, total_news={total_news_found}")

            return NewsSummarizeResponse(
                job_id=request.job_id,
                chapter=request.chapter,
                company_name=request.company_name,
                total_news_found=total_news_found,
                hashtag_results=hashtag_results
            )

        except asyncio.CancelledError:
            logger.warning(f"Request cancelled: job_id={request.job_id}")
            raise HTTPException(status_code=503, detail="Request cancelled")
        except Exception as e:
            logger.error(f"News summary failed for job_id={request.job_id}: {e}")
            # 실패 시 간단한 fallback 처리
            if "timeout" in str(e).lower():
                raise HTTPException(status_code=504, detail="Processing timeout")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/hashtag-results/{job_id}")
async def get_hashtag_results(job_id: str):
    """처리된 해시태그 결과 조회"""
    if not redis_consumer:
        raise HTTPException(status_code=503, detail="Redis consumer not available")

    try:
        results = redis_consumer.get_processed_results(job_id)
        if not results:
            raise HTTPException(status_code=404, detail=f"No results found for job {job_id}")

        return {
            "job_id": job_id,
            "categories": list(results.keys()),
            "results": results,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Failed to get hashtag results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}/hashtags")
async def get_job_hashtags(job_id: int):
    """특정 job_id의 해시태그 목록 조회"""
    try:
        from .database import database

        query = """
        SELECT DISTINCT sh.chapter, sh.hashtag, sh.hashtag_id
        FROM summary_hashtags sh
        WHERE sh.job_id = %s
        ORDER BY sh.chapter, sh.hashtag
        """

        async with database.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            results = await cursor.fetchall()

            if not results:
                raise HTTPException(status_code=404, detail=f"No hashtags found for job {job_id}")

            hashtags_by_category = {}
            for row in results:
                chapter, hashtag, hashtag_id = row
                if chapter not in hashtags_by_category:
                    hashtags_by_category[chapter] = []
                hashtags_by_category[chapter].append({
                    "hashtag": hashtag,
                    "hashtag_id": hashtag_id
                })

            return {
                "job_id": job_id,
                "categories": hashtags_by_category,
                "total_hashtags": len(results)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hashtags for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/jobs/{job_id}/news")
async def get_job_news(job_id: int, hashtag_id: Optional[int] = None, category: Optional[str] = None):
    """특정 job_id의 뉴스 목록 조회"""
    try:
        from .database import database

        # 기본 쿼리
        base_query = """
        SELECT
            rn.news_id,
            rn.title,
            rn.url,
            rn.published_date,
            rn.hashtag_id,
            sh.hashtag,
            sh.chapter,
            ns.news_content as summary
        FROM raw_news rn
        LEFT JOIN summary_hashtags sh ON rn.hashtag_id = sh.hashtag_id
        LEFT JOIN news_summaries ns ON rn.news_id = ns.news_id
            AND ns.job_id = %s
        WHERE rn.job_id = %s
        """

        params = [job_id, job_id]

        # 필터 조건 추가
        if hashtag_id:
            base_query += " AND rn.hashtag_id = %s"
            params.append(hashtag_id)

        if category:
            base_query += " AND sh.chapter = %s"
            params.append(category)

        base_query += " ORDER BY rn.published_date DESC"

        async with database.get_connection() as cursor:
            await cursor.execute(base_query, params)
            results = await cursor.fetchall()

            if not results:
                return {
                    "job_id": job_id,
                    "filters": {
                        "hashtag_id": hashtag_id,
                        "category": category
                    },
                    "news_items": [],
                    "total_count": 0
                }

            news_items = []
            for row in results:
                news_id, title, url, published_date, hashtag_id_result, hashtag, chapter, summary = row

                # 날짜 포맷팅
                formatted_date = None
                if published_date:
                    if isinstance(published_date, datetime):
                        formatted_date = published_date.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_date = str(published_date)

                news_items.append({
                    "news_id": news_id,
                    "title": title or "제목 없음",
                    "url": url or "",
                    "published_date": formatted_date,
                    "hashtag_id": hashtag_id_result,
                    "hashtag": hashtag,
                    "category": chapter,
                    "summary": summary
                })

            return {
                "job_id": job_id,
                "filters": {
                    "hashtag_id": hashtag_id,
                    "category": category
                },
                "news_items": news_items,
                "total_count": len(news_items)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get news for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/jobs/{job_id}/summary")
async def get_job_summary(job_id: int):
    """특정 job_id의 요약 정보 조회"""
    try:
        from .database import database

        # 해시태그 통계
        hashtag_query = """
        SELECT chapter, COUNT(*) as hashtag_count
        FROM summary_hashtags
        WHERE job_id = %s
        GROUP BY chapter
        """

        # 뉴스 통계
        news_query = """
        SELECT sh.chapter, COUNT(rn.news_id) as news_count
        FROM summary_hashtags sh
        LEFT JOIN raw_news rn ON sh.hashtag_id = rn.hashtag_id AND rn.job_id = %s
        WHERE sh.job_id = %s
        GROUP BY sh.chapter
        """

        async with database.get_connection() as cursor:
            # 해시태그 통계 조회
            await cursor.execute(hashtag_query, (job_id,))
            hashtag_stats = await cursor.fetchall()

            # 뉴스 통계 조회
            await cursor.execute(news_query, (job_id, job_id))
            news_stats = await cursor.fetchall()

            if not hashtag_stats:
                raise HTTPException(status_code=404, detail=f"No data found for job {job_id}")

            # 결과 구성
            categories = {}
            total_hashtags = 0
            total_news = 0

            # 해시태그 통계 처리
            for row in hashtag_stats:
                category, hashtag_count = row
                categories[category] = {
                    "hashtag_count": hashtag_count,
                    "news_count": 0
                }
                total_hashtags += hashtag_count

            # 뉴스 통계 처리
            for row in news_stats:
                category, news_count = row
                if category in categories:
                    categories[category]["news_count"] = news_count
                    total_news += news_count

            return {
                "job_id": job_id,
                "categories": categories,
                "total_hashtags": total_hashtags,
                "total_news": total_news,
                "status": "completed" if categories else "no_data"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summary for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/jobs/{job_id}/company")
async def get_job_company(job_id: int):
    """특정 job_id의 회사 정보 조회 (mappings 테이블 사용 안함)"""
    try:
        # mappings 테이블 대신 다른 방법으로 회사명 추정
        from .database import database

        # 뉴스 데이터에서 가장 많이 등장하는 회사명 패턴을 찾거나
        # 또는 단순히 job_id만 반환
        return {
            "job_id": job_id,
            "company_name": None,  # mappings 테이블 없으면 null
            "note": "Company name not available - mappings table not found"
        }

    except Exception as e:
        logger.error(f"Failed to get company info for job {job_id}: {e}")
        return {
            "job_id": job_id,
            "company_name": None,
            "error": str(e)
        }

@app.post("/jobs/{job_id}/upload")
async def upload_job_to_s3(job_id: int):
    """특정 job_id의 데이터를 S3에 업로드"""
    try:
        from .services.s3_service import s3_service

        uploaded_files = await s3_service.upload_job_completion_data(job_id)

        if not uploaded_files:
            raise HTTPException(status_code=500, detail="Failed to upload any files to S3")

        return {
            "job_id": job_id,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
            "message": f"Successfully uploaded {len(uploaded_files)} files to S3"
        }

    except Exception as e:
        logger.error(f"Failed to upload job {job_id} to S3: {e}")
        raise HTTPException(status_code=500, detail=f"S3 upload error: {str(e)}")

@app.get("/jobs/{job_id}/s3-files")
async def get_job_s3_files(job_id: int):
    """특정 job_id의 S3 파일 목록 조회"""
    try:
        from .services.s3_service import s3_service

        files = s3_service.get_job_s3_files(job_id)

        return {
            "job_id": job_id,
            "s3_files": files,
            "total_files": len(files)
        }

    except Exception as e:
        logger.error(f"Failed to list S3 files for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"S3 list error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event_handler():
    """서버 종료 시 정리"""
    global executor, redis_consumer
    shutdown_event.set()
    
    # Redis Consumer 정리
    if redis_consumer:
        redis_consumer.cleanup()
        logger.info("Redis consumer shutdown completed")
    
    if executor:
        executor.shutdown(wait=True)
        logger.info("Executor shutdown completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200, workers=1)