"""
회사명-DART 매핑 관리 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from ..utils.redis_helper import redis_helper

from ..database import get_db
from ..services.company_mapper import CompanyMappingService
from ..models.crawler_models import CompanyDartMapping, MappingStatus, Company
from ..workflows.mapping_workflow import mapping_workflow

router = APIRouter(prefix="/api/mapping", tags=["Company Mapping"])

# 서비스 인스턴스
mapping_service = CompanyMappingService()


# Pydantic 모델
class MappingVerifyRequest(BaseModel):
    """매핑 검증 요청 모델"""
    mapping_id: int
    is_correct: bool
    verified_by: str
    notes: Optional[str] = None


class BatchMappingRequest(BaseModel):
    """배치 매핑 요청 모델"""
    limit: int = Field(default=1000, ge=1, le=10000)


class MappingResponse(BaseModel):
    """매핑 응답 모델"""
    mapping_id: int
    company_name: str
    company_url: Optional[str]
    dart_corp_name: Optional[str]
    dart_corp_code: Optional[str]
    dart_stock_code: Optional[str]
    confidence_score: Optional[int]
    mapping_status: str
    created_at: datetime
    processed_at: Optional[datetime]


class MappingStatsResponse(BaseModel):
    """매핑 통계 응답 모델"""
    total_companies: int
    unmapped: int
    suggested: Optional[int] = 0
    verified: Optional[int] = 0
    failed: Optional[int] = 0
    pending: Optional[int] = 0
    processing: Optional[int] = 0
    rejected: Optional[int] = 0


@router.get("/stats", response_model=MappingStatsResponse)
async def get_mapping_stats(db: Session = Depends(get_db)):
    """매핑 통계 조회"""
    try:
        stats = mapping_service.get_mapping_stats(db)
        return MappingStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unmapped", response_model=List[Dict[str, Any]])
async def get_unmapped_companies(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """매핑되지 않은 회사 목록 조회"""
    try:
        companies = mapping_service.get_unmapped_companies(db, limit)

        return [
            {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "company_url": company.company_url,
                "company_scale": company.company_scale,
                "created_at": company.created_at,
                "job_postings_count": len(company.job_postings) if company.job_postings else 0
            }
            for company in companies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=List[MappingResponse])
async def get_pending_mappings(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """검증 대기 중인 매핑 목록 조회"""
    try:
        mappings = mapping_service.get_pending_mappings(db, limit)

        return [
            MappingResponse(
                mapping_id=mapping.mapping_id,
                company_name=mapping.crawled_company_name,
                company_url=mapping.crawled_company_url,
                dart_corp_name=mapping.dart_corp_name,
                dart_corp_code=mapping.dart_corp_code,
                dart_stock_code=mapping.dart_stock_code,
                confidence_score=mapping.confidence_score,
                mapping_status=mapping.mapping_status.value,
                created_at=mapping.created_at,
                processed_at=mapping.processed_at
            )
            for mapping in mappings
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-map")
async def start_auto_mapping(
    background_tasks: BackgroundTasks,
    request: BatchMappingRequest = BatchMappingRequest()
):
    """자동 매핑 배치 작업 시작 (파이프라인 포함)"""
    try:

        # Redis 스트림에 매핑 작업 추가 (Background Worker가 처리하여 파이프라인 연결)
        job_data = {
            "job_id": f"manual_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "trigger": "manual_auto_mapping",
            "limit": request.limit,
            "submitted_at": datetime.now().isoformat()
        }

        await redis_helper.add_job("mapping_stream", job_data)

        return {
            "status": "queued",
            "job_id": job_data['job_id'],
            "message": f"자동 매핑 작업이 큐에 추가되었습니다. (최대 {request.limit}개 회사) - 매핑 완료 후 DART 추출 및 표준화 자동 실행",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_mapping(
    request: MappingVerifyRequest,
    db: Session = Depends(get_db)
):
    """매핑 결과 수동 검증"""
    try:
        success = mapping_service.verify_mapping(
            db=db,
            mapping_id=request.mapping_id,
            verified_by=request.verified_by,
            is_correct=request.is_correct,
            notes=request.notes
        )

        if success:
            return {
                "status": "success",
                "message": "매핑이 성공적으로 검증되었습니다.",
                "mapping_id": request.mapping_id
            }
        else:
            raise HTTPException(status_code=404, detail="매핑을 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping/{mapping_id}")
async def get_mapping_detail(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """특정 매핑 상세 정보 조회"""
    try:
        mapping = db.query(CompanyDartMapping)\
            .filter(CompanyDartMapping.mapping_id == mapping_id)\
            .first()

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
            "processed_at": mapping.processed_at,
            "verified_at": mapping.verified_at,
            "verified_by": mapping.verified_by,
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-map")
async def create_manual_mapping(
    company_id: int,
    dart_corp_code: Optional[str] = None,
    dart_corp_name: Optional[str] = None,
    dart_stock_code: Optional[str] = None,
    verified_by: str = "manual",
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """수동 매핑 생성"""
    try:
        # 회사 존재 확인
        company = db.query(Company)\
            .filter(Company.company_id == company_id)\
            .first()

        if not company:
            raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

        # 기존 매핑 확인
        existing = db.query(CompanyDartMapping)\
            .filter(CompanyDartMapping.company_id == company_id)\
            .first()

        if existing:
            # 기존 매핑 업데이트
            existing.dart_corp_code = dart_corp_code
            existing.dart_corp_name = dart_corp_name
            existing.dart_stock_code = dart_stock_code
            existing.mapping_status = MappingStatus.verified
            existing.confidence_score = 100  # 수동 매핑은 100% 신뢰도
            existing.verified_at = datetime.utcnow()
            existing.verified_by = verified_by
            existing.manual_notes = notes
            mapping = existing
        else:
            # 새 매핑 생성
            mapping = CompanyDartMapping(
                company_id=company_id,
                crawled_company_name=company.company_name,
                crawled_company_url=company.company_url,
                dart_corp_code=dart_corp_code,
                dart_corp_name=dart_corp_name,
                dart_stock_code=dart_stock_code,
                mapping_status=MappingStatus.verified,
                confidence_score=100,
                verified_at=datetime.utcnow(),
                verified_by=verified_by,
                manual_notes=notes
            )
            db.add(mapping)

        db.commit()

        return {
            "status": "success",
            "message": "수동 매핑이 생성되었습니다.",
            "mapping_id": mapping.mapping_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 불필요한 API들 주석 처리 - 핵심 파이프라인에 불필요

# @router.delete("/mapping/{mapping_id}")
# async def delete_mapping(mapping_id: int, db: Session = Depends(get_db)):
#     """매핑 삭제 (유지보수용)"""
#     pass


@router.get("/verified-companies")
async def get_verified_companies(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """검증 완료된 회사 목록 (월별 보고서용)"""
    try:
        mappings = db.query(CompanyDartMapping)\
            .filter(CompanyDartMapping.mapping_status == MappingStatus.verified)\
            .filter(CompanyDartMapping.dart_corp_code.isnot(None))\
            .order_by(CompanyDartMapping.verified_at.desc())\
            .limit(limit)\
            .all()

        return [
            {
                "company_id": mapping.company_id,
                "company_name": mapping.crawled_company_name,
                "dart_corp_code": mapping.dart_corp_code,
                "dart_corp_name": mapping.dart_corp_name,
                "dart_stock_code": mapping.dart_stock_code,
                "verified_at": mapping.verified_at,
                "verified_by": mapping.verified_by
            }
            for mapping in mappings
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failed-mappings")
async def get_failed_mappings(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """실패한 매핑 목록 조회"""
    try:
        mappings = db.query(CompanyDartMapping)\
            .filter(CompanyDartMapping.mapping_status == MappingStatus.failed)\
            .order_by(CompanyDartMapping.updated_at.desc())\
            .limit(limit)\
            .all()

        return [
            {
                "mapping_id": mapping.mapping_id,
                "company_id": mapping.company_id,
                "company_name": mapping.crawled_company_name,
                "company_url": mapping.crawled_company_url,
                "mapping_status": mapping.mapping_status.value,
                "confidence_score": mapping.confidence_score,
                "gpt_response": mapping.gpt_response,
                "manual_notes": mapping.manual_notes,
                "created_at": mapping.created_at,
                "updated_at": mapping.updated_at,
                "processed_at": mapping.processed_at
            }
            for mapping in mappings
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 아래 API들은 모니터링/유지보수용으로 주석 처리

# @router.get("/workflow/summary")
# async def get_mapping_workflow_summary():
#     """매핑 워크플로우 현황 요약 (모니터링용)"""
#     pass

# @router.post("/workflow/trigger")
# async def trigger_mapping_workflow(background_tasks: BackgroundTasks):
#     """수동으로 매핑 워크플로우 실행 (유지보수용)"""
#     pass