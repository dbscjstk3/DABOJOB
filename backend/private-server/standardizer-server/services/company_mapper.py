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
            # 회사 그룹 정보 추가
            group_info = f"그룹: {company.company_group}" if hasattr(company, 'company_group') and company.company_group else ""
            csn_info = f"사람인 회사코드: {company.csn}" if hasattr(company, 'csn') and company.csn else ""

            prompt = f"""
다음 채용공고를 낸 회사와 정확히 일치하는 DART 공시 기업을 찾아주세요.

[채용 회사 정보]
회사명: {company.company_name}
웹사이트: {company.company_url if company.company_url else '정보없음'}
규모: {company.company_scale}
{group_info}
{csn_info}
채용공고 URL: https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx={company.csn if hasattr(company, 'csn') and company.csn else ''}

[매핑 규칙]
1. 같은 회사 또는 직접적인 모회사/자회사 관계면 매핑 OK
   - "네이버제트(주)" → 네이버 (OK, 자회사)
   - "삼성카드고객서비스(주)" → 삼성카드 (OK, 자회사)
   - "키움예스저축은행" → 키움증권 (OK, 계열사)
2. 전혀 다른 회사는 매핑하지 말 것:
   - "(주)월덱스" → 삼성전자 (X, 무관한 회사)
3. DART에 없는 비상장 중소기업이면 null 반환

[응답 형식]
매핑 가능한 경우:
{{
    "dart_corp_name": "DART 정식 기업명",
    "dart_corp_code": "8자리 기업코드",
    "dart_stock_code": "6자리 종목코드 (상장사만)",
    "confidence": 95-100 (정확히 일치 100, 모/자회사 95),
    "notes": "매핑 근거 (정확히 일치/자회사/모회사 등)"
}}

전혀 다른 회사이거나 DART에 없는 경우:
null
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",  # 더 정확한 모델 사용
                messages=[
                    {"role": "system", "content": "당신은 한국 기업 정보에 정통한 DART 시스템 전문가입니다. 정확한 기업 매칭만 수행하고, 불확실한 경우 null을 반환합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # 더 일관된 응답
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
        self.logger.info(f"🚀 Starting batch mapping process (limit: {limit})")

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
                self.logger.info(f"📋 Found {len(unmapped_companies)} companies to process:")
                for i, company in enumerate(unmapped_companies, 1):
                    self.logger.info(f"  {i}. {company.company_name} (ID: {company.company_id})")

                for company in unmapped_companies:
                    try:
                        self.logger.info(f"🔍 Processing: {company.company_name}")

                        # 기존 매핑이 있는지 확인 (실패한 매핑 재시도)
                        existing_mapping = db.query(CompanyDartMapping).filter(
                            CompanyDartMapping.company_id == company.company_id
                        ).first()

                        if existing_mapping:
                            self.logger.info(f"   📝 Found existing mapping (status: {existing_mapping.mapping_status.value})")
                        else:
                            self.logger.info(f"   ✨ No existing mapping, creating new one")

                        self.logger.info(f"   🤖 Calling GPT API for DART mapping...")
                        suggestion = await self.suggest_dart_mapping(company)

                        if suggestion:
                            corp_name = suggestion.get("dart_corp_name", "Unknown")
                            corp_code = suggestion.get("dart_corp_code", "N/A")
                            confidence = suggestion.get("confidence", 0)

                            self.logger.info(f"   ✅ GPT Success: {corp_name} (Code: {corp_code}, Confidence: {confidence}%)")

                            if existing_mapping:
                                # 기존 실패한 매핑 업데이트
                                self.logger.info(f"   🔄 Updating existing mapping (ID: {existing_mapping.mapping_id})")
                                existing_mapping.dart_corp_name = suggestion.get("dart_corp_name")
                                existing_mapping.dart_corp_code = suggestion.get("dart_corp_code")
                                existing_mapping.dart_stock_code = suggestion.get("dart_stock_code")
                                existing_mapping.mapping_status = MappingStatus.suggested
                                existing_mapping.confidence_score = suggestion.get("confidence", 0)
                                existing_mapping.gpt_response = str(suggestion)
                                existing_mapping.processed_at = datetime.utcnow()
                            else:
                                # 새 매핑 생성
                                self.logger.info(f"   ➕ Creating new mapping record")
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
                            self.logger.warning(f"   ❌ GPT Failed: No mapping found for {company.company_name}")

                            if existing_mapping:
                                # 기존 매핑을 다시 실패로 업데이트
                                self.logger.info(f"   🔄 Updating existing mapping to failed (ID: {existing_mapping.mapping_id})")
                                existing_mapping.mapping_status = MappingStatus.failed
                                existing_mapping.confidence_score = 0
                                existing_mapping.gpt_response = "No mapping found"
                                existing_mapping.processed_at = datetime.utcnow()
                            else:
                                # 새 실패 매핑 생성
                                self.logger.info(f"   ➕ Creating new failed mapping record")
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
                            self.logger.info(f"   💾 Intermediate commit: {stats['processed']} processed")
                            db.commit()

                        # API 요청 제한 고려
                        self.logger.info(f"   ⏳ Waiting 1 second before next company...")
                        await asyncio.sleep(1)

                    except Exception as e:
                        self.logger.error(f"   ⚠️ Error processing {company.company_name}: {e}")
                        stats["failed"] += 1
                        stats["processed"] += 1

                self.logger.info(f"💾 Final commit to database...")
                db.commit()

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"❌ Critical error in batch process: {e}")
            raise StandardizerException(f"Failed to batch process mappings: {e}")

        self.logger.info(f"🎉 Batch mapping completed!")
        self.logger.info(f"📊 Final Stats:")
        self.logger.info(f"   - Total Processed: {stats['processed']}")
        self.logger.info(f"   - Successfully Mapped: {stats['suggested']}")
        self.logger.info(f"   - Failed: {stats['failed']}")
        self.logger.info(f"   - Success Rate: {(stats['suggested']/stats['processed']*100):.1f}%" if stats['processed'] > 0 else "   - Success Rate: 0%")

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