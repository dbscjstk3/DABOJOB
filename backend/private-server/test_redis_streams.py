#!/usr/bin/env python3
"""
Redis Streams 테스트 스크립트
"""
import sys
import logging
from pathlib import Path

# common 모듈을 import하기 위한 경로 추가
sys.path.append(str(Path(__file__).parent))

from common.redis_client import RedisStreamClient
from common.file_manager import FileManager
from common.config import TOTAL_CHAPTERS, KEYWORDS_PER_CHAPTER

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_redis_setup():
    """Redis 기본 연결 및 Consumer Group 설정 테스트"""
    logger.info("=== Redis Setup Test ===")
    
    client = RedisStreamClient()
    
    # Consumer Group 설정
    client.setup_consumer_groups()
    
    # Stream 정보 확인
    info = client.get_stream_info()
    logger.info(f"Stream info: {info}")
    
    logger.info("✅ Redis setup test completed\n")

def test_file_system():
    """파일 시스템 테스트"""
    logger.info("=== File System Test ===")
    
    mapping_id = 123
    file_mgr = FileManager(mapping_id)
    
    # 테스트 데이터 저장
    file_mgr.save_raw_data("test_saramin.json", {"company": "삼성전자", "job": "백엔드 개발자"})
    file_mgr.save_raw_data("test_dart.yml", "기업정보: 삼성전자\n사업내용: 반도체")
    
    # 챕터별 표준화 데이터 저장
    for chapter in range(1, 6):
        content = f"Chapter {chapter} 표준화된 내용입니다.\n반도체, 메모리, 시스템반도체 관련 내용..."
        file_mgr.save_standardized_chapter(chapter, f"test_chapter_{chapter}", content)
    
    # 요약 데이터 저장
    for chapter in range(1, 6):
        summary = f"Chapter {chapter} 요약: 삼성전자는 글로벌 반도체 리더입니다."
        file_mgr.save_summary(chapter, summary)
    
    # 파일 목록 확인
    files = file_mgr.list_files()
    logger.info(f"Files created: {files}")
    
    # 데이터 읽기 테스트
    summaries = file_mgr.read_all_summaries()
    logger.info(f"Read {len(summaries)} summaries")
    
    logger.info("✅ File system test completed\n")
    return file_mgr

def test_message_flow():
    """메시지 흐름 테스트"""
    logger.info("=== Message Flow Test ===")
    
    client = RedisStreamClient()
    mapping_id = 123
    
    # 1. Standardizer → Summary 메시지 (5개)
    logger.info("📤 Sending Standardizer → Summary messages...")
    for chapter in range(1, 6):
        file_path = f"/app/data/mappings/{mapping_id}/standardized/chapter_{chapter}_test.txt"
        message_id = client.send_to_summary(mapping_id, chapter, file_path)
        logger.info(f"  Sent chapter {chapter}: {message_id}")
    
    # 2. Summary → News 메시지 (5개)
    logger.info("📤 Sending Summary → News messages...")
    test_keywords = [
        ["반도체", "메모리", "파운드리"],
        ["전기차", "배터리", "자율주행"],
        ["바이오", "신약", "헬스케어"],
        ["게임", "엔터테인먼트", "콘텐츠"],
        ["금융", "핀테크", "블록체인"]
    ]
    
    for chapter, keywords in enumerate(test_keywords, 1):
        message_id = client.send_to_news(mapping_id, chapter, keywords)
        logger.info(f"  Sent chapter {chapter} with keywords: {keywords}")
    
    logger.info("✅ Message sending completed\n")

def test_message_consumption():
    """메시지 수신 테스트"""
    logger.info("=== Message Consumption Test ===")
    
    client = RedisStreamClient()
    
    # Summary Stream 수신 테스트
    logger.info("📥 Testing Summary stream consumption...")
    summary_messages = client.consume_summary("test-consumer", count=5, block=1000)
    
    for msg_id, data in summary_messages:
        logger.info(f"  Received: {msg_id} -> {data}")
        # ACK 처리
        client.ack_summary(msg_id)
    
    # News Stream 수신 테스트
    logger.info("📥 Testing News stream consumption...")
    news_messages = client.consume_news("test-consumer", count=5, block=1000)
    
    for msg_id, data in news_messages:
        logger.info(f"  Received: {msg_id} -> {data}")
        # ACK 처리
        client.ack_news(msg_id)
        
        # 완료 카운터 시뮬레이션
        mapping_id = int(data['mapping_id'])
        count = client.increment_completion_counter(mapping_id)
        logger.info(f"    Completion count for mapping_id={mapping_id}: {count}")
        
        if count == TOTAL_CHAPTERS:
            logger.info(f"    🎉 All chapters completed for mapping_id={mapping_id}")
            # 완료 알림 전송
            client.send_complete(mapping_id, f"s3://bucket/mappings/{mapping_id}/report.json")
            # 카운터 삭제
            client.delete_completion_counter(mapping_id)
    
    logger.info("✅ Message consumption completed\n")

