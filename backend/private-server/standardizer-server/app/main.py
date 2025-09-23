"""
Standardizer Server - 메인 애플리케이션
DART 문서 추출 및 텍스트 표준화 서비스
"""
import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import job_routes, dart_routes, crawler_routes, mapping_routes
from .workers.background_worker import BackgroundWorker
from .services.standardizer import StandardizerService
from .database import init_db
from .crawlers.crawler_scheduler import CrawlerScheduler

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 서비스 인스턴스
standardizer_service = StandardizerService()
background_worker = BackgroundWorker()
crawler_scheduler = None  # 스케줄러는 옵션으로 실행


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global crawler_scheduler

    # 시작 시 초기화
    try:
        # 데이터베이스 초기화 (크롤러 테이블 포함)
        from .models import crawler_models
        from .database import engine

        # 크롤러 테이블 생성
        crawler_models.Base.metadata.create_all(bind=engine)
        logger.info("Crawler database tables created")

        init_db()
        logger.info("Database initialized")

        # 표준화 서비스 초기화
        await standardizer_service.initialize()
        logger.info("Standardizer service initialized")

        # 상태 관리자 초기화 (실패해도 메인 서비스에 영향 없음)
        try:
            from .shared.status_integration import standardizer_status
            await standardizer_status.initialize()
            logger.info("Status manager initialized")
        except Exception as e:
            logger.warning(f"Status manager initialization failed (non-critical): {e}")

        # 백그라운드 워커 시작
        await background_worker.initialize()
        asyncio.create_task(background_worker.start())
        logger.info("Background worker started")

        # 크롤러 스케줄러 시작 (환경변수로 제어)
        if os.getenv("ENABLE_CRAWLER_SCHEDULER", "false").lower() == "true":
            from .database import SessionLocal
            db = SessionLocal()
            crawler_scheduler = CrawlerScheduler(db_session=db)
            crawler_scheduler.start()
            logger.info("Crawler scheduler started")

        logger.info("Application startup completed")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield  # 애플리케이션 실행

    # 종료 시 정리
    try:
        await background_worker.stop()
        logger.info("Background worker stopped")

        # 크롤러 스케줄러 중지
        if crawler_scheduler is not None:
            crawler_scheduler.stop()
            logger.info("Crawler scheduler stopped")

        # StandardizerService 정리
        await standardizer_service.shutdown()
        logger.info("Standardizer service shutdown completed")

        # 상태 관리자 정리 (실패해도 무시)
        try:
            from .shared.status_integration import standardizer_status
            await standardizer_status.close()
            logger.info("Status manager closed")
        except:
            pass

        logger.info("Application shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# FastAPI 앱 생성 (lifespan 이벤트 핸들러 적용)
app = FastAPI(
    title="Standardizer Server",
    description="DART 문서 추출 및 텍스트 표준화 서비스",
    version="1.0.0",
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
app.include_router(crawler_routes.router)
app.include_router(mapping_routes.router)

# 재요약 관리 라우터 추가
try:
    from .routes.admin_resummary_routes import router as admin_resummary_router
    app.include_router(admin_resummary_router)
except ImportError as e:
    logger.warning(f"Admin resummary routes not available: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)