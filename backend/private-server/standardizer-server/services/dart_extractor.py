"""
DART 문서 추출 서비스
"""
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.base import BaseService
from utils.exceptions import StandardizerException
from config import settings


class DartExtractorService(BaseService):
    """DART 문서 추출 서비스"""

    def __init__(self):
        super().__init__("DartExtractorService")
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key: Optional[str] = None

    async def _setup(self) -> None:
        """HTTP 세션 및 API 키 초기화"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            self.api_key = settings.DART_API_KEY

            if not self.api_key:
                self.logger.warning("DART API key not configured")
            else:
                self.logger.info("DART extractor service initialized")

        except Exception as e:
            raise StandardizerException(f"Failed to initialize DART extractor: {e}")

    async def _cleanup(self) -> None:
        """세션 정리"""
        if self.session:
            await self.session.close()

    async def search_company_reports(
        self,
        corp_code: str,
        report_type: str = "A001",  # 사업보고서
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """기업의 공시 목록 조회"""
        if not self.api_key or not self.session:
            raise StandardizerException("DART API not available")

        try:
            # 기본 날짜 설정 (최근 1년)
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            url = "https://opendart.fss.or.kr/api/list.json"
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bgn_de": start_date,
                "end_de": end_date,
                "pblntf_ty": "A",  # 정기공시
                "pblntf_detail_ty": report_type,
                "page_no": 1,
                "page_count": 10
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()

                if data.get("status") != "000":
                    self.logger.error(f"DART API error: {data.get('message')}")
                    return []

                return data.get("list", [])

        except Exception as e:
            self.logger.error(f"Failed to search reports for {corp_code}: {e}")
            raise StandardizerException(f"Failed to search reports: {e}")

    async def extract_document_content(
        self,
        receipt_no: str,
        section_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """DART 문서 내용 추출"""
        if not self.api_key or not self.session:
            raise StandardizerException("DART API not available")

        try:
            url = "https://opendart.fss.or.kr/api/document.xml"
            params = {
                "crtfc_key": self.api_key,
                "rcept_no": receipt_no
            }

            async with self.session.get(url, params=params) as response:
                content = await response.text()

                # XML 파싱 및 텍스트 추출
                extracted_content = self._parse_dart_xml(content)

                return {
                    "receipt_no": receipt_no,
                    "content": extracted_content,
                    "extracted_at": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Failed to extract document {receipt_no}: {e}")
            raise StandardizerException(f"Failed to extract document: {e}")

    def _parse_dart_xml(self, xml_content: str) -> Dict[str, str]:
        """DART XML 내용 파싱"""
        try:
            try:
                from bs4 import BeautifulSoup
                import re

                soup = BeautifulSoup(xml_content, 'xml')
                sections = {}

                # 섹션별로 텍스트 추출
                for section in soup.find_all(['section', 'p', 'div']):
                    section_title = section.get('title', 'unknown')
                    if section_title == 'unknown':
                        # 제목 추출 시도
                        title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        if title_elem:
                            section_title = title_elem.get_text(strip=True)

                    # 텍스트 내용 추출 및 정리
                    text_content = section.get_text(separator=' ', strip=True)
                    text_content = re.sub(r'\s+', ' ', text_content)  # 공백 정리

                    if text_content and len(text_content) > 50:  # 충분한 내용이 있는 경우만
                        sections[section_title] = text_content

                return sections

            except ImportError:
                self.logger.warning("BeautifulSoup4 not available, using simple XML parsing")
                import re
                # 간단한 텍스트 추출
                text_content = re.sub(r'<[^>]+>', ' ', xml_content)
                text_content = re.sub(r'\s+', ' ', text_content)
                return {"content": text_content.strip()}

        except Exception as e:
            self.logger.error(f"Failed to parse DART XML: {e}")
            return {"raw_content": xml_content}

    async def extract_company_annual_report(
        self,
        corp_code: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """기업의 사업보고서 추출"""
        try:
            if not year:
                year = datetime.now().year - 1  # 작년 기준

            # 사업보고서 검색
            start_date = f"{year}0101"
            end_date = f"{year}1231"

            reports = await self.search_company_reports(
                corp_code=corp_code,
                report_type="A001",  # 사업보고서
                start_date=start_date,
                end_date=end_date
            )

            if not reports:
                return {
                    "corp_code": corp_code,
                    "year": year,
                    "status": "no_reports_found",
                    "content": {}
                }

            # 가장 최근 보고서 선택
            latest_report = reports[0]
            receipt_no = latest_report["rcept_no"]

            # 문서 내용 추출
            content = await self.extract_document_content(receipt_no)

            return {
                "corp_code": corp_code,
                "year": year,
                "receipt_no": receipt_no,
                "report_info": latest_report,
                "status": "extracted",
                "content": content
            }

        except Exception as e:
            self.logger.error(f"Failed to extract annual report for {corp_code}: {e}")
            return {
                "corp_code": corp_code,
                "year": year,
                "status": "failed",
                "error": str(e),
                "content": {}
            }

    async def extract_financial_statements(
        self,
        corp_code: str,
        business_year: str,
        report_code: str = "11011"  # 사업보고서
    ) -> Dict[str, Any]:
        """재무제표 추출"""
        if not self.api_key or not self.session:
            raise StandardizerException("DART API not available")

        try:
            url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": business_year,
                "reprt_code": report_code
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()

                if data.get("status") != "000":
                    self.logger.error(f"Financial statements API error: {data.get('message')}")
                    return {}

                return {
                    "corp_code": corp_code,
                    "business_year": business_year,
                    "financial_data": data.get("list", [])
                }

        except Exception as e:
            self.logger.error(f"Failed to extract financial statements for {corp_code}: {e}")
            raise StandardizerException(f"Failed to extract financial statements: {e}")

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        base_status = super().get_status()
        base_status.update({
            "api_key_configured": bool(self.api_key),
            "session_active": self.session is not None and not self.session.closed
        })
        return base_status