def test_complete_pipeline():
    """전체 파이프라인 시뮬레이션"""
    logger.info("=== Complete Pipeline Simulation ===")
    
    client = RedisStreamClient()
    mapping_id = 456  # 새로운 mapping_id 사용
    
    # 1. 파일 시스템 준비
    file_mgr = FileManager(mapping_id)
    
    # 2. Standardizer 시뮬레이션
    logger.info("🔧 Simulating Standardizer Server...")
    for chapter in range(1, 6):
        # 표준화된 데이터 생성
        content = f"Chapter {chapter}: 삼성전자 분석 데이터\n키워드: 반도체, 메모리, AI칩"
        file_path = file_mgr.save_standardized_chapter(chapter, f"business_{chapter}", content)
        
        # Summary Server에 메시지 전송
        client.send_to_summary(mapping_id, chapter, file_path)
    
    # 3. Summary Server 시뮬레이션
    logger.info("📝 Simulating Summary Server...")
    summary_messages = client.consume_summary("summary-worker", count=5, block=1000)
    
    for msg_id, data in summary_messages:
        chapter = int(data['chapter'])
        
        # AI 요약 시뮬레이션
        summary_text = f"Chapter {chapter} 요약: 삼성전자는 글로벌 반도체 선도기업입니다."
        file_mgr.save_summary(chapter, summary_text)
        
        # 해시태그 추출 시뮬레이션
        keywords = ["반도체", "메모리", "시스템LSI"]  # 항상 3개
        
        # News Server에 메시지 전송
        client.send_to_news(int(data['mapping_id']), chapter, keywords)
        
        # ACK
        client.ack_summary(msg_id)
    
    # 4. News Server 시뮬레이션
    logger.info("📰 Simulating News Server...")
    news_messages = client.consume_news("news-worker", count=5, block=1000)
    
    for msg_id, data in news_messages:
        keywords = data['keywords'].split(',')
        logger.info(f"  Processing news with keywords: {keywords}")
        
        # 완료 카운터 증가
        completion_count = client.increment_completion_counter(int(data['mapping_id']))
        
        # ACK
        client.ack_news(msg_id)
        
        # 모든 챕터 완료 시
        if completion_count == TOTAL_CHAPTERS:
            logger.info("🎉 All chapters completed! Uploading to S3...")
            
            # 모든 데이터 수집
            all_summaries = file_mgr.read_all_summaries()
            logger.info(f"  Collected {len(all_summaries)} summaries")
            
            # S3 업로드 시뮬레이션
            s3_path = f"s3://bucket/mappings/{mapping_id}/final_report.json"
            client.send_complete(int(data['mapping_id']), s3_path)
            
            # 카운터 정리
            client.delete_completion_counter(int(data['mapping_id']))
    
    logger.info("✅ Complete pipeline simulation finished\n")
    return file_mgr

def cleanup_test_data(file_managers):
    """테스트 데이터 정리"""
    logger.info("=== Cleanup Test Data ===")
    
    client = RedisStreamClient()
    client.cleanup_test_data()
    
    for file_mgr in file_managers:
        file_mgr.cleanup()
    
    logger.info("✅ Cleanup completed")

def main():
    """메인 테스트 함수"""
    logger.info("🚀 Starting Redis Streams Test Suite\n")
    
    file_managers = []
    
    try:
        # 1. Redis 설정 테스트
        test_redis_setup()
        
        # 2. 파일 시스템 테스트
        file_mgr1 = test_file_system()
        file_managers.append(file_mgr1)
        
        # 3. 메시지 흐름 테스트
        test_message_flow()
        
        # 4. 메시지 수신 테스트
        test_message_consumption()
        
        # 5. 전체 파이프라인 테스트
        file_mgr2 = test_complete_pipeline()
        file_managers.append(file_mgr2)
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        # 테스트 데이터 정리
        cleanup_test_data(file_managers)

if __name__ == "__main__":
    main()