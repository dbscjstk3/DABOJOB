from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..crawlers.saramin_crawler import SaraminCrawler
from ..models.crawler_models import JobPosting, Company, CrawlingLog, JobSector, Region
from ..database import get_db
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..utils.redis_helper import redis_helper

router = APIRouter(prefix="/api/crawler", tags=["Crawler"])

executor = ThreadPoolExecutor(max_workers=2)


@router.post("/saramin/start")
async def start_saramin_crawl(
    background_tasks: BackgroundTasks,
    max_pages: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    사람인 크롤링 시작

    Parameters:
    - max_pages: 크롤링할 최대 페이지 수 (1-100)
    """
    try:
        async def run_crawler_and_trigger_mapping():

            # 크롤링 실행
            crawler = SaraminCrawler(db_session=db)
            result = crawler.crawl(max_pages=max_pages)

            # 크롤링 성공 시 자동 매핑 트리거
            if result and result.get("status") == "completed":
                job_id = f"saramin_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # 매핑 작업을 Redis 스트림에 추가
                mapping_job_data = {
                    "job_id": f"auto_mapping_{job_id}",
                    "trigger": "post_saramin_crawling",
                    "limit": 20,
                    "submitted_at": datetime.now().isoformat()
                }

                await redis_helper.add_job("mapping_stream", mapping_job_data)
                print(f"✅ Auto-mapping job queued after Saramin crawling: auto_mapping_{job_id}")

        background_tasks.add_task(run_crawler_and_trigger_mapping)

        return {
            "status": "started",
            "message": f"사람인 크롤링이 시작되었습니다. (최대 {max_pages}페이지) - 완료 후 자동 매핑 실행",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saramin/status")
async def get_crawl_status(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    최근 크롤링 상태 조회
    """
    try:
        recent_logs = db.query(CrawlingLog).order_by(
            CrawlingLog.started_at.desc()
        ).limit(limit).all()
        
        return {
            "logs": [
                {
                    "log_id": log.log_id,
                    "crawl_type": log.crawl_type,
                    "status": log.crawl_status.value if log.crawl_status else None,
                    "items_found": log.items_found,
                    "items_saved": log.items_saved,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "duration_seconds": log.crawl_duration_seconds,
                    "error_message": log.error_message
                } for log in recent_logs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_crawled_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    company_name: Optional[str] = None,
    location: Optional[str] = None,
    sector: Optional[str] = None,
    is_hot: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    크롤링된 채용공고 조회
    """
    try:
        query = db.query(JobPosting).join(Company)
        
        if company_name:
            query = query.filter(Company.company_name.contains(company_name))
        
        if location:
            query = query.filter(JobPosting.work_location.contains(location))
        
        if sector:
            query = query.join(JobPosting.job_sectors).join(JobSector).filter(
                JobSector.sector_name.contains(sector)
            )
        
        if is_hot is not None:
            query = query.filter(JobPosting.is_hot == is_hot)
        
        total_count = query.count()
        
        jobs = query.order_by(JobPosting.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "jobs": [
                {
                    "job_id": job.job_id,
                    "company_name": job.company.company_name,
                    "company_scale": job.company.company_scale,
                    "job_title": job.saramin_job_title,
                    "job_url": job.saramin_job_url,
                    "location": job.work_location,
                    "career_info": job.career_info,
                    "education": job.education_requirement,
                    "salary": job.salary_info,
                    "deadline": job.application_deadline.isoformat() if job.application_deadline else None,
                    "is_hot": job.is_hot,
                    "sectors": [js.sector.sector_name for js in job.job_sectors],
                    "created_at": job.created_at.isoformat()
                } for job in jobs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 채용공고 상세 조회
    """
    try:
        job = db.query(JobPosting).filter(JobPosting.job_id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다.")
        
        return {
            "job_id": job.job_id,
            "company": {
                "company_id": job.company.company_id,
                "name": job.company.company_name,
                "csn": job.company.csn,
                "group": job.company.company_group,
                "scale": job.company.company_scale
            },
            "job_info": {
                "saramin_id": job.saramin_job_id,
                "title": job.saramin_job_title,
                "url": job.saramin_job_url,
                "location": job.work_location,
                "career": job.career_info,
                "education": job.education_requirement,
                "salary": job.salary_info,
                "posting_date": job.posting_date.isoformat() if job.posting_date else None,
                "deadline": job.application_deadline.isoformat() if job.application_deadline else None,
                "registration_info": job.registration_info,
                "status": job.status.value if job.status else None,
                "is_hot": job.is_hot
            },
            "sectors": [
                {
                    "name": js.sector.sector_name,
                    "category": js.sector.sector_category,
                    "is_primary": js.is_primary
                } for js in job.job_sectors
            ],
            "regions": [
                {
                    "name": jr.region.region_name,
                    "level": jr.region.region_level
                } for jr in job.job_regions
            ],
            "metadata": {
                "crawled_at": job.crawled_at.isoformat() if job.crawled_at else None,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies")
async def get_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    company_name: Optional[str] = None,
    company_scale: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    크롤링된 회사 목록 조회
    """
    try:
        query = db.query(Company)
        
        if company_name:
            query = query.filter(Company.company_name.contains(company_name))
        
        if company_scale:
            query = query.filter(Company.company_scale == company_scale)
        
        total_count = query.count()
        
        companies = query.order_by(Company.company_name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "companies": [
                {
                    "company_id": company.company_id,
                    "name": company.company_name,
                    "csn": company.csn,
                    "group": company.company_group,
                    "scale": company.company_scale,
                    "job_count": len(company.job_postings),
                    "created_at": company.created_at.isoformat()
                } for company in companies
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_crawl_statistics(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    크롤링 통계 조회
    """
    try:
        since_date = datetime.now() - timedelta(days=days)
        
        total_jobs = db.query(JobPosting).count()
        recent_jobs = db.query(JobPosting).filter(
            JobPosting.created_at >= since_date
        ).count()
        
        total_companies = db.query(Company).count()
        
        hot_jobs = db.query(JobPosting).filter(
            JobPosting.is_hot == True
        ).count()
        
        sectors_count = db.query(JobSector).count()
        regions_count = db.query(Region).count()
        
        recent_crawls = db.query(CrawlingLog).filter(
            CrawlingLog.started_at >= since_date
        ).count()
        
        successful_crawls = db.query(CrawlingLog).filter(
            CrawlingLog.started_at >= since_date,
            CrawlingLog.crawl_status == 'success'
        ).count()
        
        return {
            "period_days": days,
            "jobs": {
                "total": total_jobs,
                "recent": recent_jobs,
                "hot": hot_jobs
            },
            "companies": {
                "total": total_companies
            },
            "metadata": {
                "sectors": sectors_count,
                "regions": regions_count
            },
            "crawling": {
                "recent_attempts": recent_crawls,
                "successful": successful_crawls,
                "success_rate": round(successful_crawls / recent_crawls * 100, 2) if recent_crawls > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/cleanup")
async def cleanup_old_jobs(
    days_old: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """
    오래된 채용공고 정리
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = db.query(JobPosting).filter(
            JobPosting.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"{days_old}일 이상 된 {deleted_count}개의 채용공고가 삭제되었습니다."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))