"""
Redis Streams Consumer for News Summary Server
summary-server로부터 해시태그를 수신하여 뉴스 검색 수행
"""
import redis
import json
import logging
import asyncio
import os
from typing import Dict, List, Any, Optional, cast
from datetime import datetime
import threading
from .company_processor import company_processor
from .news_service import news_service
from ..database import database

logger = logging.getLogger(__name__)

class RedisConsumer:
    def __init__(self, redis_host: Optional[str] = None, redis_port: Optional[int] = None, consumer_group: str = "summary-group"):
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
        self.client: Optional[redis.Redis[str]] = None
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
        if not self.client:
            logger.error("Redis client is not connected")
            return

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
            job_id_raw = message.get('job_id')
            chapter = message.get('category')
            hashtags_json = message.get('hashtags', '[]')

            # 타입 검증 및 변환
            if not job_id_raw:
                logger.error("job_id is missing in message")
                return False
            job_id = int(job_id_raw)

            # chapter 검증
            if not chapter:
                logger.error("chapter is missing in message")
                return False

            # JSON 파싱
            if isinstance(hashtags_json, str):
                hashtags = json.loads(hashtags_json)
            else:
                hashtags = hashtags_json

            # hashtags 검증
            if not hashtags or not isinstance(hashtags, list):
                logger.warning(f"No valid hashtags found for job {job_id}, chapter {chapter}")
                return True  # 해시태그가 없어도 성공으로 처리

            logger.info(f"Processing hashtags for job {job_id}, chapter {chapter}: {hashtags}")

            # job_id로 company_name 조회
            company_name = await self._get_company_name(job_id)
            logger.info(f"Found company_name for job {job_id}: {company_name or 'None - will search without company filter'}")

            # 해시태그를 DB에 저장 (summary_id는 임시로 0 사용)
            await database.save_hashtags(job_id, 0, chapter, hashtags)
            
            # 뉴스 검색 실행
            total_news_count = 0
            for hashtag in hashtags:
                try:
                    # 해시태그를 DB에 저장하고 ID 가져오기
                    hashtag_id = await self._save_and_get_hashtag_id(job_id, chapter, hashtag)

                    news_count = await news_service.search_and_process_news(
                        job_id=job_id,
                        hashtag_id=hashtag_id,
                        summary_id=0,  # 임시
                        hashtag=hashtag,
                        company_name=company_name or ""  # MySQL에서 조회한 회사명 사용
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
            await self._increment_counter_and_check_completion(job_id)
            
            # 처리 결과를 Redis에 저장 (옵션)
            if self.client and chapter:
                result_key = f"news:result:{job_id}:{chapter}"
                result_data: Dict[str, str] = {
                    'job_id': str(job_id),
                    'chapter': str(chapter),
                    'hashtags': json.dumps(hashtags, ensure_ascii=False),
                    'processed_at': datetime.now().isoformat(),
                    'status': 'processed'
                }
                self.client.hset(result_key, mapping=cast(Any, result_data))
                self.client.expire(result_key, 86400)  # 24시간 후 만료
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return False

    async def _get_company_name(self, job_id: int) -> Optional[str]:
        """job_id로 company_name 조회"""
        try:
            # job_postings에서 company_id 조회 후 companies에서 company_name 조회
            query = """
            SELECT c.company_name
            FROM job_postings jp
            JOIN companies c ON jp.company_id = c.company_id
            WHERE jp.job_id = %s
            LIMIT 1
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                result = await cursor.fetchone()

                if result:
                    company_name = result[0]
                    logger.info(f"Found company_name for job {job_id}: {company_name}")
                    return company_name
                else:
                    logger.warning(f"No company_name found for job {job_id} in job_postings/companies tables")
                    return None

        except Exception as e:
            logger.error(f"Error getting company_name for job {job_id}: {e}")
            return None

    async def _save_and_get_hashtag_id(self, job_id: int, chapter: str, hashtag: str) -> int:
        """해시태그를 DB에 저장하고 ID 반환"""
        try:
            # 이미 존재하는 해시태그인지 확인
            query_check = """
            SELECT hashtag_id FROM summary_hashtags
            WHERE job_id = %s AND chapter = %s AND hashtag = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query_check, (job_id, chapter, hashtag))
                result = await cursor.fetchone()

                if result:
                    return result[0]

                # 새로운 해시태그 저장 (summary_id는 0으로 설정, 나중에 업데이트)
                query_insert = """
                INSERT INTO summary_hashtags (job_id, summary_id, chapter, hashtag)
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

    async def _increment_counter_and_check_completion(self, job_id: int):
        """Counter 증가 및 완료 체크"""
        if not self.client:
            logger.error("Redis client is not connected")
            return

        counter_key = f"completed:{job_id}"

        # Counter 증가
        current_count = self.client.incr(counter_key)
        self.client.expire(counter_key, 86400)  # 24시간 후 만료

        logger.info(f"Job {job_id} progress: {current_count}/5")

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
    
    async def consume_async(self, max_messages: Optional[int] = None):
        """
        비동기 방식으로 메시지 소비
        
        Args:
            max_messages: 처리할 최대 메시지 수 (None이면 무한)
        """
        self.running = True
        processed_count = 0
        logger.info(f"Starting async consumer: {self.consumer_name}")
        
        while self.running:
            try:
                # 종료 조건 확인
                if max_messages and processed_count >= max_messages:
                    logger.info(f"Processed {processed_count} messages, stopping")
                    break

                # 디버그 로그 추가
                logger.debug(f"Consumer {self.consumer_name} waiting for messages...")

                # Redis 클라이언트 체크
                if not self.client:
                    logger.error("Redis client is not connected")
                    await asyncio.sleep(1)
                    continue

                # 새로운 메시지만 읽기 (pending 메시지 처리 제거)
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
                            try:
                                success = await self.process_message(data)
                                
                                if success and self.client:
                                    # 메시지 처리 완료 확인
                                    self.client.xack(self.stream_key, self.consumer_group, message_id)
                                    logger.debug(f"Acknowledged message: {message_id}")
                                    processed_count += 1
                                    
                            except Exception as e:
                                logger.error(f"Failed to process message {message_id}: {e}")
                
                # CPU 사용률 조절
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Consumer stopped. Total messages processed: {processed_count}")
    
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
        if not self.client:
            logger.error("Redis client is not connected")
            return {}

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
        if not self.client:
            logger.error("Redis client is not connected")
            return {}

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
        if not self.client:
            logger.error("Redis client is not connected")
            return {}

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
    
    def cleanup(self):
        """리소스 정리"""
        self.stop()
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")