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
        self.news_search_callback = None  # 뉴스 검색 콜백 함수
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
    
    def set_news_search_callback(self, callback):
        """뉴스 검색 콜백 함수 설정"""
        self.news_search_callback = callback
    
    async def process_message(self, message: Dict[str, Any]) -> bool:
        """
        메시지 처리
        
        Args:
            message: 처리할 메시지
            
        Returns:
            처리 성공 여부
        """
        try:
            # 해시태그 메시지 처리
            job_id = message.get('job_id')
            chapter = message.get('category')  # Summary 서버에서 'category'로 전송
            hashtags_json = message.get('hashtags', '[]')

            # JSON 파싱
            if isinstance(hashtags_json, str):
                hashtags = json.loads(hashtags_json)
            else:
                hashtags = hashtags_json

            # job_id에서 mapping_id 추출 (summary_18_20250923_161001 -> 18)
            mapping_id = None
            try:
                if job_id.startswith('summary_'):
                    # summary_18_20250923_161001 -> 18
                    mapping_id = int(job_id.split('_')[1])
                elif job_id.startswith('mapping_'):
                    # mapping_18 -> 18
                    mapping_id = int(job_id.split('_')[1])
                else:
                    # 직접 숫자인 경우
                    mapping_id = int(job_id)
            except (ValueError, IndexError):
                logger.error(f"Failed to extract mapping_id from job_id: {job_id}")
                return False

            logger.info(f"Processing hashtags for job {job_id} (mapping_id: {mapping_id}), chapter {chapter}: {hashtags}")

            # 재요약 여부 확인 및 처리
            is_reprocessing = await database.is_reprocessing_job(job_id)
            if is_reprocessing:
                logger.info(f"Reprocessing detected for job {job_id}, chapter {chapter}")

                # 상태를 reprocessing으로 변경
                await database.update_job_processing_status(job_id, "reprocessing")

                # 해당 챕터의 기존 데이터 클린업
                await database.cleanup_job_chapter_data(job_id, chapter)

                # Redis counter 초기화
                counter_key = f"completed:{job_id}"
                if self.client:
                    self.client.delete(counter_key)
                    logger.info(f"Reset Redis counter for reprocessing job {job_id}")
            else:
                # 새로운 job인 경우 job_processing 레코드 생성
                try:
                    await database.create_job_processing(job_id)
                except Exception as e:
                    logger.warning(f"Could not create job_processing record for job {job_id}: {e}")

            # job_id로 company_name 조회
            company_name = await self._get_company_name(job_id)
            logger.info(f"Found company_name for job {job_id}: {company_name or 'None - will search without company filter'}")

            # 해시태그 매핑 보장 + ID 회수 (멱등)
            hashtag_map = await database.ensure_hashtag_ids(job_id, chapter, hashtags)
            # hashtag_map 예: {"TV": 651231, "스마트폰": 85120, ...}
            if not hashtag_map:
                logger.warning(
                    f"ensure_hashtag_ids returned empty for job {job_id}, chapter {chapter} (hashtags={hashtags})"
                )
                await self._increment_counter_and_check_completion(job_id)
                return True
            
            # 6) 뉴스 검색/처리 — 항상 hashtag_id 기준으로만 수행
            total_news_count = 0
            for hashtag in hashtags:
                try:
                    # 해시태그를 DB에 저장하고 ID 가져오기
                    hashtag_id = await self._save_and_get_hashtag_id(mapping_id, chapter, hashtag)

                    news_count = await news_service.search_and_process_news(
                        mapping_id=mapping_id,
                        hashtag_id=hashtag_id,
                        summary_id=0,  # 임시
                        hashtag=hashtag,
                        company_name=""  # 기업명은 별도로 추출 필요
                    )
                    total_news_count += news_count
                    logger.info(f"Found {news_count} news for hashtag: {hashtag} (hashtag_id: {hashtag_id})")
                except Exception as e:
                    logger.error(f"Error searching news for hashtag {hashtag}: {e}")

            logger.info(f"Total news found for job {job_id}, chapter {chapter}: {total_news_count}")

            # 뉴스 검색 콜백 함수 호출 (추가 처리가 있다면)
            if self.news_search_callback:
                await self.news_search_callback(job_id, chapter, hashtags)

            # Counter 증가 및 완료 체크
            await self._increment_counter_and_check_completion(mapping_id)
            
            # 처리 결과를 Redis에 저장 (옵션)
            result_key = f"news:result:{job_id}:{chapter}"
            result_data = {
                'job_id': job_id,
                'chapter': chapter,
                'hashtags': json.dumps(hashtags, ensure_ascii=False),
                'processed_at': datetime.now().isoformat(),
                'status': 'processed'
            }
            self.client.hset(result_key, mapping=result_data)
            self.client.expire(result_key, 86400)  # 24시간 후 만료
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

            # 상태 업데이트: 실패 (기존 로직에 영향 없음)
            if STATUS_AVAILABLE:
                try:
                    job_id = message.get('job_id')
                    if job_id:
                        # job_id에서 mapping_id 추출
                        try:
                            if job_id.startswith('summary_'):
                                mapping_id = int(job_id.split('_')[1])
                            elif job_id.startswith('mapping_'):
                                mapping_id = int(job_id.split('_')[1])
                            else:
                                mapping_id = int(job_id)

                            await news_status.update_news_status(
                                mapping_id=mapping_id,
                                status=JobStatus.NEWS_FAILED,
                                error_message=str(e)
                            )
                        except:
                            pass
                except:
                    pass

            return False

    async def _save_and_get_hashtag_id(self, job_id: int, chapter: int, hashtag: str) -> int:
        """해시태그를 DB에 저장하고 ID 반환"""
        try:
            # 이미 존재하는 해시태그인지 확인
            query_check = """
            SELECT hashtag_id FROM summary_hashtags
            WHERE mapping_id = %s AND chapter = %s AND hashtag = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query_check, (job_id, chapter, hashtag))
                result = await cursor.fetchone()

                if result:
                    return result[0]

                # 새로운 해시태그 저장 (summary_id는 0으로 설정, 나중에 업데이트)
                query_insert = """
                INSERT INTO summary_hashtags (mapping_id, summary_id, chapter, hashtag)
                VALUES (%s, %s, %s, %s)
                """

                await cursor.execute(query_insert, (job_id, 0, chapter, hashtag))
                hashtag_id = cursor.lastrowid

                logger.info(f"Saved hashtag: {hashtag} with ID: {hashtag_id}")
                return hashtag_id

        except Exception as e:
            logger.error(f"Error saving hashtag {hashtag}: {e}")
            # 에러 시 해시태그 이름으로 고유 ID 생성
            return abs(hash(f"{job_id}_{chapter}_{hashtag}")) % 1000000

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

        # 5개 챕터 모두 완료 시 기업 분석 데이터 처리 및 S3 업로드
        if current_count >= 5:
            logger.info(f"All chapters completed for job {job_id}, processing company analysis and S3 upload")

            # 기업 분석 데이터 처리
            await company_processor.process_hashtag_completion(job_id, 'all', [])

            # S3에 자동 업로드
            try:
                from .s3_service import s3_service
                uploaded_files = await s3_service.upload_job_completion_data(job_id)
                if uploaded_files:
                    logger.info(f"Successfully uploaded {len(uploaded_files)} files to S3 for job {job_id}: {list(uploaded_files.keys())}")
                else:
                    logger.warning(f"No files were uploaded to S3 for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to upload job completion data to S3 for job {job_id}: {e}")

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
                count=10,
                consumer=self.consumer_name
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.consume_async())
        
        thread = threading.Thread(target=run_consumer, daemon=True)
        thread.start()
        logger.info(f"Started background consumer thread")
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
    
    def get_processed_results(self, job_id: str) -> Dict[str, Any]:
        """
        처리된 결과 조회
        
        Args:
            job_id: 작업 ID
            
        Returns:
            챕터별 처리 결과
        """
        try:
            pattern = f"news:result:{job_id}:*"
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
    
    def get_job_completion_status(self, job_id: int) -> Dict[str, Any]:
        """
        작업 완료 상태 조회

        Args:
            job_id: 작업 ID

        Returns:
            완료 상태 정보
        """
        try:
            counter_key = f"completed:{job_id}"
            current_count = self.client.get(counter_key)
            current_count = int(current_count) if current_count else 0

            return {
                'job_id': job_id,
                'completed_chapters': current_count,
                'total_chapters': 5,
                'is_completed': current_count >= 5,
                'progress_percentage': (current_count / 5) * 100
            }

        except Exception as e:
            logger.error(f"Failed to get completion status for job {job_id}: {e}")
            return {}

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

    def force_process_pending(self, max_age_seconds: int = 300) -> int:
        """
        강제로 오래된 pending 메시지들을 처리

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
                            # 메시지 처리 시도
                            _, data = claimed[0]
                            success = asyncio.run(self.process_message(data))

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
    
    def cleanup(self):
        """리소스 정리"""
        self.stop()
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")