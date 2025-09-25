"""
관리자 달력 뷰 API
채용공고 기반 월별 달력 관리
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_
from pydantic import BaseModel
import asyncio
import json
import logging

from ..database import get_db
from ..models.crawler_models import JobPosting, Company, CompanyDartMapping, MappingStatus
from ..utils.redis_helper import redis_helper
from ..services.dart_extractor import DartDocumentExtractor
from ..config import DART_API_KEY

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/calendar", tags=["Admin Calendar"])


# Pydantic 모델 정의
class RemapRequest(BaseModel):
    """회사 재매핑 요청 모델"""
    dart_corp_name: str
    dart_corp_code: str
    dart_stock_code: Optional[str] = None
    manual_notes: Optional[str] = None


@router.get("/companies")
async def get_monthly_companies(
    year: int = Query(..., description="연도 (예: 2025)"),
    month: int = Query(..., ge=1, le=12, description="월 (1-12)"),
    db: Session = Depends(get_db)
):
    """월별 회사별 달력 조회 (채용공고 그룹핑)"""
    try:
        from sqlalchemy import func

        # 해당 월의 회사별 채용공고 그룹핑 조회
        companies_data = db.query(
            Company.company_id,
            Company.company_name,
            func.min(JobPosting.posting_date).label('first_posting_date'),
            func.max(JobPosting.posting_date).label('last_posting_date'),
            func.count(JobPosting.job_id).label('job_count'),
            CompanyDartMapping.mapping_status,
            CompanyDartMapping.mapping_id,
            CompanyDartMapping.created_at.label('mapping_created_at')
        ).join(
            JobPosting, Company.company_id == JobPosting.company_id
        ).outerjoin(
            CompanyDartMapping, Company.company_id == CompanyDartMapping.company_id
        ).filter(
            and_(
                extract('year', JobPosting.posting_date) == year,
                extract('month', JobPosting.posting_date) == month
            )
        ).group_by(
            Company.company_id,
            Company.company_name,
            CompanyDartMapping.mapping_status,
            CompanyDartMapping.mapping_id,
            CompanyDartMapping.created_at
        ).order_by(func.min(JobPosting.posting_date).desc()).all()

        # 응답 데이터 구성
        result = {
            "year": year,
            "month": month,
            "total_companies": len(companies_data),
            "companies": []
        }

        for company_data in companies_data:
            # 해당 회사의 채용공고 목록 조회
            job_postings = db.query(JobPosting).filter(
                JobPosting.company_id == company_data.company_id,
                and_(
                    extract('year', JobPosting.posting_date) == year,
                    extract('month', JobPosting.posting_date) == month
                )
            ).all()

            job_list = []
            for job in job_postings:
                job_list.append({
                    "job_id": job.job_id,
                    "job_title": job.saramin_job_title,
                    "posting_date": job.posting_date.isoformat() if job.posting_date else None,
                    "application_deadline": job.application_deadline.isoformat() if job.application_deadline else None,
                    "job_url": job.saramin_job_url
                })

            result["companies"].append({
                "company_id": company_data.company_id,
                "company_name": company_data.company_name,
                "mapping_status": company_data.mapping_status.value if company_data.mapping_status else "pending",
                "mapping_id": company_data.mapping_id,
                "first_posting_date": company_data.first_posting_date.isoformat() if company_data.first_posting_date else None,
                "last_posting_date": company_data.last_posting_date.isoformat() if company_data.last_posting_date else None,
                "job_count": company_data.job_count,
                "mapping_created_at": company_data.mapping_created_at.isoformat() if company_data.mapping_created_at else None,
                "can_remap": company_data.mapping_status.value in ["failed", "suggested"] if company_data.mapping_status else True,
                "job_postings": job_list
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"달력 조회 실패: {str(e)}")


@router.get("/companies/{company_id}")
async def get_company_detail(
    company_id: int,
    year: int = Query(..., description="연도 (예: 2025)"),
    month: int = Query(..., ge=1, le=12, description="월 (1-12)"),
    db: Session = Depends(get_db)
):
    """회사별 상세 정보 조회 (특정 년/월 기준 매핑 정보 + 채용공고)"""
    try:
        # 회사 정보
        company = db.query(Company).filter(Company.company_id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="회사 정보를 찾을 수 없습니다")

        # 매핑 정보
        mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.company_id == company_id
        ).first()

        # 해당 회사의 특정 년/월 채용공고만 조회
        job_postings = db.query(JobPosting).filter(
            JobPosting.company_id == company_id,
            and_(
                extract('year', JobPosting.posting_date) == year,
                extract('month', JobPosting.posting_date) == month
            )
        ).order_by(JobPosting.posting_date.desc()).all()

        # 해당 기간의 첫 번째/마지막 공고 날짜 계산
        first_posting_date = None
        last_posting_date = None
        if job_postings:
            posting_dates = [job.posting_date for job in job_postings if job.posting_date]
            if posting_dates:
                first_posting_date = min(posting_dates)
                last_posting_date = max(posting_dates)

        # 응답 구성
        result = {
            "company": {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "company_url": company.company_url,
                "company_scale": company.company_scale,
                "company_group": company.company_group if hasattr(company, 'company_group') else None,
                "created_at": company.created_at.isoformat() if company.created_at else None
            },
            "mapping": None,
            "period": {
                "year": year,
                "month": month,
                "first_posting_date": first_posting_date.isoformat() if first_posting_date else None,
                "last_posting_date": last_posting_date.isoformat() if last_posting_date else None
            },
            "job_postings": []
        }

        # 매핑 정보 구성
        if mapping:
            result["mapping"] = {
                "mapping_id": mapping.mapping_id,
                "mapping_status": mapping.mapping_status.value,
                "dart_corp_name": mapping.dart_corp_name,
                "dart_corp_code": mapping.dart_corp_code,
                "dart_stock_code": mapping.dart_stock_code,
                "confidence_score": mapping.confidence_score,
                "gpt_response": mapping.gpt_response,
                "manual_notes": mapping.manual_notes,
                "processed_at": mapping.processed_at.isoformat() if mapping.processed_at else None,
                "verified_at": mapping.verified_at.isoformat() if mapping.verified_at else None,
                "verified_by": mapping.verified_by,
                "can_remap": mapping.mapping_status.value in ["failed", "suggested"]
            }
        else:
            # 매핑이 없는 경우 (pending)
            result["mapping"] = {
                "mapping_id": None,
                "mapping_status": "pending",
                "dart_corp_name": None,
                "dart_corp_code": None,
                "dart_stock_code": None,
                "confidence_score": 0,
                "gpt_response": None,
                "manual_notes": None,
                "processed_at": None,
                "verified_at": None,
                "verified_by": None,
                "can_remap": True
            }

        # 채용공고 목록 구성
        for job in job_postings:
            result["job_postings"].append({
                "job_id": job.job_id,
                "job_title": job.saramin_job_title,
                "work_location": job.work_location,
                "salary_info": job.salary_info,
                "career_info": job.career_info,
                "education_requirement": job.education_requirement,
                "posting_date": job.posting_date.isoformat() if job.posting_date else None,
                "application_deadline": job.application_deadline.isoformat() if job.application_deadline else None,
                "job_url": job.saramin_job_url,
                "status": job.status.value if job.status else None,
                "is_hot": job.is_hot,
                "registration_info": job.registration_info
            })

        result["job_postings_count"] = len(job_postings)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회사 상세 조회 실패: {str(e)}")


@router.post("/companies/{company_id}/remap")
async def remap_company(
    company_id: int,
    request: RemapRequest,  # Request Body로 받기
    db: Session = Depends(get_db)
):
    """회사 수동 재매핑 (해당 회사의 모든 채용공고에 적용)"""
    try:
        # 회사 정보 조회
        company = db.query(Company).filter(Company.company_id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="회사 정보를 찾을 수 없습니다")

        # 해당 회사의 채용공고 개수 확인
        job_count = db.query(JobPosting).filter(JobPosting.company_id == company_id).count()

        # 기존 매핑 조회
        existing_mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.company_id == company.company_id
        ).first()

        if existing_mapping:
            # 기존 매핑 업데이트
            existing_mapping.dart_corp_name = request.dart_corp_name
            existing_mapping.dart_corp_code = request.dart_corp_code
            existing_mapping.dart_stock_code = request.dart_stock_code
            existing_mapping.mapping_status = MappingStatus.verified
            existing_mapping.confidence_score = 100
            existing_mapping.manual_notes = request.manual_notes
            existing_mapping.verified_at = datetime.utcnow()
            existing_mapping.verified_by = "admin_manual"
            existing_mapping.updated_at = datetime.utcnow()
        else:
            # 새 매핑 생성
            new_mapping = CompanyDartMapping(
                company_id=company.company_id,
                crawled_company_name=company.company_name,
                crawled_company_url=company.company_url,
                dart_corp_name=request.dart_corp_name,
                dart_corp_code=request.dart_corp_code,
                dart_stock_code=request.dart_stock_code,
                mapping_status=MappingStatus.verified,
                confidence_score=100,
                gpt_response="Manual mapping by admin",
                manual_notes=request.manual_notes,
                processed_at=datetime.utcnow(),
                verified_at=datetime.utcnow(),
                verified_by="admin_manual"
            )
            db.add(new_mapping)

        db.commit()

        # DART 보고서 추출을 위한 Redis 메시지 발행
        try:
            # Redis에 DART 추출 작업 메시지 발행
            dart_job_data = {
                "company_id": str(company.company_id),
                "company_name": company.company_name,
                "dart_corp_name": request.dart_corp_name,
                "dart_corp_code": request.dart_corp_code,
                "dart_stock_code": request.dart_stock_code,
                "mapping_id": str(existing_mapping.mapping_id if existing_mapping else new_mapping.mapping_id),
                "action": "extract_dart_report",
                "triggered_by": "admin_remap",
                "timestamp": datetime.utcnow().isoformat()
            }

            # 비동기로 Redis 스트림에 메시지 추가
            stream_id = await redis_helper.add_job("dart_extract_stream", dart_job_data)

            logger.info(f"DART extraction job queued for {company.company_name} -> {request.dart_corp_name}, stream_id: {stream_id}")

            # 작업 상태 추적을 위한 job_id 생성
            job_id = f"dart_{company.company_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            await redis_helper.set_job_status(job_id, "queued", {
                "company_id": str(company.company_id),
                "dart_corp_code": request.dart_corp_code,
                "stream_id": stream_id
            })

            return {
                "status": "success",
                "message": f"{company.company_name} → {request.dart_corp_name} 매핑이 완료되었습니다 ({job_count}개 채용공고에 적용)",
                "mapping": {
                    "company_id": company.company_id,
                    "company_name": company.company_name,
                    "dart_corp_name": request.dart_corp_name,
                    "dart_corp_code": request.dart_corp_code,
                    "dart_stock_code": request.dart_stock_code,
                    "job_count": job_count,
                    "confidence_score": 100,
                    "verified_by": "admin_manual",
                    "verified_at": datetime.utcnow().isoformat()
                },
                "dart_extraction": {
                    "job_id": job_id,
                    "stream_id": stream_id,
                    "status": "queued",
                    "message": "DART 보고서 추출이 백그라운드에서 진행됩니다"
                }
            }

        except Exception as e:
            logger.error(f"Failed to queue DART extraction job: {e}")
            # Redis 메시지 발행 실패해도 매핑은 성공했으므로 성공 응답 반환
            return {
                "status": "success",
                "message": f"{company.company_name} → {request.dart_corp_name} 매핑이 완료되었습니다 ({job_count}개 채용공고에 적용)",
                "mapping": {
                    "company_id": company.company_id,
                    "company_name": company.company_name,
                    "dart_corp_name": request.dart_corp_name,
                    "dart_corp_code": request.dart_corp_code,
                    "dart_stock_code": request.dart_stock_code,
                    "job_count": job_count,
                    "confidence_score": 100,
                    "verified_by": "admin_manual",
                    "verified_at": datetime.utcnow().isoformat()
                },
                "dart_extraction": {
                    "status": "failed",
                    "message": f"DART 보고서 추출 작업 큐잉 실패: {str(e)}"
                }
            }

    except HTTPException:
        db.rollback()  # HTTPException 시에도 롤백
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"재매핑 실패: {str(e)}")