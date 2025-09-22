import logging
import os
import re
from datetime import datetime
from typing import Optional, Tuple
import OpenDartReader
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
    
    def extract_document_text(self, rcp_no: str, extract_business_only: bool = True) -> str:
        """
        접수번호로 공시문서 원문을 텍스트로 추출
        
        Args:
            rcp_no (str): 접수번호
            extract_business_only (bool): True면 'II. 사업의 내용' 섹션만 추출
        
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
            
            # BeautifulSoup으로 XML 파싱
            soup = BeautifulSoup(xml_text, 'xml')
            
            if extract_business_only:
                logger.info("Extracting 'II. 사업의 내용' section only...")
                extracted_text = self._extract_business_section(soup)
            else:
                logger.info("Parsing XML and extracting full text...")
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
    
    def _extract_business_section(self, soup: BeautifulSoup) -> str:
        """
        'II. 사업의 내용' 섹션만 추출 (III. 재무에 관한 사항 전까지)
        """
        import re
        
        try:
            # 전체 텍스트 가져오기
            full_text = soup.get_text()
            
            # II. 사업의 내용 시작 지점 찾기
            start_patterns = [
                r'II[\s\.]+사업의\s*내용',
                r'2[\s\.]+사업의\s*내용',
                r'제\s*2\s*부[\s\.]+사업의\s*내용'
            ]
            
            # III. 재무에 관한 사항 시작 지점 찾기 (종료 지점)
            # 실제 섹션 제목만 인식하도록 엄격한 패턴 사용
            end_patterns = [
                r'\n\s*III[\s\.]+재무에\s*관한\s*사항(?=\s*\n)',       # 줄바꿈으로 둘러싸인 경우
                r'\n\s*3[\s\.]+재무에\s*관한\s*사항(?=\s*\n)',         # 줄바꿈으로 둘러싸인 경우
                r'\n\s*제\s*3\s*부[\s\.]+재무에\s*관한\s*사항(?=\s*\n)' # 줄바꿈으로 둘러싸인 경우
            ]
            
            start_idx = -1
            end_idx = len(full_text)

            # 모든 "II. 사업의 내용" 패턴 찾기 (목차 vs 실제 내용 구분)
            all_matches = []
            for pattern in start_patterns:
                for match in re.finditer(pattern, full_text, re.IGNORECASE):
                    all_matches.append((match.start(), match.group()))

            if not all_matches:
                logger.warning("Could not find 'II. 사업의 내용' section")
                return ""

            logger.info(f"Found {len(all_matches)} business section patterns")

            # 각 매치에서 내용 길이 확인하여 가장 적합한 것 선택
            best_match = None
            best_content_length = 0

            for i, (pos, text) in enumerate(all_matches):
                # 해당 위치에서 다음 major section까지의 내용 길이 확인
                temp_end_idx = len(full_text)
                search_text = full_text[pos:]

                for pattern in end_patterns:
                    match = re.search(pattern, search_text, re.IGNORECASE)
                    if match:
                        temp_end_idx = pos + match.start()
                        break

                content_length = temp_end_idx - pos
                logger.info(f"Match {i+1} at position {pos}: content length {content_length}")

                # 내용이 100자 이상이고 가장 긴 것을 선택 (목차는 보통 매우 짧음)
                if content_length > 100 and content_length > best_content_length:
                    best_match = pos
                    best_content_length = content_length

            if best_match is None:
                # fallback: 첫 번째 매치 사용
                start_idx = all_matches[0][0]
                logger.warning("No substantial content found, using first match")
            else:
                start_idx = best_match
                logger.info(f"Selected business section at position {start_idx} with {best_content_length} characters")
            
            # 종료 지점 찾기 (시작 지점 이후에서 검색)
            search_text = full_text[start_idx:]
            for pattern in end_patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    end_idx = start_idx + match.start()
                    logger.info(f"Found end of business section at position {end_idx}")
                    break
            
            # 섹션 추출
            business_section = full_text[start_idx:end_idx]
            
            # 텍스트 정리 - 줄바꿈은 보존하고 과도한 공백만 제거
            business_section = re.sub(r'[ \t]+', ' ', business_section)  # 스페이스와 탭만 정리
            business_section = re.sub(r'\n{3,}', '\n\n', business_section)  # 과도한 줄바꿈만 정리
            business_section = business_section.strip()
            
            return business_section
            
        except Exception as e:
            logger.error(f"Error extracting business section: {e}")
            return ""
    
    def extract_business_subsections(self, soup: BeautifulSoup) -> dict:
        """
        'II. 사업의 내용' 섹션을 소제목별로 구조화하여 추출
        
        Returns:
            dict: 소제목을 키로 하고 내용을 값으로 하는 딕셔너리
        """
        import re
        
        try:
            # 전체 텍스트 가져오기
            full_text = soup.get_text()
            
            # II. 사업의 내용 시작 지점 찾기
            start_patterns = [
                r'II[\s\.]+사업의\s*내용',
                r'2[\s\.]+사업의\s*내용',
                r'제\s*2\s*부[\s\.]+사업의\s*내용'
            ]
            
            # III. 재무에 관한 사항 시작 지점 찾기 (종료 지점)
            # 실제 섹션 제목만 인식하도록 엄격한 패턴 사용
            end_patterns = [
                r'\n\s*III[\s\.]+재무에\s*관한\s*사항(?=\s*\n)',       # 줄바꿈으로 둘러싸인 경우
                r'\n\s*3[\s\.]+재무에\s*관한\s*사항(?=\s*\n)',         # 줄바꿈으로 둘러싸인 경우
                r'\n\s*제\s*3\s*부[\s\.]+재무에\s*관한\s*사항(?=\s*\n)' # 줄바꿈으로 둘러싸인 경우
            ]
            
            start_idx = -1
            end_idx = len(full_text)
            
            # 시작 지점 찾기 - "II. 사업의 내용" 이후 "1. 사업의 개요" 찾기
            for pattern in start_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    section_end = match.end()
                    # "II. 사업의 내용" 이후에서 "1. 사업의 개요" 찾기
                    remaining_text = full_text[section_end:]
                    content_match = re.search(r'1\.\s*사업의\s*개요', remaining_text, re.IGNORECASE)
                    
                    if content_match:
                        start_idx = section_end + content_match.start()
                        logger.info(f"Found '1. 사업의 개요' at position {start_idx}")
                    else:
                        # "1. 사업의 개요"를 못 찾으면 원래 위치 사용
                        start_idx = match.start()
                        logger.warning("Could not find '1. 사업의 개요', using section title position")
                    break
            
            if start_idx == -1:
                logger.warning("Could not find 'II. 사업의 내용' section")
                return {}
            
            # 종료 지점 찾기 - "III. 재무에 관한 사항" 시작점 찾기
            search_text = full_text[start_idx:]
            for pattern in end_patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    # "III. 재무에 관한 사항" 시작점에서 끝내기
                    end_idx = start_idx + match.start()
                    logger.info(f"Found 'III. 재무에 관한 사항' at position {end_idx}")
                    break
            
            # 사업 섹션 텍스트 추출
            business_text = full_text[start_idx:end_idx]
            logger.info(f"Business section extracted: {len(business_text):,} characters")
            
            # 대제목 패턴: "1.", "2.", "3." 형태로 시작하는 제목들
            major_section_pattern = r'^[\s]*([0-9]+\.\s+[가-힣].+)$'
            
            subsections = {}
            lines = business_text.split('\n')
            current_title = None
            current_content = []
            
            logger.info(f"Processing {len(lines):,} lines for subsection extraction")
            
            last_section_number = 0
            
            for i, line in enumerate(lines):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 대제목 패턴 확인 (1. 사업의 개요, 2. 주요 제품 및 서비스 등)
                    match = re.match(major_section_pattern, line)
                    if match:
                        title_candidate = match.group(1).strip()
                        
                        # 섹션 번호 추출
                        section_number_match = re.match(r'^(\d+)\.', title_candidate)
                        if section_number_match:
                            section_number = int(section_number_match.group(1))
                            
                            # 순차적 증가 확인: 이전 번호보다 1 증가하거나 첫 번째 섹션(1번)
                            if section_number == 1 or section_number == last_section_number + 1:
                                # 이전 소제목의 내용 저장
                                if current_title and current_content:
                                    subsections[current_title] = '\n'.join(current_content).strip()
                                
                                # 새 소제목 설정
                                current_title = title_candidate
                                current_content = []
                                last_section_number = section_number
                                logger.info(f"Found major section #{len(subsections)+1}: {title_candidate}")
                                continue
                            else:
                                # 순차적이지 않은 번호는 무시 (법조항 등)
                                logger.debug(f"Skipping non-sequential section: {title_candidate} (expected: {last_section_number + 1}, got: {section_number})")
                        else:
                            # 번호를 추출할 수 없는 경우도 무시
                            logger.debug(f"Skipping section without clear number: {title_candidate}")
                    
                    # 소제목이 아니면 내용으로 추가
                    if current_title:
                        current_content.append(line)
                    else:
                        # 첫 번째 소제목 이전의 내용은 "개요"로 분류
                        if "개요" not in subsections:
                            subsections["개요"] = ""
                        subsections["개요"] += line + "\n"
                        
                except Exception as e:
                    logger.error(f"Error processing line {i+1}: {e}")
                    logger.error(f"Problematic line: {line[:100]}")
                    continue
            
            # 마지막 소제목 내용 저장
            if current_title and current_content:
                subsections[current_title] = '\n'.join(current_content).strip()
            
            # 텍스트 정리
            for key in subsections:
                content = subsections[key]
                content = re.sub(r'\s+', ' ', content)  # 과도한 공백 제거
                subsections[key] = content.strip()
            
            # 추가로 놓친 섹션이 있는지 확인
            remaining_lines = business_text.split('\n')[len([l for l in business_text.split('\n') if l.strip()]):] 
            
            # 처리하지 못한 대제목이 있는지 검사
            unprocessed_sections = []
            for line in business_text.split('\n'):
                line = line.strip()
                if re.match(major_section_pattern, line):
                    section_title = re.match(major_section_pattern, line).group(1).strip()
                    if section_title not in subsections:
                        unprocessed_sections.append(section_title)
            
            if unprocessed_sections:
                logger.warning(f"Found {len(unprocessed_sections)} unprocessed sections:")
                for section in unprocessed_sections:
                    logger.warning(f"  - {section}")
            
            # 각 섹션별 글자 수 로그 출력
            section_info = []
            total_chars = 0
            for key, content in subsections.items():
                char_count = len(content)
                total_chars += char_count
                section_info.append(f"{key}: {char_count:,}자")
            
            logger.info(f"Extracted {len(subsections)} subsections (총 {total_chars:,}자):")
            for info in section_info:
                logger.info(f"  - {info}")
            
            return subsections
            
        except Exception as e:
            logger.error(f"Error extracting business subsections: {e}")
            return {}
    
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