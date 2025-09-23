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
            try:
                self.pool.close()
                await self.pool.wait_closed()
                logger.info("Database disconnected")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.pool = None
    
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
            news_content TEXT DEFAULT NULL COMMENT '뉴스 요약',
            company_name VARCHAR(200) DEFAULT NULL COMMENT '기업명',
            status ENUM('raw', 'completed') DEFAULT 'raw' COMMENT '처리 상태',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_mapping_id (mapping_id),
            INDEX idx_hashtag (hashtag_id),
            INDEX idx_summary_id (summary_id),
            INDEX idx_status (status),
            UNIQUE KEY uk_mapping_hashtag_url (mapping_id, hashtag_id, news_url(255))
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
            UNIQUE KEY uk_mapping_chapter_hashtag (mapping_id, chapter(50), summary_id)
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

    
    async def save_company_analysis(self, mapping_id: int, analysis_data: Dict[str, str]) -> int:
        """기업 분석 요약 저장"""
        insert_query = """
        INSERT INTO company_analysis_summaries (
            mapping_id, business_overview, products_service, 
            sales_contracts, rnd_activities, other_notes
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            business_overview = VALUES(business_overview),
            products_service = VALUES(products_service),
            sales_contracts = VALUES(sales_contracts),
            rnd_activities = VALUES(rnd_activities),
            other_notes = VALUES(other_notes),
            updated_at = NOW()
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(insert_query, (
                mapping_id,
                analysis_data.get('business_overview'),
                analysis_data.get('products_service'), 
                analysis_data.get('sales_contracts'),
                analysis_data.get('rnd_activities'),
                analysis_data.get('other_notes')
            ))
            
            if cursor.rowcount > 0:
                logger.info(f"Saved company analysis for mapping_id={mapping_id}")
                return cursor.lastrowid or mapping_id
            return 0

    async def get_company_analysis(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """기업 분석 요약 조회"""
        query = """
        SELECT summary_id, mapping_id, business_overview, products_service,
               sales_contracts, rnd_activities, other_notes, created_at, updated_at
        FROM company_analysis_summaries
        WHERE mapping_id = %s
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (mapping_id,))
            row = await cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    async def save_hashtags(self, mapping_id: int, summary_id: int, chapter: str, hashtags: List[str]) -> int:
        """해시태그 저장"""
        if not hashtags:
            return 0
        
        insert_query = """
        INSERT INTO summary_hashtags (
            mapping_id, summary_id, chapter, hashtag
        ) VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at = NOW()
        """
        
        saved_count = 0
        async with self.get_connection() as cursor:
            for hashtag in hashtags:
                if hashtag and hashtag.strip():  # 빈 해시태그 제외
                    await cursor.execute(insert_query, (
                        mapping_id,
                        summary_id,
                        str(chapter),
                        hashtag.strip()[:100]  # 100자 제한
                    ))
                    saved_count += cursor.rowcount
        
        logger.info(f"Saved {saved_count} hashtags for mapping_id={mapping_id}, chapter={chapter}")
        return saved_count

    async def get_hashtags_by_mapping(self, mapping_id: int) -> List[Dict[str, Any]]:
        """매핑 ID로 해시태그 조회"""
        query = """
        SELECT hashtag_id, mapping_id, summary_id, chapter, hashtag, created_at, updated_at
        FROM summary_hashtags
        WHERE mapping_id = %s
        ORDER BY chapter, hashtag_id
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (mapping_id,))
            rows = await cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_hashtags_by_chapter(self, mapping_id: int, chapter: str) -> List[str]:
        """챕터별 해시태그 조회"""
        query = """
        SELECT hashtag
        FROM summary_hashtags
        WHERE mapping_id = %s AND chapter = %s
        ORDER BY hashtag_id
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (mapping_id, str(chapter)))
            rows = await cursor.fetchall()
            
            return [row[0] for row in rows]

    async def update_hashtags_summary_id(self, mapping_id: int, summary_id: int) -> int:
        """해시태그의 summary_id 업데이트"""
        update_query = """
        UPDATE summary_hashtags 
        SET summary_id = %s, updated_at = NOW()
        WHERE mapping_id = %s AND summary_id = 0
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(update_query, (summary_id, mapping_id))
            updated_count = cursor.rowcount
            
            logger.info(f"Updated {updated_count} hashtags with summary_id={summary_id} for mapping_id={mapping_id}")
            return updated_count

    async def save_hashtags_with_version(self, mapping_id: int, version: int, summary_id: int, chapter: str, hashtags: List[str]) -> int:
        """버전별 해시태그 저장 (재요약용)"""
        try:
            saved_count = 0
            for hashtag in hashtags:
                try:
                    # 중복 체크 (버전별)
                    check_query = """
                    SELECT hashtag_id FROM summary_hashtags
                    WHERE mapping_id = %s AND chapter = %s AND hashtag = %s
                    AND version_id = (SELECT version_id FROM summary_versions WHERE mapping_id = %s AND version_number = %s)
                    """

                    async with self.get_connection() as cursor:
                        await cursor.execute(check_query, (mapping_id, chapter, hashtag, mapping_id, version))
                        existing = await cursor.fetchone()

                        if existing:
                            continue  # 이미 존재하면 스킵

                        # 새 해시태그 저장
                        insert_query = """
                        INSERT INTO summary_hashtags (mapping_id, summary_id, chapter, hashtag, version_id)
                        SELECT %s, %s, %s, %s, sv.version_id
                        FROM summary_versions sv
                        WHERE sv.mapping_id = %s AND sv.version_number = %s
                        """

                        await cursor.execute(insert_query, (mapping_id, summary_id, chapter, hashtag, mapping_id, version))
                        saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving hashtag {hashtag} (v{version}): {e}")
                    continue

            logger.info(f"Saved {saved_count} hashtags for mapping_id={mapping_id} v{version} chapter={chapter}")
            return saved_count

        except Exception as e:
            logger.error(f"Failed to save hashtags with version: {e}")
            return 0

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