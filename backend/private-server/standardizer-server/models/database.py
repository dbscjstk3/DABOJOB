"""
데이터베이스 연결 및 설정
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import settings
from utils.logger import get_logger
from utils.exceptions import DatabaseError

logger = get_logger(__name__)

# SQLAlchemy 설정
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성
    FastAPI 의존성 주입에서 사용
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise DatabaseError(f"Database operation failed: {e}")
    finally:
        db.close()


def init_database() -> None:
    """
    데이터베이스 초기화
    테이블 생성
    """
    try:
        # 모든 모델 import
        from models import crawler, dart  # noqa

        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    except Exception as e:
        raise DatabaseError(f"Failed to initialize database: {e}")


def check_database_connection() -> bool:
    """
    데이터베이스 연결 확인

    Returns:
        연결 성공 여부
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection OK")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False