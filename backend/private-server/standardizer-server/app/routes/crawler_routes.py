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


@router.post("/saramin/resume/{crawl_id}")
async def resume_saramin_crawl(
    crawl_id: str,
    db: Session = Depends(get_db)
):
    """
    중단된 사람인 크롤링 재개

    Parameters:
    - crawl_id: 재개할 크롤링 작업 ID
    """
    try:
        # Redis에서 크롤링 상태 확인
        status = await redis_helper.get_status(f"crawl:{crawl_id}")

        if not status:
            raise HTTPException(status_code=404, detail=f"크롤링 작업을 찾을 수 없습니다: {crawl_id}")

        if status.get("status") != "running":
            raise HTTPException(
                status_code=400,
                detail=f"크롤링이 실행 중이 아닙니다. 현재 상태: {status.get('status')}"
            )

        max_pages = status.get("max_pages", 5)

        # 백그라운드에서 크롤링 재개
        def resume_crawler():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                from ..database import SessionLocal
                db_session = SessionLocal()

                # 크롤링 재개
                crawler = SaraminCrawler(db_session=db_session)
                result = crawler.crawl(max_pages=max_pages, crawl_id=crawl_id, resume=True)

                # Redis 상태 업데이트
                loop.run_until_complete(redis_helper.set_status(f"crawl:{crawl_id}", {
                    "status": result.get("status", "failed"),
                    "max_pages": max_pages,
                    "completed_at": datetime.now().isoformat(),
                    "result": result
                }))

                db_session.close()

            except Exception as e:
                loop.run_until_complete(redis_helper.set_status(f"crawl:{crawl_id}", {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }))
            finally:
                loop.close()

        # ThreadPoolExecutor로 백그라운드 실행
        executor.submit(resume_crawler)

        return {
            "status": "resumed",
            "crawl_id": crawl_id,
            "message": f"크롤링이 재개되었습니다. (마지막 페이지: {status.get('progress', {}).get('current_page', 0)})",
            "check_status_url": f"/api/crawler/saramin/status/{crawl_id}",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saramin/incomplete")
async def get_incomplete_crawls():
    """
    중단된 크롤링 작업 목록 조회
    """
    try:
        # Redis에서 crawl: 패턴의 키들 조회
        if not redis_helper.redis_client:
            return {"incomplete_crawls": [], "message": "Redis 연결 없음"}

        keys = redis_helper.redis_client.keys("crawl:*")
        incomplete_crawls = []

        for key in keys:
            status = await redis_helper.get_status(key)
            if status and status.get("status") in ["running", "failed"]:
                crawl_id = key.replace("crawl:", "")
                incomplete_crawls.append({
                    "crawl_id": crawl_id,
                    "status": status.get("status"),
                    "max_pages": status.get("max_pages", 0),
                    "progress": status.get("progress", {}),
                    "started_at": status.get("started_at"),
                    "last_updated": status.get("completed_at", status.get("started_at")),
                    "error": status.get("error")
                })

        return {
            "incomplete_crawls": incomplete_crawls,
            "total": len(incomplete_crawls)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/saramin/start")
async def start_saramin_crawl(
    max_pages: int = Query(default=5, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    사람인 크롤링 시작 (백그라운드 실행)

    Parameters:
    - max_pages: 크롤링할 최대 페이지 수 (1-500)
    """
    try:
        import logging
        logger = logging.getLogger(__name__)

        # 크롤링 작업 ID 생성
        crawl_id = f"saramin_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🆔 크롤링 작업 ID 생성: {crawl_id}")

        # Redis에 크롤링 상태 저장
        logger.info(f"💾 Redis에 크롤링 상태 저장 중...")
        await redis_helper.set_status(f"crawl:{crawl_id}", {
            "status": "running",
            "max_pages": max_pages,
            "started_at": datetime.now().isoformat(),
            "progress": {"current_page": 0, "items_found": 0, "items_saved": 0}
        })

        # 백그라운드에서 크롤링 실행
        def run_crawler():
            import asyncio
            import logging
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 백그라운드 스레드에서도 로그가 보이도록 설정
            logger = logging.getLogger(__name__)
            logger.info(f"🚀 백그라운드에서 크롤링 시작: {crawl_id}")

            try:
                # 새로운 DB 세션 생성 (백그라운드 스레드용)
                from ..database import SessionLocal
                db_session = SessionLocal()

                logger.info(f"📊 DB 세션 생성 완료")

                # 크롤링 실행
                crawler = SaraminCrawler(db_session=db_session)
                logger.info(f"🕷️ SaraminCrawler 생성 완료, 크롤링 시작...")
                result = crawler.crawl(max_pages=max_pages, crawl_id=crawl_id)
                logger.info(f"✅ 크롤링 완료: {result.get('status')}")

                # Redis 상태 업데이트
                loop.run_until_complete(redis_helper.set_status(f"crawl:{crawl_id}", {
                    "status": result.get("status", "failed"),
                    "max_pages": max_pages,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "result": result
                }))

                # 크롤링 성공 시 자동 매핑 트리거
                if result and result.get("status") == "completed":
                    mapping_job_data = {
                        "job_id": f"auto_mapping_{crawl_id}",
                        "trigger": "post_saramin_crawling",
                        "limit": 1000,
                        "submitted_at": datetime.now().isoformat()
                    }
                    loop.run_until_complete(redis_helper.add_job("mapping_stream", mapping_job_data))
                    logger.info(f"✅ Auto-mapping job queued after Saramin crawling: auto_mapping_{crawl_id}")

                db_session.close()
                logger.info(f"🔒 DB 세션 정리 완료")

            except Exception as e:
                logger.error(f"❌ 크롤링 실패: {str(e)}")
                logger.error(f"📋 오류 상세: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"🔍 스택 트레이스:\n{traceback.format_exc()}")

                loop.run_until_complete(redis_helper.set_status(f"crawl:{crawl_id}", {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }))
            finally:
                logger.info(f"🧹 정리 중...")
                loop.close()
                logger.info(f"✅ 백그라운드 크롤링 작업 종료: {crawl_id}")

        # ThreadPoolExecutor로 백그라운드 실행
        executor.submit(run_crawler)

        return {
            "status": "started",
            "crawl_id": crawl_id,
            "message": f"사람인 크롤링이 백그라운드에서 시작되었습니다. (최대 {max_pages}페이지)",
            "check_status_url": f"/api/crawler/saramin/status/{crawl_id}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saramin/status/{crawl_id}")
async def get_specific_crawl_status(crawl_id: str):
    """
    특정 크롤링 작업의 상태 조회
    """
    try:
        status = await redis_helper.get_status(f"crawl:{crawl_id}")

        if not status:
            raise HTTPException(status_code=404, detail="크롤링 작업을 찾을 수 없습니다.")

        return status
    except HTTPException:
        raise
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


# 아래 API들은 디버그/유지보수용으로 주석 처리
# 핵심 파이프라인에는 필요하지 않음

# @router.get("/statistics")
# async def get_crawl_statistics(
#     days: int = Query(default=7, ge=1, le=30),
#     db: Session = Depends(get_db)
# ):
#     """크롤링 통계 조회 (디버그용)"""
#     pass

# @router.delete("/jobs/cleanup")
# async def cleanup_old_jobs(
#     days_old: int = Query(default=30, ge=7, le=90),
#     db: Session = Depends(get_db)
# ):
#     """오래된 채용공고 정리 (유지보수용)"""
#     pass