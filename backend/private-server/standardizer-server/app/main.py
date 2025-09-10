import os
import logging
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from bs4 import BeautifulSoup

from .models.standardizer_models import StandardizeRequest, StandardizeResponse
from .models.dart_models import DartExtractRequest, DartExtractResponse, DartStandardizeRequest, DartStandardizeResponse, DartSubsectionResponse
from .services.standardizer import StandardizerService
from .services.dart_extractor import DartDocumentExtractor
from .services.file_manager import FileManager
from .services.redis_client import RedisClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="standardizer-server")

# 서비스 인스턴스
standardizer_service = StandardizerService()
dart_extractor = None
file_manager = FileManager()
redis_client = RedisClient()

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global dart_extractor
    
    try:
        # 표준화 서비스 초기화
        await standardizer_service.initialize()
        
        # Redis 클라이언트 초기화
        await redis_client.initialize()
        
        # DART 추출기 초기화 (API 키가 있을 때만)
        dart_api_key = os.getenv('DART_API_KEY')
        if dart_api_key:
            dart_extractor = DartDocumentExtractor(dart_api_key)
            logger.info("DART extractor initialized")
        else:
            logger.warning("DART_API_KEY not found - DART extraction features disabled")
        
        # 백그라운드 워커 시작
        asyncio.create_task(process_job_worker())
        logger.info("Background job worker started")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

async def process_job_worker():
    """백그라운드 작업 처리 워커"""
    while True:
        try:
            # Redis에서 대기 중인 작업 가져오기
            jobs = await redis_client.get_pending_jobs(count=1)
            
            if jobs:
                for job in jobs:
                    await process_single_job(job['stream_id'], job['data'])
            else:
                # 작업이 없으면 1초 대기
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)  # 에러 시 5초 대기

async def process_single_job(stream_id: str, job_data: dict):
    """개별 작업 처리"""
    job_id = job_data.get('job_id')
    
    try:
        logger.info(f"Processing job: {job_id}")
        
        # 1. 작업 상태를 진행 중으로 변경
        await redis_client.update_job_status(
            job_id, 
            "in_progress", 
            {
                "stage": "dart_extraction",
                "current_step": 0,
                "total_steps": 8
            }
        )
        
        # 2. DART 문서 추출
        company_name = job_data.get('company_name')
        report_type = job_data.get('report_type', 'A')
        
        rcp_no, report_nm, rcept_dt = dart_extractor.get_latest_report(
            company_name, report_type
        )
        
        if not rcp_no:
            raise Exception(f"No reports found for {company_name}")
        
        xml_text = dart_extractor.dart.document(rcp_no)
        if not xml_text:
            raise Exception("Failed to download document")
        
        soup = BeautifulSoup(xml_text, 'xml')
        subsections = dart_extractor.extract_business_subsections(soup)
        
        if not subsections:
            raise Exception("Failed to extract subsections")
        
        # 3. 메타데이터 및 원본 파일 저장
        metadata = {
            "job_id": job_id,
            "company_name": company_name,
            "report_name": report_nm,
            "report_date": rcept_dt,
            "receipt_no": rcp_no,
            "created_at": datetime.now().isoformat()
        }
        file_manager.save_metadata(job_id, metadata)
        
        raw_files = {}
        for i, (title, content) in enumerate(subsections.items(), 1):
            raw_files[f"개요{i}_{title.replace(' ', '_').replace('.', '')}.txt"] = content
        file_manager.save_raw_files(job_id, raw_files)
        
        # 4. 표준화 시작
        await redis_client.update_job_status(
            job_id, 
            "in_progress", 
            {
                "stage": "standardization",
                "current_step": 1,
                "total_steps": 8,
                "message": "DART extraction completed, starting standardization"
            }
        )
        
        # 5. 각 챕터별 표준화
        standardized_chapters = {}
        total_chapters = len(subsections)
        
        for i, (title, content) in enumerate(subsections.items(), 1):
            logger.info(f"Standardizing chapter {i}/{total_chapters}: {title}")
            
            standardized_content = await standardizer_service.standardize_text(content)
            standardized_chapters[title] = standardized_content
            
            await redis_client.update_job_status(
                job_id, 
                "in_progress", 
                {
                    "stage": "standardization",
                    "current_step": i + 1,
                    "total_steps": 8,
                    "current_chapter": title,
                    "message": f"Completed {i}/{total_chapters} chapters"
                }
            )
        
        # 6. 표준화된 파일 저장
        file_manager.save_standardized_files(job_id, standardized_chapters)
        
        # 7. 작업 완료
        await redis_client.update_job_status(
            job_id, 
            "completed", 
            {
                "stage": "completed",
                "current_step": 8,
                "total_steps": 8,
                "message": "All processing completed successfully",
                "completed_at": datetime.now().isoformat()
            }
        )
        
        await redis_client.ack_job(stream_id)
        logger.info(f"Job completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Job failed: {job_id}, error: {e}")
        
        await redis_client.update_job_status(
            job_id, 
            "failed", 
            {
                "stage": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
        )
        
        await redis_client.ack_job(stream_id)

@app.get("/health")
def health_check() -> dict:
    """헬스 체크"""
    status = {
        "status": "ok",
        "service": "standardizer",
        "standardizer": standardizer_service.get_status(),
        "dart_enabled": dart_extractor is not None
    }
    return status

@app.post("/standardize", response_model=StandardizeResponse)
async def standardize_content(request: StandardizeRequest) -> StandardizeResponse:
    """텍스트 표준화 처리"""
    try:
        logger.info(f"Processing standardization: mapping_id={request.mapping_id}, chapter={request.chapter}")
        
        standardized_content = await standardizer_service.standardize_text(request.content)
        
        logger.info(f"Standardization completed: mapping_id={request.mapping_id}")
        
        return StandardizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            standardized_content=standardized_content
        )
        
    except Exception as e:
        logger.error(f"Standardization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-dart", response_model=DartExtractResponse)
