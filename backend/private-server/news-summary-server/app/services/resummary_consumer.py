"""
재요약 전용 Redis Consumer
기존 시스템과 분리된 재요약 처리
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

# 상태 관리 추가
try:
    from ..shared.status_integration import news_status
    from ..shared.status_manager import JobStatus
    STATUS_AVAILABLE = True
except ImportError:
    STATUS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ResummaryConsumer:
    """재요약 전용 Consumer - 기존 시스템과 완전 분리"""

    def __init__(self, redis_host: str = None, redis_port: int = None):
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'redis')
        self.redis_port = redis_port or int(os.getenv('REDIS_PORT', '6379'))
        self.resummary_stream = 'stream:resummary'
        self.consumer_group = 'resummary-group'
        self.consumer_name = f"resummary-consumer-{os.getpid()}"
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
            logger.info(f"Resummary Consumer connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _create_consumer_group(self):
        """재요약 전용 컨슈머 그룹 생성"""
        try:
            self.client.xgroup_create(
                self.resummary_stream,
                self.consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"Created resummary consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Resummary consumer group {self.consumer_group} already exists")
            else:
                logger.error(f"Failed to create resummary consumer group: {e}")

    async def process_resummary_message(self, message: Dict[str, Any]) -> bool:
        """재요약 메시지 처리"""
        try:
            job_id = message.get('job_id')
            version = message.get('version', 2)
            message_type = message.get('type')
            chapter = message.get('chapter')
            hashtags_json = message.get('hashtags', '[]')

            logger.info(f"Processing resummary message: job_id={job_id}, version=v{version}, type={message_type}")

            # 재요약 활성 상태 확인
            active_version = self.client.get(f"resummary:active:{job_id}")
            if not active_version or active_version != f"v{version}":
                logger.warning(f"Job {job_id} v{version} is not in active resummary mode")
                return False

            if message_type == 'resummary_trigger':
                # 재요약 시작 신호
                await self._handle_resummary_trigger(job_id, version, message)
                return True

            elif message_type == 'hashtag_data':
                # 해시태그 데이터 처리 (기존 로직과 동일하지만 버전 분리)
                return await self._process_resummary_hashtags(job_id, version, chapter, hashtags_json)

            else:
                logger.warning(f"Unknown resummary message type: {message_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to process resummary message: {e}")

            # 상태 업데이트: 실패
            if STATUS_AVAILABLE:
                try:
                    await news_status.update_news_status(
                        mapping_id=int(job_id),
                        status=JobStatus.NEWS_FAILED,
                        error_message=f"Resummary failed: {str(e)}"
                    )
                except:
                    pass

            return False

    async def _handle_resummary_trigger(self, job_id: int, version: int, message: Dict[str, Any]) -> bool:
        """재요약 시작 처리"""
        try:
            logger.info(f"Starting resummary for job {job_id} version {version}")

            # 재요약 진행률 초기화
            progress_key = f"completed:{job_id}:v{version}"
            self.client.set(progress_key, 0)
            self.client.expire(progress_key, 86400)

            # 상태 업데이트: 재요약 시작
            if STATUS_AVAILABLE:
                try:
                    await news_status.update_news_status(
                        mapping_id=job_id,
                        status=JobStatus.NEWS_PROCESSING,
                        version=version,
                        chapters_completed=0
                    )
                except:
                    pass

            logger.info(f"Resummary initialization completed for job {job_id} v{version}")
            return True

        except Exception as e:
            logger.error(f"Failed to handle resummary trigger: {e}")
            return False

    async def _process_resummary_hashtags(self, job_id: int, version: int, chapter: str, hashtags_json: str) -> bool:
        """재요약 해시태그 처리 (기존 로직 + 버전 분리)"""
        try:
            # JSON 파싱
            if isinstance(hashtags_json, str):
                hashtags = json.loads(hashtags_json)
            else:
                hashtags = hashtags_json

            logger.info(f"Processing resummary hashtags for job {job_id} v{version}, chapter {chapter}: {hashtags}")

            # 상태 업데이트: 처리 시작
            if STATUS_AVAILABLE:
                try:
                    await news_status.update_news_status(
                        mapping_id=job_id,
                        status=JobStatus.NEWS_PROCESSING,
                        version=version,
                        hashtags_count=len(hashtags)
                    )
                except:
                    pass

            # 해시태그를 DB에 저장 (버전별)
            await database.save_hashtags_with_version(job_id, version, 0, str(chapter), hashtags)

            # 뉴스 검색 실행
            total_news_count = 0
            for hashtag in hashtags:
                try:
                    # 해시태그를 DB에 저장하고 ID 가져오기 (버전별)
                    hashtag_id = await self._save_and_get_hashtag_id_versioned(job_id, version, chapter, hashtag)

                    news_count = await news_service.search_and_process_news_versioned(
                        mapping_id=job_id,
                        version=version,
                        hashtag_id=hashtag_id,
                        summary_id=0,  # 임시
                        hashtag=hashtag,
                        company_name=""
                    )
                    total_news_count += news_count
                    logger.info(f"Found {news_count} news for hashtag: {hashtag} (v{version})")

                except Exception as e:
                    logger.error(f"Error searching news for hashtag {hashtag} (v{version}): {e}")

            logger.info(f"Total news found for job {job_id} v{version}, chapter {chapter}: {total_news_count}")

            # Counter 증가 및 완료 체크 (버전별)
            await self._increment_resummary_counter_and_check_completion(job_id, version)

            # 처리 결과를 Redis에 저장
            result_key = f"resummary:result:{job_id}:v{version}:{chapter}"
            result_data = {
                'job_id': job_id,
                'version': version,
                'chapter': chapter,
                'hashtags': json.dumps(hashtags, ensure_ascii=False),
                'news_count': total_news_count,
                'processed_at': datetime.now().isoformat(),
                'status': 'processed'
            }
            self.client.hset(result_key, mapping=result_data)
            self.client.expire(result_key, 86400)

            return True

        except Exception as e:
            logger.error(f"Failed to process resummary hashtags: {e}")
            return False

    async def _save_and_get_hashtag_id_versioned(self, job_id: int, version: int, chapter: str, hashtag: str) -> int:
        """버전별 해시태그 저장"""
        try:
            # 버전별 해시태그 확인
            query_check = """
            SELECT hashtag_id FROM summary_hashtags
            WHERE mapping_id = %s AND version_id = (
                SELECT version_id FROM summary_versions
                WHERE mapping_id = %s AND version_number = %s
            ) AND chapter = %s AND hashtag = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query_check, (job_id, job_id, version, chapter, hashtag))
                result = await cursor.fetchone()

                if result:
                    return result[0]

                # 새로운 해시태그 저장 (버전별)
                # 먼저 version_id 조회
                version_query = """
                SELECT version_id FROM summary_versions
                WHERE mapping_id = %s AND version_number = %s
                """
                await cursor.execute(version_query, (job_id, version))
                version_result = await cursor.fetchone()

                if not version_result:
                    raise ValueError(f"Version not found: job_id={job_id}, version={version}")

                version_id = version_result[0]

                query_insert = """
                INSERT INTO summary_hashtags (version_id, mapping_id, summary_id, chapter, hashtag)
                VALUES (%s, %s, %s, %s, %s)
                """

                await cursor.execute(query_insert, (version_id, job_id, 0, chapter, hashtag))
                hashtag_id = cursor.lastrowid

                logger.info(f"Saved resummary hashtag: {hashtag} with ID: {hashtag_id} (v{version})")
                return hashtag_id

        except Exception as e:
            logger.error(f"Error saving resummary hashtag {hashtag} (v{version}): {e}")
            # 에러 시 해시태그 이름으로 고유 ID 생성
            return abs(hash(f"{job_id}_{version}_{chapter}_{hashtag}")) % 1000000

    async def _increment_resummary_counter_and_check_completion(self, job_id: int, version: int):
        """재요약 Counter 증가 및 완료 체크 (기존 시스템과 완전 분리)"""
        counter_key = f"completed:{job_id}:v{version}"

        # Counter 증가 (버전별)
        current_count = self.client.incr(counter_key)
        self.client.expire(counter_key, 86400)

        logger.info(f"Resummary job {job_id} v{version} progress: {current_count}/5")

        # 상태 업데이트: 진행률
        if STATUS_AVAILABLE:
            try:
                if current_count >= 5:
                    # 재요약 완료
                    await news_status.update_news_status(
                        mapping_id=job_id,
                        status=JobStatus.NEWS_COMPLETED,
                        version=version,
                        chapters_completed=current_count
                    )
                else:
                    # 진행 중
                    await news_status.update_news_status(
                        mapping_id=job_id,
                        status=JobStatus.NEWS_PROCESSING,
                        version=version,
                        chapters_completed=current_count
                    )
            except:
                pass

        # 5개 챕터 모두 완료 시 재요약 완료 처리
        if current_count >= 5:
            logger.info(f"All chapters completed for resummary job {job_id} v{version}")

            # 재요약 완료 처리
            await self._complete_resummary(job_id, version)

            # 기업 분석 데이터 처리 (버전별)
            await company_processor.process_hashtag_completion_versioned(job_id, version, 'all', [])

            # Counter 및 활성 플래그 정리
            self.client.delete(counter_key)
            self.client.delete(f"resummary:active:{job_id}")

    async def _complete_resummary(self, job_id: int, version: int):
        """재요약 완료 처리"""
        try:
            # DB 업데이트: 재요약 상태 완료로 변경
            complete_query = """
            UPDATE summary_versions
            SET status = 'completed', completed_at = NOW()
            WHERE mapping_id = %s AND version_number = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(complete_query, (job_id, version))

            # 재요약 요청 상태 업데이트
            request_update_query = """
            UPDATE resummary_requests
            SET status = 'completed', completed_at = NOW()
            WHERE mapping_id = %s AND to_version = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(request_update_query, (job_id, version))

            logger.info(f"Resummary completed for job {job_id} v{version}")

        except Exception as e:
            logger.error(f"Failed to complete resummary for job {job_id} v{version}: {e}")

    async def consume_async(self, max_messages: int = None):
        """재요약 메시지 소비"""
        self.running = True
        processed_count = 0
        logger.info(f"Starting resummary consumer: {self.consumer_name}")

        while self.running:
            try:
                # 종료 조건 확인
                if max_messages and processed_count >= max_messages:
                    logger.info(f"Processed {processed_count} resummary messages, stopping")
                    break

                # 재요약 메시지 읽기
                messages = self.client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.resummary_stream: '>'},
                    count=5,
                    block=2000  # 2초 대기
                )

                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, data in stream_messages:
                            try:
                                success = await self.process_resummary_message(data)

                                if success:
                                    # 메시지 처리 완료 확인
                                    self.client.xack(self.resummary_stream, self.consumer_group, message_id)
                                    logger.debug(f"Acknowledged resummary message: {message_id}")
                                    processed_count += 1

                            except Exception as e:
                                logger.error(f"Failed to process resummary message {message_id}: {e}")

                # CPU 사용률 조절
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Resummary consumer error: {e}")
                await asyncio.sleep(2)

        logger.info(f"Resummary consumer stopped. Total messages processed: {processed_count}")

    def start_background_consumer(self):
        """백그라운드 스레드에서 재요약 컨슈머 실행"""
        def run_consumer():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.consume_async())

        thread = threading.Thread(target=run_consumer, daemon=True)
        thread.start()
        logger.info(f"Started resummary background consumer thread")
        return thread

    def stop(self):
        """재요약 컨슈머 중지"""
        self.running = False
        logger.info("Stopping resummary consumer...")

    def cleanup(self):
        """리소스 정리"""
        self.stop()
        if self.client:
            self.client.close()
            logger.info("Resummary consumer Redis connection closed")