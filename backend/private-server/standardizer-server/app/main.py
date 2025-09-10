import os
import logging
from fastapi import FastAPI, HTTPException

from .models.standardizer_models import StandardizeRequest, StandardizeResponse
from .models.dart_models import DartExtractRequest, DartExtractResponse, DartStandardizeRequest, DartStandardizeResponse
from .services.standardizer import StandardizerService
from .services.dart_extractor import DartDocumentExtractor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="standardizer-server")

# 서비스 인스턴스
standardizer_service = StandardizerService()
dart_extractor = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global dart_extractor
    
    try:
        # 표준화 서비스 초기화
        await standardizer_service.initialize()
        
        # DART 추출기 초기화 (API 키가 있을 때만)
        dart_api_key = os.getenv('DART_API_KEY')
        if dart_api_key:
            dart_extractor = DartDocumentExtractor(dart_api_key)
            logger.info("DART extractor initialized")
        else:
            logger.warning("DART_API_KEY not found - DART extraction features disabled")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)