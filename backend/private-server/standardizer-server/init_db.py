#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
MySQL에 크롤러 관련 테이블들을 생성합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, init_db, get_db_stats
from app.models.crawler_models import Base
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_connection():
    """데이터베이스 연결 확인"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("✅ 데이터베이스 연결 성공!")

            # MySQL 버전 확인
            if "mysql" in str(engine.url):
                result = conn.execute("SELECT VERSION()")
                version = result.scalar()
                logger.info(f"📊 MySQL 버전: {version}")

                # 현재 데이터베이스 확인
                result = conn.execute("SELECT DATABASE()")
                db_name = result.scalar()
                logger.info(f"📁 사용 중인 데이터베이스: {db_name}")

            return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False


def show_existing_tables():
    """기존 테이블 목록 표시"""
    try:
        with engine.connect() as conn:
            if "mysql" in str(engine.url):
                result = conn.execute("SHOW TABLES")
                tables = [row[0] for row in result]

                if tables:
                    logger.info(f"📋 기존 테이블 목록: {tables}")
                else:
                    logger.info("📋 기존 테이블이 없습니다.")

                return tables
    except Exception as e:
        logger.error(f"테이블 목록 조회 실패: {e}")
        return []


def create_tables(drop_existing=False):
    """테이블 생성"""
    try:
        if drop_existing:
            logger.warning("⚠️ 기존 테이블을 모두 삭제합니다...")
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ 기존 테이블 삭제 완료")

        logger.info("📦 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 모든 테이블 생성 완료!")

        # 생성된 테이블 확인
        tables = show_existing_tables()

        # 예상되는 테이블 목록
        expected_tables = [
            'companies',
            'job_postings',
            'job_sectors',
            'job_posting_sectors',
            'regions',
            'job_posting_regions',
            'crawling_logs'
        ]

        # 생성 확인
        for table in expected_tables:
            if table in tables:
                logger.info(f"  ✓ {table} 테이블 생성됨")
            else:
                logger.warning(f"  ✗ {table} 테이블이 생성되지 않음")

        return True

    except Exception as e:
        logger.error(f"❌ 테이블 생성 실패: {e}")
        return False


def show_database_stats():
    """데이터베이스 통계 표시"""
    try:
        stats = get_db_stats()
        logger.info("📊 데이터베이스 통계:")
        for table, count in stats.items():
            logger.info(f"  • {table}: {count}개 레코드")
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")


def main():
    """메인 함수"""
    logger.info("=" * 50)
    logger.info("🚀 크롤러 데이터베이스 초기화 시작")
    logger.info("=" * 50)

    # 데이터베이스 URL 표시 (비밀번호는 마스킹)
    db_url = str(engine.url)
    if "@" in db_url:
        # 비밀번호 마스킹
        parts = db_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split("//")[1]
            user = user_pass.split(":")[0]
            masked_url = f"{db_url.split('//')[0]}//{user}:****@{parts[1]}"
            logger.info(f"🔗 데이터베이스 URL: {masked_url}")
    else:
        logger.info(f"🔗 데이터베이스 URL: {db_url}")

    # 1. 연결 확인
    if not check_database_connection():
        logger.error("데이터베이스 연결 실패. 종료합니다.")
        sys.exit(1)

    # 2. 기존 테이블 확인
    existing_tables = show_existing_tables()

    # 3. 사용자 확인 (기존 테이블이 있는 경우)
    if existing_tables:
        response = input("\n⚠️ 기존 테이블이 있습니다. 삭제하고 새로 생성하시겠습니까? (y/N): ")
        drop_existing = response.lower() == 'y'
    else:
        drop_existing = False

    # 4. 테이블 생성
    if create_tables(drop_existing):
        logger.info("✅ 데이터베이스 초기화 완료!")

        # 5. 통계 표시
        show_database_stats()
    else:
        logger.error("❌ 데이터베이스 초기화 실패")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("🎉 작업 완료!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()