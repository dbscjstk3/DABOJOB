"""
테스트용 DB 데이터 생성 API
테스트를 위한 회사, 매핑 데이터를 DB에 생성
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models.crawler_models import Company, CompanyDartMapping, MappingStatus, JobPosting, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["Test Data"])

class TestDataRequest(BaseModel):
    test_name: str = "삼성전자_테스트데이터"
    mapping_id: int = 99999

@router.post("/create-test-data")
async def create_test_data(
    request: TestDataRequest,
    db: Session = Depends(get_db)
):
    """
    🧪 삼성전자 테스트 데이터 생성
    Summary 서버 테스트와 연동할 수 있는 삼성전자 DB 데이터 생성
    """
    try:
        test_mapping_id = request.mapping_id
        logger.info(f"🧪 삼성전자 테스트 데이터 생성 시작: mapping_id={test_mapping_id}")

        # 1. 기존 데이터 정리 (같은 mapping_id가 있으면 삭제)
        existing_mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_id == test_mapping_id
        ).first()

        existing_company = None
        existing_job_postings = []
        if existing_mapping:
            existing_company = db.query(Company).filter(
                Company.company_id == existing_mapping.company_id
            ).first()

            if existing_company:
                # 기존 채용공고들도 먼저 삭제
                existing_job_postings = db.query(JobPosting).filter(
                    JobPosting.company_id == existing_company.company_id
                ).all()

                for job in existing_job_postings:
                    db.delete(job)

            logger.info(f"기존 테스트 데이터 삭제: mapping_id={test_mapping_id}")
            db.delete(existing_mapping)

            if existing_company:
                db.delete(existing_company)

        # 2. 테스트 회사 데이터 생성
        test_company = Company(
            company_name="삼성전자(주)",
            company_url="https://www.samsung.com/sec/",
            company_scale="대기업",
            company_group="삼성그룹",
            csn="131-81-00998",  # Samsung Electronics CSN
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(test_company)
        db.flush()  # company_id 생성을 위해

        logger.info(f"✅ 테스트 회사 생성: company_id={test_company.company_id}, name={test_company.company_name}")

        # 3. 테스트 DART 매핑 데이터 생성
        test_mapping = CompanyDartMapping(
            mapping_id=test_mapping_id,
            company_id=test_company.company_id,
            crawled_company_name=test_company.company_name,
            crawled_company_url=test_company.company_url,
            dart_corp_name="삼성전자",
            dart_corp_code="00126380",
            dart_stock_code="005930",
            mapping_status=MappingStatus.verified,
            confidence_score=100,
            gpt_response="삼성전자 테스트용 매핑 데이터",
            manual_notes="테스트 API로 생성된 삼성전자 데이터",
            processed_at=datetime.utcnow(),
            verified_at=datetime.utcnow(),
            verified_by="test_api",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(test_mapping)

        logger.info(f"✅ 테스트 매핑 생성: mapping_id={test_mapping_id}, dart_code={test_mapping.dart_corp_code}")

        # 4. 테스트 채용공고 데이터 생성
        test_job_posting = JobPosting(
            company_id=test_company.company_id,
            saramin_job_id="samsung99999",
            saramin_job_title="삼성전자 SW개발자 채용",
            saramin_job_url="https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=samsung99999",
            work_location="경기도 수원시 영통구",
            career_info="경력 3~10년",
            education_requirement="대졸 이상",
            salary_info="회사 내규에 따름",
            posting_date=datetime.utcnow().date(),
            application_deadline=datetime.utcnow().date(),
            registration_info="상시모집",
            status=JobStatus.active,
            is_hot=True,
            crawled_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(test_job_posting)
        db.flush()  # job_id 생성을 위해

        logger.info(f"✅ 테스트 채용공고 생성: job_id={test_job_posting.job_id}, title={test_job_posting.saramin_job_title}")

        # 5. 커밋
        db.commit()

        logger.info(f"🎉 삼성전자 테스트 데이터 생성 완료!")

        return {
            "success": True,
            "test_name": request.test_name,
            "created_data": {
                "company": {
                    "company_id": test_company.company_id,
                    "company_name": test_company.company_name,
                    "company_url": test_company.company_url,
                    "company_scale": test_company.company_scale,
                    "company_group": test_company.company_group,
                    "csn": test_company.csn
                },
                "mapping": {
                    "mapping_id": test_mapping.mapping_id,
                    "dart_corp_name": test_mapping.dart_corp_name,
                    "dart_corp_code": test_mapping.dart_corp_code,
                    "dart_stock_code": test_mapping.dart_stock_code,
                    "mapping_status": test_mapping.mapping_status.value,
                    "confidence_score": test_mapping.confidence_score
                },
                "job_posting": {
                    "job_id": test_job_posting.job_id,
                    "saramin_job_id": test_job_posting.saramin_job_id,
                    "saramin_job_title": test_job_posting.saramin_job_title,
                    "work_location": test_job_posting.work_location,
                    "career_info": test_job_posting.career_info,
                    "salary_info": test_job_posting.salary_info,
                    "status": test_job_posting.status.value
                }
            },
            "message": f"✅ 삼성전자 테스트 데이터 생성 완료! (mapping_id: {test_mapping_id}, job_id: {test_job_posting.job_id})",
            "next_step": f"이제 Summary 서버에서 POST /test/full-pipeline 호출하세요"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 테스트 데이터 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Test data creation failed: {str(e)}")

@router.get("/check-data/{mapping_id}")
async def check_test_data(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    🔍 테스트 데이터 확인
    """
    try:
        # 매핑 데이터 조회
        mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_id == mapping_id
        ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail=f"mapping_id {mapping_id} not found")

        # 회사 데이터 조회
        company = db.query(Company).filter(
            Company.company_id == mapping.company_id
        ).first()

        # 채용공고 데이터 조회
        job_posting = db.query(JobPosting).filter(
            JobPosting.company_id == mapping.company_id
        ).first() if company else None

        return {
            "mapping_id": mapping_id,
            "found": True,
            "company": {
                "company_id": company.company_id if company else None,
                "company_name": company.company_name if company else None,
                "company_url": company.company_url if company else None
            } if company else None,
            "mapping": {
                "dart_corp_name": mapping.dart_corp_name,
                "dart_corp_code": mapping.dart_corp_code,
                "mapping_status": mapping.mapping_status.value,
                "confidence_score": mapping.confidence_score,
                "verified_at": mapping.verified_at.isoformat() if mapping.verified_at else None
            },
            "job_posting": {
                "job_id": job_posting.job_id if job_posting else None,
                "saramin_job_title": job_posting.saramin_job_title if job_posting else None,
                "work_location": job_posting.work_location if job_posting else None,
                "status": job_posting.status.value if job_posting else None
            } if job_posting else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"데이터 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup/{mapping_id}")
