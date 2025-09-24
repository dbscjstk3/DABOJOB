"""
관리자 달력 뷰 API
채용공고 기반 월별 달력 관리
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_

from ..database import get_db
from ..models.crawler_models import JobPosting, Company, CompanyDartMapping, MappingStatus

router = APIRouter(prefix="/api/admin/calendar", tags=["Admin Calendar"])


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
                "mapping_status": company_data.mapping_status.value if company_data.mapping_status else "unmapped",
                "mapping_id": company_data.mapping_id,
                "first_posting_date": company_data.first_posting_date.isoformat() if company_data.first_posting_date else None,
                "last_posting_date": company_data.last_posting_date.isoformat() if company_data.last_posting_date else None,
                "job_count": company_data.job_count,
                "mapping_created_at": company_data.mapping_created_at.isoformat() if company_data.mapping_created_at else None,
                "can_remap": company_data.mapping_status.value in ["failed", "suggested", "unmapped"] if company_data.mapping_status else True,
                "job_postings": job_list
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"달력 조회 실패: {str(e)}")


@router.get("/job-postings/{job_id}")
async def get_job_posting_detail(
    job_id: int,
    db: Session = Depends(get_db)
):
    """채용공고 상세 정보 조회 (매핑 정보 포함)"""
    try:
        # 채용공고 기본 정보
        job_posting = db.query(JobPosting).filter(JobPosting.job_id == job_id).first()
        if not job_posting:
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다")

        # 회사 정보
        company = db.query(Company).filter(Company.company_id == job_posting.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="회사 정보를 찾을 수 없습니다")

        # 매핑 정보
        mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.company_id == company.company_id
        ).first()

        # 응답 구성
        result = {
            "job_posting": {
                "job_id": job_posting.job_id,
                "job_title": job_posting.saramin_job_title,
                "company_name": company.company_name,
                "company_url": company.company_url,
                "work_location": job_posting.work_location,
                "salary_info": job_posting.salary_info,
                "career_info": job_posting.career_info,
                "education_requirement": job_posting.education_requirement,
                "posting_date": job_posting.posting_date.isoformat() if job_posting.posting_date else None,
                "application_deadline": job_posting.application_deadline.isoformat() if job_posting.application_deadline else None,
                "job_url": job_posting.saramin_job_url,
                "registration_info": job_posting.registration_info
            },
            "company_mapping": None
        }

        if mapping:
            result["company_mapping"] = {
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
            # 매핑이 없는 경우 (unmapped)
            result["company_mapping"] = {
                "mapping_id": None,
                "mapping_status": "unmapped",
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

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세 조회 실패: {str(e)}")


@router.post("/companies/{company_id}/remap")
async def remap_company(
    company_id: int,
    dart_corp_name: str,
    dart_corp_code: str,
    dart_stock_code: str = None,
    manual_notes: str = None,
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
            existing_mapping.dart_corp_name = dart_corp_name
            existing_mapping.dart_corp_code = dart_corp_code
            existing_mapping.dart_stock_code = dart_stock_code
            existing_mapping.mapping_status = MappingStatus.verified
            existing_mapping.confidence_score = 100
            existing_mapping.manual_notes = manual_notes
            existing_mapping.verified_at = datetime.utcnow()
            existing_mapping.verified_by = "admin_manual"
            existing_mapping.updated_at = datetime.utcnow()
        else:
            # 새 매핑 생성
            new_mapping = CompanyDartMapping(
                company_id=company.company_id,
                crawled_company_name=company.company_name,
                crawled_company_url=company.company_url,
                dart_corp_name=dart_corp_name,
                dart_corp_code=dart_corp_code,
                dart_stock_code=dart_stock_code,
                mapping_status=MappingStatus.verified,
                confidence_score=100,
                gpt_response="Manual mapping by admin",
                manual_notes=manual_notes,
                processed_at=datetime.utcnow(),
                verified_at=datetime.utcnow(),
                verified_by="admin_manual"
            )
            db.add(new_mapping)

        db.commit()

        return {
            "status": "success",
            "message": f"{company.company_name} → {dart_corp_name} 매핑이 완료되었습니다 ({job_count}개 채용공고에 적용)",
            "mapping": {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "dart_corp_name": dart_corp_name,
                "dart_corp_code": dart_corp_code,
                "job_count": job_count,
                "confidence_score": 100,
                "verified_by": "admin_manual",
                "verified_at": datetime.utcnow().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"재매핑 실패: {str(e)}")