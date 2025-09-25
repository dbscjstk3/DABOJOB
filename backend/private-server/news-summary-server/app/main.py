import os
import logging
import asyncio
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
from concurrent.futures import ThreadPoolExecutor
import threading

from .utils import qwen_summarize
from .services.redis_consumer import RedisConsumer
from .routes.admin_routes import router as admin_router

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# health 체크 로그 필터 (너무 많은 로그 방지)
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/health" not in record.getMessage()

# uvicorn 로거에 필터 적용
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(HealthCheckFilter())

app = FastAPI(title="news-summary-server")

# 라우터 등록
app.include_router(admin_router)

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
    mapping_id: int
    chapter: int
    summary: str
    file_path: str = ""
    target_sentences: Optional[int] = 2

class NewsSummarizeResponse(BaseModel):
    mapping_id: int
    chapter: int
    news_summary: str
    status: str = "completed"

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global ollama_client, executor, request_semaphore, redis_consumer, consumer_thread
    
    try:
        # 상태 관리자 초기화 (실패해도 메인 서비스에 영향 없음)
        try:
            from .shared.status_integration import news_status
            await news_status.initialize()
            logger.info("Status manager initialized")
        except Exception as e:
            logger.warning(f"Status manager initialization failed (non-critical): {e}")

        host = OLLAMA_HOST if OLLAMA_HOST.startswith('http') else f'http://{OLLAMA_HOST}'
        ollama_client = ollama.Client(host=host)

        # 동시 처리 제한을 위한 설정
        max_workers = int(os.getenv('MAX_WORKERS', '2'))  # 동시 처리 수 제한
        executor = ThreadPoolExecutor(max_workers=max_workers)
        request_semaphore = asyncio.Semaphore(max_workers)  # 동시 요청 제한
        
        # Redis Consumer 시작 (일반 뉴스 처리)
        if os.getenv('ENABLE_REDIS_CONSUMER', 'true').lower() == 'true':
            try:
                redis_consumer = RedisConsumer()
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
    """뉴스 스타일 요약 처리 (동시성 제한 포함)"""
    
    # 서버 종료 중이면 요청 거부
    if shutdown_event.is_set():
        raise HTTPException(status_code=503, detail="Server is shutting down")
    
    # 세마포어로 동시 요청 수 제한
    async with request_semaphore:
        try:
            logger.info(f"Processing news summary: mapping_id={request.mapping_id}, chapter={request.chapter}")
            
            # CPU 부하를 줄이기 위해 비동기 처리
            loop = asyncio.get_event_loop()
            news_summary = await loop.run_in_executor(
                executor,
                qwen_summarize,
                ollama_client,
                MODEL_NAME,
                request.summary,
                request.target_sentences or 2
            )
            
            # 짧은 대기로 CPU 부하 분산
            await asyncio.sleep(0.1)
            
            logger.info(f"News summary completed: mapping_id={request.mapping_id}")
            
            return NewsSummarizeResponse(
                mapping_id=request.mapping_id,
                chapter=request.chapter,
                news_summary=news_summary
            )
            
        except asyncio.CancelledError:
            logger.warning(f"Request cancelled: mapping_id={request.mapping_id}")
            raise HTTPException(status_code=503, detail="Request cancelled")
        except Exception as e:
            logger.error(f"News summary failed for mapping_id={request.mapping_id}: {e}")
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
    
    # 상태 관리자 정리 (실패해도 무시)
    try:
        from .shared.status_integration import news_status
        await news_status.close()
        logger.info("Status manager closed")
    except:
        pass

    # Redis Consumer 정리
    if redis_consumer:
        redis_consumer.cleanup()
        logger.info("Redis consumer shutdown completed")


    if executor:
        executor.shutdown(wait=True, timeout=5)
        logger.info("Executor shutdown completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200, workers=1)