async def cleanup_test_data(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    🧹 테스트 데이터 정리
    """
    try:
        # 매핑 데이터 삭제
        mapping = db.query(CompanyDartMapping).filter(
            CompanyDartMapping.mapping_id == mapping_id
        ).first()

        if mapping:
            company_id = mapping.company_id

            # 채용공고 데이터 먼저 삭제
            job_postings = db.query(JobPosting).filter(
                JobPosting.company_id == company_id
            ).all()

            for job in job_postings:
                db.delete(job)

            db.delete(mapping)

            # 회사 데이터 삭제
            company = db.query(Company).filter(
                Company.company_id == company_id
            ).first()

            if company:
                db.delete(company)

            db.commit()

            return {
                "success": True,
                "mapping_id": mapping_id,
                "message": f"✅ 테스트 데이터 정리 완료 (mapping_id: {mapping_id}) - 회사, 매핑, 채용공고 데이터 삭제됨"
            }
        else:
            return {
                "success": True,
                "mapping_id": mapping_id,
                "message": "데이터가 존재하지 않음"
            }

    except Exception as e:
        db.rollback()
        logger.error(f"데이터 정리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def test_health():
    """🏥 테스트 API 상태"""
    return {
        "status": "healthy",
        "message": "테스트 데이터 API 정상 작동",
        "available_apis": [
            "POST /test/create-test-data - 삼성전자 테스트 데이터 생성 (회사/매핑/채용공고)",
            "GET /test/check-data/{mapping_id} - 테스트 데이터 확인",
            "DELETE /test/cleanup/{mapping_id} - 테스트 데이터 정리"
        ]
    }