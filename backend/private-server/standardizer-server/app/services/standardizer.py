import logging
import os
import re
from typing import Optional, Dict, Tuple
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
        
    async def initialize(self):
        """Ollama 클라이언트 초기화"""
        try:
            host = self.ollama_host if self.ollama_host.startswith('http') else f'http://{self.ollama_host}'
            self.client = ollama.Client(host=host)
            
            # 연결 테스트
            models = self.client.list()
            logger.info(f"Connected to Ollama at {host}")
            logger.info(f"Available models: {[m['name'] for m in models['models']]}")
            logger.info(f"Using model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    async def standardize_text(self, content: str) -> str:
        """
        텍스트 표준화 처리
        
        Args:
            content (str): 표준화할 텍스트
            
        Returns:
            str: 표준화된 텍스트
        """
        if not self.client:
            raise RuntimeError("Standardizer service not initialized")
        
        try:
            # 표준화 프롬프트
            prompt = f"""다음 텍스트를 표준화해주세요:

원본 텍스트:
{content}

표준화 요구사항:
1. 불필요한 공백 정리
2. 특수문자 정규화
3. 일관된 표기법 사용

표준화된 텍스트만 출력:"""
            
            # Ollama API 호출
            response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Text standardization failed: {e}")
            raise
    
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
            
            # 표준화 수행
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
        LLM을 사용한 분류 (매핑에 없는 경우에만 사용)
        """
        if not self.client:
            raise RuntimeError("Standardizer service not initialized")
        
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
            
            # 분류 수행
            classification_response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            # 단순 텍스트 파싱
            response_text = classification_response['message']['content'].strip().lower()
            
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
        텍스트 표준화 수행
        """
        if not self.client:
            return content
        
        try:
            standardized_prompt = f"""다음 텍스트를 표준화해주세요:

원본 텍스트:
{content}

표준화 요구사항:
1. 불필요한 공백 및 특수문자 정리
2. 테이블은 구조를 유지하면서 정리
3. 숫자와 단위는 일관된 형식으로 표기
4. 중요 정보(금액, 비율, 날짜)는 명확히 표시

표준화된 텍스트:"""
            
            standardization_response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": standardized_prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            return standardization_response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Text standardization failed: {e}")
            return content
    
    def get_status(self) -> dict:
        """서비스 상태 반환"""
        return {
            "ollama_host": self.ollama_host,
            "model_name": self.model_name,
            "initialized": self.client is not None
        }