"""
회사명 매핑 워크플로우
크롤링 완료 후 자동으로 DART 매핑 실행
"""

import os
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from ..services.company_mapper import CompanyMappingService
from ..database import SessionLocal
from ..models.crawler_models import Company, CompanyDartMapping, MappingStatus

logger = logging.getLogger(__name__)


class MappingWorkflow:
    """회사명 매핑 워크플로우 관리"""

    def __init__(self):
        self.mapping_service = CompanyMappingService()
        self.auto_mapping_enabled = os.getenv("AUTO_MAPPING_ENABLED", "false").lower() == "true"
        self.batch_size = int(os.getenv("MAPPING_BATCH_SIZE", "10"))
        self.confidence_threshold = int(os.getenv("MAPPING_CONFIDENCE_THRESHOLD", "80"))

    async def process_new_companies(self) -> Dict[str, Any]:
        """새로 크롤링된 회사들에 대해 자동 매핑 실행"""
        if not self.auto_mapping_enabled:
            logger.info("Auto mapping is disabled")
            return {"status": "disabled", "processed": 0}

        try:
            logger.info("Starting automatic company mapping workflow")

            # 배치 처리 실행
            stats = await self.mapping_service.batch_process_mappings(self.batch_size)

            logger.info(f"Mapping workflow completed: {stats}")

            # 고신뢰도 매핑 자동 검증
            await self._auto_verify_high_confidence_mappings()

            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                **stats
            }

        except Exception as e:
            logger.error(f"Mapping workflow error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _auto_verify_high_confidence_mappings(self):
        """신뢰도가 높은 매핑을 자동으로 검증"""
        db = SessionLocal()
        try:
            # 높은 신뢰도의 제안된 매핑들 조회
            high_confidence_mappings = db.query(CompanyDartMapping)\
                .filter(CompanyDartMapping.mapping_status == MappingStatus.suggested)\
                .filter(CompanyDartMapping.confidence_score >= self.confidence_threshold)\
                .all()

            verified_count = 0
            for mapping in high_confidence_mappings:
                # 자동 검증
                success = self.mapping_service.verify_mapping(
                    db=db,
                    mapping_id=mapping.mapping_id,
                    verified_by="auto_system",
                    is_correct=True,
                    notes=f"Auto-verified (confidence: {mapping.confidence_score}%)"
                )

                if success:
                    verified_count += 1
                    logger.info(f"Auto-verified mapping for {mapping.crawled_company_name}")

            if verified_count > 0:
                logger.info(f"Auto-verified {verified_count} high-confidence mappings")

        except Exception as e:
            logger.error(f"Auto verification error: {e}")
        finally:
            db.close()

    async def run_periodic_mapping(self):
        """주기적 매핑 작업 (스케줄러용)"""
        logger.info("Running periodic mapping check")

        # 매핑되지 않은 회사 수 확인
        db = SessionLocal()
        try:
            unmapped_count = len(self.mapping_service.get_unmapped_companies(db, limit=1000))

            if unmapped_count > 0:
                logger.info(f"Found {unmapped_count} unmapped companies, starting batch mapping")
                await self.process_new_companies()
            else:
                logger.info("No unmapped companies found")

        finally:
            db.close()

    def get_mapping_summary(self) -> Dict[str, Any]:
        """매핑 현황 요약"""
        db = SessionLocal()
        try:
            stats = self.mapping_service.get_mapping_stats(db)

            # 추가 통계 계산
            total_mapped = stats.get("verified", 0) + stats.get("suggested", 0)
            mapping_rate = (total_mapped / stats["total_companies"] * 100) if stats["total_companies"] > 0 else 0

            return {
                "total_companies": stats["total_companies"],
                "mapping_rate": round(mapping_rate, 2),
                "verified_mappings": stats.get("verified", 0),
                "pending_verification": stats.get("suggested", 0),
                "unmapped": stats.get("unmapped", 0),
                "failed": stats.get("failed", 0),
                "last_updated": datetime.now().isoformat()
            }

        finally:
            db.close()


# 전역 워크플로우 인스턴스
mapping_workflow = MappingWorkflow()


async def trigger_mapping_after_crawl():
    """크롤링 완료 후 호출되는 매핑 트리거 함수"""
    logger.info("Triggering company mapping after crawl completion")

    # 짧은 지연 후 매핑 시작 (크롤링 트랜잭션 완료 대기)
    await asyncio.sleep(5)

    result = await mapping_workflow.process_new_companies()
    logger.info(f"Post-crawl mapping result: {result}")

    return result