"""
데이터베이스 모델 및 연결 - 심플하게
"""
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Dict, Any
import aiomysql
from contextlib import asynccontextmanager
import logging

from .config import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """DB 연결 풀 생성"""
        try:
            self.pool = await aiomysql.create_pool(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                db=config.MYSQL_DATABASE,
                charset='utf8mb4',
                autocommit=True,
                minsize=1,
                maxsize=5
            )
            await self.create_tables()
            logger.info("Database connected")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """DB 연결 해제"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database disconnected")
    
    @asynccontextmanager
    async def get_connection(self):
        """DB 커넥션 컨텍스트 매니저"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    yield cursor
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Database error: {e}")
                    raise
    
    async def create_tables(self):
        """테이블 생성"""
        create_news_table = """
        CREATE TABLE IF NOT EXISTS news_summaries (
            news_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mapping_id BIGINT NOT NULL COMMENT '공고 ID',
            hashtag_id BIGINT NOT NULL COMMENT '해시태그 ID',
            summary_id BIGINT NOT NULL COMMENT '최종 요약보고서 ID',
            news_title VARCHAR(500) NOT NULL COMMENT '뉴스 제목',
            news_url VARCHAR(1000) NOT NULL COMMENT '뉴스 URL',
            news_created_at DATETIME NOT NULL COMMENT '뉴스 생성 날짜',
            news_content TEXT NOT NULL COMMENT '뉴스 요약',
            company_name VARCHAR(200) DEFAULT NULL COMMENT '기업명',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            INDEX idx_mapping_id (mapping_id),
            INDEX idx_hashtag (hashtag_id),
            INDEX idx_summary_id (summary_id),
            UNIQUE KEY uk_mapping_hashtag_url (mapping_id, hashtag_id, news_url)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        create_summary_hashtags = """
        CREATE TABLE IF NOT EXISTS summary_hashtags (
            hashtag_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mapping_id BIGINT NOT NULL COMMENT '매핑 고유 아이디', 
            summary_id BIGINT NOT NULL COMMENT '최종 요약 보고서 아이디',
            chapter VARCHAR(50) NOT NULL,
            hashtag VARCHAR(100) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_mapping_id (mapping_id),
            INDEX idx_summary_id (summary_id),
            INDEX idx_chapter (chapter),
            UNIQUE KEY uk_mapping_chapter_hashtag (mapping_id, chapter, summary_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        create_company_summaries = """
        CREATE TABLE IF NOT EXISTS company_analysis_summaries (
            summary_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mapping_id BIGINT NOT NULL COMMENT '매핑 고유 아이디', 
            business_overview TEXT NULL COMMENT '1. 사업의 개요',
            products_service TEXT NULL COMMENT '2. 주요 제품 및 서비스',
            sales_contracts TEXT NULL COMMENT '4. 매출 및 수주 상황',
            rnd_activities TEXT NULL COMMENT '6. 주요 계약 및 연구 개발 활동',
            other_notes TEXT NULL COMMENT '7. 기타 참고사항',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_mapping_id (mapping_id),
            INDEX idx_summary_id (summary_id),
            UNIQUE KEY uk_mapping_summary (mapping_id, summary_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    
        async with self.get_connection() as cursor:
            await cursor.execute(create_news_table)
            await cursor.execute(create_summary_hashtags)
            await cursor.execute(create_company_summaries)
            logger.info("Tables created/verified")
    
    # CRUD 메서드들
    async def save_news_batch(self,
                            mapping_id: int,
                            summary_id: int,
                            hashtag_id: int,
                            news_list: List[Dict[str, Any]]) -> int:
        """뉴스 배치 저장 (중복: mapping_id+hashtag_id+news_url)"""
        if not news_list:
            return 0

        insert_query = """
        INSERT INTO news_summaries (
            mapping_id, summary_id, hashtag_id,
            news_title, news_url, news_created_at, news_content, company_name,
            created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            news_content = VALUES(news_content),
            company_name = VALUES(company_name),
            updated_at = NOW();
        """

        async with self.get_connection() as cursor:
            values = []
            for n in news_list:
                values.append((
                    mapping_id,
                    summary_id,
                    hashtag_id,
                    n["title"][:500],
                    n["url"][:1000],
                    n["pub_date"],      # datetime
                    n["summary"],
                    (n.get("company_name") or "")[:200] if n.get("company_name") else None
                ))
            await cursor.executemany(insert_query, values)
            return cursor.rowcount

    
    async def get_news_by_mapping_id(self, mapping_id: int) -> List[Dict[str, Any]]:
        query = """
        SELECT news_id, mapping_id, summary_id, hashtag_id,
            news_title, news_url, news_created_at, news_content,
            company_name, created_at, updated_at
        FROM news_summaries
        WHERE mapping_id = %s
        ORDER BY news_created_at DESC;
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, (mapping_id,))
            rows = await cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, r)) for r in rows]

    
    async def get_statistics(self) -> Dict[str, int]:
        queries = {
            "total_news": "SELECT COUNT(*) FROM news_summaries",
            "unique_mappings": "SELECT COUNT(DISTINCT mapping_id) FROM news_summaries",
            "unique_hashtags": "SELECT COUNT(DISTINCT hashtag_id) FROM news_summaries"
        }
        stats = {}
        async with self.get_connection() as cursor:
            for k, q in queries.items():
                await cursor.execute(q)
                (v,) = await cursor.fetchone()
                stats[k] = int(v or 0)
        return stats


# 전역 데이터베이스 인스턴스
database = Database()