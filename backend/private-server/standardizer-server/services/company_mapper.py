"""
회사-DART 매핑 서비스
"""
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from services.base import BaseService
from models.crawler import Company, CompanyDartMapping, MappingStatus
from utils.exceptions import StandardizerException
from config import settings


class CompanyMappingService(BaseService):
    """회사-DART 매핑 서비스"""

    def __init__(self):
        super().__init__("CompanyMappingService")
        self.openai_client: Optional[Any] = None

    async def _setup(self) -> None:
        """OpenAI 클라이언트 초기화"""
        try:
            if settings.OPENAI_API_KEY:
                import openai
                self.openai_client = openai.AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY
                )
                self.logger.info("OpenAI client initialized")
            else:
                self.logger.warning("OpenAI API key not found - mapping features limited")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")

    def get_mapping_stats(self, db: Session) -> Dict[str, int]:
        """매핑 통계 조회"""
        try:
            total_companies = db.query(Company).count()

            unmapped = db.query(Company).filter(
                ~Company.company_id.in_(
                    db.query(CompanyDartMapping.company_id)
                )
            ).count()

            pending = db.query(CompanyDartMapping).filter(
                CompanyDartMapping.mapping_status == MappingStatus.suggested
            ).count()

            verified = db.query(CompanyDartMapping).filter(
                CompanyDartMapping.mapping_status == MappingStatus.verified
            ).count()

            failed = db.query(CompanyDartMapping).filter(
                CompanyDartMapping.mapping_status == MappingStatus.failed
            ).count()

            return {
                "total_companies": total_companies,
                "unmapped": unmapped,
                "pending": pending,
                "verified": verified,
                "failed": failed
            }
        except Exception as e:
            self.logger.error(f"Failed to get mapping stats: {e}")
            raise StandardizerException(f"Failed to get mapping stats: {e}")

    def get_unmapped_companies(self, db: Session, limit: int = 50) -> List[Company]:
        """매핑되지 않은 회사 및 실패한 매핑 회사 목록 조회"""
        try:
            # 성공적으로 매핑된 회사들 (verified, suggested 상태)만 제외
            successfully_mapped_ids = db.query(CompanyDartMapping.company_id).filter(
                CompanyDartMapping.mapping_status.in_([MappingStatus.verified, MappingStatus.suggested])
            )

            return db.query(Company).filter(
                ~Company.company_id.in_(successfully_mapped_ids)
            ).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Failed to get unmapped companies: {e}")
            raise StandardizerException(f"Failed to get unmapped companies: {e}")

    def get_pending_mappings(self, db: Session, limit: int = 50) -> List[CompanyDartMapping]:
        """검증 대기 중인 매핑 목록 조회"""
        try:
            return db.query(CompanyDartMapping).filter(
                CompanyDartMapping.mapping_status == MappingStatus.suggested
            ).order_by(CompanyDartMapping.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Failed to get pending mappings: {e}")
            raise StandardizerException(f"Failed to get pending mappings: {e}")

    async def suggest_dart_mapping(self, company: Company) -> Optional[Dict[str, Any]]:
        """GPT를 사용한 DART 매핑 제안"""
        if not self.openai_client:
            self.logger.warning("OpenAI client not available for mapping")
            return None

        try:
            prompt = f"""
다음 회사 정보를 보고 DART 시스템에서 해당하는 기업을 찾아주세요.

회사명: {company.company_name}
웹사이트: {company.company_url}
규모: {company.company_scale}

DART 기업 정보를 JSON 형태로 제공해주세요:
{{
    "dart_corp_name": "DART에서의 정식 기업명",
    "dart_corp_code": "8자리 기업코드",
    "dart_stock_code": "6자리 종목코드 (상장사인 경우)",
    "confidence": 1-100 신뢰도,
    "notes": "매핑 근거"
}}

찾을 수 없는 경우 null을 반환하세요.
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content
            if content and content.strip() != "null":
                import json
                return json.loads(content)

            return None

        except Exception as e:
            self.logger.error(f"Failed to suggest DART mapping for {company.company_name}: {e}")
            return None

    async def batch_process_mappings(self, limit: int = 10) -> Dict[str, int]:
        """배치로 매핑 처리"""
        stats = {
            "processed": 0,
            "suggested": 0,
            "failed": 0
        }

        try:
            from models.database import SessionLocal
            db = SessionLocal()

            try:
                unmapped_companies = self.get_unmapped_companies(db, limit)

                for company in unmapped_companies:
                    try:
                        suggestion = await self.suggest_dart_mapping(company)

                        # 기존 매핑이 있는지 확인 (실패한 매핑 재시도)
                        existing_mapping = db.query(CompanyDartMapping).filter(
                            CompanyDartMapping.company_id == company.company_id
                        ).first()

                        if suggestion:
                            if existing_mapping:
                                # 기존 실패한 매핑 업데이트
                                existing_mapping.dart_corp_name = suggestion.get("dart_corp_name")
                                existing_mapping.dart_corp_code = suggestion.get("dart_corp_code")
                                existing_mapping.dart_stock_code = suggestion.get("dart_stock_code")
                                existing_mapping.mapping_status = MappingStatus.suggested
                                existing_mapping.confidence_score = suggestion.get("confidence", 0)
                                existing_mapping.gpt_response = str(suggestion)
                                existing_mapping.processed_at = datetime.utcnow()
                            else:
                                # 새 매핑 생성
                                mapping = CompanyDartMapping(
                                    company_id=company.company_id,
                                    crawled_company_name=company.company_name,
                                    crawled_company_url=company.company_url,
                                    dart_corp_name=suggestion.get("dart_corp_name"),
                                    dart_corp_code=suggestion.get("dart_corp_code"),
                                    dart_stock_code=suggestion.get("dart_stock_code"),
                                    mapping_status=MappingStatus.suggested,
                                    confidence_score=suggestion.get("confidence", 0),
                                    gpt_response=str(suggestion)
                                )
                                db.add(mapping)
                            stats["suggested"] += 1
                        else:
                            if existing_mapping:
                                # 기존 매핑을 다시 실패로 업데이트
                                existing_mapping.mapping_status = MappingStatus.failed
                                existing_mapping.confidence_score = 0
                                existing_mapping.gpt_response = "No mapping found"
                                existing_mapping.processed_at = datetime.utcnow()
                            else:
                                # 새 실패 매핑 생성
                                mapping = CompanyDartMapping(
                                    company_id=company.company_id,
                                    crawled_company_name=company.company_name,
                                    crawled_company_url=company.company_url,
                                    mapping_status=MappingStatus.failed,
                                    confidence_score=0,
                                    gpt_response="No mapping found"
                                )
                                db.add(mapping)
                            stats["failed"] += 1

                        stats["processed"] += 1

                        # 주기적으로 커밋
                        if stats["processed"] % 5 == 0:
                            db.commit()

                        # API 요청 제한 고려
                        await asyncio.sleep(1)

                    except Exception as e:
                        self.logger.error(f"Failed to process mapping for {company.company_name}: {e}")
                        stats["failed"] += 1

                db.commit()

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Failed to batch process mappings: {e}")
            raise StandardizerException(f"Failed to batch process mappings: {e}")

        self.logger.info(f"Batch mapping completed: {stats}")
        return stats

    def verify_mapping(
        self,
        db: Session,
        mapping_id: int,
        verified_by: str,
        is_correct: bool,
        notes: Optional[str] = None
    ) -> bool:
        """매핑 검증"""
        try:
            mapping = db.query(CompanyDartMapping).filter(
                CompanyDartMapping.mapping_id == mapping_id
            ).first()

            if not mapping:
                return False

            from datetime import datetime
            mapping.mapping_status = MappingStatus.verified if is_correct else MappingStatus.rejected
            mapping.verified_at = datetime.utcnow()
            mapping.verified_by = verified_by
            mapping.manual_notes = notes

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to verify mapping {mapping_id}: {e}")
            raise StandardizerException(f"Failed to verify mapping: {e}")

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        base_status = super().get_status()
        base_status.update({
            "openai_available": self.openai_client is not None,
            "api_key_configured": bool(settings.OPENAI_API_KEY)
        })
        return base_status