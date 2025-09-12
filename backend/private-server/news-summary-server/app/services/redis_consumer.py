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

logger = logging.getLogger(__name__)

class RedisConsumer:
    def __init__(self, redis_host: str = None, redis_port: int = None, consumer_group: str = "news-consumer"):
        """
        Redis Consumer 초기화
        
        Args:
            redis_host: Redis 호스트
            redis_port: Redis 포트
            consumer_group: 컨슈머 그룹 이름
        """
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'redis')
        self.redis_port = redis_port or int(os.getenv('REDIS_PORT', '6379'))
        self.stream_key = 'news:hashtag:stream'
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
            # 메시지 타입 확인
            if message.get('type') == 'hashtag_extraction_complete':
                logger.info(f"Received completion signal for job {message.get('job_id')}")
                return True
            
            # 해시태그 메시지 처리
            job_id = message.get('job_id')
            category = message.get('category')
            hashtags_json = message.get('hashtags', '[]')
            
            # JSON 파싱
            if isinstance(hashtags_json, str):
                hashtags = json.loads(hashtags_json)
            else:
                hashtags = hashtags_json
            
            logger.info(f"Processing hashtags for job {job_id}, category {category}: {hashtags}")
            
            # 뉴스 검색 콜백 함수 호출
            if self.news_search_callback:
                await self.news_search_callback(job_id, category, hashtags)
            else:
                # 기본 처리 (로그만)
                for hashtag in hashtags:
                    logger.info(f"Would search news for: {hashtag}")
            
            # 처리 결과를 Redis에 저장 (옵션)
            result_key = f"news:result:{job_id}:{category}"
            result_data = {
                'job_id': job_id,
                'category': category,
                'hashtags': json.dumps(hashtags, ensure_ascii=False),
                'processed_at': datetime.now().isoformat(),
                'status': 'processed'
            }
            self.client.hset(result_key, mapping=result_data)
            self.client.expire(result_key, 86400)  # 24시간 후 만료
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return False
    
    async def consume_async(self, max_messages: int = None):
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
                
                # 메시지 읽기 (블로킹, 타임아웃 1초)
                messages = self.client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_key: '>'},
                    count=10,
                    block=1000
                )
                
                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, data in stream_messages:
                            try:
                                success = await self.process_message(data)
                                
                                if success:
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
            카테고리별 처리 결과
        """
        try:
            pattern = f"news:result:{job_id}:*"
            keys = self.client.keys(pattern)
            
            results = {}
            for key in keys:
                category = key.split(':')[-1]
                data = self.client.hgetall(key)
                results[category] = data
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get processed results: {e}")
            return {}
    
    def cleanup(self):
        """리소스 정리"""
        self.stop()
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")