"""
회사명-DART 매핑 서비스
GPT API를 활용한 회사명 자동 매핑 및 관리
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.crawler_models import Company, CompanyDartMapping, MappingStatus
from ..database import SessionLocal

logger = logging.getLogger(__name__)


class CompanyMappingService:
    """회사-DART 매핑 서비스"""

    def __init__(self):
        self.openai_client: Optional[Any] = None

    async def initialize(self) -> None:
        """OpenAI 클라이언트 초기화"""
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                import openai
                self.openai_client = openai.AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client initialized for company mapping")
            else:
                logger.warning("OpenAI API key not found - mapping features limited")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

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
            logger.error(f"Failed to get unmapped companies: {e}")
            raise Exception(f"Failed to get unmapped companies: {e}")

    async def suggest_dart_mapping(self, company: Company) -> Optional[Dict[str, Any]]:
        """GPT를 사용한 DART 매핑 제안"""
        if not self.openai_client:
            logger.warning("OpenAI client not available for mapping")
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
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "당신은 한국 기업 정보에 정통한 DART 시스템 전문가입니다. 정확한 기업 매칭만 수행하고, 불확실한 경우 null을 반환합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )

            content = response.choices[0].message.content
            if content and content.strip() != "null":
                import json
                return json.loads(content)

            return None

        except Exception as e:
            logger.error(f"Failed to suggest DART mapping for {company.company_name}: {e}")
            return None

    async def batch_process_mappings(self, limit: int = 10) -> Dict[str, int]:
        """배치로 매핑 처리"""
        logger.info(f"🚀 Starting batch mapping process (limit: {limit})")

        stats = {
            "processed": 0,
            "suggested": 0,
            "failed": 0
        }

        try:
            db = SessionLocal()

            try:
                unmapped_companies = self.get_unmapped_companies(db, limit)
                logger.info(f"📋 Found {len(unmapped_companies)} companies to process:")
                for i, company in enumerate(unmapped_companies, 1):
                    logger.info(f"  {i}. {company.company_name} (ID: {company.company_id})")

                for company in unmapped_companies:
                    try:
                        logger.info(f"🔍 Processing: {company.company_name}")

                        # 기존 매핑이 있는지 확인
                        existing_mapping = db.query(CompanyDartMapping).filter(
                            CompanyDartMapping.company_id == company.company_id
                        ).first()

                        if existing_mapping:
                            logger.info(f"   📝 Found existing mapping (status: {existing_mapping.mapping_status.value})")
                        else:
                            logger.info(f"   ✨ No existing mapping, creating new one")

                        logger.info(f"   🤖 Calling GPT API for DART mapping...")
                        suggestion = await self.suggest_dart_mapping(company)

                        if suggestion:
                            corp_name = suggestion.get("dart_corp_name", "Unknown")
                            corp_code = suggestion.get("dart_corp_code", "N/A")
                            confidence = suggestion.get("confidence", 0)

                            logger.info(f"   ✅ GPT Success: {corp_name} (Code: {corp_code}, Confidence: {confidence}%)")

                            if existing_mapping:
                                # 기존 실패한 매핑 업데이트
                                logger.info(f"   🔄 Updating existing mapping (ID: {existing_mapping.mapping_id})")
                                existing_mapping.dart_corp_name = suggestion.get("dart_corp_name")
                                existing_mapping.dart_corp_code = suggestion.get("dart_corp_code")
                                existing_mapping.dart_stock_code = suggestion.get("dart_stock_code")
                                existing_mapping.mapping_status = MappingStatus.suggested
                                existing_mapping.confidence_score = suggestion.get("confidence", 0)
                                existing_mapping.gpt_response = str(suggestion)
                                existing_mapping.processed_at = datetime.utcnow()
                            else:
                                # 새 매핑 생성
                                logger.info(f"   ➕ Creating new mapping record")
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
                            logger.warning(f"   ❌ GPT Failed: No mapping found for {company.company_name}")

                            if existing_mapping:
                                # 기존 매핑을 다시 실패로 업데이트
                                logger.info(f"   🔄 Updating existing mapping to failed (ID: {existing_mapping.mapping_id})")
                                existing_mapping.mapping_status = MappingStatus.failed
                                existing_mapping.confidence_score = 0
                                existing_mapping.gpt_response = "No mapping found"
                                existing_mapping.processed_at = datetime.utcnow()
                            else:
                                # 새 실패 매핑 생성
                                logger.info(f"   ➕ Creating new failed mapping record")
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
                            logger.info(f"   💾 Intermediate commit: {stats['processed']} processed")
                            db.commit()

                        # API 요청 제한 고려
                        logger.info(f"   ⏳ Waiting 1 second before next company...")
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"   ⚠️ Error processing {company.company_name}: {e}")
                        stats["failed"] += 1
                        stats["processed"] += 1

                logger.info(f"💾 Final commit to database...")
                db.commit()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Critical error in batch process: {e}")
            raise Exception(f"Failed to batch process mappings: {e}")

        logger.info(f"🎉 Batch mapping completed!")
        logger.info(f"📊 Final Stats:")
        logger.info(f"   - Total Processed: {stats['processed']}")
        logger.info(f"   - Successfully Mapped: {stats['suggested']}")
        logger.info(f"   - Failed: {stats['failed']}")
        logger.info(f"   - Success Rate: {(stats['suggested']/stats['processed']*100):.1f}%" if stats['processed'] > 0 else "   - Success Rate: 0%")

        return stats