import logging
import os
import re
from datetime import datetime
from typing import Optional, Tuple
from OpenDartReader import OpenDartReader
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)

class DartDocumentExtractor:
    def __init__(self, api_key: Optional[str] = None):
        """
        DART 문서 추출기 초기화
        
        Args:
            api_key (str): DART Open API 키
        """
        self.api_key = api_key or os.getenv('DART_API_KEY')
        if not self.api_key:
            raise ValueError("DART API key is required")
        
        self.dart = OpenDartReader(self.api_key)
    
    def get_latest_report(self, company_name: str, report_type: str = 'A') -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        특정 기업의 최신 정기보고서 접수번호 찾기
        
        Args:
            company_name (str): 회사명 또는 종목코드
            report_type (str): 보고서 종류 ('A': 정기보고서)
        
        Returns:
            tuple: (접수번호, 보고서명, 제출일)
        """
        try:
            logger.info(f"Searching for latest report: {company_name}")
            
            # 최근 2년간 정기보고서 목록 조회
            reports = self.dart.list(company_name, kind=report_type, start='2022-01-01')
            
            if reports.empty:
                logger.warning(f"No reports found for {company_name}")
                return None, None, None
            
            # 가장 최근 보고서 선택
            latest_report = reports.iloc[0]
            
            rcp_no = latest_report['rcept_no']
            report_nm = latest_report['report_nm']
            rcept_dt = latest_report['rcept_dt']
            
            logger.info(f"Latest report found: {rcp_no} - {report_nm} ({rcept_dt})")
            
            return rcp_no, report_nm, rcept_dt
            
        except Exception as e:
            logger.error(f"Error searching reports: {e}")
            return None, None, None
    
    def extract_document_text(self, rcp_no: str) -> str:
        """
        접수번호로 공시문서 원문을 텍스트로 추출
        
        Args:
            rcp_no (str): 접수번호
        
        Returns:
            str: 추출된 텍스트
        """
        try:
            logger.info(f"Downloading document: {rcp_no}")
            
            # 공시서류 원본파일 XML 다운로드
            xml_text = self.dart.document(rcp_no)
            
            if not xml_text:
                logger.warning("Failed to download document")
                return ""
            
            logger.info("Parsing XML and extracting text...")
            
            # BeautifulSoup으로 XML 파싱
            soup = BeautifulSoup(xml_text, 'xml')
            
            # 텍스트 추출
            extracted_text = self._parse_xml_to_text(soup)
            
            logger.info(f"Text extraction completed: {len(extracted_text):,} characters")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting document: {e}")
            return ""
    
    def _parse_xml_to_text(self, soup: BeautifulSoup) -> str:
        """
        XML soup 객체에서 텍스트 추출
        """
        text_parts = []
        
        # 문서 제목 추출
        title = soup.find('DOCUMENT-NAME')
        if title:
            text_parts.append(f"=== {title.get_text().strip()} ===\n")
        
        # 회사명 추출
        company = soup.find('COMPANY-NAME')
        if company:
            text_parts.append(f"회사명: {company.get_text().strip()}\n")
        
        # SECTION들 추출
        sections = soup.find_all(['SECTION-1', 'SECTION-2', 'SECTION-3'])
        
        for section in sections:
            # 섹션 제목
            section_title = section.find('TITLE')
            if section_title:
                title_text = section_title.get_text().strip()
                text_parts.append(f"\n{'='*50}\n{title_text}\n{'='*50}\n")
            
            # 섹션 내용 추출
            section_text = self._extract_section_content(section)
            if section_text:
                text_parts.append(section_text)
        
        # 테이블들 추출
        tables = soup.find_all('TABLE')
        table_count = 0
        
        for table in tables:
            table_text = self._extract_table_text(table)
            if table_text:
                table_count += 1
                text_parts.append(f"\n[표 {table_count}]\n{table_text}\n")
        
        return '\n'.join(text_parts)
    
    def _extract_section_content(self, section) -> str:
        """
        섹션에서 텍스트 내용 추출
        """
        text_parts = []
        
        # P 태그들에서 텍스트 추출
        paragraphs = section.find_all('P')
        for p in paragraphs:
            p_text = p.get_text().strip()
            if p_text and p_text not in ['', '\n']:
                text_parts.append(p_text)
        
        # TABLE이 아닌 다른 텍스트 내용들도 추출
        for text in section.stripped_strings:
            if text and len(text.strip()) > 1:
                # 이미 추가된 내용은 제외
                if text.strip() not in ' '.join(text_parts):
                    text_parts.append(text.strip())
        
        return '\n'.join(text_parts) if text_parts else ""
    
    def _extract_table_text(self, table) -> str:
        """
        테이블을 텍스트 형식으로 변환
        """
        try:
            rows = table.find_all(['TR', 'tr'])
            if not rows:
                return ""
            
            table_data = []
            
            for row in rows:
                cells = row.find_all(['TD', 'TH', 'td', 'th', 'TU', 'TE'])
                if cells:
                    row_data = []
                    for cell in cells:
                        cell_text = cell.get_text().strip()
                        row_data.append(cell_text)
                    
                    if any(cell for cell in row_data if cell):  # 빈 행 제외
                        table_data.append(row_data)
            
            if not table_data:
                return ""
            
            # 테이블을 텍스트 형식으로 포맷
            formatted_table = []
            
            # 각 열의 최대 너비 계산
            max_widths = []
            for col_idx in range(max(len(row) for row in table_data) if table_data else 0):
                max_width = max(
                    len(str(row[col_idx]) if col_idx < len(row) else "")
                    for row in table_data
                )
                max_widths.append(min(max_width, 30))  # 최대 30자로 제한
            
            # 테이블 포맷팅
            for i, row in enumerate(table_data):
                formatted_cells = []
                for j, cell in enumerate(row):
                    width = max_widths[j] if j < len(max_widths) else 15
                    cell_str = str(cell)[:width]  # 너무 긴 텍스트 자르기
                    formatted_cells.append(cell_str.ljust(width))
                
                formatted_table.append(" | ".join(formatted_cells))
                
                # 헤더 구분선 (첫 번째 행 이후)
                if i == 0 and len(table_data) > 1:
                    separator = " | ".join("-" * width for width in max_widths)
                    formatted_table.append(separator)
            
            return '\n'.join(formatted_table)
            
        except Exception as e:
            logger.error(f"Error extracting table: {e}")
            return ""
    
    def extract_company_report_to_text(self, company_name: str) -> str:
        """
        특정 기업의 최근 정기보고서를 텍스트로 추출하는 메인 함수
        
        Args:
            company_name (str): 회사명 또는 종목코드
        
        Returns:
            str: 추출된 텍스트
        """
        logger.info(f"Starting report extraction for: {company_name}")
        
        # 1. 최신 보고서 찾기
        rcp_no, report_nm, rcept_dt = self.get_latest_report(company_name)
        
        if not rcp_no:
            return ""
        
        # 2. 문서 텍스트 추출
        extracted_text = self.extract_document_text(rcp_no)
        
        return extracted_text