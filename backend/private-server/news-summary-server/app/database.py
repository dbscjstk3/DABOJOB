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
                use_unicode=True,
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
        """테이블 생성 + 인덱스 정리"""
        
        create_news_table = """
        CREATE TABLE IF NOT EXISTS news_summaries (
            news_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            job_id BIGINT NOT NULL COMMENT '공고 ID',
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
            
            INDEX idx_job_id (job_id),
            INDEX idx_hashtag (hashtag_id),
            INDEX idx_summary_id (summary_id),
            INDEX idx_status (status),
            UNIQUE KEY uk_mapping_hashtag_url (job_id, hashtag_id, news_url(255))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        create_summary_hashtags = """
        CREATE TABLE IF NOT EXISTS summary_hashtags (
            hashtag_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            job_id BIGINT NOT NULL COMMENT '매핑 고유 아이디', 
            summary_id BIGINT NOT NULL COMMENT '최종 요약 보고서 아이디',
            chapter VARCHAR(50) NOT NULL,
            hashtag VARCHAR(100) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_job_id (job_id),
            INDEX idx_summary_id (summary_id),
            INDEX idx_chapter (chapter)
            -- UNIQUE KEY는 아래 ALTER 로직에서 보정
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        create_company_summaries = """
        CREATE TABLE IF NOT EXISTS company_analysis_summaries (
            summary_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            job_id BIGINT NOT NULL COMMENT '매핑 고유 아이디',
            business_overview TEXT NULL COMMENT '1. 사업의 개요',
            products_service TEXT NULL COMMENT '2. 주요 제품 및 서비스',
            sales_contracts TEXT NULL COMMENT '4. 매출 및 수주 상황',
            rnd_activities TEXT NULL COMMENT '6. 주요 계약 및 연구 개발 활동',
            other_notes TEXT NULL COMMENT '7. 기타 참고사항',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            INDEX idx_job_id (job_id),
            INDEX idx_summary_id (summary_id),
            UNIQUE KEY uk_mapping_summary (job_id, summary_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        create_job_processing = """
        CREATE TABLE IF NOT EXISTS job_processing (
            job_id BIGINT PRIMARY KEY COMMENT '공고 ID',
            status ENUM('processing', 'completed', 'finished', 'reprocessing') NOT NULL DEFAULT 'processing' COMMENT '처리 상태',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    
        async with self.get_connection() as cursor:
            await cursor.execute(create_news_table)
            await cursor.execute(create_summary_hashtags)
            await cursor.execute(create_company_summaries)
            await cursor.execute(create_job_processing)

            # 인덱스 교체: (기존) uk_mapping_chapter_hashtag → (신규) uk_job_chapter_hashtag
            # 기존 인덱스 드롭 (있을 때만)
            try:
                await cursor.execute("ALTER TABLE summary_hashtags DROP INDEX uk_mapping_chapter_hashtag;")
                logger.info("Dropped old unique index uk_mapping_chapter_hashtag on summary_hashtags")
            except Exception as e:
                # 없으면 무시
                pass
            
            # 신규 유니크 키 생성 (job_id, chapter, hashtag)
            try:
                await cursor.execute("""
                    ALTER TABLE summary_hashtags
                    ADD CONSTRAINT uk_job_chapter_hashtag
                    UNIQUE KEY (job_id, chapter, hashtag);
                """)
                logger.info("Added unique index uk_job_chapter_hashtag on summary_hashtags (job_id, chapter, hashtag)")
            except Exception as e:
                # 이미 있으면 무시
                pass
            
            logger.info("Tables created/verified")
            
    # ----------------------------------------------------------------------
    # CRUD 메서드들
    # ----------------------------------------------------------------------
    async def save_news_batch(
        self,
        job_id: int,
        summary_id: int,
        hashtag_id: int,
        news_list: List[Dict[str, Any]]
    ) -> int:
        """뉴스 배치 저장 (중복: job_id + hashtag_id + news_url)"""
        if not news_list:
            return 0

        insert_query = """
        INSERT INTO news_summaries (
            job_id, summary_id, hashtag_id,
            news_title, news_url, news_created_at, news_content, company_name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            news_content = VALUES(news_content),
            company_name = VALUES(company_name),
            updated_at = NOW();
        """

        async with self.get_connection() as cursor:
            values = []
            for n in news_list:
                values.append((
                    job_id,
                    summary_id,
                    hashtag_id,
                    (n.get("title") or "")[:500],
                    (n.get("url") or "")[:1000],
                    n.get("pub_date"),      # datetime
                    n.get("summary"),
                    (n.get("company_name") or None)[:200] if n.get("company_name") else None
                ))
            await cursor.executemany(insert_query, values)
            return cursor.rowcount

    
    async def get_news_by_job_id(self, job_id: int) -> List[Dict[str, Any]]:
        query = """
        SELECT news_id, job_id, summary_id, hashtag_id,
               news_title, news_url, news_created_at, news_content,
               company_name, created_at, updated_at
        FROM news_summaries
        WHERE job_id = %s
        ORDER BY news_created_at DESC, news_id DESC;
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            rows = await cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, r)) for r in rows]

    
    async def save_company_analysis(self, job_id: int, analysis_data: Dict[str, str]) -> int:
        """기업 분석 요약 저장 (멱등 업데이트)"""
        insert_query = """
        INSERT INTO company_analysis_summaries (
            job_id, business_overview, products_service, 
            sales_contracts, rnd_activities, other_notes
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            business_overview = VALUES(business_overview),
            products_service = VALUES(products_service),
            sales_contracts = VALUES(sales_contracts),
            rnd_activities = VALUES(rnd_activities),
            other_notes = VALUES(other_notes),
            updated_at = NOW();
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(insert_query, (
                job_id,
                analysis_data.get('business_overview'),
                analysis_data.get('products_service'), 
                analysis_data.get('sales_contracts'),
                analysis_data.get('rnd_activities'),
                analysis_data.get('other_notes')
            ))
            
            if cursor.rowcount > 0:
                logger.info(f"Saved company analysis for job_id={job_id}")
                return cursor.lastrowid or job_id
            return 0

    async def get_company_analysis(self, job_id: int) -> Optional[Dict[str, Any]]:
        """기업 분석 요약 조회"""
        query = """
        SELECT summary_id, job_id, business_overview, products_service,
               sales_contracts, rnd_activities, other_notes, created_at, updated_at
        FROM company_analysis_summaries
        WHERE job_id = %s
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            row = await cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None


    # ---------------------------
    # 멱등 해시태그 업서트 + ID 반환
    # ---------------------------
    async def ensure_hashtag_ids(self, job_id: int, chapter: str, hashtags: List[str]) -> Dict[str, int]:
        """
        (job_id, chapter, hashtag) 조합을 모두 보장하고 hashtag_id를 반환.
        - 동일 조합이 이미 있으면 그대로 재사용
        - 없으면 INSERT (ON DUPLICATE KEY UPDATE로 멱등)
        - 결과: { hashtag_text: hashtag_id, ... }
        """
        
         # 1) 정규화 & 중복 제거
        norm_tags: List[str] = []
        seen = set()
        for h in hashtags:
            if not h:
                continue
            t = h.strip()
            if not t or t in seen:
                continue
            seen.add(t)
            norm_tags.append(t)

        if not norm_tags:
            return {}

        result: Dict[str, int] = {}
        
        if not hashtags:
            return 0

        async with self.get_connection() as cursor:
            # 2) 기존 존재하는 것들 먼저 조회
            select_q = """
            SELECT hashtag, hashtag_id
            FROM summary_hashtags
            WHERE job_id = %s AND chapter = %s AND hashtag IN ({})
            """.format(", ".join(["%s"] * len(norm_tags)))
            await cursor.execute(select_q, (job_id, chapter, *norm_tags))
            for hashtag, hid in await cursor.fetchall():
                result[hashtag] = int(hid)

            # 3) 없는 것들만 INSERT (멱등)
            to_insert = [h for h in norm_tags if h not in result]
            if to_insert:
                insert_q = """
                INSERT INTO summary_hashtags (job_id, summary_id, chapter, hashtag)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE updated_at = NOW();
                """
                values = [(job_id, 0, chapter, h) for h in to_insert]
                await cursor.executemany(insert_q, values)

            # 4) 전체 다시 조회해서 ID 회수
            await cursor.execute(select_q, (job_id, chapter, *norm_tags))
            for hashtag, hid in await cursor.fetchall():
                result[hashtag] = int(hid)

        logger.info(f"Ensured {len(result)} hashtags for job_id={job_id}, chapter={chapter}")
        return result

     # (레거시) 해시태그 저장: 새로는 ensure_hashtag_ids 사용 권장
    async def save_hashtags(self, job_id: int, summary_id: int, chapter: str, hashtags: List[str]) -> int:
        """해시태그 저장 (레거시) — 멱등 업서트 ensure_hashtag_ids 사용 권장"""
        if not hashtags:
            return 0
        insert_query = """
        INSERT INTO summary_hashtags (job_id, summary_id, chapter, hashtag)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE updated_at = NOW();
        """
        saved_count = 0
        async with self.get_connection() as cursor:
            for hashtag in hashtags:
                if hashtag and hashtag.strip():  # 빈 해시태그 제외
                    await cursor.execute(insert_query, (
                        job_id,
                        summary_id,
                        str(chapter),
                        hashtag.strip()[:100]
                    ))
                    saved_count += cursor.rowcount
        logger.info(f"Saved {saved_count} hashtags for job_id={job_id}, chapter={chapter}")
        return saved_count
    
    async def get_hashtags_by_mapping(self, job_id: int) -> List[Dict[str, Any]]:
        """매핑 ID로 해시태그 조회 (챕터 고정 순서 정렬)"""
        query = """
        SELECT hashtag_id, job_id, summary_id, chapter, hashtag, created_at, updated_at
        FROM summary_hashtags
        WHERE job_id = %s
        ORDER BY FIELD(chapter,'business_overview','products_services','revenue_orders','contracts_rnd','others'),
                 hashtag_id;
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            rows = await cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_hashtags_by_chapter(self, job_id: int, chapter: str) -> List[str]:
        """챕터별 해시태그 조회"""
        query = """
        SELECT hashtag
        FROM summary_hashtags
        WHERE job_id = %s AND chapter = %s
        ORDER BY hashtag_id
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    async def get_hashtags_by_chapter(self, job_id: int, chapter: str) -> List[str]:
        """챕터별 해시태그 조회"""
        query = """
        SELECT hashtag
        FROM summary_hashtags
        WHERE job_id = %s AND chapter = %s
        ORDER BY hashtag_id;
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id, str(chapter)))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def update_hashtags_summary_id(self, job_id: int, summary_id: int) -> int:
        """해시태그의 summary_id 업데이트"""
        update_query = """
        UPDATE summary_hashtags 
        SET summary_id = %s, updated_at = NOW()
        WHERE job_id = %s AND summary_id = 0
        """
        
        async with self.get_connection() as cursor:
            await cursor.execute(update_query, (summary_id, job_id))
            updated_count = cursor.rowcount
            logger.info(f"Updated {updated_count} hashtags with summary_id={summary_id} for job_id={job_id}")
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
                    """

                    async with self.get_connection() as cursor:
                        await cursor.execute(check_query, (mapping_id, chapter, hashtag))
                        existing = await cursor.fetchone()

                        if existing:
                            continue  # 이미 존재하면 스킵

                        # 새 해시태그 저장
                        insert_query = """
                        INSERT INTO summary_hashtags (mapping_id, summary_id, chapter, hashtag)
                        VALUES (%s, %s, %s, %s)
                        """

                        await cursor.execute(insert_query, (mapping_id, summary_id, chapter, hashtag))
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
            "unique_mappings": "SELECT COUNT(DISTINCT job_id) FROM news_summaries",
            "unique_hashtags": "SELECT COUNT(DISTINCT hashtag_id) FROM news_summaries"
        }
        stats: Dict[str, int] = {}
        async with self.get_connection() as cursor:
            for k, q in queries.items():
                await cursor.execute(q)
                (v,) = await cursor.fetchone()
                stats[k] = int(v or 0)
        return stats

    async def create_job_processing(self, job_id: int) -> None:
        """job_processing 레코드 생성"""
        query = """
        INSERT INTO job_processing (job_id, status)
        VALUES (%s, 'processing')
        ON DUPLICATE KEY UPDATE updated_at = NOW()
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            logger.info(f"Created job_processing record for job_id={job_id}")

    async def update_job_processing_status(self, job_id: int, status: str) -> bool:
        """job_processing 상태 업데이트"""
        query = """
        UPDATE job_processing
        SET status = %s, updated_at = NOW()
        WHERE job_id = %s
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, (status, job_id))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated job_id={job_id} status to {status}")
            return success

    async def get_job_processing_status(self, job_id: int) -> Optional[str]:
        """job_processing 상태 조회"""
        query = """
        SELECT status FROM job_processing WHERE job_id = %s
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, (job_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    async def get_jobs_by_status(self, status: str) -> List[Dict[str, Any]]:
        """특정 상태의 job 목록 조회"""
        query = """
        SELECT job_id, status, created_at, updated_at
        FROM job_processing
        WHERE status = %s
        ORDER BY updated_at DESC
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query, (status,))
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_all_job_processing(self) -> List[Dict[str, Any]]:
        """모든 job_processing 레코드 조회"""
        query = """
        SELECT job_id, status, created_at, updated_at
        FROM job_processing
        ORDER BY updated_at DESC
        """
        async with self.get_connection() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def cleanup_job_chapter_data(self, job_id: int, chapter: str) -> None:
        """특정 job_id + chapter의 기존 데이터 클린업 (재요약용)"""
        try:
            async with self.get_connection() as cursor:
                # 1. 해당 챕터의 기존 해시태그 ID들 조회
                hashtag_query = """
                SELECT hashtag_id FROM summary_hashtags
                WHERE job_id = %s AND chapter = %s
                """
                await cursor.execute(hashtag_query, (job_id, chapter))
                hashtag_ids = [row[0] for row in await cursor.fetchall()]

                if hashtag_ids:
                    # 2. 해당 해시태그들의 뉴스 데이터 삭제
                    placeholders = ",".join(["%s"] * len(hashtag_ids))
                    news_delete_query = f"""
                    DELETE FROM news_summaries
                    WHERE job_id = %s AND hashtag_id IN ({placeholders})
                    """
                    await cursor.execute(news_delete_query, [job_id] + hashtag_ids)
                    deleted_news = cursor.rowcount

                    # 3. 해당 챕터의 해시태그 삭제
                    hashtag_delete_query = """
                    DELETE FROM summary_hashtags
                    WHERE job_id = %s AND chapter = %s
                    """
                    await cursor.execute(hashtag_delete_query, (job_id, chapter))
                    deleted_hashtags = cursor.rowcount

                    logger.info(f"Cleaned up job {job_id} chapter {chapter}: {deleted_hashtags} hashtags, {deleted_news} news")
                else:
                    logger.info(f"No existing data to clean up for job {job_id} chapter {chapter}")

        except Exception as e:
            logger.error(f"Error cleaning up job {job_id} chapter {chapter}: {e}")
            raise

    async def is_reprocessing_job(self, job_id: int) -> bool:
        """job_id가 재요약 대상인지 확인 (completed/finished 상태인 경우)"""
        try:
            current_status = await self.get_job_processing_status(job_id)
            return current_status in ["completed", "finished"]
        except Exception as e:
            logger.error(f"Error checking reprocessing status for job {job_id}: {e}")
            return False

    async def reset_job_counter(self, job_id: int) -> None:
        """재요약 시 Redis counter 초기화"""
        try:
            # Redis 클라이언트는 여기서 직접 접근하기 어려우므로
            # redis_consumer에서 호출하도록 설계
            logger.info(f"Job {job_id} counter reset requested")
        except Exception as e:
            logger.error(f"Error resetting counter for job {job_id}: {e}")

    async def start_job_reprocessing(self, job_id: int) -> Dict[str, Any]:
        """
        Job을 reprocessing 상태로 변경하고 관련 데이터 정리

        Args:
            job_id: 재처리할 job ID

        Returns:
            정리된 데이터 통계
        """
        try:
            async with self.get_connection() as cursor:
                # 1. 현재 상태 확인
                current_status = await self.get_job_processing_status(job_id)
                if current_status not in ["completed", "finished"]:
                    raise ValueError(f"Job {job_id} status '{current_status}' is not eligible for reprocessing")

                logger.info(f"Starting reprocessing for job {job_id}, current status: {current_status}")

                # 2. 상태를 reprocessing으로 변경
                await self.update_job_processing_status(job_id, "reprocessing")

                # 3. 뉴스 요약 데이터 삭제
                delete_news_summary_query = """
                DELETE FROM news_summaries
                WHERE mapping_id = %s
                """
                await cursor.execute(delete_news_summary_query, (job_id,))
                deleted_news_summaries = cursor.rowcount

                # 4. 요약 해시태그 삭제
                delete_hashtags_query = """
                DELETE FROM summary_hashtags
                WHERE mapping_id = %s
                """
                await cursor.execute(delete_hashtags_query, (job_id,))
                deleted_hashtags = cursor.rowcount

                # 6. 요약 데이터 삭제 (summaries 테이블이 있다면)
                try:
                    delete_summaries_query = """
                    DELETE FROM summaries
                    WHERE mapping_id = %s
                    """
                    await cursor.execute(delete_summaries_query, (job_id,))
                    deleted_summaries = cursor.rowcount
                except Exception:
                    deleted_summaries = 0  # 테이블이 없을 수 있음

                cleanup_stats = {
                    "job_id": job_id,
                    "previous_status": current_status,
                    "new_status": "reprocessing",
                    "deleted_news_summaries": deleted_news_summaries,
                    "deleted_hashtags": deleted_hashtags,
                    "deleted_summaries": deleted_summaries,
                    "cleanup_timestamp": datetime.now().isoformat()
                }

                logger.info(f"Reprocessing cleanup completed for job {job_id}: {cleanup_stats}")
                return cleanup_stats

        except Exception as e:
            logger.error(f"Error starting reprocessing for job {job_id}: {e}")
            # 실패시 원래 상태로 롤백 시도
            try:
                if 'current_status' in locals():
                    await self.update_job_processing_status(job_id, current_status)
            except:
                pass
            raise

    async def get_job_reprocessing_eligibility(self, job_id: int) -> Dict[str, Any]:
        """
        Job이 reprocessing 가능한지 확인하고 관련 정보 반환

        Args:
            job_id: 확인할 job ID

        Returns:
            재처리 가능 여부 및 관련 정보
        """
        try:
            async with self.get_connection() as cursor:
                # 현재 상태 확인
                current_status = await self.get_job_processing_status(job_id)

                if not current_status:
                    return {
                        "eligible": False,
                        "reason": "Job not found",
                        "job_id": job_id
                    }

                # 관련 데이터 개수 조회
                data_counts = {}

                # 뉴스 요약 개수
                await cursor.execute("SELECT COUNT(*) FROM news_summaries WHERE mapping_id = %s", (job_id,))
                result = await cursor.fetchone()
                data_counts['news_summaries'] = result[0] if result else 0

                # 해시태그 개수
                await cursor.execute("SELECT COUNT(*) FROM summary_hashtags WHERE mapping_id = %s", (job_id,))
                result = await cursor.fetchone()
                data_counts['hashtags'] = result[0] if result else 0

                # 해시태그 관련 뉴스 개수
                await cursor.execute("""
                    SELECT COUNT(*) FROM news_summaries ns
                    INNER JOIN summary_hashtags sh ON ns.hashtag_id = sh.hashtag_id
                    WHERE sh.mapping_id = %s
                """, (job_id,))
                result = await cursor.fetchone()
                data_counts['hashtag_news'] = result[0] if result else 0

                eligible = current_status in ["completed", "finished"]

                return {
                    "eligible": eligible,
                    "job_id": job_id,
                    "current_status": current_status,
                    "reason": "Job is eligible for reprocessing" if eligible else f"Job status '{current_status}' not eligible",
                    "data_counts": data_counts,
                    "estimated_deletion": sum(data_counts.values())
                }

        except Exception as e:
            logger.error(f"Error checking reprocessing eligibility for job {job_id}: {e}")
            return {
                "eligible": False,
                "job_id": job_id,
                "reason": f"Error checking eligibility: {str(e)}"
            }



# 전역 데이터베이스 인스턴스
database = Database()