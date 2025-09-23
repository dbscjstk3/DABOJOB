#!/usr/bin/env python3
"""
매핑이 완료된 기업들에 대해 DART 추출 작업을 트리거하는 스크립트
"""
import asyncio
import sys
import os
from datetime import datetime

# 환경변수 설정
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['DB_HOST'] = 'localhost'

# 경로 추가
sys.path.append('backend/private-server/standardizer-server')

from app.utils.redis_helper import redis_helper
from app.database import SessionLocal
from app.models.crawler_models import CompanyDartMapping, MappingStatus


async def trigger_dart_extraction():
    """매핑이 완료된 회사들의 DART 추출 트리거"""

    # Redis 초기화
    await redis_helper.setup_streams()

    # DB에서 매핑 완료된 회사 조회
    db = SessionLocal()
    try:
        # verified 상태의 회사들 조회
        verified_mappings = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_status == MappingStatus.verified,
            CompanyDartMapping.dart_corp_code.isnot(None)
        ).all()

        print(f"📋 Found {len(verified_mappings)} verified companies")

        for mapping in verified_mappings:
            # DART 추출 작업 큐에 추가
            dart_job_data = {
                "job_id": f"manual_dart_extract_{mapping.mapping_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "mapping_id": mapping.mapping_id,
                "company_name": mapping.crawled_company_name,
                "dart_corp_name": mapping.dart_corp_name,
                "dart_corp_code": mapping.dart_corp_code,
                "report_type": "annual",
                "submitted_at": datetime.now().isoformat()
            }

            await redis_helper.add_job("dart_extract_stream", dart_job_data)
            print(f"✅ DART extraction queued for {mapping.crawled_company_name} → {mapping.dart_corp_name} (Code: {mapping.dart_corp_code})")

    finally:
        db.close()

    print("🎯 All DART extraction jobs queued successfully!")


if __name__ == "__main__":
    asyncio.run(trigger_dart_extraction())