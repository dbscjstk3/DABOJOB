"""
Redis 클라이언트 - Summary Server용
"""
import json
import logging
import os
from typing import Dict, Optional
import redis
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, redis_url: Optional[str] = None):
        """
        Redis 클라이언트 초기화
        
        Args:
            redis_url (str): Redis 연결 URL
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis = None
        self.summarization_stream = "summarization_jobs"
        self.consumer_group = "summary_workers"
        self.consumer_name = "summary_worker_1"
    
    async def initialize(self):
        """Redis 연결 초기화"""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            
            # 연결 테스트
            await asyncio.to_thread(self.redis.ping)
            logger.info(f"Connected to Redis at {self.redis_url}")
            
            # Consumer Group 생성 (이미 존재하면 무시)
            try:
                await asyncio.to_thread(
                    self.redis.xgroup_create,
                    self.summarization_stream,
                    self.consumer_group,
                    id='0',
                    mkstream=True
                )
                logger.info(f"Created consumer group: {self.consumer_group}")
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(f"Consumer group already exists: {self.consumer_group}")
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def get_pending_summarization_jobs(self, count: int = 10):
        """
        처리 대기중인 요약 작업들 가져오기
        
        Args:
            count (int): 가져올 작업 수
            
        Returns:
            list: 작업 목록
        """
        try:
            # Consumer Group에서 새로운 메시지 읽기
            messages = await asyncio.to_thread(
                self.redis.xreadgroup,
                self.consumer_group,
                self.consumer_name,
                {self.summarization_stream: '>'},
                count=count,
                block=30000  # 30초 대기
            )
            
            jobs = []
            for stream_name, msgs in messages:
                for msg_id, fields in msgs:
                    # JSON 필드 역직렬화
                    job_data = {}
                    for key, value in fields.items():
                        try:
                            # JSON 파싱 시도
                            job_data[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            # 일반 문자열
                            job_data[key] = value
                    
                    jobs.append({
                        'stream_id': msg_id,
                        'data': job_data
                    })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get pending summarization jobs: {e}")
            return []
    
    async def ack_job(self, stream_id: str):
        """
        작업 완료 확인
        
        Args:
            stream_id (str): 스트림 ID
        """
        try:
            await asyncio.to_thread(
                self.redis.xack,
                self.summarization_stream,
                self.consumer_group,
                stream_id
            )
            logger.info(f"Acknowledged summarization job: {stream_id}")
            
        except Exception as e:
            logger.error(f"Failed to acknowledge job: {e}")
    
    async def update_job_status(self, job_id: str, status: str, progress: Optional[Dict] = None):
        """
        작업 상태 업데이트 (Standardizer Server와 공유)
        
        Args:
            job_id (str): 작업 ID
            status (str): 상태 (summarization_in_progress, summarization_completed, summarization_failed)
            progress (dict): 진행률 정보
        """
        try:
            status_key = f"job_status:{job_id}"
            status_data = {
                'status': status,
                'updated_at': datetime.now().isoformat(),
                'service': 'summary_server'
            }
            
            if progress:
                status_data.update(progress)
            
            await asyncio.to_thread(
                self.redis.hset,
                status_key,
                mapping=status_data
            )
            
            # TTL 설정 (24시간)
            await asyncio.to_thread(self.redis.expire, status_key, 86400)
            
            logger.info(f"Updated job status: {job_id} -> {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
    
    async def close(self):
        """Redis 연결 종료"""
        if self.redis:
            await asyncio.to_thread(self.redis.close)
            logger.info("Redis connection closed")