import os
import logging
import asyncio
import time
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

async def _save_and_get_hashtag_id(job_id: int, chapter: str, hashtag: str) -> int:
    """해시태그를 DB에 저장하고 ID 반환"""
    try:
        from .database import database

        # 이미 존재하는 해시태그인지 확인
        query_check = """
        SELECT hashtag_id FROM summary_hashtags
        WHERE mapping_id = %s AND chapter = %s AND hashtag = %s
        """

        async with database.get_connection() as cursor:
            await cursor.execute(query_check, (job_id, chapter, hashtag))
            result = await cursor.fetchone()

            if result:
                return result[0]

            # 새로운 해시태그 저장 (summary_id는 0으로 설정)
            query_insert = """
            INSERT INTO summary_hashtags (mapping_id, summary_id, chapter, hashtag)
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
        WHERE mapping_id = %s AND hashtag_id = %s AND status = 'completed'
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
    global ollama_client, executor, request_semaphore, redis_consumer, consumer_thread
    
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
                        mapping_id=request.job_id,
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