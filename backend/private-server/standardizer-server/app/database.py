from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os
from typing import Generator

# 데이터베이스 URL 설정 (환경변수에서 읽기)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./crawler_data.db"  # 기본값: SQLite
)

# PostgreSQL 예시: postgresql://user:password@localhost/dbname
# MySQL 예시: mysql+pymysql://user:password@localhost/dbname

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성 주입을 위한 데이터베이스 세션 생성기
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    데이터베이스 테이블 초기화
    """
    from .models import crawler_models
    
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def drop_all_tables():
    """
    모든 테이블 삭제 (주의: 데이터가 모두 삭제됨)
    """
    from .models import crawler_models
    
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped")


def get_db_stats():
    """
    데이터베이스 통계 조회
    """
    from .models.crawler_models import Company, JobPosting, JobSector, Region, CrawlingLog
    
    db = SessionLocal()
    try:
        stats = {
            "companies": db.query(Company).count(),
            "job_postings": db.query(JobPosting).count(),
            "job_sectors": db.query(JobSector).count(),
            "regions": db.query(Region).count(),
            "crawling_logs": db.query(CrawlingLog).count()
        }
        return stats
    finally:
        db.close()


# 데이터베이스 초기화 (앱 시작 시)
if __name__ == "__main__":
    init_db()
    stats = get_db_stats()
    print("Database statistics:", stats)