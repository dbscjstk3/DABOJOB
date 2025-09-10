from pydantic import BaseModel
from typing import Optional, Dict

class DartExtractRequest(BaseModel):
    """DART 문서 추출 요청 모델"""
    mapping_id: int
    company_name: str
    report_type: str = "A"  # 기본값: 정기보고서

class DartExtractResponse(BaseModel):
    """DART 문서 추출 응답 모델"""
    mapping_id: int
    company_name: str
    report_name: Optional[str] = None
    report_date: Optional[str] = None
    receipt_no: Optional[str] = None
    extracted_text: str
    text_length: int
    status: str = "completed"

class DartStandardizeRequest(BaseModel):
    """DART 추출 + 표준화 통합 요청 모델"""
    mapping_id: int
    company_name: str
    report_type: str = "A"
    chapter: int = 1

class DartStandardizeResponse(BaseModel):
    """DART 추출 + 표준화 통합 응답 모델"""
    mapping_id: int
    chapter: int
    company_name: str
    report_name: Optional[str] = None
    report_date: Optional[str] = None
    receipt_no: Optional[str] = None
    original_text: str
    standardized_text: str
    original_length: int
    standardized_length: int
    status: str = "completed"

class BusinessSections(BaseModel):
    """사업 내용 5개 카테고리"""
    business_overview: str  # 1. 사업의 개요
    products_services: str  # 2. 주요 제품 및 서비스
    revenue_orders: str     # 3. 매출 및 수주 상황
    contracts_rnd: str      # 4. 주요 계약 및 연구개발 활동
    other_references: str   # 5. 기타 참고사항

class DartClassifyRequest(BaseModel):
    """DART 문서 분류 요청 모델"""
    mapping_id: int
    company_name: str
    report_type: str = "A"

class DartClassifyResponse(BaseModel):
    """DART 문서 분류 응답 모델"""
    mapping_id: int
    company_name: str
    report_name: Optional[str] = None
    report_date: Optional[str] = None
    receipt_no: Optional[str] = None
    sections: BusinessSections
    status: str = "completed"

class DartSubsectionResponse(BaseModel):
    """DART 소제목별 구조화 응답 모델"""
    mapping_id: int
    company_name: str
    report_name: Optional[str] = None
    report_date: Optional[str] = None
    receipt_no: Optional[str] = None
    subsections: Dict[str, str]  # 소제목: 내용
    status: str = "completed"