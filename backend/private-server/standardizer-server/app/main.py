"""
Standardizer Server - 메인 애플리케이션
DART 문서 추출 및 텍스트 표준화 서비스
"""
import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import job_routes, dart_routes
from .workers.background_worker import BackgroundWorker
from .services.standardizer import StandardizerService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Standardizer Server",
    description="DART 문서 추출 및 텍스트 표준화 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 인스턴스
standardizer_service = StandardizerService()
background_worker = BackgroundWorker()


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    try:
        # 표준화 서비스 초기화
        await standardizer_service.initialize()
        logger.info("Standardizer service initialized")
        
        # 백그라운드 워커 시작
        await background_worker.initialize()
        asyncio.create_task(background_worker.start())
        logger.info("Background worker started")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    try:
        await background_worker.stop()
        logger.info("Background worker stopped")
        
        # StandardizerService 정리
        await standardizer_service.shutdown()
        logger.info("Standardizer service shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Standardizer Server",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check() -> dict:
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "standardizer",
        "standardizer": standardizer_service.get_status(),
        "worker_running": background_worker.running
    }


# 라우터 등록
app.include_router(job_routes.router)
app.include_router(dart_routes.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)