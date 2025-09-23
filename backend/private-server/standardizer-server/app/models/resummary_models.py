"""
재요약 시스템 SQLAlchemy 모델
"""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, Enum, ForeignKey, JSON, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class SummaryStatus(enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"
    archived = "archived"

class ResummaryRequestStatus(enum.Enum):
    requested = "requested"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class SummaryVersion(Base):
    """요약 버전 관리 테이블"""
    __tablename__ = 'summary_versions'

    version_id = Column(BigInteger, primary_key=True, autoincrement=True)
    mapping_id = Column(BigInteger, nullable=False, comment='매핑 ID')
    version_number = Column(Integer, nullable=False, default=1, comment='버전 번호')
    status = Column(Enum(SummaryStatus), default=SummaryStatus.processing)

    # 품질 관리
    quality_score = Column(Integer, comment='관리자 평가 점수 (1-5)')
    quality_issues = Column(JSON, comment='품질 문제점 배열')
    admin_notes = Column(Text, comment='관리자 메모')

    # 처리 이력
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    requested_by = Column(String(100), comment='재요약 요청자')
    request_reason = Column(Text, comment='재요약 요청 이유')

    # 통계 정보
    total_chapters = Column(Integer, default=5)
    completed_chapters = Column(Integer, default=0)
    total_news_count = Column(Integer, default=0)

    # 관계 설정
    company_analysis_summaries = relationship("CompanyAnalysisSummary", back_populates="summary_version")
    summary_hashtags = relationship("SummaryHashtag", back_populates="summary_version")
    news_summaries = relationship("NewsSummary", back_populates="summary_version")

class CompanyAnalysisSummary(Base):
    """회사 분석 요약 (버전별)"""
    __tablename__ = 'company_analysis_summaries'

    summary_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(BigInteger, ForeignKey('summary_versions.version_id', ondelete='CASCADE'), nullable=False)
    mapping_id = Column(BigInteger, nullable=False, comment='매핑 ID')

    # 5개 챕터 요약
    business_overview = Column(Text, comment='1. 사업의 개요')
    products_service = Column(Text, comment='2. 주요 제품 및 서비스')
    sales_contracts = Column(Text, comment='4. 매출 및 수주 상황')
    rnd_activities = Column(Text, comment='6. 주요 계약 및 연구 개발 활동')
    other_notes = Column(Text, comment='7. 기타 참고사항')

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    summary_version = relationship("SummaryVersion", back_populates="company_analysis_summaries")
    summary_hashtags = relationship("SummaryHashtag", back_populates="company_analysis_summary")
    news_summaries = relationship("NewsSummary", back_populates="company_analysis_summary")

class SummaryHashtag(Base):
    """해시태그 (버전별)"""
    __tablename__ = 'summary_hashtags'

    hashtag_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(BigInteger, ForeignKey('summary_versions.version_id', ondelete='CASCADE'), nullable=False)
    mapping_id = Column(BigInteger, nullable=False, comment='매핑 ID')
    summary_id = Column(BigInteger, ForeignKey('company_analysis_summaries.summary_id', ondelete='CASCADE'), nullable=False)

    chapter = Column(String(50), nullable=False, comment='챕터명')
    hashtag = Column(String(100), nullable=False, comment='해시태그')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    summary_version = relationship("SummaryVersion", back_populates="summary_hashtags")
    company_analysis_summary = relationship("CompanyAnalysisSummary", back_populates="summary_hashtags")
    news_summaries = relationship("NewsSummary", back_populates="summary_hashtag")

class NewsSummary(Base):
    """뉴스 요약 (버전별)"""
    __tablename__ = 'news_summaries'

    news_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(BigInteger, ForeignKey('summary_versions.version_id', ondelete='CASCADE'), nullable=False)
    mapping_id = Column(BigInteger, nullable=False, comment='매핑 ID')
    hashtag_id = Column(BigInteger, ForeignKey('summary_hashtags.hashtag_id', ondelete='CASCADE'), nullable=False)
    summary_id = Column(BigInteger, ForeignKey('company_analysis_summaries.summary_id', ondelete='CASCADE'), nullable=False)

    # 뉴스 정보
    news_title = Column(String(500), nullable=False, comment='뉴스 제목')
    news_url = Column(String(1000), nullable=False, comment='뉴스 URL')
    news_created_at = Column(DateTime, nullable=False, comment='뉴스 생성 날짜')
    news_content = Column(Text, comment='뉴스 요약')
    company_name = Column(String(200), comment='기업명')

    status = Column(Enum('raw', 'completed', name='news_status'), default='raw', comment='처리 상태')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    summary_version = relationship("SummaryVersion", back_populates="news_summaries")
    summary_hashtag = relationship("SummaryHashtag", back_populates="news_summaries")
    company_analysis_summary = relationship("CompanyAnalysisSummary", back_populates="news_summaries")

class ResummaryRequest(Base):
    """재요약 요청 로그"""
    __tablename__ = 'resummary_requests'

    request_id = Column(BigInteger, primary_key=True, autoincrement=True)
    mapping_id = Column(BigInteger, nullable=False)
    from_version = Column(Integer, nullable=False, comment='이전 버전')
    to_version = Column(Integer, nullable=False, comment='새 버전')

    # 요청 정보
    requested_by = Column(String(100), nullable=False, comment='요청자')
    request_reason = Column(Text, nullable=False, comment='재요약 이유')
    quality_issues = Column(JSON, comment='발견된 품질 문제')

    # 상태 추적
    status = Column(Enum(ResummaryRequestStatus), default=ResummaryRequestStatus.requested)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

class VersionComparison(Base):
    """버전 비교 로그"""
    __tablename__ = 'version_comparisons'

    comparison_id = Column(BigInteger, primary_key=True, autoincrement=True)
    mapping_id = Column(BigInteger, nullable=False)
    version_1 = Column(Integer, nullable=False)
    version_2 = Column(Integer, nullable=False)

    # 비교 메트릭
    summary_length_diff = Column(JSON, comment='요약 길이 차이')
    news_count_diff = Column(Integer, comment='뉴스 개수 차이')
    quality_improvement = Column(DECIMAL(5,2), comment='품질 개선도')
    processing_time_diff = Column(Integer, comment='처리 시간 차이(초)')

    compared_at = Column(DateTime, default=datetime.utcnow)
    compared_by = Column(String(100))