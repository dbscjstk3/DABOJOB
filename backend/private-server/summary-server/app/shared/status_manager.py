"""
공통 상태 관리자 - Summary Server용
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class JobStage(Enum):
    """파이프라인 단계"""
    MAPPING = "mapping"
    SUMMARY = "summary"
    NEWS = "news"

class JobStatus(Enum):
    """작업 상태"""
    # Mapping 단계
    MAPPING_PENDING = "mapping_pending"
    MAPPING_PROCESSING = "mapping_processing"
    MAPPING_SUGGESTED = "mapping_suggested"      # 95% 미만
    MAPPING_VERIFIED = "mapping_verified"        # 95% 이상 또는 수동 확정
    MAPPING_FAILED = "mapping_failed"

    # Summary 단계
    SUMMARY_PROCESSING = "summary_processing"
    SUMMARY_COMPLETED = "summary_completed"      # complete
    SUMMARY_FAILED = "summary_failed"

    # News 단계
    NEWS_PROCESSING = "news_processing"          # processing
    NEWS_COMPLETED = "news_completed"            # complete (뉴스 요약 완료)
    NEWS_FINISHED = "news_finished"              # finish (S3 업로드 완료)
    NEWS_FAILED = "news_failed"

class SharedStatusManager:
    """모든 서버가 공유하는 상태 관리자"""

    def __init__(self, redis_url: str = None):
        import os
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis: Optional[redis.Redis] = None
        self.status_prefix = "job:status:"
        self.event_channel = "job:events"

    async def initialize(self):
        """Redis 연결 초기화"""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info(f"SharedStatusManager connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Redis 연결 실패해도 메인 로직은 계속 동작하도록
            self.redis = None

    async def get_job_status(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        if not self.redis:
            return None

        try:
            key = f"{self.status_prefix}{mapping_id}"
            data = await self.redis.hget(key, "data")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get job status for {mapping_id}: {e}")
            return None

    async def update_job_status(
        self,
        mapping_id: int,
        stage: JobStage,
        status: JobStatus,
        data: Optional[Dict[str, Any]] = None,
        service_name: str = "unknown"
    ):
        """작업 상태 업데이트 (비동기, 실패해도 메인 로직에 영향 없음)"""
        if not self.redis:
            logger.warning("Redis not available, skipping status update")
            return

        try:
            key = f"{self.status_prefix}{mapping_id}"

            # 기존 상태 가져오기
            current_data = await self.get_job_status(mapping_id)
            if not current_data:
                current_data = {
                    "mapping_id": mapping_id,
                    "created_at": datetime.now().isoformat(),
                    "stages": {}
                }

            # 스테이지 데이터 업데이트
            stage_data = {
                "status": status.value,
                "updated_at": datetime.now().isoformat(),
                "service": service_name
            }

            if data:
                stage_data.update(data)

            current_data["stages"][stage.value] = stage_data
            current_data["current_status"] = self._determine_overall_status(current_data["stages"])
            current_data["updated_at"] = datetime.now().isoformat()

            # Redis에 저장
            await self.redis.hset(key, "data", json.dumps(current_data))
            await self.redis.expire(key, 86400 * 7)  # 7일 TTL

            # 이벤트 발행
            await self._publish_status_event(mapping_id, stage, status, stage_data)

            logger.info(f"Status updated: {mapping_id} -> {stage.value}:{status.value}")

        except Exception as e:
            logger.error(f"Failed to update job status (non-critical): {e}")
            # 상태 업데이트 실패는 메인 로직에 영향 주지 않음

    def _determine_overall_status(self, stages: Dict[str, Any]) -> str:
        """전체 상태 결정 로직"""
        news_status = stages.get("news", {}).get("status")
        summary_status = stages.get("summary", {}).get("status")
        mapping_status = stages.get("mapping", {}).get("status")

        # News 단계 상태 우선
        if news_status == "news_finished":
            return "finished"
        elif news_status == "news_completed":
            return "news_completed"
        elif news_status == "news_processing":
            return "news_processing"
        elif news_status == "news_failed":
            return "news_failed"

        # Summary 단계 상태
        elif summary_status == "summary_completed":
            return "summary_completed"
        elif summary_status == "summary_processing":
            return "summary_processing"
        elif summary_status == "summary_failed":
            return "summary_failed"

        # Mapping 단계 상태
        elif mapping_status == "mapping_verified":
            return "mapping_verified"
        elif mapping_status == "mapping_suggested":
            return "mapping_suggested"
        elif mapping_status == "mapping_processing":
            return "mapping_processing"
        elif mapping_status == "mapping_failed":
            return "mapping_failed"
        else:
            return "mapping_pending"

    async def _publish_status_event(
        self,
        mapping_id: int,
        stage: JobStage,
        status: JobStatus,
        data: Dict[str, Any]
    ):
        """상태 변경 이벤트 발행"""
        if not self.redis:
            return

        try:
            event = {
                "mapping_id": mapping_id,
                "stage": stage.value,
                "status": status.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            await self.redis.publish(self.event_channel, json.dumps(event))

        except Exception as e:
            logger.error(f"Failed to publish status event: {e}")

    async def close(self):
        """연결 종료"""
        if self.redis:
            try:
                await self.redis.aclose()
            except:
                pass