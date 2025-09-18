"""
크롤러 관련 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from models.database import get_db
from models.crawler import JobPosting, Company, CrawlingLog, JobSector, Region
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/crawler", tags=["Crawler"])


@router.post("/start")
async def start_crawling(
    background_tasks: BackgroundTasks,
    max_pages: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """크롤링 시작"""
    try:
        # TODO: 서비스 레이어에서 크롤링 처리
        # crawler_service = CrawlerService()
        # background_tasks.add_task(crawler_service.start_crawling, max_pages)

        return {
            "status": "started",
            "message": f"크롤링이 시작되었습니다. (최대 {max_pages}페이지)",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start crawling: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_crawl_status(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """크롤링 상태 조회"""
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
        logger.error(f"Failed to get crawl status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    company_name: Optional[str] = None,
    location: Optional[str] = None,
    sector: Optional[str] = None,
    is_hot: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """채용공고 목록 조회"""
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
        logger.error(f"Failed to get jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies")
async def get_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    company_name: Optional[str] = None,
    company_scale: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """회사 목록 조회"""
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
        logger.error(f"Failed to get companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """크롤링 통계"""
    try:
        since_date = datetime.now() - timedelta(days=days)

        total_jobs = db.query(JobPosting).count()
        recent_jobs = db.query(JobPosting).filter(
            JobPosting.created_at >= since_date
        ).count()

        total_companies = db.query(Company).count()
        hot_jobs = db.query(JobPosting).filter(JobPosting.is_hot == True).count()

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
            "crawling": {
                "recent_attempts": recent_crawls,
                "successful": successful_crawls,
                "success_rate": round(successful_crawls / recent_crawls * 100, 2) if recent_crawls > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))