async def extract_dart_document(request: DartExtractRequest) -> DartExtractResponse:
    """DART 문서 추출"""
    if not dart_extractor:
        raise HTTPException(status_code=503, detail="DART extraction service not available")
    
    try:
        logger.info(f"Processing DART extraction: mapping_id={request.mapping_id}, company={request.company_name}")
        
        # 최신 보고서 조회
        rcp_no, report_nm, rcept_dt = dart_extractor.get_latest_report(
            request.company_name, 
            request.report_type
        )
        
        if not rcp_no:
            raise HTTPException(status_code=404, detail=f"No reports found for {request.company_name}")
        
        # 텍스트 추출 ('II. 사업의 내용' 섹션만)
        extracted_text = dart_extractor.extract_document_text(rcp_no, extract_business_only=True)
        
        if not extracted_text:
            raise HTTPException(status_code=500, detail="Failed to extract document text")
        
        logger.info(f"DART extraction completed: mapping_id={request.mapping_id}")
        
        return DartExtractResponse(
            mapping_id=request.mapping_id,
            company_name=request.company_name,
            report_name=report_nm,
            report_date=rcept_dt,
            receipt_no=rcp_no,
            extracted_text=extracted_text,
            text_length=len(extracted_text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DART extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dart-standardize", response_model=DartStandardizeResponse)
async def extract_and_standardize_dart(request: DartStandardizeRequest) -> DartStandardizeResponse:
    """DART 문서 추출 + 표준화 통합 처리"""
    if not dart_extractor:
        raise HTTPException(status_code=503, detail="DART extraction service not available")
    
    try:
        logger.info(f"Processing DART extraction + standardization: mapping_id={request.mapping_id}, company={request.company_name}")
        
        # 1. DART 문서 추출
        rcp_no, report_nm, rcept_dt = dart_extractor.get_latest_report(
            request.company_name, 
            request.report_type
        )
        
        if not rcp_no:
            raise HTTPException(status_code=404, detail=f"No reports found for {request.company_name}")
        
        # 'II. 사업의 내용' 섹션만 추출
        extracted_text = dart_extractor.extract_document_text(rcp_no, extract_business_only=True)
        
        if not extracted_text:
            raise HTTPException(status_code=500, detail="Failed to extract document text")
        
        # 2. 텍스트 표준화
        standardized_text = await standardizer_service.standardize_text(extracted_text)
        
        logger.info(f"DART extraction + standardization completed: mapping_id={request.mapping_id}")
        
        return DartStandardizeResponse(
            mapping_id=request.mapping_id,
            chapter=request.chapter,
            company_name=request.company_name,
            report_name=report_nm,
            report_date=rcept_dt,
            receipt_no=rcp_no,
            original_text=extracted_text,
            standardized_text=standardized_text,
            original_length=len(extracted_text),
            standardized_length=len(standardized_text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DART extraction + standardization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dart-subsections", response_model=DartSubsectionResponse)
async def extract_dart_subsections(request: DartExtractRequest) -> DartSubsectionResponse:
    """DART 문서를 소제목별로 구조화하여 추출 + 파일 저장"""
    if not dart_extractor:
        raise HTTPException(status_code=503, detail="DART extraction service not available")
    
    try:
        logger.info(f"Processing DART subsection extraction: mapping_id={request.mapping_id}, company={request.company_name}")
        
        # 작업 단계 시작
        job_id = request.mapping_id
        file_manager.update_job_stage(job_id, "raw_extraction", "in_progress")
        
        # 최신 보고서 조회
        rcp_no, report_nm, rcept_dt = dart_extractor.get_latest_report(
            request.company_name, 
            request.report_type
        )
        
        if not rcp_no:
            raise HTTPException(status_code=404, detail=f"No reports found for {request.company_name}")
        
        # XML 다운로드 및 파싱
        xml_text = dart_extractor.dart.document(rcp_no)
        if not xml_text:
            raise HTTPException(status_code=500, detail="Failed to download document")
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(xml_text, 'xml')
        
        # 소제목별 구조화 추출
        subsections = dart_extractor.extract_business_subsections(soup)
        
        if not subsections:
            raise HTTPException(status_code=500, detail="Failed to extract subsections")
        
        # 메타데이터 저장
        metadata = {
            "job_id": job_id,
            "company_name": request.company_name,
            "report_name": report_nm,
            "report_date": rcept_dt,
            "receipt_no": rcp_no,
            "created_at": datetime.now().isoformat()
        }
        file_manager.save_metadata(job_id, metadata)
        
        # 원본 파일들 저장 (raw/)
        raw_files = {}
        for i, (title, content) in enumerate(subsections.items(), 1):
            raw_files[f"개요{i}_{title.replace(' ', '_').replace('.', '')}.txt"] = content
        file_manager.save_raw_files(job_id, raw_files)
        
        # 작업 단계 완료
        file_manager.update_job_stage(job_id, "raw_extraction", "completed")
        file_manager.update_job_stage(job_id, "standardization", "in_progress")
        
        # 표준화된 파일들 저장 (standardized/)
        standardized_chapters = {}
        for title, content in subsections.items():
            standardized_content = await standardizer_service.standardize_text(content)
            standardized_chapters[title] = standardized_content
        
        file_manager.save_standardized_files(job_id, standardized_chapters)
        
        # 표준화 단계 완료
        file_manager.update_job_stage(job_id, "standardization", "completed")
        
        logger.info(f"DART subsection extraction + standardization completed: mapping_id={request.mapping_id}")
        
        return DartSubsectionResponse(
            mapping_id=request.mapping_id,
            company_name=request.company_name,
            report_name=report_nm,
            report_date=rcept_dt,
            receipt_no=rcp_no,
            subsections=standardized_chapters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DART subsection extraction failed: {e}")
        # 실패 시 상태 업데이트
        file_manager.update_job_stage(request.mapping_id, "raw_extraction", "failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dart-subsections-async")
async def extract_dart_subsections_async(request: DartExtractRequest) -> dict:
    """DART 문서를 소제목별로 구조화하여 추출 (비동기)"""
    if not dart_extractor:
        raise HTTPException(status_code=503, detail="DART extraction service not available")
    
    try:
        job_id = str(request.mapping_id)
        logger.info(f"Processing async DART extraction: mapping_id={job_id}, company={request.company_name}")
        
        # Redis에 작업 상태 초기화
        await redis_client.update_job_status(job_id, "pending")
        
        # 작업 데이터 준비
        job_data = {
            "job_id": job_id,
            "mapping_id": request.mapping_id,
            "company_name": request.company_name,
            "report_type": request.report_type,
            "submitted_at": datetime.now().isoformat()
        }
        
        # Redis Stream에 작업 제출
        stream_id = await redis_client.submit_job(job_data)
        
        logger.info(f"Async job submitted: {job_id}, stream_id: {stream_id}")
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job submitted successfully",
            "stream_id": stream_id
        }
        
    except Exception as e:
        logger.error(f"Failed to submit async job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}/status")
async def get_job_status_redis(job_id: str):
    """Redis에서 작업 상태 조회"""
    try:
        # Redis에서 상태 조회
        redis_status = await redis_client.get_job_status(job_id)
        
        # 파일 시스템에서 상태 조회
        file_status = file_manager.get_job_status(job_id)
        
        # 두 정보 병합
        combined_status = {
            "job_id": job_id,
            "redis_status": redis_status,
            "file_status": file_status
        }
        
        if not redis_status and not file_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return combined_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
def list_jobs():
    """모든 작업 목록 조회"""
    try:
        jobs = file_manager.list_jobs()
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """특정 작업 상태 조회"""
    try:
        status = file_manager.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}/raw")
def get_raw_data(job_id: str):
    """작업의 원본 데이터 조회 (파일 내용 포함)"""
    try:
        if not file_manager.job_exists(job_id):
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # raw 디렉토리의 모든 파일 내용 읽기
        job_path = file_manager.get_job_path(job_id)
        raw_path = job_path / "raw"
        
        if not raw_path.exists():
            return {"job_id": job_id, "raw_files": {}}
        
        raw_files = {}
        for file_path in raw_path.iterdir():
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    raw_files[file_path.name] = content
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    raw_files[file_path.name] = f"Error reading file: {e}"
        
        metadata = file_manager.load_metadata(job_id)
        
        return {
            "job_id": job_id,
            "metadata": metadata,
            "raw_files": raw_files,
            "file_count": len(raw_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}/standardized")
def get_standardized_data(job_id: str):
    """작업의 표준화된 데이터 조회 (파일 내용 포함)"""
    try:
        if not file_manager.job_exists(job_id):
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # standardized 디렉토리의 모든 파일 내용 읽기
        job_path = file_manager.get_job_path(job_id)
        standardized_path = job_path / "standardized"
        
        if not standardized_path.exists():
            return {"job_id": job_id, "standardized_files": {}}
        
        standardized_files = {}
        for file_path in standardized_path.iterdir():
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    standardized_files[file_path.name] = content
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    standardized_files[file_path.name] = f"Error reading file: {e}"
        
        metadata = file_manager.load_metadata(job_id)
        
        return {
            "job_id": job_id,
            "metadata": metadata,
            "standardized_files": standardized_files,
            "file_count": len(standardized_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get standardized data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)