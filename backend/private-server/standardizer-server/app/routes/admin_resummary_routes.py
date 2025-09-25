"""
Admin 재요약 관리 API
완료된 보고서의 품질 검토 및 재요약 요청 관리
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from ..database import get_db
from ..models.resummary_models import (
    SummaryVersion, ResummaryRequest, VersionComparison
)
from ..services.resummary_service import ResummaryService
from ..shared.status_integration import standardizer_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/resummary", tags=["Admin Resummary"])

# ==========================================
# Pydantic Models
# ==========================================

class QualityReviewRequest(BaseModel):
    """품질 검토 요청"""
    quality_score: int = Field(..., ge=1, le=5, description="품질 점수 (1-5)")
    quality_issues: List[str] = Field(default=[], description="품질 문제점")
    admin_notes: Optional[str] = Field(None, description="관리자 메모")
    action: str = Field(..., description="액션: approve, resummary, archive")

class ResummaryTriggerRequest(BaseModel):
    """재요약 요청"""
    reason: str = Field(..., description="재요약 이유")
    requested_by: str = Field(..., description="요청자")
    priority: str = Field(default="normal", description="우선순위: high, normal, low")
    quality_issues: List[str] = Field(default=[], description="품질 문제점")

class AdminDashboardResponse(BaseModel):
    """관리자 대시보드 응답"""
    total_completed: int
    needs_review: int
    poor_quality: int
    in_resummary: int
    recent_completions: List[Dict[str, Any]]

class CompletedReportResponse(BaseModel):
    """완료된 보고서 응답"""
    mapping_id: int
    version_number: int
    company_name: str
    dart_corp_name: Optional[str]
    status: str
    quality_score: Optional[int]
    quality_status: str
    completed_at: Optional[datetime]
    total_news_count: int
    resummary_count: int
    chapters: List[Dict[str, Any]]

class ResummaryStatusResponse(BaseModel):
    """재요약 상태 응답"""
    mapping_id: int
    current_version: int
    status: str
    progress: Dict[str, Any]
    estimated_completion: Optional[datetime]

# ==========================================
# Dependencies
# ==========================================

def get_resummary_service(db: Session = Depends(get_db)):
    """재요약 서비스 의존성"""
    return ResummaryService(db)

# ==========================================
# Admin Dashboard APIs
# ==========================================

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    관리자 대시보드 - 전체 현황 요약
    """
    try:
        dashboard_data = await resummary_service.get_dashboard_summary()
        return AdminDashboardResponse(**dashboard_data)
    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/completed-reports", response_model=List[CompletedReportResponse])
