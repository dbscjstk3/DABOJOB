"""
Redis Streams Consumer for News Summary Server
summary-server로부터 해시태그를 수신하여 뉴스 검색 수행
"""
import redis
import json
import logging
import asyncio
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
from .company_processor import company_processor
from .news_service import news_service
from ..database import database

# 상태 관리 추가 (기존 로직에 영향 없음)
try:
    from ..shared.status_integration import news_status
    from ..shared.status_manager import JobStatus
    STATUS_AVAILABLE = True
except ImportError:
    STATUS_AVAILABLE = False

logger = logging.getLogger(__name__)

class RedisConsumer:
    def __init__(self, redis_host: str = None, redis_port: int = None, consumer_group: str = "summary-group"):
        """
        Redis Consumer 초기화
        
        Args:
            redis_host: Redis 호스트
            redis_port: Redis 포트
            consumer_group: 컨슈머 그룹 이름
        """
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'redis')
        self.redis_port = redis_port or int(os.getenv('REDIS_PORT', '6379'))
        self.stream_key = 'stream:news'
        self.consumer_group = consumer_group
        self.consumer_name = f"{consumer_group}-{os.getpid()}"
        self.client = None
        self.running = False
        self._connect()
        self._create_consumer_group()
    
    def _connect(self):
        """Redis 연결"""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _create_consumer_group(self):
        """컨슈머 그룹 생성"""
        try:
            self.client.xgroup_create(
                self.stream_key, 
                self.consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {self.consumer_group} already exists")
            else:
                logger.error(f"Failed to create consumer group: {e}")
    
    async def process_message(self, message: Dict[str, Any]) -> bool:
        """
        메시지 처리 (동시 처리 방지를 위한 락 사용)

        Args:
            message: 처리할 메시지

        Returns:
            처리 성공 여부
        """
        try:
            # 메시지 타입 확인
            message_type = message.get('type', '')

            # hashtag_extraction_complete 메시지 처리
            if message_type == 'hashtag_extraction_complete':
                logger.info(f"Received hashtag extraction completion notification: {message}")
                return True  # 알림 메시지이므로 성공으로 처리

            # 해시태그 메시지 처리
            mapping_id = message.get('mapping_id')
            chapter = message.get('category')  # Summary 서버에서 'category'로 전송
            hashtags_json = message.get('hashtags', '[]')

            # mapping_id가 없거나 유효하지 않으면 에러
            if not mapping_id:
                logger.error(f"No mapping_id in message: {message}")
                return False

            # chapter가 None이거나 빈 문자열이면 에러
            if not chapter:
                logger.error(f"No chapter in message: {message}")
                return False

            try:
                mapping_id = int(mapping_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid mapping_id: {mapping_id}")
                return False

            # JSON 파싱
            if isinstance(hashtags_json, str):
                hashtags = json.loads(hashtags_json)
            else:
                hashtags = hashtags_json

            # mapping_id별 동시 처리 방지 락
            lock_key = f"processing_lock:{mapping_id}"
            lock_acquired = False

            try:
                # 락 획득 시도 (nx=True: 키가 없을 때만 설정, ex=300: 5분 후 만료)
                lock_acquired = self.client.set(lock_key, "locked", nx=True, ex=300)

                if not lock_acquired:
                    logger.warning(f"Another process is already handling mapping_id {mapping_id}, skipping")
                    return True  # 다른 프로세스가 처리 중이므로 성공으로 간주

                logger.info(f"Acquired processing lock for mapping_id {mapping_id}")

                # 빈 해시태그 리스트 처리
                if not hashtags or len(hashtags) == 0:
                    logger.warning(f"Empty hashtags for mapping_id {mapping_id}, chapter {chapter}, skipping")
                    await self._increment_counter_and_check_completion(mapping_id)
                    return True

                logger.info(f"Processing hashtags for mapping_id {mapping_id}, chapter {chapter}: {hashtags}")

                # mapping_id로 모든 job_id를 가져오기
                job_ids = await self._get_job_ids_from_mapping(mapping_id)
                if not job_ids:
                    logger.error(f"Could not find any job_id for mapping_id {mapping_id}")
                    return False

                # 모든 job_id에 대해 job_processing 레코드 자동 생성/업데이트
                for job_id in job_ids:
                    try:
                        await self._ensure_job_processing_record(mapping_id, job_id)
                    except Exception as e:
                        logger.error(f"Failed to ensure job_processing record for mapping_id {mapping_id}, job_id {job_id}: {e}")
                        return False

                # 첫 번째 job_id로 재요약 여부 확인 및 처리 (모든 job이 동일한 company_id를 가지므로)
                primary_job_id = job_ids[0]
                is_reprocessing = await database.is_reprocessing_job(primary_job_id)
                if is_reprocessing:
                    logger.info(f"Reprocessing detected for primary_job_id {primary_job_id}, chapter {chapter}")

                    # 모든 job_id에 대해 상태를 reprocessing으로 변경
                    for job_id in job_ids:
                        await database.update_job_processing_status(job_id, "reprocessing")

                    # 해당 챕터의 기존 데이터 클린업
                    await database.cleanup_job_chapter_data(mapping_id, chapter)

                    # Redis counter 초기화
                    counter_key = f"completed:{mapping_id}"
                    if self.client:
                        self.client.delete(counter_key)
                        logger.info(f"Reset Redis counter for reprocessing mapping_id {mapping_id}")
                else:
                    logger.info(f"Normal processing for job_ids {job_ids}, mapping_id {mapping_id}")

                # mapping_id로 company_name 조회
                company_name = await self._get_company_name(mapping_id)
                logger.info(f"Found company_name for mapping_id {mapping_id}: {company_name or 'None - will search without company filter'}")

                # 해시태그 매핑 보장 + ID 회수 (멱등)
                hashtag_map = await database.ensure_hashtag_ids(mapping_id, chapter, hashtags)
                # hashtag_map 예: {"TV": 651231, "스마트폰": 85120, ...}
                if not hashtag_map:
                    logger.warning(
                        f"ensure_hashtag_ids returned empty for mapping_id {mapping_id}, chapter {chapter} (hashtags={hashtags})"
                    )
                    await self._increment_counter_and_check_completion(mapping_id)
                    return True

                # 6) 뉴스 검색/처리 — ensure_hashtag_ids에서 반환된 hashtag_map 사용
                total_news_count = 0
                for hashtag in hashtags:
                    try:
                        # ensure_hashtag_ids에서 이미 가져온 hashtag_id 사용 (중복 처리 제거)
                        hashtag_id = hashtag_map.get(hashtag)
                        if not hashtag_id:
                            logger.warning(f"No hashtag_id found for hashtag: {hashtag}, skipping")
                            continue

                        news_count = await news_service.search_and_process_news(
                            mapping_id=mapping_id,
                            hashtag_id=hashtag_id,
                            summary_id=0,  # 임시
                            hashtag=hashtag,
                            company_name=company_name or ""  # 조회한 기업명 사용
                        )
                        total_news_count += news_count
                        logger.info(f"Found {news_count} news for hashtag: {hashtag} (hashtag_id: {hashtag_id})")
                    except Exception as e:
                        logger.error(f"Error searching news for hashtag {hashtag}: {e}")

                logger.info(f"Total news found for mapping_id {mapping_id}, chapter {chapter}: {total_news_count}")

                # Counter 증가 및 완료 체크
                await self._increment_counter_and_check_completion(mapping_id)

                # 처리 결과를 Redis에 저장 (옵션)
                result_key = f"news:result:{mapping_id}:{chapter}"
                result_data = {
                    'mapping_id': mapping_id,
                    'chapter': chapter,
                    'hashtags': json.dumps(hashtags, ensure_ascii=False),
                    'processed_at': datetime.now().isoformat(),
                    'status': 'processed'
                }
                self.client.hset(result_key, mapping=result_data)
                self.client.expire(result_key, 86400)  # 24시간 후 만료

                return True

            finally:
                # 락 해제
                if lock_acquired:
                    self.client.delete(lock_key)
                    logger.info(f"Released processing lock for mapping_id {mapping_id}")

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return False

    async def _get_company_name(self, mapping_id: int) -> Optional[str]:
        """
        mapping_id로 회사명을 조회
        company_dart_mappings -> companies 경로로 회사명 조회

        Args:
            mapping_id: 매핑 ID

        Returns:
            회사명 (없으면 None)
        """
        try:
            async with database.get_connection() as cursor:
                query = """
                SELECT c.company_name
                FROM company_dart_mappings cdm
                JOIN companies c ON cdm.company_id = c.company_id
                WHERE cdm.mapping_id = %s
                LIMIT 1
                """
                await cursor.execute(query, (mapping_id,))
                result = await cursor.fetchone()

                if result:
                    company_name = result[0]
                    logger.debug(f"Found company name for mapping_id {mapping_id}: {company_name}")
                    return company_name
                else:
                    logger.warning(f"No company found for mapping_id: {mapping_id}")
                    return None

        except Exception as e:
            logger.error(f"Error getting company name for mapping_id {mapping_id}: {e}")
            return None

    async def _ensure_job_processing_record(self, mapping_id: int, job_id: int) -> None:
        """
        job_processing 레코드가 존재하는지 확인하고 없으면 생성
        Redis stream으로 메시지를 받을 때마다 자동으로 호출됨

        Args:
            mapping_id: 매핑 ID
            job_id: 작업 ID
        """
        try:
            # 1. 기존 레코드 존재 여부 확인
            existing_status = await database.get_job_processing_status(job_id)

            if existing_status is None:
                # 2. 레코드가 없으면 생성 (status='processing')
                await database.create_job_processing(mapping_id, job_id)
                logger.info(f"✅ Created new job_processing record: job_id={job_id}, mapping_id={mapping_id}, status='processing'")
            else:
                # 3. 기존 레코드가 있으면 확인만 로그
                logger.debug(f"📋 Existing job_processing record: job_id={job_id}, mapping_id={mapping_id}, status='{existing_status}'")

        except Exception as e:
            logger.error(f"❌ Error ensuring job_processing record for mapping_id {mapping_id}, job_id {job_id}: {e}")
            raise

    async def _get_job_ids_from_mapping(self, mapping_id: int) -> List[int]:
        """
        mapping_id로 모든 job_id를 조회

        Args:
            mapping_id: 매핑 ID

        Returns:
            job_id 리스트 (없으면 빈 리스트)
        """
        try:
            async with database.get_connection() as cursor:
                query = """
                SELECT job_id
                FROM job_postings
                WHERE company_id = (
                    SELECT company_id
                    FROM company_dart_mappings
                    WHERE mapping_id = %s
                )
                """
                await cursor.execute(query, (mapping_id,))
                results = await cursor.fetchall()

                if results:
                    job_ids = [result[0] for result in results]
                    logger.debug(f"Found job_ids for mapping_id {mapping_id}: {job_ids}")
                    return job_ids
                else:
                    logger.warning(f"No job_ids found for mapping_id: {mapping_id}")
                    return []

        except Exception as e:
            logger.error(f"Error getting job_ids for mapping_id {mapping_id}: {e}")
            return []

    async def _get_job_id_from_mapping(self, mapping_id: int) -> Optional[int]:
        """
        mapping_id로 첫 번째 job_id를 조회 (기존 호환성 유지)

        Args:
            mapping_id: 매핑 ID

        Returns:
            job_id (없으면 None)
        """
        job_ids = await self._get_job_ids_from_mapping(mapping_id)
        return job_ids[0] if job_ids else None

    async def _get_mapping_id_from_job_id(self, job_id: int) -> Optional[int]:
        """
        job_id로 mapping_id를 조회

        Args:
            job_id: 작업 ID

        Returns:
            mapping_id (없으면 None)
        """
        try:
            async with database.get_connection() as cursor:
                query = """
                SELECT cdm.mapping_id
                FROM company_dart_mappings cdm
                JOIN job_postings jp ON cdm.company_id = jp.company_id
                WHERE jp.job_id = %s
                LIMIT 1
                """
                await cursor.execute(query, (job_id,))
                result = await cursor.fetchone()

                if result:
                    mapping_id = result[0]
                    logger.debug(f"Found mapping_id for job_id {job_id}: {mapping_id}")
                    return mapping_id
                else:
                    logger.warning(f"No mapping_id found for job_id: {job_id}")
                    return None

        except Exception as e:
            logger.error(f"Error getting mapping_id for job_id {job_id}: {e}")
            return None

    async def _save_and_get_hashtag_id(self, mapping_id: int, chapter: int, hashtag: str) -> int:
        """해시태그를 DB에 저장하고 ID 반환"""
        try:
            # 이미 존재하는 해시태그인지 확인
            query_check = """
            SELECT hashtag_id FROM summary_hashtags
            WHERE mapping_id = %s AND chapter = %s AND hashtag = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query_check, (mapping_id, chapter, hashtag))
                result = await cursor.fetchone()

                if result:
                    return result[0]

                # 새로운 해시태그 저장 (summary_id는 0으로 설정, 나중에 업데이트)
                query_insert = """
                INSERT INTO summary_hashtags (mapping_id, summary_id, chapter, hashtag)
                VALUES (%s, %s, %s, %s)
                """

                await cursor.execute(query_insert, (mapping_id, 0, chapter, hashtag))
                hashtag_id = cursor.lastrowid

                logger.info(f"Saved hashtag: {hashtag} with ID: {hashtag_id}")
                return hashtag_id

        except Exception as e:
            logger.error(f"Error saving hashtag {hashtag}: {e}")
            # DB 오류 시 None 반환하여 상위에서 처리하도록 함
            raise Exception(f"Failed to save hashtag {hashtag}: {e}")

    async def _increment_counter_and_check_completion(self, mapping_id: int):
        """Counter 증가 및 완료 체크 (재요약 충돌 방지)"""

        # ✅ 재요약 중인지 확인 (기존 로직 보호)
        resummary_active = self.client.get(f"resummary:active:{mapping_id}")
        if resummary_active:
            logger.info(f"Job {mapping_id} is in resummary mode ({resummary_active}), skipping normal completion")
            return  # 재요약 중이면 기존 완료 로직 건너뜀

        counter_key = f"completed:{mapping_id}"

        # Counter 증가
        current_count = self.client.incr(counter_key)
        self.client.expire(counter_key, 86400)  # 24시간 후 만료

        logger.info(f"Job {mapping_id} progress: {current_count}/5")

        # 5개 챕터 모두 완료 시 기업 분석 데이터 처리 (S3 업로드는 관리자 승인 후)
        if current_count >= 5:
            logger.info(f"All chapters completed for mapping_id {mapping_id}, processing company analysis")

            # 기업 분석 데이터 처리
            await company_processor.process_hashtag_completion(mapping_id, 'all', [])

            # 모든 job 상태를 completed로 변경 (관리자 승인 대기)
            try:
                job_ids = await self._get_job_ids_from_mapping(mapping_id)
                if job_ids:
                    for job_id in job_ids:
                        await database.update_job_processing_status(job_id, "completed")
                    logger.info(f"Jobs {job_ids} marked as completed, waiting for admin approval for S3 upload")
                else:
                    logger.error(f"Could not find job_ids for mapping_id {mapping_id}")
            except Exception as e:
                logger.error(f"Failed to update job status for mapping_id {mapping_id}: {e}")

            # Counter 삭제 (선택사항)
            self.client.delete(counter_key)
    
    async def consume_async(self, max_messages: int = None):
        """
        비동기 방식으로 메시지 소비

        Args:
            max_messages: 처리할 최대 메시지 수 (None이면 무한)
        """
        self.running = True
        processed_count = 0
        pending_check_interval = 30  # 30초마다 pending 메시지 확인
        last_pending_check = 0

        logger.info(f"Starting async consumer: {self.consumer_name}")

        # 시작할 때 pending 메시지 먼저 처리
        await self._process_pending_messages()

        while self.running:
            try:
                # 종료 조건 확인
                if max_messages and processed_count >= max_messages:
                    logger.info(f"Processed {processed_count} messages, stopping")
                    break

                # 주기적으로 pending 메시지 확인 및 처리
                current_time = asyncio.get_event_loop().time()
                if current_time - last_pending_check > pending_check_interval:
                    await self._process_pending_messages()
                    last_pending_check = current_time

                logger.debug(f"Consumer {self.consumer_name} waiting for messages...")

                # 메시지 읽기 (블로킹, 타임아웃 1초)
                messages = self.client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_key: '>'},
                    count=10,
                    block=1000
                )

                logger.debug(f"Received {len(messages)} stream responses")

                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, data in stream_messages:
                            processed = await self._process_single_message(message_id, data)
                            if processed:
                                processed_count += 1

                # CPU 사용률 조절
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Consumer stopped. Total messages processed: {processed_count}")

    async def _process_pending_messages(self):
        """Pending 메시지들을 처리"""
        try:
            # Pending 메시지 조회 (오래된 것부터, 최대 10개)
            pending_messages = self.client.xpending_range(
                self.stream_key,
                self.consumer_group,
                min='-',
                max='+',
                count=10
            )

            if pending_messages:
                logger.info(f"Found {len(pending_messages)} pending messages to process")

                for pending_msg in pending_messages:
                    message_id = pending_msg['message_id']
                    idle_time = pending_msg['time_since_delivered']

                    # 10초 이상 pending된 메시지만 처리 (중복 처리 방지)
                    if idle_time > 10000:  # 밀리초
                        try:
                            # 메시지 내용 조회
                            message_data = self.client.xrange(self.stream_key, message_id, message_id)
                            if message_data:
                                _, data = message_data[0]
                                await self._process_single_message(message_id, data)
                        except Exception as e:
                            logger.error(f"Failed to process pending message {message_id}: {e}")
                            # 처리 실패한 pending 메시지는 ACK하여 제거
                            self.client.xack(self.stream_key, self.consumer_group, message_id)

        except Exception as e:
            logger.error(f"Error processing pending messages: {e}")

    async def _process_single_message(self, message_id: str, data: dict) -> bool:
        """단일 메시지 처리"""
        try:
            success = await self.process_message(data)

            if success:
                # 메시지 처리 완료 확인
                self.client.xack(self.stream_key, self.consumer_group, message_id)
                logger.debug(f"Acknowledged message: {message_id}")
                return True
            else:
                logger.warning(f"Message processing failed for {message_id}, will retry later")
                return False

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}")
            # 처리 실패한 메시지는 일정 시간 후 재시도하거나 ACK하여 제거할 수 있음
            # 여기서는 로그만 남기고 pending 상태로 유지하여 나중에 재시도
            return False

    def start_background_consumer(self):
        """백그라운드 스레드에서 컨슈머 실행"""
        def run_consumer():
            # 새로운 이벤트 루프 생성 (메인 스레드와 격리)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 백그라운드에서 지속적으로 실행
                loop.run_until_complete(self.consume_async())
            except Exception as e:
                logger.error(f"Background consumer error: {e}")
            finally:
                loop.close()

        thread = threading.Thread(target=run_consumer, daemon=True)
        thread.start()
        logger.info(f"Started background consumer thread: {thread.name}")
        return thread
    
    def stop(self):
        """컨슈머 중지"""
        self.running = False
        logger.info("Stopping consumer...")
    
    def get_pending_messages(self) -> Dict:
        """
        펜딩 메시지 정보 조회
        
        Returns:
            펜딩 메시지 정보
        """
        try:
            pending_info = self.client.xpending(
                self.stream_key,
                self.consumer_group
            )
            return {
                'total': pending_info['pending'],
                'smallest': pending_info['min'],
                'largest': pending_info['max'],
                'consumers': pending_info['consumers']
            }
        except Exception as e:
            logger.error(f"Failed to get pending messages: {e}")
            return {}
    
    def get_processed_results(self, mapping_id: str) -> Dict[str, Any]:
        """
        처리된 결과 조회
        
        Args:
            mapping_id: 작업 ID
            
        Returns:
            챕터별 처리 결과
        """
        try:
            pattern = f"news:result:{mapping_id}:*"
            keys = self.client.keys(pattern)
            
            results = {}
            for key in keys:
                chapter = key.split(':')[-1]
                data = self.client.hgetall(key)
                results[chapter] = data
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get processed results: {e}")
            return {}
    
    async def get_job_completion_status_async(self, job_id: int) -> Dict[str, Any]:
        """
        작업 완료 상태 조회 (비동기 버전)

        Args:
            job_id: 작업 ID

        Returns:
            완료 상태 정보
        """
        try:
            # job_id를 mapping_id로 변환
            mapping_id = await self._get_mapping_id_from_job_id(job_id)

            if not mapping_id:
                logger.warning(f"No mapping_id found for job_id {job_id}")
                return {
                    'job_id': job_id,
                    'completed_chapters': 0,
                    'total_chapters': 5,
                    'is_completed': False,
                    'progress_percentage': 0,
                    'error': 'Mapping_id not found'
                }

            # mapping_id 기반으로 올바른 counter 키 사용
            counter_key = f"completed:{mapping_id}"
            current_count = self.client.get(counter_key)
            current_count = int(current_count) if current_count else 0

            return {
                'job_id': job_id,
                'mapping_id': mapping_id,
                'completed_chapters': current_count,
                'total_chapters': 5,
                'is_completed': current_count >= 5,
                'progress_percentage': (current_count / 5) * 100
            }

        except Exception as e:
            logger.error(f"Failed to get completion status for job {job_id}: {e}")
            return {
                'job_id': job_id,
                'completed_chapters': 0,
                'total_chapters': 5,
                'is_completed': False,
                'progress_percentage': 0,
                'error': str(e)
            }

    def get_job_completion_status(self, job_id: int) -> Dict[str, Any]:
        """
        작업 완료 상태 조회 (동기 wrapper - 이벤트 루프 충돌 방지)

        Args:
            job_id: 작업 ID

        Returns:
            완료 상태 정보
        """
        try:
            # job_id를 mapping_id로 직접 변환 (동기 방식)
            mapping_id = self._get_mapping_id_sync(job_id)

            if not mapping_id:
                logger.warning(f"No mapping_id found for job_id {job_id}")
                return {
                    'job_id': job_id,
                    'completed_chapters': 0,
                    'total_chapters': 5,
                    'is_completed': False,
                    'progress_percentage': 0,
                    'error': 'Mapping_id not found'
                }

            # mapping_id 기반으로 올바른 counter 키 사용
            counter_key = f"completed:{mapping_id}"
            current_count = self.client.get(counter_key)
            current_count = int(current_count) if current_count else 0

            return {
                'job_id': job_id,
                'mapping_id': mapping_id,
                'completed_chapters': current_count,
                'total_chapters': 5,
                'is_completed': current_count >= 5,
                'progress_percentage': (current_count / 5) * 100
            }

        except Exception as e:
            logger.error(f"Failed to get completion status for job {job_id}: {e}")
            return {
                'job_id': job_id,
                'completed_chapters': 0,
                'total_chapters': 5,
                'is_completed': False,
                'progress_percentage': 0,
                'error': str(e)
            }

    def get_consumer_health(self) -> Dict[str, Any]:
        """
        Consumer 건강 상태 조회

        Returns:
            Consumer 건강 상태 정보
        """
        try:
            # Pending 메시지 정보
            pending_info = self.get_pending_messages()

            # Stream 길이
            stream_length = self.client.xlen(self.stream_key)

            # Consumer group 정보
            group_info = self.client.xinfo_groups(self.stream_key)
            consumer_group_info = None

            for group in group_info:
                if group['name'] == self.consumer_group:
                    consumer_group_info = group
                    break

            return {
                'consumer_name': self.consumer_name,
                'consumer_group': self.consumer_group,
                'stream_key': self.stream_key,
                'stream_length': stream_length,
                'pending_messages': pending_info.get('total', 0),
                'consumer_lag': consumer_group_info.get('lag', 0) if consumer_group_info else 0,
                'is_running': self.running,
                'redis_connected': self._is_redis_connected()
            }

        except Exception as e:
            logger.error(f"Failed to get consumer health: {e}")
            return {
                'consumer_name': self.consumer_name,
                'error': str(e),
                'is_running': self.running,
                'redis_connected': False
            }

    def _is_redis_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    async def force_process_pending(self, max_age_seconds: int = 300) -> int:
        """
        강제로 오래된 pending 메시지들을 처리 (비동기 버전)

        Args:
            max_age_seconds: 이 시간(초) 이상 pending된 메시지들을 강제 처리

        Returns:
            처리된 메시지 수
        """
        try:
            max_age_ms = max_age_seconds * 1000
            processed_count = 0

            # 모든 consumer의 pending 메시지 조회
            pending_messages = self.client.xpending_range(
                self.stream_key,
                self.consumer_group,
                min='-',
                max='+',
                count=100
            )

            for pending_msg in pending_messages:
                message_id = pending_msg['message_id']
                idle_time = pending_msg['time_since_delivered']
                consumer = pending_msg['consumer']

                # 지정된 시간 이상 pending된 메시지 처리
                if idle_time > max_age_ms:
                    try:
                        # 메시지를 현재 consumer로 claim
                        claimed = self.client.xclaim(
                            self.stream_key,
                            self.consumer_group,
                            self.consumer_name,
                            0,  # min-idle-time
                            message_id
                        )

                        if claimed:
                            # 메시지 처리 시도 (비동기 호출)
                            _, data = claimed[0]
                            success = await self.process_message(data)

                            if success:
                                self.client.xack(self.stream_key, self.consumer_group, message_id)
                                processed_count += 1
                                logger.info(f"Force processed pending message {message_id}")
                            else:
                                logger.warning(f"Failed to process claimed message {message_id}")

                    except Exception as e:
                        logger.error(f"Failed to claim/process message {message_id}: {e}")
                        # 처리할 수 없는 메시지는 ACK하여 제거
                        self.client.xack(self.stream_key, self.consumer_group, message_id)

            logger.info(f"Force processed {processed_count} pending messages")
            return processed_count

        except Exception as e:
            logger.error(f"Failed to force process pending messages: {e}")
            return 0
    
    def _get_mapping_id_sync(self, job_id: int) -> Optional[int]:
        """
        job_id로 mapping_id를 조회 (동기 버전 - DB 직접 접근)

        Args:
            job_id: 작업 ID

        Returns:
            mapping_id (없으면 None)
        """
        try:
            import pymysql
            from ..database import database

            # database 설정에서 연결 정보 가져오기
            if not database.config:
                logger.error("Database config not available")
                return None

            connection = pymysql.connect(
                host=database.config['host'],
                user=database.config['user'],
                password=database.config['password'],
                database=database.config['database'],
                port=database.config['port'],
                autocommit=True
            )

            with connection.cursor() as cursor:
                query = """
                SELECT cdm.mapping_id
                FROM company_dart_mappings cdm
                JOIN job_postings jp ON cdm.company_id = jp.company_id
                WHERE jp.job_id = %s
                LIMIT 1
                """
                cursor.execute(query, (job_id,))
                result = cursor.fetchone()

                if result:
                    mapping_id = result[0]
                    logger.debug(f"Found mapping_id for job_id {job_id}: {mapping_id}")
                    return mapping_id
                else:
                    logger.warning(f"No mapping_id found for job_id: {job_id}")
                    return None

        except Exception as e:
            logger.error(f"Error getting mapping_id for job_id {job_id}: {e}")
            return None
        finally:
            if 'connection' in locals():
                connection.close()

    def cleanup(self):
        """리소스 정리"""
        self.stop()
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")