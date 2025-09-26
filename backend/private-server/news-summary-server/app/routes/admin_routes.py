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
from ..file_manager import FileManager

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
        # 데이터베이스 연결 확인
        if not database.pool:
            logger.error("Database connection pool not available")
            raise HTTPException(status_code=503, detail="Database service unavailable")

        status = await database.get_job_processing_status(job_id)
        if status is None:
            # job_processing 테이블에 해당 job_id가 없는 경우
            logger.warning(f"Job {job_id} not found in job_processing table")
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {"job_id": job_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error getting job detail for {job_id}: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")

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
        WHERE mapping_id = (SELECT mapping_id FROM job_processing WHERE job_id = %s)
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
                    "other_references": result[4] or "요약 없음"
                }
            else:
                # 요약 데이터가 없는 경우 기본값
                summaries = {
                    "business_overview": "요약 데이터 없음",
                    "products_services": "요약 데이터 없음",
                    "revenue_orders": "요약 데이터 없음",
                    "contracts_rnd": "요약 데이터 없음",
                    "other_references": "요약 데이터 없음"
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
        LEFT JOIN news_summaries ns ON sh.hashtag_id = ns.hashtag_id
            AND ns.mapping_id = (SELECT mapping_id FROM job_processing WHERE job_id = %s)
        WHERE sh.mapping_id = (SELECT mapping_id FROM job_processing WHERE job_id = %s)
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

        processed_count = await redis_consumer.force_process_pending(max_age_seconds)

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

        # 3. Redis stream 정리 작업을 백그라운드에서 처리 (논블로킹)
        stream_cleanup_stats = {"status": "scheduled", "note": "Cleanup scheduled in background"}
        try:
            from ..main import redis_consumer
            if redis_consumer and redis_consumer.client:
                # 백그라운드에서 정리 작업 수행
                import threading

                def background_stream_cleanup():
                    try:
                        cleanup_stats = {"removed_messages": 0, "acked_pending": 0}

                        # job_id 패턴들
                        job_patterns = [str(job_id), f"summary_{job_id}", f"mapping_{job_id}"]

                        # stream 메시지 정리
                        try:
                            messages = redis_consumer.client.xrange("stream:news", count=1000)
                            messages_to_delete = []

                            for message_id, data in messages:
                                message_job_id = data.get('job_id', '')
                                if any(pattern in message_job_id for pattern in job_patterns):
                                    messages_to_delete.append(message_id)

                            if messages_to_delete:
                                deleted_count = redis_consumer.client.xdel("stream:news", *messages_to_delete)
                                cleanup_stats["removed_messages"] = deleted_count
                                logger.info(f"Background: Removed {deleted_count} messages for job {job_id}")
                        except Exception as e:
                            logger.warning(f"Background stream cleanup failed for job {job_id}: {e}")

                        # pending 메시지 ACK
                        try:
                            pending_messages = redis_consumer.client.xpending_range(
                                "stream:news", "summary-group", min='-', max='+', count=100
                            )

                            pending_to_ack = []
                            for pending_msg in pending_messages:
                                message_id = pending_msg['message_id']
                                try:
                                    message_data = redis_consumer.client.xrange("stream:news", message_id, message_id)
                                    if message_data:
                                        _, data = message_data[0]
                                        message_job_id = data.get('job_id', '')
                                        if any(pattern in message_job_id for pattern in job_patterns):
                                            pending_to_ack.append(message_id)
                                except:
                                    pass

                            if pending_to_ack:
                                acked_count = redis_consumer.client.xack("stream:news", "summary-group", *pending_to_ack)
                                cleanup_stats["acked_pending"] = acked_count
                                logger.info(f"Background: ACKed {acked_count} pending messages for job {job_id}")
                        except Exception as e:
                            logger.warning(f"Background pending cleanup failed for job {job_id}: {e}")

                        logger.info(f"Background stream cleanup completed for job {job_id}: {cleanup_stats}")
                    except Exception as e:
                        logger.error(f"Background stream cleanup error for job {job_id}: {e}")

                # 백그라운드 스레드 시작
                cleanup_thread = threading.Thread(target=background_stream_cleanup, daemon=True)
                cleanup_thread.start()
                stream_cleanup_stats["thread_started"] = True

        except Exception as e:
            logger.warning(f"Failed to start background stream cleanup: {e}")
            stream_cleanup_stats["error"] = str(e)

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

@router.get("/files/validate/{mapping_id}")
async def validate_mapping_files(mapping_id: int) -> Dict[str, Any]:
    """
    mapping_id의 디렉터리 구조와 txt 파일 저장 상태 검증
    /app/data/{mapping_id}/summaries/ 경로의 파일 존재 여부 및 내용 확인
    """
    try:
        # FileManager를 통해 파일 시스템 접근
        file_manager = FileManager(mapping_id)

        # 1. 디렉터리 구조 확인
        directory_status = {
            "base_path": str(file_manager.base_path),
            "base_exists": file_manager.base_path.exists(),
            "raw_dir": str(file_manager.raw_dir),
            "raw_exists": file_manager.raw_dir.exists(),
            "standardized_dir": str(file_manager.standardized_dir),
            "standardized_exists": file_manager.standardized_dir.exists(),
            "summaries_dir": str(file_manager.summaries_dir),
            "summaries_exists": file_manager.summaries_dir.exists()
        }

        # 2. 요약 파일별 상태 확인
        chapters = ["business_overview", "products_services", "revenue_orders", "contracts_rnd", "other_references"]
        file_status = {}
        total_files = 0
        valid_files = 0

        for chapter in chapters:
            filename = file_manager._get_summary_filename(chapter)
            file_path = file_manager.summaries_dir / filename

            file_info = {
                "filename": filename,
                "path": str(file_path),
                "exists": file_path.exists(),
                "size_bytes": 0,
                "content_preview": "",
                "is_valid": False
            }

            if file_path.exists():
                total_files += 1
                try:
                    file_info["size_bytes"] = file_path.stat().st_size

                    # 파일 내용 읽기 (처음 200자만)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_info["content_preview"] = content[:200] + ("..." if len(content) > 200 else "")

                        # 유효성 검사 (빈 파일이 아니고 최소 길이 확인)
                        if content.strip() and len(content.strip()) > 10:
                            file_info["is_valid"] = True
                            valid_files += 1

                except Exception as e:
                    file_info["error"] = str(e)

            file_status[chapter] = file_info

        # 3. 전체 파일 목록
        all_files = file_manager.list_files()

        # 4. DB 데이터와 비교 (company_analysis_summaries 테이블)
        db_summary_exists = False
        db_summary_data = None

        try:
            db_summary_data = await database.get_company_analysis(mapping_id)
            db_summary_exists = bool(db_summary_data)
        except Exception as e:
            logger.warning(f"Failed to get DB summary for mapping_id {mapping_id}: {e}")

        # 5. 종합 평가
        summary = {
            "mapping_id": mapping_id,
            "directory_structure_valid": all([
                directory_status["base_exists"],
                directory_status["summaries_exists"]
            ]),
            "total_expected_files": len(chapters),
            "total_files_found": total_files,
            "valid_files_count": valid_files,
            "completion_percentage": round((valid_files / len(chapters)) * 100, 2),
            "db_summary_exists": db_summary_exists,
            "overall_status": "valid" if valid_files == len(chapters) and db_summary_exists else "incomplete"
        }

        return {
            "summary": summary,
            "directory_status": directory_status,
            "file_status": file_status,
            "all_files": all_files,
            "db_summary_data": db_summary_data,
            "validation_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error validating files for mapping_id {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate files: {str(e)}")

@router.post("/test/complete-to-s3/{mapping_id}")
async def complete_mapping_to_s3(mapping_id: int) -> Dict[str, Any]:
    """
    테스트용: mapping_id로 요약 데이터 찾기 → DB 저장 → completed → S3 업로드 → finished
    실패 시 상태 rollback
    """
    job_ids = []
    original_statuses = {}

    try:
        # 1. mapping_id로 모든 job_id와 상태 찾기
        async with database.get_connection() as cursor:
            query = """
            SELECT jp.job_id, jp.status
            FROM job_processing jp
            JOIN job_postings j ON jp.job_id = j.job_id
            JOIN company_dart_mappings cdm ON j.company_id = cdm.company_id
            WHERE cdm.mapping_id = %s
            """
            await cursor.execute(query, (mapping_id,))
            results = await cursor.fetchall()

            if not results:
                raise HTTPException(status_code=404, detail=f"No job found for mapping_id {mapping_id}")

            job_data = [(row[0], row[1]) for row in results]
            job_ids = [job_id for job_id, _ in job_data]
            original_statuses = {job_id: status for job_id, status in job_data}

            logger.info(f"Found job_ids {job_ids} for mapping_id {mapping_id}")
            logger.info(f"Original statuses: {original_statuses}")

        # 2. FileManager로 실제 요약 데이터 읽기
        file_manager = FileManager(mapping_id)
        analysis_data = file_manager.get_company_analysis_data()

        if not analysis_data:
            raise HTTPException(status_code=404, detail=f"No summary data found for mapping_id {mapping_id}")

        # 3. DB에 요약 데이터 저장
        await database.save_company_analysis_summaries(mapping_id, analysis_data)
        logger.info(f"✅ Saved summary data to DB for mapping_id: {mapping_id}")

        # 4. 모든 job 상태를 completed로 변경
        completed_jobs = []
        for job_id in job_ids:
            success = await database.update_job_processing_status(job_id, "completed")
            if success:
                completed_jobs.append(job_id)
            else:
                logger.error(f"Failed to update job status to completed for job_id {job_id}")

        if not completed_jobs:
            raise Exception("Failed to update any job status to completed")
        logger.info(f"✅ Updated jobs {completed_jobs} status to 'completed'")

        # 5. S3 업로드 실행 (첫 번째 job_id 사용)
        primary_job_id = job_ids[0]
        logger.info(f"🚀 Starting S3 upload for primary job_id {primary_job_id}")
        uploaded_files = await s3_service.upload_job_completion_data(primary_job_id)

        if not uploaded_files:
            raise Exception("S3 upload failed - no files uploaded")
        logger.info(f"✅ S3 upload completed: {list(uploaded_files.keys())}")

        # 6. 모든 job 상태를 finished로 변경
        finished_jobs = []
        for job_id in job_ids:
            success = await database.update_job_processing_status(job_id, "finished")
            if success:
                finished_jobs.append(job_id)
            else:
                logger.warning(f"Failed to update status to finished for job {job_id}")

        logger.info(f"✅ Updated jobs {finished_jobs} status to 'finished'")

        return {
            "success": True,
            "mapping_id": mapping_id,
            "job_ids": job_ids,
            "primary_job_id": primary_job_id,
            "original_statuses": original_statuses,
            "completed_jobs": completed_jobs,
            "finished_jobs": finished_jobs,
            "final_status": "finished",
            "summary_data_keys": list(analysis_data.keys()),
            "uploaded_files": uploaded_files,
            "message": f"Successfully completed full flow for {len(job_ids)} jobs: summaries → DB → completed → S3 → finished"
        }

    except Exception as e:
        logger.error(f"❌ Error in complete flow for mapping_id {mapping_id}: {e}")

        # Rollback: 모든 job을 원래 상태로 되돌리기
        if 'job_ids' in locals() and 'original_statuses' in locals():
            try:
                rolled_back_jobs = []
                for job_id in job_ids:
                    original_status = original_statuses.get(job_id)
                    if original_status:
                        rollback_success = await database.update_job_processing_status(job_id, original_status)
                        if rollback_success:
                            rolled_back_jobs.append(job_id)

                if rolled_back_jobs:
                    logger.info(f"🔄 Rolled back jobs {rolled_back_jobs} to their original statuses")
                else:
                    logger.error(f"🔄 Failed to rollback any job status")
            except Exception as rollback_error:
                logger.error(f"🔄 Rollback error: {rollback_error}")

        raise HTTPException(status_code=500, detail=f"Failed to complete flow: {str(e)}")

@router.get("/data/s3-preview/{job_id}")
async def get_s3_preview_data(job_id: int) -> Dict[str, Any]:
    """
    S3 업로드와 동일한 데이터를 JSON으로 미리보기
    (s3_service.upload_job_completion_data와 완전히 동일한 로직)
    """
    try:
        from ..services.s3_service import s3_service

        # S3 업로드 시와 동일한 데이터 수집
        companies_data = await s3_service._get_companies_data(job_id)
        job_postings_data = await s3_service._get_job_postings_data(job_id)
        job_sectors_data = await s3_service._get_job_sectors_data(job_id)
        dart_data = await s3_service._get_dart_data(job_id)

        # S3 업로드 시와 동일한 형태로 반환
        return {
            "job_id": job_id,
            "companies": companies_data,
            "job_postings": job_postings_data,
            "job_sectors": job_sectors_data,
            "Dart": dart_data,
            "preview_timestamp": datetime.now().isoformat(),
            "note": "This is the exact same data that would be uploaded to S3"
        }

    except Exception as e:
        logger.error(f"Error getting S3 preview data for job_id {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get S3 preview data: {str(e)}")
