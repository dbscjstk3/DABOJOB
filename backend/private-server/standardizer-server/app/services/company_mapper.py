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


class CompanyMappingResult:
    """매핑 결과 데이터 클래스"""

    def __init__(self,
                 dart_corp_code: Optional[str] = None,
                 dart_corp_name: Optional[str] = None,
                 dart_stock_code: Optional[str] = None,
                 confidence_score: int = 0,
                 reasoning: str = "",
                 success: bool = False):
        self.dart_corp_code = dart_corp_code
        self.dart_corp_name = dart_corp_name
        self.dart_stock_code = dart_stock_code
        self.confidence_score = confidence_score
        self.reasoning = reasoning
        self.success = success


class GPTCompanyMapper:
    """GPT API를 활용한 회사명 매핑 서비스"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('GPT_MODEL', 'gpt-4')
        self.timeout = int(os.getenv('GPT_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('GPT_MAX_RETRIES', '3'))

        if not self.api_key:
            logger.warning("OpenAI API key not found. GPT mapping will be disabled.")

    async def map_company_to_dart(self,
                                  company_name: str,
                                  company_url: Optional[str] = None,
                                  additional_info: Optional[str] = None) -> CompanyMappingResult:
        """
        회사명과 URL을 DART 기업명과 매핑

        Args:
            company_name: 크롤링된 회사명
            company_url: 회사 URL (선택사항)
            additional_info: 추가 정보 (선택사항)

        Returns:
            CompanyMappingResult: 매핑 결과
        """
        if not self.api_key:
            return CompanyMappingResult(
                success=False,
                reasoning="OpenAI API key not configured"
            )

        try:
            prompt = self._create_mapping_prompt(company_name, company_url, additional_info)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": self._get_system_prompt()
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.1
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return self._parse_gpt_response(result)
                else:
                    logger.error(f"GPT API error: {response.status_code} - {response.text}")
                    return CompanyMappingResult(
                        success=False,
                        reasoning=f"API error: {response.status_code}"
                    )

        except Exception as e:
            logger.error(f"GPT mapping error: {e}")
            return CompanyMappingResult(
                success=False,
                reasoning=f"Exception: {str(e)}"
            )

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 반환"""
        return """
당신은 한국 기업명 매핑 전문가입니다. 채용 사이트의 회사명을 DART(전자공시시스템)의 정식 기업명과 매핑하는 역할을 합니다.

규칙:
1. 채용 사이트 회사명을 분석하여 DART에 등록된 정식 기업명을 찾아주세요
2. 상장기업이 아닌 경우 "NOT_LISTED"로 표시
3. 매핑 신뢰도를 0-100 점수로 제공
4. 응답은 반드시 JSON 형식으로 제공

응답 형식:
{
    "dart_corp_code": "기업코드 8자리 또는 null",
    "dart_corp_name": "DART 정식 기업명 또는 null",
    "dart_stock_code": "주식코드 6자리 또는 null",
    "confidence_score": 0-100,
    "reasoning": "매핑 근거 설명",
    "is_listed": true/false
}
"""

    def _create_mapping_prompt(self,
                              company_name: str,
                              company_url: Optional[str] = None,
                              additional_info: Optional[str] = None) -> str:
        """매핑을 위한 프롬프트 생성"""
        prompt = f"채용 사이트 회사명: {company_name}\n"

        if company_url:
            prompt += f"회사 URL: {company_url}\n"

        if additional_info:
            prompt += f"추가 정보: {additional_info}\n"

        prompt += "\n이 회사를 DART 정식 기업명과 매핑해주세요."

        return prompt

    def _parse_gpt_response(self, gpt_result: Dict[str, Any]) -> CompanyMappingResult:
        """GPT 응답 파싱"""
        try:
            content = gpt_result['choices'][0]['message']['content'].strip()

            # JSON 파싱 시도
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()

            data = json.loads(content)

            return CompanyMappingResult(
                dart_corp_code=data.get('dart_corp_code'),
                dart_corp_name=data.get('dart_corp_name'),
                dart_stock_code=data.get('dart_stock_code'),
                confidence_score=int(data.get('confidence_score', 0)),
                reasoning=data.get('reasoning', ''),
                success=True
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"GPT response parsing error: {e}")
            return CompanyMappingResult(
                success=False,
                reasoning=f"Response parsing error: {str(e)}"
            )