async def get_completed_reports(
    quality_filter: Optional[str] = Query(None, description="품질 필터: needs_review, poor_quality, good_quality"),
    limit: int = Query(50, description="결과 개수 제한"),
    offset: int = Query(0, description="오프셋"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    완료된 보고서 목록 조회 (품질별 필터링 지원)
    """
    try:
        reports = await resummary_service.get_completed_reports(
            quality_filter=quality_filter,
            limit=limit,
            offset=offset
        )
        return [CompletedReportResponse(**report) for report in reports]
    except Exception as e:
        logger.error(f"Failed to get completed reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{mapping_id}", response_model=CompletedReportResponse)
async def get_report_detail(
    mapping_id: int,
    version: Optional[int] = Query(None, description="특정 버전 조회"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    특정 보고서 상세 조회
    """
    try:
        report = await resummary_service.get_report_detail(mapping_id, version)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return CompletedReportResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Quality Review APIs
# ==========================================

@router.post("/review/{mapping_id}")
async def review_report_quality(
    mapping_id: int,
    review: QualityReviewRequest,
    version: Optional[int] = Query(None, description="검토할 버전"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    보고서 품질 검토 및 액션 결정
    - approve: 품질 승인, 완료 처리
    - resummary: 재요약 요청
    - archive: 아카이브 처리
    """
    try:
        result = await resummary_service.review_report_quality(
            mapping_id=mapping_id,
            version=version,
            quality_score=review.quality_score,
            quality_issues=review.quality_issues,
            admin_notes=review.admin_notes,
            action=review.action
        )

        # 재요약 액션인 경우 자동으로 재요약 큐에 추가
        if review.action == "resummary":
            await resummary_service.trigger_resummary(
                mapping_id=mapping_id,
                reason=f"Quality review: score {review.quality_score}/5",
                requested_by="admin_review",
                quality_issues=review.quality_issues
            )

        return {
            "success": True,
            "action": review.action,
            "mapping_id": mapping_id,
            "version": result.get("version"),
            "message": f"Report {review.action} completed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to review report quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/needs-review")
async def get_reports_needing_review(
    limit: int = Query(20, description="결과 개수 제한"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    검토가 필요한 보고서 목록 (quality_score가 null인 완료된 보고서)
    """
    try:
        reports = await resummary_service.get_reports_needing_review(limit)
        return {
            "total_count": len(reports),
            "reports": reports
        }
    except Exception as e:
        logger.error(f"Failed to get reports needing review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Re-summarization APIs
# ==========================================

@router.post("/trigger/{mapping_id}")
async def trigger_resummary(
    mapping_id: int,
    request: ResummaryTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    재요약 수동 요청 - 백그라운드에서 비동기 처리
    """
    try:
        # 현재 상태 확인
        current_status = await standardizer_status.get_job_status(mapping_id)
        if current_status != "news_completed":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resummary job in status: {current_status}"
            )

        # 백그라운드 태스크로 재요약 작업 추가
        async def process_resummary():
            try:
                logger.info(f"Starting background resummary for mapping_id: {mapping_id}")
                result = await resummary_service.trigger_resummary(
                    mapping_id=mapping_id,
                    reason=request.reason,
                    requested_by=request.requested_by,
                    priority=request.priority,
                    quality_issues=request.quality_issues
                )
                logger.info(f"Resummary queued successfully: {result}")
            except Exception as e:
                logger.error(f"Background resummary failed: {e}")

        # 백그라운드 태스크 추가
        background_tasks.add_task(process_resummary)

        # 즉시 응답 반환 (서버 블로킹 방지)
        return {
            "success": True,
            "status": "queued",
            "mapping_id": mapping_id,
            "message": f"Re-summarization request queued for mapping {mapping_id}. Check status endpoint for progress."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger resummary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{mapping_id}", response_model=ResummaryStatusResponse)
async def get_resummary_status(
    mapping_id: int,
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    재요약 진행 상태 조회
    """
    try:
        status = await resummary_service.get_resummary_status(mapping_id)
        if not status:
            raise HTTPException(status_code=404, detail="No resummary found")
        return ResummaryStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resummary status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue")
async def get_resummary_queue(
    status_filter: Optional[str] = Query(None, description="상태 필터: requested, processing, failed"),
    limit: int = Query(20, description="결과 개수 제한"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    재요약 큐 상태 조회
    """
    try:
        queue = await resummary_service.get_resummary_queue(status_filter, limit)
        return {
            "total_in_queue": len(queue),
            "queue": queue
        }
    except Exception as e:
        logger.error(f"Failed to get resummary queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Version Management APIs
# ==========================================

@router.get("/versions/{mapping_id}")
async def get_version_history(
    mapping_id: int,
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    특정 매핑의 모든 버전 이력 조회
    """
    try:
        versions = await resummary_service.get_version_history(mapping_id)
        return {
            "mapping_id": mapping_id,
            "total_versions": len(versions),
            "versions": versions
        }
    except Exception as e:
        logger.error(f"Failed to get version history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare/{mapping_id}")
async def compare_versions(
    mapping_id: int,
    version1: int = Query(..., description="비교할 첫 번째 버전"),
    version2: int = Query(..., description="비교할 두 번째 버전"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    두 버전 간 비교 분석
    """
    try:
        comparison = await resummary_service.compare_versions(mapping_id, version1, version2)
        return comparison
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Statistics APIs
# ==========================================

@router.get("/stats/quality")
async def get_quality_statistics(
    days: int = Query(30, description="통계 기간 (일)"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    품질 통계 조회
    """
    try:
        stats = await resummary_service.get_quality_statistics(days)
        return stats
    except Exception as e:
        logger.error(f"Failed to get quality statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/resummary")
async def get_resummary_statistics(
    days: int = Query(30, description="통계 기간 (일)"),
    db: Session = Depends(get_db),
    resummary_service: ResummaryService = Depends(get_resummary_service)
):
    """
    재요약 통계 조회
    """
    try:
        stats = await resummary_service.get_resummary_statistics(days)
        return stats
    except Exception as e:
        logger.error(f"Failed to get resummary statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))