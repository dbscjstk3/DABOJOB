"""
DART 관련 데이터 모델
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, Date
from datetime import datetime

from .database import Base


class DartDocument(Base):
    """DART 문서 정보"""
    __tablename__ = 'dart_documents'

    document_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # DART 정보
    receipt_no = Column(String(20), nullable=False, unique=True)  # 접수번호
    corp_code = Column(String(8), nullable=False)               # 기업코드
    corp_name = Column(String(255), nullable=False)             # 기업명
    stock_code = Column(String(6))                              # 종목코드

    # 보고서 정보
    report_name = Column(String(255), nullable=False)           # 보고서명
    report_type = Column(String(50))                            # 보고서 유형
    receipt_date = Column(Date, nullable=False)                 # 접수일자

    # 문서 상태
    extraction_status = Column(String(20), default='pending')   # 추출 상태
    standardization_status = Column(String(20), default='pending')  # 표준화 상태

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StandardizedText(Base):
    """표준화된 텍스트"""
    __tablename__ = 'standardized_texts'

    text_id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, nullable=False)  # DART 문서 ID
    job_id = Column(String(100), nullable=False)      # 작업 ID

    # 텍스트 정보
    category = Column(String(50), nullable=False)     # 카테고리 (business_overview 등)
    chapter_title = Column(String(500))               # 챕터 제목
    original_text = Column(Text)                      # 원본 텍스트
    standardized_text = Column(Text)                  # 표준화된 텍스트

    # 처리 정보
    processing_stage = Column(String(50), default='pending')  # 처리 단계
    confidence_score = Column(Integer)                        # 신뢰도

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)