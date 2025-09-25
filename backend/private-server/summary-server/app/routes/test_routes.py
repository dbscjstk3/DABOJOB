"""
전체 파이프라인 테스트 API
하드코딩된 데이터로 요약 → 해시태그 → news 전송까지 한 번에 테스트
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..services.redis_publisher import RedisPublisher
from ..services.hashtag_extractor import HashtagExtractor
from ..services.file_manager import FileManager
from ..routes.summary_routes import get_ollama_client
from ..database import get_db
from ..models.crawler_models import Company, CompanyDartMapping, MappingStatus
from sqlalchemy.orm import Session
from fastapi import Depends
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["Pipeline Test"])

class TestRequest(BaseModel):
    test_name: str = "전체파이프라인테스트"

@router.post("/full-pipeline")
async def test_full_pipeline(request: TestRequest):
    """
    🧪 전체 파이프라인 테스트 (하드코딩 데이터)
    테스트 회사 → 요약 → 해시태그 → news 전송까지 한 번에
    """
    try:
        test_id = f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🧪 전체 파이프라인 테스트 시작: {test_id}")

        # 하드코딩된 테스트 데이터 (5개 카테고리)
        test_summaries = {
            "business_overview": """
            삼성전자는 1969년 설립된 대한민국 최대 전자기업입니다.
            메모리 반도체 세계 1위, 스마트폰 글로벌 점유율 상위권을 유지하며
            반도체, 디스플레이, 모바일, 가전 등 다양한 IT 제품을 생산합니다.
            수원 본사를 비롯해 전 세계 74개국에 사업장을 운영하고 있습니다.
            """,

            "products_services": """
            주력 제품으로는 갤럭시 시리즈 스마트폰, DRAM/NAND 메모리,
            OLED/QLED 디스플레이, 삼성 TV, 냉장고, 세탁기 등이 있습니다.
            B2B 영역에서는 서버용 SSD, 네트워크 장비, 반도체 파운드리 서비스를 제공하며
            최근에는 폴더블폰과 8K TV 시장을 선도하고 있습니다.
            """,

            "revenue_orders": """
            2023년 연결 매출액 258조원을 달성했습니다.
            DS(반도체) 부문이 전체 매출의 약 60%를 차지하며,
            주요 고객사는 Apple, Google, Amazon, Microsoft 등입니다.
            중국 시장 점유율 20%, 북미 시장 25%를 기록하고 있으며
            갤럭시 S24 시리즈 출시로 모바일 매출이 전년 대비 15% 증가했습니다.
            """,

            "contracts_rnd": """
            연간 R&D 투자 22조원을 집행하며 3나노 반도체 공정 개발에 집중하고 있습니다.
            퀄컴과 5G 모뎀 칩셋 공동개발 계약을 체결했고,
            AMD와 GPU 기술 라이선스 계약을 연장했습니다.
            차세대 QD-OLED 기술 개발을 위해 독일 머크와 소재 공급 계약을 맺었습니다.
            """,

            "other_references": """
            2050년 탄소중립 달성을 위해 RE100에 가입했습니다.
            삼성디스플레이는 별도 자회사로 분리 운영되며,
            반도체 부문에서는 파운드리 사업 확대를 추진하고 있습니다.
            ESG 경영을 강화하여 다우존스 지속가능성 지수(DJSI)에 6년 연속 편입되었습니다.
            """
        }

        # FileManager를 통해 파일로 저장 (실제 플로우와 동일)
        file_manager = FileManager()

        # mapping_id는 99999로 테스트용 설정
        test_mapping_id = 99999

        logger.info(f"📁 테스트 요약 파일 저장 시작: mapping_id={test_mapping_id}")

        for category, summary in test_summaries.items():
            file_manager.save_summary(test_id, category, summary)
            logger.info(f"  ✅ {category}: {len(summary)}자 저장")

        # Redis Publisher 및 HashtagExtractor 초기화
        publisher = RedisPublisher()

        # Ollama 클라이언트 설정
        ollama_client = get_ollama_client()
        model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
        extractor = HashtagExtractor(ollama_client, model_name)

        logger.info(f"🏷️ 해시태그 추출 및 news 전송 시작")

        # 해시태그 추출 및 스트리밍 전송 (실제 로직과 동일)
        hashtags = await extractor.extract_hashtags_streaming(test_id, test_summaries, publisher)

        # 정리
        extractor.cleanup()
        publisher.cleanup()

        total_hashtags = sum(len(tags) for tags in hashtags.values())

        logger.info(f"✅ 전체 파이프라인 테스트 완료!")
        logger.info(f"  📊 처리된 카테고리: {len(test_summaries)}개")
        logger.info(f"  🏷️ 추출된 해시태그: {total_hashtags}개")
        logger.info(f"  📡 Redis stream:news로 전송 완료")

        return {
            "success": True,
            "test_id": test_id,
            "test_name": request.test_name,
            "test_mapping_id": test_mapping_id,
            "summary": {
                "categories_processed": len(test_summaries),
                "total_characters": sum(len(s) for s in test_summaries.values()),
                "files_saved": [f"mapping_{test_mapping_id}/summaries/{cat}_summary.txt" for cat in test_summaries.keys()]
            },
            "hashtags": {
                "total_extracted": total_hashtags,
                "by_category": {cat: len(tags) for cat, tags in hashtags.items()},
                "all_hashtags": hashtags
            },
            "pipeline_completed": [
                "✅ 1. 테스트 요약 데이터 생성",
                "✅ 2. 파일 시스템에 저장",
                "✅ 3. 해시태그 추출 (Ollama)",
                "✅ 4. Redis stream:news로 전송",
                "✅ 5. 뉴스 서버에서 매칭 대기"
            ],
            "message": f"🎉 전체 파이프라인 테스트 완료! {total_hashtags}개 해시태그를 news 서버로 전송했습니다."
        }

    except Exception as e:
        logger.error(f"❌ 전체 파이프라인 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.post("/quick-news-test/{mapping_id}")
async def quick_news_test(mapping_id: int):
    """
    ⚡ 기존 mapping_id의 요약으로 news 전송 테스트
    """
    try:
        test_id = f"news_test_{mapping_id}_{datetime.now().strftime('%H%M%S')}"
        logger.info(f"⚡ News 전송 테스트: mapping_id={mapping_id}")

        file_manager = FileManager()

        # 기존 요약 파일 읽기
        summaries = file_manager.get_summary_results(str(mapping_id))
        if not summaries:
            raise HTTPException(status_code=404, detail=f"mapping_id {mapping_id}에 요약 파일이 없습니다")

        # Redis Publisher 및 HashtagExtractor 초기화
        publisher = RedisPublisher()
        ollama_client = get_ollama_client()
        model_name = os.getenv('SUMMARY_MODEL', 'llama3.2:1b-instruct-fp16')
        extractor = HashtagExtractor(ollama_client, model_name)

        # 해시태그 추출 및 전송
        hashtags = await extractor.extract_hashtags_streaming(test_id, summaries, publisher)

        # 정리
        extractor.cleanup()
        publisher.cleanup()

        total_hashtags = sum(len(tags) for tags in hashtags.values())

        return {
            "success": True,
            "test_id": test_id,
            "mapping_id": mapping_id,
            "found_summaries": list(summaries.keys()),
            "total_hashtags": total_hashtags,
            "hashtags": hashtags,
            "message": f"✅ mapping_id {mapping_id}의 요약으로 {total_hashtags}개 해시태그를 news 서버로 전송!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"News 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def test_health():
    """🏥 테스트 API 상태"""
    return {
        "status": "healthy",
        "message": "파이프라인 테스트 API 정상 작동",
        "available_tests": [
            "POST /test/full-pipeline - 하드코딩 데이터로 전체 테스트",
            "POST /test/quick-news-test/{mapping_id} - 기존 요약으로 news 테스트"
        ]
    }