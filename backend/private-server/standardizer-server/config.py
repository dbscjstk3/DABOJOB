"""
통합 설정 관리
모든 환경변수와 설정을 한 곳에서 관리
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # === 기본 앱 설정 ===
    APP_NAME: str = "Standardizer Server"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # === 데이터베이스 설정 ===
    DATABASE_URL: Optional[str] = None
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "dabojob"

    # === Redis 설정 ===
    REDIS_URL: str = "redis://redis:6379"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # === Redis Streams 설정 ===
    JOBS_STREAM: str = "standardization_jobs"
    SUMMARY_STREAM: str = "summarization_jobs"
    COMPLETE_STREAM: str = "complete_jobs"
    CONSUMER_GROUP: str = "standardizer_workers"
    CONSUMER_NAME: str = "worker_1"

    # === AI/LLM 설정 ===
    OPENAI_API_KEY: Optional[str] = None
    GPT_MODEL: str = "gpt-4"
    GPT_TIMEOUT: int = 30
    GPT_MAX_RETRIES: int = 3

    # === Ollama 설정 ===
    OLLAMA_HOST: str = "ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:0.5b-instruct-fp16"

    # === DART API 설정 ===
    DART_API_KEY: Optional[str] = None

    # === AWS 설정 ===
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET: str = "dart-analysis-bucket"

    # === 파일 시스템 설정 ===
    DATA_ROOT: str = "/app/data"

    # === 워커 설정 ===
    MAX_WORKERS: int = 2
    WORKER_SLEEP_INTERVAL: int = 1

    # === 크롤러 설정 ===
    ENABLE_CRAWLER_SCHEDULER: bool = False
    CRAWLER_MAX_PAGES: int = 5
    CRAWLER_PAGE_SIZE: int = 100
    CRAWLER_DELAY_MIN: int = 3
    CRAWLER_DELAY_MAX: int = 8

    # === 로깅 설정 ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """데이터베이스 URL 생성"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # 테스트 환경에서는 SQLite 사용
        if self.DEBUG:
            return "sqlite:///./test.db"
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def redis_url(self) -> str:
        """Redis URL 생성"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# 전역 설정 인스턴스
settings = Settings()