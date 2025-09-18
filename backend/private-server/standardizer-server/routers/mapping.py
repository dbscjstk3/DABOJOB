"""
회사-DART 매핑 관련 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from models.database import get_db
from models.crawler import CompanyDartMapping, MappingStatus, Company
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/mapping", tags=["Company Mapping"])


class MappingVerifyRequest(BaseModel):
    """매핑 검증 요청"""
    mapping_id: int
    is_correct: bool
    verified_by: str
    notes: Optional[str] = None


class BatchMappingRequest(BaseModel):
    """배치 매핑 요청"""
    limit: int = Field(default=10, ge=1, le=100)


@router.get("/stats")
async def get_mapping_stats(db: Session = Depends(get_db)):
    """매핑 통계 조회"""
    try:
        total_companies = db.query(Company).count()

        # 매핑 상태별 집계
        unmapped = db.query(Company).filter(
            ~Company.company_id.in_(
                db.query(CompanyDartMapping.company_id)
            )
        ).count()

        pending = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_status == MappingStatus.suggested
        ).count()

        verified = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_status == MappingStatus.verified
        ).count()

        failed = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_status == MappingStatus.failed
        ).count()

        return {
            "total_companies": total_companies,
            "unmapped": unmapped,
            "pending": pending,
            "verified": verified,
            "failed": failed
        }
    except Exception as e:
        logger.error(f"Failed to get mapping stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unmapped")
async def get_unmapped_companies(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """매핑되지 않은 회사 목록"""
    try:
        companies = db.query(Company).filter(
            ~Company.company_id.in_(
                db.query(CompanyDartMapping.company_id)
            )
        ).limit(limit).all()

        return [
            {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "company_url": company.company_url,
                "company_scale": company.company_scale,
                "created_at": company.created_at.isoformat(),
                "job_postings_count": len(company.job_postings) if company.job_postings else 0
            }
            for company in companies
        ]
    except Exception as e:
        logger.error(f"Failed to get unmapped companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_mappings(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """검증 대기 중인 매핑 목록"""
    try:
        mappings = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_status == MappingStatus.suggested
        ).order_by(CompanyDartMapping.created_at.desc()).limit(limit).all()

        return [
            {
                "mapping_id": mapping.mapping_id,
                "company_name": mapping.crawled_company_name,
                "company_url": mapping.crawled_company_url,
                "dart_corp_name": mapping.dart_corp_name,
                "dart_corp_code": mapping.dart_corp_code,
                "dart_stock_code": mapping.dart_stock_code,
                "confidence_score": mapping.confidence_score,
                "mapping_status": mapping.mapping_status.value,
                "created_at": mapping.created_at.isoformat(),
                "processed_at": mapping.processed_at.isoformat() if mapping.processed_at else None
            }
            for mapping in mappings
        ]
    except Exception as e:
        logger.error(f"Failed to get pending mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-map")
async def start_auto_mapping(
    background_tasks: BackgroundTasks,
    request: BatchMappingRequest = BatchMappingRequest()
):
    """자동 매핑 배치 작업 시작"""
    try:
        # TODO: 서비스 레이어에서 자동 매핑 처리
        # mapping_service = CompanyMappingService()
        # background_tasks.add_task(mapping_service.batch_process_mappings, request.limit)

        return {
            "status": "started",
            "message": f"자동 매핑 작업이 시작되었습니다. (최대 {request.limit}개 회사)",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start auto mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_mapping(
    request: MappingVerifyRequest,
    db: Session = Depends(get_db)
):
    """매핑 결과 수동 검증"""
    try:
        mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_id == request.mapping_id
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

        # 매핑 상태 업데이트
        mapping.mapping_status = MappingStatus.verified if request.is_correct else MappingStatus.rejected
        mapping.verified_at = datetime.utcnow()
        mapping.verified_by = request.verified_by
        mapping.manual_notes = request.notes

        db.commit()

        return {
            "status": "success",
            "message": "매핑이 성공적으로 검증되었습니다.",
            "mapping_id": request.mapping_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to verify mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping/{mapping_id}")
async def get_mapping_detail(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """특정 매핑 상세 정보"""
    try:
        mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_id == mapping_id
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

        return {
            "mapping_id": mapping.mapping_id,
            "company_id": mapping.company_id,
            "crawled_company_name": mapping.crawled_company_name,
            "crawled_company_url": mapping.crawled_company_url,
            "dart_corp_code": mapping.dart_corp_code,
            "dart_corp_name": mapping.dart_corp_name,
            "dart_stock_code": mapping.dart_stock_code,
            "mapping_status": mapping.mapping_status.value,
            "confidence_score": mapping.confidence_score,
            "gpt_response": mapping.gpt_response,
            "manual_notes": mapping.manual_notes,
            "processed_at": mapping.processed_at.isoformat() if mapping.processed_at else None,
            "verified_at": mapping.verified_at.isoformat() if mapping.verified_at else None,
            "verified_by": mapping.verified_by,
            "created_at": mapping.created_at.isoformat(),
            "updated_at": mapping.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mapping detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verified-companies")
async def get_verified_companies(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """검증 완료된 회사 목록"""
    try:
        mappings = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_status == MappingStatus.verified,
            CompanyDartMapping.dart_corp_code.isnot(None)
        ).order_by(CompanyDartMapping.verified_at.desc()).limit(limit).all()

        return [
            {
                "company_id": mapping.company_id,
                "company_name": mapping.crawled_company_name,
                "dart_corp_code": mapping.dart_corp_code,
                "dart_corp_name": mapping.dart_corp_name,
                "dart_stock_code": mapping.dart_stock_code,
                "verified_at": mapping.verified_at.isoformat() if mapping.verified_at else None,
                "verified_by": mapping.verified_by
            }
            for mapping in mappings
        ]
    except Exception as e:
        logger.error(f"Failed to get verified companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))