"""
Standardizer Server - 새로운 메인 애플리케이션
간단하고 깔끔한 구조
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from utils.logger import setup_logging, get_logger
from models.database import init_database, check_database_connection
from utils.redis_helper import redis_helper

# 로깅 설정
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # === 시작 시 초기화 ===
    try:
        logger.info("Starting Standardizer Server...")

        # 1. 데이터베이스 연결 확인
        if not check_database_connection():
            raise Exception("Database connection failed")

        # 2. 데이터베이스 테이블 초기화
        init_database()

        # 3. Redis 연결 및 스트림 설정
        await redis_helper.connect()
        await redis_helper.setup_streams()

# 4. 백그라운드 워커 초기화
        from workers.background_worker import BackgroundWorker
        worker = BackgroundWorker()
        await worker.initialize()
        await worker.start_workers()
        app.state.background_worker = worker

        logger.info("✅ Standardizer Server started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise

    yield  # 애플리케이션 실행

    # === 종료 시 정리 ===
    try:
        logger.info("Shutting down Standardizer Server...")

        # 백그라운드 워커 정리
        if hasattr(app.state, 'background_worker'):
            await app.state.background_worker.shutdown()

        # Redis 연결 종료
        await redis_helper.close()

        logger.info("✅ Server shutdown completed")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="DART 문서 추출 및 텍스트 표준화 서비스",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "standardizer",
        "database": "connected" if check_database_connection() else "disconnected",
# 서비스 상태 추가
        "background_worker": app.state.background_worker.get_status() if hasattr(app.state, 'background_worker') else None
    }


# API 라우터 등록
from routers import crawler, mapping, dart, jobs

app.include_router(crawler.router)
app.include_router(mapping.router)
app.include_router(dart.router)
app.include_router(jobs.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )