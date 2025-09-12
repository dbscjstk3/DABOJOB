"""
Redis Streams Publisher for Summary Server
요약 결과와 해시태그를 news-server로 전송
"""
import redis
import json
import logging
import os
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisPublisher:
    def __init__(self, redis_host: str = None, redis_port: int = None):
        """
        Redis Publisher 초기화
        
        Args:
            redis_host: Redis 호스트 (기본값: 환경변수)
            redis_port: Redis 포트 (기본값: 환경변수)
        """
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'redis')
        self.redis_port = redis_port or int(os.getenv('REDIS_PORT', '6379'))
        self.stream_key = 'news:hashtag:stream'
        self.client = None
        self._connect()
    
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
    
    def publish_hashtags(self, job_id: str, hashtags: Dict[str, List[str]]) -> bool:
        """
        해시태그를 Redis Streams로 발행
        
        Args:
            job_id: 작업 ID
            hashtags: {카테고리: [해시태그]} 딕셔너리
            
        Returns:
            성공 여부
        """
        try:
            published_count = 0
            
            for category, tags in hashtags.items():
                if not tags:
                    continue
                
                # 메시지 데이터 준비
                message_data = {
                    'job_id': job_id,
                    'category': category,
                    'hashtags': json.dumps(tags, ensure_ascii=False),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'summary-server'
                }
                
                # Redis Streams에 메시지 추가
                message_id = self.client.xadd(
                    self.stream_key,
                    message_data,
                    maxlen=1000  # 스트림 최대 길이 제한
                )
                
                logger.info(f"Published to Redis Streams - ID: {message_id}, Category: {category}, Tags: {tags}")
                published_count += 1
            
            # 전체 작업 완료 신호 전송
            if published_count > 0:
                completion_data = {
                    'job_id': job_id,
                    'type': 'hashtag_extraction_complete',
                    'total_categories': str(published_count),
                    'timestamp': datetime.now().isoformat()
                }
                self.client.xadd(self.stream_key, completion_data, maxlen=1000)
                logger.info(f"Published completion signal for job {job_id}")
            
            return published_count > 0
            
        except Exception as e:
            logger.error(f"Failed to publish to Redis Streams: {e}")
            return False
    
    def publish_single_message(self, message: Dict[str, Any]) -> str:
        """
        단일 메시지 발행
        
        Args:
            message: 발행할 메시지
            
        Returns:
            메시지 ID
        """
        try:
            # JSON 필드는 문자열로 변환
            processed_message = {}
            for key, value in message.items():
                if isinstance(value, (list, dict)):
                    processed_message[key] = json.dumps(value, ensure_ascii=False)
                else:
                    processed_message[key] = str(value)
            
            processed_message['timestamp'] = datetime.now().isoformat()
            
            message_id = self.client.xadd(
                self.stream_key,
                processed_message,
                maxlen=1000
            )
            
            logger.info(f"Published message to Redis Streams - ID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
    
    def get_stream_info(self) -> Dict:
        """스트림 정보 조회"""
        try:
            info = self.client.xinfo_stream(self.stream_key)
            return {
                'length': info['length'],
                'first_entry': info['first-entry'],
                'last_entry': info['last-entry'],
                'consumer_groups': len(info.get('groups', []))
            }
        except redis.ResponseError:
            logger.info(f"Stream {self.stream_key} does not exist yet")
            return None
        except Exception as e:
            logger.error(f"Failed to get stream info: {e}")
            return None
    
    def cleanup(self):
        """리소스 정리"""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")