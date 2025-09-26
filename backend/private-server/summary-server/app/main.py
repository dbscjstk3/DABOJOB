"""
Summary Server - 메인 애플리케이션
텍스트 요약 및 카테고리별 병렬 처리 서비스
"""
import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import summary_routes
from .routes import admin_resummary_routes
from .routes import test_routes
from .workers.summary_worker import SummaryWorker

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# health 체크 로그 필터 (너무 많은 로그 방지)
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/health" not in record.getMessage()

# uvicorn 로거에 필터 적용
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(HealthCheckFilter())

# FastAPI 앱 생성
app = FastAPI(
    title="Summary Server",
    description="텍스트 요약 및 카테고리별 병렬 처리 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://j13a402.p.ssafy.io",
        "https://j13a402a.p.ssafy.io",
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://13.125.3.92",
        "http://13.125.3.92:3000",
        "http://13.125.3.92:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 백그라운드 워커
summary_worker = SummaryWorker()

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    try:
        # 상태 관리자 초기화 (실패해도 메인 서비스에 영향 없음)
        try:
            from .shared.status_integration import summary_status
            await summary_status.initialize()
            logger.info("Status manager initialized")
        except Exception as e:
            logger.warning(f"Status manager initialization failed (non-critical): {e}")

        # 백그라운드 워커 시작
        await summary_worker.initialize()
        asyncio.create_task(summary_worker.start())
        logger.info("Summary worker started")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    try:
        await summary_worker.stop()
        logger.info("Summary worker stopped")

        # 상태 관리자 정리 (실패해도 무시)
        try:
            from .shared.status_integration import summary_status
            await summary_status.close()
            logger.info("Status manager closed")
        except:
            pass

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Summary Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check() -> dict:
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "summary",
        "model": os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16'),
        "ollama_host": os.getenv('OLLAMA_HOST', 'ollama:11434'),
        "worker_running": summary_worker.running
    }

# 라우터 등록
app.include_router(summary_routes.router)
app.include_router(admin_resummary_routes.router)
app.include_router(test_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)