class CompanyMappingService:
    """회사 매핑 관리 서비스"""

    def __init__(self):
        self.gpt_mapper = GPTCompanyMapper()

    def get_unmapped_companies(self, db: Session, limit: int = 50) -> List[Company]:
        """매핑되지 않은 회사 목록 조회"""
        return db.query(Company)\
            .outerjoin(CompanyDartMapping)\
            .filter(CompanyDartMapping.mapping_id.is_(None))\
            .limit(limit)\
            .all()

    def get_pending_mappings(self, db: Session, limit: int = 50) -> List[CompanyDartMapping]:
        """검증 대기 중인 매핑 목록"""
        return db.query(CompanyDartMapping)\
            .filter(CompanyDartMapping.mapping_status == MappingStatus.suggested)\
            .order_by(CompanyDartMapping.confidence_score.desc())\
            .limit(limit)\
            .all()

    async def process_company_mapping(self, db: Session, company: Company) -> bool:
        """개별 회사 매핑 처리"""
        try:
            # 이미 매핑이 존재하는지 확인
            existing = db.query(CompanyDartMapping)\
                .filter(CompanyDartMapping.company_id == company.company_id)\
                .first()

            if existing and existing.mapping_status in [MappingStatus.verified, MappingStatus.processing]:
                logger.info(f"Company {company.company_name} already processed")
                return True

            # 새 매핑 레코드 생성 또는 업데이트
            if not existing:
                mapping = CompanyDartMapping(
                    company_id=company.company_id,
                    crawled_company_name=company.company_name,
                    crawled_company_url=company.company_url,
                    mapping_status=MappingStatus.processing
                )
                db.add(mapping)
            else:
                mapping = existing
                mapping.mapping_status = MappingStatus.processing
                mapping.updated_at = datetime.utcnow()

            db.commit()

            # GPT API 호출
            result = await self.gpt_mapper.map_company_to_dart(
                company_name=company.company_name,
                company_url=company.company_url
            )

            # 결과 저장
            if result.success:
                mapping.dart_corp_code = result.dart_corp_code
                mapping.dart_corp_name = result.dart_corp_name
                mapping.dart_stock_code = result.dart_stock_code
                mapping.confidence_score = result.confidence_score
                mapping.gpt_response = result.reasoning
                mapping.mapping_status = MappingStatus.suggested
                mapping.processed_at = datetime.utcnow()
            else:
                mapping.mapping_status = MappingStatus.failed
                mapping.gpt_response = result.reasoning
                mapping.processed_at = datetime.utcnow()

            db.commit()
            logger.info(f"Processed mapping for {company.company_name}")
            return True

        except Exception as e:
            logger.error(f"Error processing company mapping: {e}")
            db.rollback()
            return False

    async def batch_process_mappings(self, limit: int = 10) -> Dict[str, int]:
        """배치로 매핑 처리"""
        db = SessionLocal()
        stats = {"processed": 0, "success": 0, "failed": 0}

        try:
            unmapped_companies = self.get_unmapped_companies(db, limit)

            for company in unmapped_companies:
                stats["processed"] += 1
                success = await self.process_company_mapping(db, company)

                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

                # API 호출 제한을 위한 지연
                await asyncio.sleep(1)

            return stats

        finally:
            db.close()

    def verify_mapping(self,
                      db: Session,
                      mapping_id: int,
                      verified_by: str,
                      is_correct: bool,
                      notes: Optional[str] = None) -> bool:
        """수동 매핑 검증"""
        try:
            mapping = db.query(CompanyDartMapping)\
                .filter(CompanyDartMapping.mapping_id == mapping_id)\
                .first()

            if not mapping:
                return False

            if is_correct:
                mapping.mapping_status = MappingStatus.verified
            else:
                mapping.mapping_status = MappingStatus.rejected

            mapping.verified_at = datetime.utcnow()
            mapping.verified_by = verified_by
            mapping.manual_notes = notes

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error verifying mapping: {e}")
            db.rollback()
            return False

    def get_mapping_stats(self, db: Session) -> Dict[str, int]:
        """매핑 통계 조회"""
        total_companies = db.query(Company).count()

        stats = {"total_companies": total_companies}

        for status in MappingStatus:
            count = db.query(CompanyDartMapping)\
                .filter(CompanyDartMapping.mapping_status == status)\
                .count()
            stats[status.value] = count

        stats["unmapped"] = total_companies - db.query(CompanyDartMapping).count()

        return stats