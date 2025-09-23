import logging
import os
import re
import asyncio
import time
from typing import Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
import ollama
import json

logger = logging.getLogger(__name__)

class StandardizerService:
    def __init__(self, ollama_host: Optional[str] = None, model_name: Optional[str] = None):
        """
        표준화 서비스 초기화
        
        Args:
            ollama_host (str): Ollama 서버 호스트
            model_name (str): 사용할 모델명
        """
        self.ollama_host = ollama_host or os.getenv('OLLAMA_HOST', 'ollama:11434')
        self.model_name = model_name or os.getenv('STANDARDIZER_MODEL', 'qwen2.5:0.5b-instruct-fp16')
        self.client = None
        self.executor = None
        self.request_semaphore = None
        self.max_workers = int(os.getenv('MAX_WORKERS', '2'))
        
    async def initialize(self):
        """Ollama 클라이언트 초기화"""
        try:
            host = self.ollama_host if self.ollama_host.startswith('http') else f'http://{self.ollama_host}'
            self.client = ollama.Client(host=host)
            
            # 동시 처리 제한을 위한 설정
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            self.request_semaphore = asyncio.Semaphore(self.max_workers)
            
            # 연결 테스트
            models = self.client.list()
            logger.info(f"Connected to Ollama at {host}")
            logger.info(f"Available models: {[m['name'] for m in models['models']]}")
            logger.info(f"Using model: {self.model_name}")
            logger.info(f"Max concurrent workers: {self.max_workers}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    async def standardize_text(self, content: str) -> str:
        """
        텍스트 표준화 처리 (Python 코드로 처리, LLM 호출 제거)
        
        Args:
            content (str): 표준화할 텍스트
            
        Returns:
            str: 표준화된 텍스트
        """
        try:
            # _standardize_content 메서드 재사용
            return await self._standardize_content(content)
                
        except Exception as e:
            logger.error(f"Text standardization failed: {e}")
            raise
    
    def _call_ollama(self, prompt: str) -> str:
        """Ollama API 동기 호출 (executor에서 실행용)"""
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 2000  # Ollama에서는 max_tokens 대신 num_predict 사용
            }
        )
        return response['message']['content']
    
    # DART 원본 목차 -> 카테고리 매핑
    DART_SECTION_MAPPING = {
        # 사업 개요 관련
        "1. 사업의 개요": "business_overview",
        "사업의 개요": "business_overview",
        "사업개요": "business_overview",
        
        # 제품/서비스 관련
        "2. 주요 제품 및 서비스": "products_services",
        "주요 제품 및 서비스": "products_services",
        "주요제품 및 서비스": "products_services",
        "주요제품및서비스": "products_services",
        
        # 매출/수주 관련
        "3. 원재료 및 생산설비": "revenue_orders",
        "4. 매출 및 수주상황": "revenue_orders",
        "매출 및 수주상황": "revenue_orders",
        "매출및수주상황": "revenue_orders",
        "원재료 및 생산설비": "revenue_orders",
        "원재료및생산설비": "revenue_orders",
        
        # 계약/R&D 관련
        "6. 주요계약 및 연구개발활동": "contracts_rnd",
        "주요계약 및 연구개발활동": "contracts_rnd",
        "주요계약및연구개발활동": "contracts_rnd",
        
        # 기타 참고사항
        "5. 위험관리 및 파생거래": "other_references",
        "7. 기타 참고사항": "other_references",
        "기타 참고사항": "other_references",
        "기타참고사항": "other_references",
        "위험관리 및 파생거래": "other_references",
        "위험관리및파생거래": "other_references"
    }
    
    def classify_by_title_mapping(self, title: str) -> Optional[str]:
        """
        제목 기반 매핑으로 카테고리 분류
        
        Args:
            title (str): 챕터 제목
            
        Returns:
            str: 카테고리명 또는 None
        """
        # 제목 정규화 (공백, 숫자, 특수문자 제거)
        normalized_title = re.sub(r'[\s\d\-\.︎️　]+', '', title.strip())
        
        # 직접 매칭 시도
        if title in self.DART_SECTION_MAPPING:
            return self.DART_SECTION_MAPPING[title]
        
        if normalized_title in self.DART_SECTION_MAPPING:
            return self.DART_SECTION_MAPPING[normalized_title]
        
        # 키워드 기반 매칭
        if ("사업" in title and "개요" in title) or ("사업개요" in title):
            return "business_overview"
        elif ("제품" in title or "서비스" in title) and ("주요" in title):
            return "products_services"
        elif ("매출" in title or "수주" in title or "원재료" in title or "생산" in title):
            return "revenue_orders"
        elif ("계약" in title or "연구" in title or "개발" in title):
            return "contracts_rnd"
        elif ("기타" in title or "위험" in title or "파생" in title):
            return "other_references"
        
        return None
    
    def parse_dart_sections(self, content: str) -> Dict[str, str]:
        """
        DART 문서를 섹션별로 파싱하여 5개 카테고리로 분류

        Args:
            content (str): 전체 DART 문서 내용

        Returns:
            dict: {카테고리: 해당_섹션_내용}
        """
        sections_by_category = {
            'business_overview': [],
            'products_services': [],
            'revenue_orders': [],
            'contracts_rnd': [],
            'other_references': []
        }

        # 대제목 패턴: "1.", "2.", "3." 형태로 시작하는 제목들
        major_section_pattern = r'^[\s]*([0-9]+)\.\s+(.+)'

        # 섹션 제목과 카테고리 매핑 (실제 DART 구조에 맞춤)
        section_mapping = {
            # 사업의 개요 관련
            '사업의 개요': 'business_overview',
            '회사의 개요': 'business_overview',
            '개요': 'business_overview',

            # 주요 제품 및 서비스 관련
            '주요 제품': 'products_services',
            '주요제품': 'products_services',
            '제품': 'products_services',
            '서비스': 'products_services',
            '제품 및 서비스': 'products_services',
            '주요 제품 및 서비스': 'products_services',

            # 매출, 수주, 원재료, 생산 관련
            '매출': 'revenue_orders',
            '수주': 'revenue_orders',
            '수주상황': 'revenue_orders',
            '매출 및 수주': 'revenue_orders',
            '매출 및 수주상황': 'revenue_orders',
            '원재료': 'revenue_orders',
            '생산설비': 'revenue_orders',
            '원재료 및 생산설비': 'revenue_orders',
            '생산': 'revenue_orders',

            # 계약 및 연구개발 관련
            '주요계약': 'contracts_rnd',
            '계약': 'contracts_rnd',
            '연구개발': 'contracts_rnd',
            '연구개발활동': 'contracts_rnd',
            '주요계약 및 연구개발': 'contracts_rnd',
            '주요계약 및 연구개발활동': 'contracts_rnd',
            'R&D': 'contracts_rnd',

            # 기타 참고사항
            '기타': 'other_references',
            '참고사항': 'other_references',
            '기타 참고사항': 'other_references',
            '위험관리': 'other_references',
            '파생거래': 'other_references',
            '위험관리 및 파생거래': 'other_references'
        }

        lines = content.split('\n')
        current_section_title = None
        current_section_content = []
        current_category = None
        last_section_number = 0

        logger.info(f"DART 문서 파싱 시작: 총 {len(lines)}줄")

        # 문서 시작 부분 로깅 (디버깅용)
        first_20_lines = '\n'.join(lines[:20])
        logger.info(f"문서 미리보기 (처음 20줄):\n{first_20_lines}")

        total_sections_found = 0

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                if current_section_content:
                    current_section_content.append('')
                continue

            # 대제목 패턴 확인 (1. 사업의 개요, 2. 주요 제품 등)
            match = re.match(major_section_pattern, line_stripped)
            if match:
                section_number = int(match.group(1))
                section_title = match.group(2).strip()

                logger.info(f"{i+1}번째 줄: 섹션 패턴 발견: '{line_stripped}'")

                # 순차적 증가 확인
                # 첫 번째 1번만 허용하고, 그 이후는 반드시 순차 증가만 허용
                if (section_number == 1 and last_section_number == 0) or section_number == last_section_number + 1:
                    total_sections_found += 1

                    # 이전 섹션 저장
                    if current_section_title and current_section_content and current_category:
                        section_text = f"\n=== {current_section_title} ===\n\n" + '\n'.join(current_section_content)
                        sections_by_category[current_category].append(section_text)
                        logger.info(f"섹션 저장 완료: '{current_section_title}' -> '{current_category}' 카테고리에 {len(section_text)}자")

                    # 새 섹션 시작
                    current_section_title = f"{section_number}. {section_title}"
                    current_section_content = []
                    # 순차적으로 section_number 업데이트
                    last_section_number = section_number

                    # 카테고리 결정
                    current_category = None
                    matched_keyword = None
                    for keyword, category in section_mapping.items():
                        if keyword in section_title:
                            current_category = category
                            matched_keyword = keyword
                            break

                    if not current_category:
                        current_category = 'other_references'

                    logger.info(f"섹션 #{section_number}: '{section_title}' - 키워드 '{matched_keyword}' 매칭 -> '{current_category}' 카테고리")
                    continue
                else:
                    logger.warning(f"섹션 번호 {section_number}가 순차적이지 않음 (이전: {last_section_number}), 무시함")

            # 섹션 내용 추가
            if current_category:
                current_section_content.append(line_stripped)

        # 마지막 섹션 저장
        if current_section_title and current_section_content and current_category:
            section_text = f"\n=== {current_section_title} ===\n\n" + '\n'.join(current_section_content)
            sections_by_category[current_category].append(section_text)
            logger.info(f"마지막 섹션 저장 완료: '{current_section_title}' -> '{current_category}' 카테고리에 {len(section_text)}자")

        # 각 카테고리의 섹션들을 하나로 병합
        result = {}
        for category, sections in sections_by_category.items():
            if sections:
                result[category] = '\n\n'.join(sections)
                logger.info(f"카테고리 '{category}': {len(sections)}개 섹션, 총 {len(result[category])}자")
            else:
                result[category] = ""
                logger.info(f"카테고리 '{category}': 비어있음")

        # 아무 섹션도 분류되지 않았다면 전체를 other_references로
        if not any(result.values()):
            logger.warning(f"어떤 섹션도 분류되지 않음! 전체 내용을 other_references에 저장")
            result['other_references'] = content

        logger.info(f"DART 파싱 완료: {total_sections_found}개 섹션 발견, {sum(1 for v in result.values() if v)}개 카테고리에 내용 저장됨")

        return result

    async def classify_and_standardize_all_sections(self, company_name: str, content: str) -> Dict[str, str]:
        """
        DART 문서 전체를 5개 카테고리로 분류하고 각각 표준화

        Args:
            company_name (str): 회사명
            content (str): 전체 DART 문서 내용

        Returns:
            dict: {카테고리: 표준화된_내용}
        """
        try:
            # 1. DART 문서를 섹션별로 파싱 및 분류
            logger.info(f"{company_name} 회사의 DART 문서 파싱 시작")
            sections_by_category = self.parse_dart_sections(content)

            # 2. 각 카테고리별 내용 표준화
            result = {}
            for category, section_content in sections_by_category.items():
                if section_content:
                    logger.info(f"'{category}' 카테고리 표준화 시작: {len(section_content)}자")
                    # 표준화 수행
                    standardized = await self._standardize_content(section_content)
                    result[category] = standardized
                    logger.info(f"'{category}' 카테고리 표준화 완료: {len(standardized)}자")
                else:
                    result[category] = ""
                    logger.info(f"'{category}' 카테고리: 내용 없음")

            logger.info(f"{company_name} 회사 DART 문서 분류 및 표준화 완료")
            return result

        except Exception as e:
            logger.error(f"Failed to classify and standardize all sections: {e}")
            # 실패 시 전체를 other_references로
            return {
                'business_overview': "",
                'products_services': "",
                'revenue_orders': "",
                'contracts_rnd': "",
                'other_references': content
            }

    async def classify_and_standardize(self, title: str, content: str) -> Tuple[str, str]:
        """
        텍스트를 5개 카테고리로 분류하고 표준화 처리
        1단계: 제목 기반 매핑 시도
        2단계: 매핑 실패 시 LLM 분류

        Args:
            title (str): 챕터 제목
            content (str): 챕터 내용

        Returns:
            tuple: (카테고리명, 표준화된 텍스트)
        """
        try:
            # 1단계: 제목 기반 매핑 시도
            category = self.classify_by_title_mapping(title)

            if category:
                logger.info(f"Chapter '{title}' mapped directly to: {category}")
            else:
                # 2단계: LLM 분류 (매핑 실패 시만)
                logger.info(f"Chapter '{title}' not found in mapping, using LLM classification")
                category = await self._classify_with_llm(title, content)

            # 표준화 수행 (LLM 호출 없이 Python으로 처리)
            standardized_content = await self._standardize_content(content)

            # 챕터 제목을 포함한 최종 텍스트
            final_content = f"\n\n=== {title} ===\n\n{standardized_content}"

            return category, final_content

        except Exception as e:
            logger.error(f"Text classification and standardization failed: {e}")
            # 실패 시 기본값 반환
            return 'other_references', f"\n\n=== {title} ===\n\n{content}"
    
    async def _classify_with_llm(self, title: str, content: str) -> str:
        """
        LLM을 사용한 분류 (매핑에 없는 경우에만 사용, 동시성 제한 포함)
        """
        if not self.client:
            raise RuntimeError("Standardizer service not initialized")
        
        async with self.request_semaphore:
            try:
                # 분류 프롬프트
                prompt = f"""다음 공시 문서의 챕터를 분석하여 카테고리를 분류해주세요.

챕터 제목: {title}

챕터 내용:
{content[:1500]}

카테고리 분류 기준:
1. business_overview: 회사 개요, 사업 전반적인 설명, 회사 역사, 조직 구조
2. products_services: 제품/서비스 상세, 브랜드, 생산/판매 방식, 제품별 특징
3. revenue_orders: 매출 현황, 수주 실적, 판매 실적, 재무 성과 수치, 원재료, 생산설비
4. contracts_rnd: 주요 계약, 연구개발 활동, 특허, 기술 개발, 투자
5. other_references: 위험관리, 파생거래, 기타 참고사항

가장 적합한 카테고리 1개만 선택하여 단순히 답하세요:"""
                
                # CPU 부하를 줄이기 위해 비동기 처리
                loop = asyncio.get_event_loop()
                response_text = await loop.run_in_executor(
                    self.executor,
                    self._call_ollama,
                    prompt
                )
                
                # 짧은 대기로 CPU 부하 분산
                await asyncio.sleep(0.05)
                
                # 단순 텍스트 파싱
                response_text = response_text.strip().lower()
                
                # 유효한 카테고리 추출
                valid_categories = ['business_overview', 'products_services', 'revenue_orders', 'contracts_rnd', 'other_references']
                for category in valid_categories:
                    if category in response_text:
                        logger.info(f"LLM classified '{title}' as: {category}")
                        return category
                
                # 기본값
                logger.warning(f"LLM classification failed for '{title}', defaulting to other_references")
                return 'other_references'
                
            except Exception as e:
                logger.error(f"LLM classification failed: {e}")
                return 'other_references'
    
    async def _standardize_content(self, content: str) -> str:
        """
        텍스트 표준화 수행 (Python 코드로 처리, LLM 호출 제거)
        """
        try:
            # 1. 불필요한 공백 및 특수문자 정리
            standardized = re.sub(r'\s+', ' ', content)  # 연속된 공백을 하나로
            standardized = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', standardized)  # Zero-width 문자 제거
            standardized = re.sub(r'[　]', ' ', standardized)  # 전각 공백을 반각으로
            
            # 2. 테이블 구조 정리 (기본 형식 유지)
            # 테이블 구분자 표준화
            standardized = re.sub(r'[│┃┅]', '|', standardized)  # 세로선 통일
            standardized = re.sub(r'[─━┄]', '-', standardized)  # 가로선 통일
            
            # 3. 숫자와 단위 형식 표준화
            # 천 단위 구분자 통일 (1,000 형식)
            standardized = re.sub(r'(\d)\s+(\d{3})', r'\1,\2', standardized)
            
            # 퍼센트 표기 통일
            standardized = re.sub(r'(\d+)\s*[％%]', r'\1%', standardized)
            
            # 원화 표기 통일
            standardized = re.sub(r'(\d+)\s*원', r'\1원', standardized)
            standardized = re.sub(r'(\d+)\s*백만\s*원', r'\1백만원', standardized)
            standardized = re.sub(r'(\d+)\s*천\s*원', r'\1천원', standardized)
            standardized = re.sub(r'(\d+)\s*억\s*원', r'\1억원', standardized)
            
            # 4. 날짜 형식 표준화 (YYYY년 MM월 DD일)
            standardized = re.sub(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', r'\1년 \2월 \3일', standardized)
            standardized = re.sub(r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1년 \2월 \3일', standardized)
            
            # 5. 줄바꿈 정리
            lines = standardized.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            standardized = '\n'.join(cleaned_lines)
            
            # 6. 앞뒤 공백 제거
            standardized = standardized.strip()
            
            return standardized
            
        except Exception as e:
            logger.error(f"Text standardization failed: {e}")
            return content
    
    def get_status(self) -> dict:
        """서비스 상태 반환"""
        active_tasks = 0
        if self.request_semaphore:
            active_tasks = self.max_workers - self.request_semaphore._value if hasattr(self.request_semaphore, '_value') else 0
        
        return {
            "ollama_host": self.ollama_host,
            "model_name": self.model_name,
            "initialized": self.client is not None,
            "active_tasks": active_tasks,
            "max_workers": self.max_workers
        }
    
    async def shutdown(self):
        """서비스 종료 시 정리"""
        if self.executor:
            self.executor.shutdown(wait=True, timeout=5)
            logger.info("StandardizerService executor shutdown completed")