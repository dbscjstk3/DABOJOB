from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Text, Enum, ForeignKey, Integer, Date, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class JobStatus(enum.Enum):
    active = "active"
    closed = "closed"
    expired = "expired"


class CrawlStatus(enum.Enum):
    success = "success"
    failed = "failed"
    partial = "partial"
    running = "running"


class MappingStatus(enum.Enum):
    pending = "pending"          # 매핑 대기 중
    processing = "processing"    # GPT API 처리 중
    suggested = "suggested"      # GPT가 제안함
    verified = "verified"        # 수동 검증 완료
    rejected = "rejected"        # 매핑 거부됨
    failed = "failed"           # 매핑 실패


class Company(Base):
    __tablename__ = 'companies'
    
    company_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    csn = Column(String(255), unique=True, index=True)
    company_group = Column(String(255))
    company_scale = Column(String(50))
    company_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job_postings = relationship("JobPosting", back_populates="company")
    
    __table_args__ = (
        Index('idx_company_name', 'company_name'),
    )


class JobPosting(Base):
    __tablename__ = 'job_postings'
    
    job_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('companies.company_id'), nullable=False)
    
    saramin_job_id = Column(String(50), nullable=False, unique=True)
    saramin_job_title = Column(String(500), nullable=False)
    saramin_job_url = Column(String(500), nullable=False)
    
    work_location = Column(String(255))
    career_info = Column(String(255))
    education_requirement = Column(String(100))
    salary_info = Column(String(255))
    
    posting_date = Column(Date)
    application_deadline = Column(Date)
    registration_info = Column(String(100))
    
    status = Column(Enum(JobStatus), default=JobStatus.active)
    is_hot = Column(Boolean, default=False)
    
    crawled_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company", back_populates="job_postings")
    job_sectors = relationship("JobPostingSector", back_populates="job_posting", cascade="all, delete-orphan")
    job_regions = relationship("JobPostingRegion", back_populates="job_posting", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_company_id', 'company_id'),
        Index('idx_posting_date', 'posting_date'),
        Index('idx_deadline', 'application_deadline'),
        Index('idx_status', 'status'),
    )


class JobSector(Base):
    __tablename__ = 'job_sectors'
    
    sector_id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_name = Column(String(100), nullable=False, unique=True)
    sector_category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job_postings = relationship("JobPostingSector", back_populates="sector")


class JobPostingSector(Base):
    __tablename__ = 'job_posting_sectors'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey('job_postings.job_id', ondelete='CASCADE'), nullable=False)
    sector_id = Column(BigInteger, ForeignKey('job_sectors.sector_id'), nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job_posting = relationship("JobPosting", back_populates="job_sectors")
    sector = relationship("JobSector", back_populates="job_postings")
    
    __table_args__ = (
        UniqueConstraint('job_id', 'sector_id', name='unique_job_sector'),
        Index('idx_job_id', 'job_id'),
        Index('idx_sector_id', 'sector_id'),
    )


class Region(Base):
    __tablename__ = 'regions'
    
    region_id = Column(BigInteger, primary_key=True, autoincrement=True)
    region_name = Column(String(100), nullable=False)
    parent_region_id = Column(BigInteger, ForeignKey('regions.region_id'))
    region_level = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("Region", remote_side=[region_id])
    job_postings = relationship("JobPostingRegion", back_populates="region")
    
    __table_args__ = (
        Index('idx_parent_region', 'parent_region_id'),
        Index('idx_region_level', 'region_level'),
    )


class JobPostingRegion(Base):
    __tablename__ = 'job_posting_regions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey('job_postings.job_id', ondelete='CASCADE'), nullable=False)
    region_id = Column(BigInteger, ForeignKey('regions.region_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job_posting = relationship("JobPosting", back_populates="job_regions")
    region = relationship("Region", back_populates="job_postings")
    
    __table_args__ = (
        UniqueConstraint('job_id', 'region_id', name='unique_job_region'),
    )


class CrawlingLog(Base):
    __tablename__ = 'crawling_logs'
    
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    crawl_type = Column(String(50), nullable=False)
    crawl_url = Column(String(500))
    crawl_status = Column(Enum(CrawlStatus), nullable=False)
    items_found = Column(Integer, default=0)
    items_saved = Column(Integer, default=0)
    error_message = Column(Text)
    crawl_duration_seconds = Column(Integer)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_crawl_type', 'crawl_type'),
        Index('idx_crawl_status', 'crawl_status'),
        Index('idx_started_at', 'started_at'),
    )


class CompanyDartMapping(Base):
    """회사명-DART 매핑 테이블 (기존 테이블과 느슨한 결합)"""
    __tablename__ = 'company_dart_mappings'

    mapping_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('companies.company_id'), nullable=False)

    # 크롤링된 회사 정보
    crawled_company_name = Column(String(255), nullable=False)
    crawled_company_url = Column(String(500))

    # DART 매핑 정보
    dart_corp_code = Column(String(8))      # DART 고유 기업 코드
    dart_corp_name = Column(String(255))    # DART 기업명 (정식명칭)
    dart_stock_code = Column(String(10))    # 주식 종목 코드 (A123456 형태)

    # 매핑 메타데이터
    mapping_status = Column(Enum(MappingStatus), default=MappingStatus.pending)
    confidence_score = Column(Integer)       # GPT 신뢰도 (0-100)
    gpt_response = Column(Text)             # GPT 원본 응답
    manual_notes = Column(Text)             # 수동 검증 메모

    # 처리 이력
    processed_at = Column(DateTime)         # GPT 처리 완료 시간
    verified_at = Column(DateTime)          # 수동 검증 완료 시간
    verified_by = Column(String(100))       # 검증자

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    company = relationship("Company")

    __table_args__ = (
        Index('idx_company_id', 'company_id'),
        Index('idx_mapping_status', 'mapping_status'),
        Index('idx_dart_corp_code', 'dart_corp_code'),
        Index('idx_processed_at', 'processed_at'),
        UniqueConstraint('company_id', name='unique_company_mapping'),
    )