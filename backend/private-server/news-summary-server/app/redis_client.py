"""
Redis Streams 클라이언트 관리
"""
import redis
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    STREAM_SUMMARY, STREAM_NEWS, STREAM_COMPLETE,
    GROUP_SUMMARY, GROUP_NEWS
)

logger = logging.getLogger(__name__)

class RedisStreamClient:
    """Redis Streams 클라이언트"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        
    def setup_consumer_groups(self):
        """Consumer Group 설정"""
        try:
            # Summary Consumer Group
            self.redis_client.xgroup_create(
                STREAM_SUMMARY,
                GROUP_SUMMARY,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {GROUP_SUMMARY}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {GROUP_SUMMARY} already exists")
            else:
                logger.error(f"Error creating {GROUP_SUMMARY}: {e}")
                raise
                
        try:
            # News Consumer Group
            self.redis_client.xgroup_create(
                STREAM_NEWS,
                GROUP_NEWS,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {GROUP_NEWS}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {GROUP_NEWS} already exists")
            else:
                logger.error(f"Error creating {GROUP_NEWS}: {e}")
                raise
    
    def send_to_summary(self, mapping_id: int, chapter: int, file_path: str) -> str:
        """Standardizer → Summary 메시지 전송"""
        message_data = {
            'mapping_id': mapping_id,
            'chapter': chapter,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        
        message_id = self.redis_client.xadd(STREAM_SUMMARY, message_data)
        logger.info(f"Sent to {STREAM_SUMMARY}: mapping_id={mapping_id}, chapter={chapter}")
        return message_id
    
    def send_to_news(self, mapping_id: int, chapter: int, keywords: List[str]) -> str:
        """Summary → News 메시지 전송"""
        if len(keywords) != 3:
            raise ValueError(f"Keywords must be exactly 3, got {len(keywords)}")
            
        message_data = {
            'mapping_id': mapping_id,
            'chapter': chapter,
            'keywords': ','.join(keywords),
            'timestamp': datetime.now().isoformat()
        }
        
        message_id = self.redis_client.xadd(STREAM_NEWS, message_data)
        logger.info(f"Sent to {STREAM_NEWS}: mapping_id={mapping_id}, chapter={chapter}, keywords={keywords}")
        return message_id
    
    def send_complete(self, mapping_id: int, s3_path: Optional[str] = None) -> str:
        """완료 알림 전송"""
        message_data = {
            'mapping_id': mapping_id,
            'status': 'COMPLETED',
            'timestamp': datetime.now().isoformat()
        }
        
        if s3_path:
            message_data['s3_path'] = s3_path
            
        message_id = self.redis_client.xadd(STREAM_COMPLETE, message_data)
        logger.info(f"Sent completion notification: mapping_id={mapping_id}")
        return message_id
    
    def consume_summary(self, consumer_name: str, count: int = 10, block: int = 1000) -> List[Tuple[str, Dict]]:
        """Summary Stream 메시지 수신"""
        messages = self.redis_client.xreadgroup(
            GROUP_SUMMARY,
            consumer_name,
            {STREAM_SUMMARY: '>'},
            count=count,
            block=block
        )
        
        result = []
        if messages:
            for stream, stream_messages in messages:
                for msg_id, data in stream_messages:
                    result.append((msg_id, data))
                    logger.info(f"Consumed from {STREAM_SUMMARY}: {msg_id}")
        
        return result
    
    def consume_news(self, consumer_name: str, count: int = 10, block: int = 1000) -> List[Tuple[str, Dict]]:
        """News Stream 메시지 수신"""
        messages = self.redis_client.xreadgroup(
            GROUP_NEWS,
            consumer_name,
            {STREAM_NEWS: '>'},
            count=count,
            block=block
        )
        
        result = []
        if messages:
            for stream, stream_messages in messages:
                for msg_id, data in stream_messages:
                    result.append((msg_id, data))
                    logger.info(f"Consumed from {STREAM_NEWS}: {msg_id}")
        
        return result
    
    def ack_message(self, stream: str, group: str, message_id: str):
        """메시지 ACK"""
        self.redis_client.xack(stream, group, message_id)
        logger.debug(f"ACK: {stream} - {message_id}")
    
    def ack_summary(self, message_id: str):
        """Summary 메시지 ACK"""
        self.ack_message(STREAM_SUMMARY, GROUP_SUMMARY, message_id)
    
    def ack_news(self, message_id: str):
        """News 메시지 ACK"""
        self.ack_message(STREAM_NEWS, GROUP_NEWS, message_id)
    
    def increment_completion_counter(self, mapping_id: int) -> int:
        """완료 카운터 증가"""
        counter_key = f"completed:{mapping_id}"
        count = self.redis_client.incr(counter_key)
        logger.info(f"Completion counter for mapping_id={mapping_id}: {count}")
        return count
    
    def delete_completion_counter(self, mapping_id: int):
        """완료 카운터 삭제"""
        counter_key = f"completed:{mapping_id}"
        self.redis_client.delete(counter_key)
        logger.info(f"Deleted completion counter for mapping_id={mapping_id}")
    
    def get_stream_info(self) -> Dict:
        """Stream 정보 조회"""
        info = {}
        
        try:
            info['summary_length'] = self.redis_client.xlen(STREAM_SUMMARY)
            info['news_length'] = self.redis_client.xlen(STREAM_NEWS)
            info['complete_length'] = self.redis_client.xlen(STREAM_COMPLETE)
            
            # Consumer Group 정보
            try:
                info['summary_groups'] = self.redis_client.xinfo_groups(STREAM_SUMMARY)
            except:
                info['summary_groups'] = []
                
            try:
                info['news_groups'] = self.redis_client.xinfo_groups(STREAM_NEWS)
            except:
                info['news_groups'] = []
                
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            
        return info
    
    def cleanup_test_data(self):
        """테스트 데이터 정리"""
        logger.info("Cleaning up test data...")
        
        # Stream 삭제
        self.redis_client.delete(STREAM_SUMMARY)
        self.redis_client.delete(STREAM_NEWS)
        self.redis_client.delete(STREAM_COMPLETE)
        
        # 테스트 카운터 삭제
        for mapping_id in [123, 456, 789]:  # 테스트용 mapping_id들
            self.redis_client.delete(f"completed:{mapping_id}")
            
        logger.info("Cleanup complete")