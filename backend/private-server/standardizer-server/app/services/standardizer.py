import logging
import os
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
    
    async def classify_and_standardize(self, title: str, content: str) -> Tuple[str, str]:
        """
        텍스트를 5개 카테고리로 분류하고 표준화 처리
        
        Args:
            title (str): 챕터 제목
            content (str): 챕터 내용
            
        Returns:
            tuple: (카테고리명, 표준화된 텍스트)
        """
        if not self.client:
            raise RuntimeError("Standardizer service not initialized")
        
        try:
            # 분류 및 표준화 프롬프트
            prompt = f"""다음 공시 문서의 챕터를 분석하여 카테고리를 분류하고 내용을 표준화해주세요.

챕터 제목: {title}

챕터 내용:
{content[:2000]}  # 분류를 위해 앞부분만 사용

카테고리 분류 기준:
1. business_overview: 회사 개요, 사업 전반적인 설명, 회사 역사, 조직 구조
2. products_services: 제품/서비스 상세, 브랜드, 생산/판매 방식, 제품별 특징
3. revenue_orders: 매출 현황, 수주 실적, 판매 실적, 재무 성과 수치
4. contracts_rnd: 주요 계약, 연구개발 활동, 특허, 기술 개발, 투자
5. other_references: 위 카테고리에 해당하지 않는 기타 정보

응답 형식 (JSON):
{{
    "category": "카테고리명 (위 5개 중 하나)",
    "reason": "분류 이유 (한 문장)"
}}

응답:"""
            
            # 분류 수행
            classification_response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            # JSON 파싱
            try:
                classification_text = classification_response['message']['content'].strip()
                # JSON 블록 추출 (```json ... ``` 형식 처리)
                if '```json' in classification_text:
                    classification_text = classification_text.split('```json')[1].split('```')[0]
                elif '```' in classification_text:
                    classification_text = classification_text.split('```')[1].split('```')[0]
                
                classification = json.loads(classification_text)
                category = classification.get('category', 'other_references')
                
                # 유효한 카테고리인지 확인
                valid_categories = ['business_overview', 'products_services', 'revenue_orders', 'contracts_rnd', 'other_references']
                if category not in valid_categories:
                    category = 'other_references'
                    
                logger.info(f"Chapter '{title}' classified as: {category} - {classification.get('reason', '')}")
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse classification, defaulting to other_references: {e}")
                category = 'other_references'
            
            # 표준화 수행
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
            
            standardized_content = standardization_response['message']['content'].strip()
            
            # 챕터 제목을 포함한 최종 텍스트
            final_content = f"\n\n=== {title} ===\n\n{standardized_content}"
            
            return category, final_content
            
        except Exception as e:
            logger.error(f"Text classification and standardization failed: {e}")
            # 실패 시 기본값 반환
            return 'other_references', f"\n\n=== {title} ===\n\n{content}"
    
    def get_status(self) -> dict:
        """서비스 상태 반환"""
        return {
            "ollama_host": self.ollama_host,
            "model_name": self.model_name,
            "initialized": self.client is not None
        }