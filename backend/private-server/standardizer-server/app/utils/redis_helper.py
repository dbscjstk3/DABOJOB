"""
Redis 헬퍼 함수들
"""
import json
import redis
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .. import config
import logging


logger = logging.getLogger(__name__)


class RedisError(Exception):
    """Redis 관련 예외"""
    pass


class RedisHelper:
    """Redis 작업을 위한 헬퍼 클래스"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Redis 연결"""
        try:
            self.redis_client = redis.from_url(
                config.REDIS_URL,
                decode_responses=True
            )
            # 연결 테스트
            await asyncio.to_thread(self.redis_client.ping)
            logger.info(f"Connected to Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")

        except Exception as e:
            raise RedisError(f"Failed to connect to Redis: {e}")

    async def setup_streams(self) -> None:
        """Consumer Group 설정"""
        if not self.redis_client:
            await self.connect()

        # 설정할 스트림들
        streams = [
            "crawler_stream",
            "mapping_stream",
            "dart_extract_stream",
            "standardize_stream",
            config.JOBS_STREAM
        ]

        for stream_name in streams:
            try:
                await asyncio.to_thread(
                    self.redis_client.xgroup_create,
                    stream_name,
                    config.CONSUMER_GROUP,
                    id='0',
                    mkstream=True
                )
                logger.info(f"Created consumer group for stream {stream_name}: {config.CONSUMER_GROUP}")

            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(f"Consumer group already exists for {stream_name}: {config.CONSUMER_GROUP}")
                else:
                    raise RedisError(f"Failed to create consumer group for {stream_name}: {e}")

    async def add_job(self, stream: str, data: Dict[str, Any]) -> str:
        """
        작업을 스트림에 추가

        Args:
            stream: 스트림 이름
            data: 작업 데이터

        Returns:
            스트림 ID
        """
        if not self.redis_client:
            await self.connect()

        try:
            # JSON 직렬화
            serialized = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    serialized[key] = json.dumps(value, ensure_ascii=False)
                else:
                    serialized[key] = str(value)

            stream_id = await asyncio.to_thread(
                self.redis_client.xadd,
                stream,
                serialized
            )

            logger.info(f"Added job to stream {stream}: {stream_id}")
            return stream_id

        except Exception as e:
            raise RedisError(f"Failed to add job to stream: {e}")

    async def get_pending_jobs(self, stream: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        대기 중인 작업 가져오기

        Args:
            stream: 스트림 이름
            count: 가져올 작업 수

        Returns:
            작업 목록
        """
        if not self.redis_client:
            await self.connect()

        try:
            messages = await asyncio.to_thread(
                self.redis_client.xreadgroup,
                config.CONSUMER_GROUP,
                config.CONSUMER_NAME,
                {stream: '>'},
                count=count,
                block=1000
            )

            jobs = []
            for stream_name, msgs in messages:
                for msg_id, fields in msgs:
                    # JSON 역직렬화
                    job_data = {}
                    for key, value in fields.items():
                        try:
                            job_data[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            job_data[key] = value

                    jobs.append({
                        'stream_id': msg_id,
                        'data': job_data
                    })

            return jobs

        except Exception as e:
            logger.error(f"Failed to get pending jobs: {e}")
            return []

    async def ack_job(self, stream_id: str) -> None:
        """
        작업 완료 확인

        Args:
            stream_id: 스트림 ID
        """
        if not self.redis_client:
            await self.connect()

        try:
            await asyncio.to_thread(
                self.redis_client.xack,
                config.JOBS_STREAM,
                config.CONSUMER_GROUP,
                stream_id
            )
            logger.debug(f"Acknowledged job: {stream_id}")

        except Exception as e:
            raise RedisError(f"Failed to acknowledge job: {e}")

    async def set_job_status(self, job_id: str, status: str, data: Optional[Dict] = None) -> None:
        """
        작업 상태 설정

        Args:
            job_id: 작업 ID
            status: 상태
            data: 추가 데이터
        """
        if not self.redis_client:
            await self.connect()

        try:
            status_key = f"job_status:{job_id}"
            status_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }

            if data:
                # 복잡한 데이터 타입을 문자열로 변환
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        status_data[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        status_data[key] = str(value)

            await asyncio.to_thread(
                self.redis_client.hset,
                status_key,
                mapping=status_data
            )

            # TTL 설정 (24시간)
            await asyncio.to_thread(self.redis_client.expire, status_key, 86400)

        except Exception as e:
            raise RedisError(f"Failed to set job status: {e}")

    async def update_job_status(self, job_id: str, status: str, data: Optional[Dict] = None) -> None:
        """작업 상태 업데이트 (set_job_status의 별칭)"""
        await self.set_job_status(job_id, status, data)

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        작업 상태 조회

        Args:
            job_id: 작업 ID

        Returns:
            상태 정보
        """
        if not self.redis_client:
            await self.connect()

        try:
            status_key = f"job_status:{job_id}"
            status_data = await asyncio.to_thread(self.redis_client.hgetall, status_key)

            if not status_data:
                return None

            # 숫자 필드 변환
            for key in ['current_step', 'total_steps']:
                if key in status_data:
                    status_data[key] = int(status_data[key])

            return status_data

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def set_status(self, key: str, data: Dict[str, Any]) -> None:
        """
        일반 상태 정보 설정 (크롤링 상태 등)

        Args:
            key: Redis 키
            data: 상태 데이터
        """
        if not self.redis_client:
            await self.connect()

        try:
            # JSON으로 저장
            await asyncio.to_thread(
                self.redis_client.set,
                key,
                json.dumps(data, ensure_ascii=False),
                ex=86400  # 24시간 TTL
            )
        except Exception as e:
            raise RedisError(f"Failed to set status: {e}")

    async def get_status(self, key: str) -> Optional[Dict[str, Any]]:
        """
        일반 상태 정보 조회

        Args:
            key: Redis 키

        Returns:
            상태 데이터
        """
        if not self.redis_client:
            await self.connect()

        try:
            data = await asyncio.to_thread(self.redis_client.get, key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return None

    async def close(self) -> None:
        """연결 종료"""
        if self.redis_client:
            await asyncio.to_thread(self.redis_client.close)
            logger.info("Redis connection closed")


# 전역 Redis 헬퍼 인스턴스
redis_helper = RedisHelper()