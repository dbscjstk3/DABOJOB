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