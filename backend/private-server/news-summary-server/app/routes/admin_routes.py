"""
관리자용 API 라우트
뉴스 처리 상태 관리 및 S3 업로드 승인
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import logging

from ..database import database
from ..services.s3_service import s3_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

class JobIdsRequest(BaseModel):
    job_ids: List[int]

@router.get("/jobs/completed")
async def get_completed_jobs() -> Dict[str, Any]:
    """완료된 job 목록 조회 (관리자 승인 대기 중)"""
    try:
        jobs = await database.get_jobs_by_status("completed")
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error(f"Error getting completed jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get completed jobs")

@router.get("/jobs/reprocessing")
async def get_reprocessing_jobs() -> Dict[str, Any]:
    """재요약 중인 job 목록 조회"""
    try:
        jobs = await database.get_jobs_by_status("reprocessing")
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error(f"Error getting reprocessing jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reprocessing jobs")

@router.post("/jobs/batch")
async def get_jobs_by_ids(request: JobIdsRequest) -> Dict[str, Any]:
    """특정 job_id 리스트로 job들 조회"""
    try:
        jobs = []
        for job_id in request.job_ids:
            status = await database.get_job_processing_status(job_id)
            if status:
                # 추가 정보가 필요하면 여기서 조회
                jobs.append({
                    "job_id": job_id,
                    "status": status
                })

        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error(f"Error getting jobs by IDs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jobs")

@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: int) -> Dict[str, Any]:
    """특정 job의 상세 정보 조회"""
    try:
        status = await database.get_job_processing_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job not found")

        # 추가 정보 조회 (필요에 따라)
        # - 뉴스 개수, 해시태그 정보 등

        return {"job_id": job_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job detail for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job detail")

@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: int) -> Dict[str, Any]:
    """job 승인 및 S3 업로드 실행"""
    try:
        current_status = await database.get_job_processing_status(job_id)
        if current_status is None:
            raise HTTPException(status_code=404, detail="Job not found")

        if current_status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job status must be 'completed' but is '{current_status}'"
            )

        # S3 업로드 실행
        logger.info(f"Starting S3 upload for approved job {job_id}")
        uploaded_files = await s3_service.upload_job_completion_data(job_id)

        if not uploaded_files:
            raise HTTPException(status_code=500, detail="S3 upload failed")

        # 상태를 finished로 업데이트
        success = await database.update_job_processing_status(job_id, "finished")
        if not success:
            logger.warning(f"Failed to update status to finished for job {job_id}")

        logger.info(f"Successfully approved and uploaded job {job_id} to S3: {list(uploaded_files.keys())}")

        return {
            "job_id": job_id,
            "status": "finished",
            "uploaded_files": uploaded_files,
            "message": "Job approved and uploaded to S3 successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve job: {str(e)}")


    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject job: {str(e)}")

@router.get("/jobs/{job_id}/complete-data")
async def get_job_complete_data(job_id: int) -> Dict[str, Any]:
    """completed 상태 job의 요약 보고서와 뉴스 데이터 모두 반환"""
    try:
        # 1. job 상태 확인
        current_status = await database.get_job_processing_status(job_id)
        if current_status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job status must be 'completed' but is '{current_status}'"
            )

        # 2. MySQL에서 요약 보고서 조회
        summary_query = """
        SELECT business_overview, products_service, sales_contracts, rnd_activities, other_notes
        FROM company_analysis_summaries
        WHERE job_id = %s
        LIMIT 1
        """

        summaries = {}
        async with database.get_connection() as cursor:
            await cursor.execute(summary_query, (job_id,))
            result = await cursor.fetchone()

            if result:
                summaries = {
                    "business_overview": result[0] or "요약 없음",
                    "products_services": result[1] or "요약 없음",
                    "revenue_orders": result[2] or "요약 없음",
                    "contracts_rnd": result[3] or "요약 없음",
                    "others": result[4] or "요약 없음"
                }
            else:
                # 요약 데이터가 없는 경우 기본값
                summaries = {
                    "business_overview": "요약 데이터 없음",
                    "products_services": "요약 데이터 없음",
                    "revenue_orders": "요약 데이터 없음",
                    "contracts_rnd": "요약 데이터 없음",
                    "others": "요약 데이터 없음"
                }

        # 3. 뉴스 데이터 조회 (해시태그별로 그룹화)
        news_query = """
        SELECT
            sh.chapter,
            sh.hashtag,
            sh.hashtag_id,
            ns.news_id,
            ns.news_title,
            ns.news_url,
            ns.news_created_at,
            ns.news_content,
            ns.company_name,
            ns.status
        FROM summary_hashtags sh
        LEFT JOIN news_summaries ns ON sh.hashtag_id = ns.hashtag_id AND ns.job_id = %s
        WHERE sh.job_id = %s
        ORDER BY FIELD(sh.chapter,'business_overview','products_services','revenue_orders','contracts_rnd','others'),
                 sh.hashtag_id, ns.news_created_at DESC
        """

        news_by_chapter = {}
        async with database.get_connection() as cursor:
            await cursor.execute(news_query, (job_id, job_id))
            rows = await cursor.fetchall()

            for row in rows:
                chapter, hashtag, hashtag_id, news_id, title, url, created_at, content, company_name, status = row

                if chapter not in news_by_chapter:
                    news_by_chapter[chapter] = {}

                if hashtag not in news_by_chapter[chapter]:
                    news_by_chapter[chapter][hashtag] = {
                        "hashtag_id": hashtag_id,
                        "news_items": []
                    }

                # 뉴스가 있는 경우만 추가
                if news_id:
                    news_item = {
                        "news_id": news_id,
                        "title": title,
                        "url": url,
                        "published_date": created_at.isoformat() if created_at else None,
                        "summary": content,
                        "company_name": company_name,
                        "status": status
                    }
                    news_by_chapter[chapter][hashtag]["news_items"].append(news_item)

        # 4. 회사 정보 조회
        company_query = """
        SELECT c.company_name, c.company_scale
        FROM companies c
        JOIN job_postings jp ON c.company_id = jp.company_id
        WHERE jp.job_id = %s
        LIMIT 1
        """

        company_info = {}
        async with database.get_connection() as cursor:
            await cursor.execute(company_query, (job_id,))
            result = await cursor.fetchone()
            if result:
                company_info = {
                    "company_name": result[0],
                    "company_scale": result[1]
                }

        return {
            "job_id": job_id,
            "status": current_status,
            "company_info": company_info,
            "summary_reports": summaries,
            "news_data": news_by_chapter,
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting complete data for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get complete data: {str(e)}")

@router.get("/stats")
async def get_admin_stats() -> Dict[str, Any]:
    """관리자 대시보드용 통계"""
    try:
        processing_jobs = await database.get_jobs_by_status("processing")
        completed_jobs = await database.get_jobs_by_status("completed")
        finished_jobs = await database.get_jobs_by_status("finished")
        reprocessing_jobs = await database.get_jobs_by_status("reprocessing")
        news_stats = await database.get_statistics()

        return {
            "job_stats": {
                "processing": len(processing_jobs),
                "completed": len(completed_jobs),
                "finished": len(finished_jobs),
                "reprocessing": len(reprocessing_jobs)
            },
            "news_stats": news_stats
        }

    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/consumer/health")
async def get_consumer_health() -> Dict[str, Any]:
    """Redis Consumer 건강 상태 조회"""
    try:
        # global consumer 인스턴스 가져오기
        from ..main import redis_consumer

        if redis_consumer is None:
            return {"error": "Redis consumer not initialized"}

        health_info = redis_consumer.get_consumer_health()
        return health_info

    except Exception as e:
        logger.error(f"Error getting consumer health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consumer/force-process-pending")
async def force_process_pending(max_age_seconds: int = 300) -> Dict[str, Any]:
    """오래된 pending 메시지 강제 처리"""
    try:
        from ..main import redis_consumer

        if redis_consumer is None:
            raise HTTPException(status_code=503, detail="Redis consumer not initialized")

        processed_count = redis_consumer.force_process_pending(max_age_seconds)

        return {
            "processed_count": processed_count,
            "max_age_seconds": max_age_seconds,
            "message": f"Processed {processed_count} pending messages"
        }

    except Exception as e:
        logger.error(f"Error force processing pending messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consumer/pending")
async def get_pending_messages() -> Dict[str, Any]:
    """Pending 메시지 정보 조회"""
    try:
        from ..main import redis_consumer

        if redis_consumer is None:
            raise HTTPException(status_code=503, detail="Redis consumer not initialized")

        pending_info = redis_consumer.get_pending_messages()
        return pending_info

    except Exception as e:
        logger.error(f"Error getting pending messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/reprocessing")
async def start_job_reprocessing(job_id: int, force: bool = False) -> Dict[str, Any]:
    """
    Job을 재처리 상태로 변경하고 관련 데이터 삭제

    Args:
        job_id: 재처리할 job ID
        force: 강제 실행 여부 (기본: False)
    """
    try:
        # 1. 재처리 가능 여부 확인 (force가 아닌 경우에만)
        if not force:
            eligibility = await database.get_job_reprocessing_eligibility(job_id)
            if not eligibility.get("eligible", False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Job {job_id} is not eligible for reprocessing: {eligibility.get('reason', 'Unknown reason')}"
                )

        # 2. 재처리 시작 및 데이터 정리
        cleanup_stats = await database.start_job_reprocessing(job_id)

        # 3. Redis stream에서 해당 job_id 관련 메시지들 정리
        stream_cleanup_stats = {"removed_messages": 0, "acked_pending": 0}
        try:
            from ..main import redis_consumer
            if redis_consumer and redis_consumer.client:
                # job_id 패턴들 (다양한 형태 대응)
                job_patterns = [
                    str(job_id),
                    f"summary_{job_id}",
                    f"mapping_{job_id}"
                ]

                # 3-1. stream:news에서 해당 job_id 메시지 찾기 및 제거
                # 최근 1000개 메시지를 확인 (너무 많이 확인하지 않도록 제한)
                try:
                    messages = redis_consumer.client.xrange("stream:news", count=1000)
                    messages_to_delete = []

                    for message_id, data in messages:
                        message_job_id = data.get('job_id', '')
                        # job_id가 매치되는 메시지 식별
                        if any(pattern in message_job_id for pattern in job_patterns):
                            messages_to_delete.append(message_id)

                    # 식별된 메시지들 삭제
                    if messages_to_delete:
                        deleted_count = redis_consumer.client.xdel("stream:news", *messages_to_delete)
                        stream_cleanup_stats["removed_messages"] = deleted_count
                        logger.info(f"Removed {deleted_count} messages from stream:news for job {job_id}")

                except Exception as e:
                    logger.warning(f"Failed to clean stream messages for job {job_id}: {e}")

                # 3-2. pending 메시지에서 해당 job_id 찾아서 ACK
                try:
                    pending_messages = redis_consumer.client.xpending_range(
                        "stream:news",
                        "summary-group",
                        min='-',
                        max='+',
                        count=100
                    )

                    pending_to_ack = []
                    for pending_msg in pending_messages:
                        message_id = pending_msg['message_id']
                        try:
                            # 메시지 내용 확인
                            message_data = redis_consumer.client.xrange("stream:news", message_id, message_id)
                            if message_data:
                                _, data = message_data[0]
                                message_job_id = data.get('job_id', '')
                                if any(pattern in message_job_id for pattern in job_patterns):
                                    pending_to_ack.append(message_id)
                        except:
                            pass

                    # pending 메시지 ACK
                    if pending_to_ack:
                        acked_count = redis_consumer.client.xack("stream:news", "summary-group", *pending_to_ack)
                        stream_cleanup_stats["acked_pending"] = acked_count
                        logger.info(f"ACKed {acked_count} pending messages for job {job_id}")

                except Exception as e:
                    logger.warning(f"Failed to clean pending messages for job {job_id}: {e}")

        except Exception as e:
            logger.warning(f"Failed to access Redis for stream cleanup: {e}")

        logger.info(f"Job {job_id} reprocessing started successfully")

        return {
            "success": True,
            "message": f"Job {job_id} has been marked for reprocessing",
            "cleanup_stats": cleanup_stats,
            "stream_cleanup": stream_cleanup_stats,
            "next_steps": [
                "Job status changed to 'reprocessing'",
                "Related database data has been cleaned up",
                "Redis stream messages for this job have been removed",
                "Job is ready for summary-server processing"
            ]
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error for job {job_id} reprocessing: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting reprocessing for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start reprocessing: {str(e)}")
