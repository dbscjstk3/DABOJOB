from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os
from typing import Generator

# 데이터베이스 URL 설정 (환경변수에서 읽기)
# Docker 환경에서는 DATABASE_URL이 자동으로 설정됨
# 예: mysql+pymysql://private_user:private_password@mysql:3306/private_app
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./crawler_data.db"  # 로컬 개발용 기본값
)

# 데이터베이스 타입 확인
is_sqlite = "sqlite" in DATABASE_URL
is_mysql = "mysql" in DATABASE_URL
is_postgresql = "postgresql" in DATABASE_URL

# MySQL 연결 파라미터 설정
mysql_connect_args = {
    "charset": "utf8mb4",
    "connect_timeout": 10,
} if is_mysql else {}

# SQLAlchemy 엔진 생성 (MySQL 최적화 설정 포함)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else mysql_connect_args,
    pool_pre_ping=True,  # 연결 상태 자동 확인
    pool_size=10,        # 연결 풀 크기
    max_overflow=20,     # 최대 오버플로우 연결 수
    pool_recycle=3600,   # 1시간마다 연결 재활용
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"  # SQL 디버깅
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