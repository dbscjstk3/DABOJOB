"""
텍스트 처리 서비스
DART 텍스트 표준화 및 분류
"""
import re
import asyncio
import ollama
from typing import Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from config import settings
from services.base import BaseService
from utils.exceptions import LLMError


class TextProcessor(BaseService):
    """텍스트 표준화 및 분류 서비스"""

    def __init__(self):
        super().__init__("TextProcessor")
        self.ollama_client: Optional[ollama.Client] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        self.semaphore: Optional[asyncio.Semaphore] = None

    async def _setup(self) -> None:
        """Ollama 클라이언트 초기화"""
        try:
            # Ollama 클라이언트 설정
            host = settings.OLLAMA_HOST
            if not host.startswith('http'):
                host = f'http://{host}'

            self.ollama_client = ollama.Client(host=host)
            self.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
            self.semaphore = asyncio.Semaphore(settings.MAX_WORKERS)

            # 연결 테스트 (선택적)
            try:
                models = self.ollama_client.list()
                self.logger.info(f"Connected to Ollama at {host}")
                self.logger.info(f"Available models: {[m['name'] for m in models['models']]}")
            except Exception as conn_e:
                self.logger.warning(f"Ollama connection failed: {conn_e}")
                self.ollama_client = None

        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None

    async def _cleanup(self) -> None:
        """리소스 정리"""
        if self.executor:
            self.executor.shutdown(wait=True, timeout=5)

    async def standardize_text(self, content: str) -> str:
        """
        텍스트 표준화 처리

        Args:
            content: 표준화할 텍스트

        Returns:
            표준화된 텍스트
        """
        try:
            return self._standardize_content(content)
        except Exception as e:
            self.logger.error(f"Text standardization failed: {e}")
            raise LLMError(f"Text standardization failed: {e}")

    def _standardize_content(self, content: str) -> str:
        """
        실제 텍스트 표준화 로직
        """
        try:
            # 1. 불필요한 공백 및 특수문자 정리
            standardized = re.sub(r'\s+', ' ', content)
            standardized = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', standardized)
            standardized = re.sub(r'[　]', ' ', standardized)

            # 2. 테이블 구조 정리
            standardized = re.sub(r'[│┃┅]', '|', standardized)
            standardized = re.sub(r'[─━┄]', '-', standardized)

            # 3. 숫자와 단위 형식 표준화
            standardized = re.sub(r'(\d)\s+(\d{3})', r'\1,\2', standardized)
            standardized = re.sub(r'(\d+)\s*[％%]', r'\1%', standardized)
            standardized = re.sub(r'(\d+)\s*원', r'\1원', standardized)

            # 4. 날짜 형식 표준화
            standardized = re.sub(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', r'\1년 \2월 \3일', standardized)
            standardized = re.sub(r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1년 \2월 \3일', standardized)

            # 5. 줄바꿈 정리
            lines = standardized.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            standardized = '\n'.join(cleaned_lines)

            return standardized.strip()

        except Exception as e:
            self.logger.error(f"Content standardization failed: {e}")
            return content

    async def classify_and_standardize(self, title: str, content: str) -> Tuple[str, str]:
        """
        텍스트 분류 및 표준화

        Args:
            title: 챕터 제목
            content: 챕터 내용

        Returns:
            (카테고리명, 표준화된 텍스트)
        """
        try:
            # 1. 제목 기반 매핑 시도
            category = self._classify_by_title(title)

            if not category:
                # 2. LLM 분류 (매핑 실패 시)
                category = await self._classify_with_llm(title, content)

            # 3. 표준화 수행
            standardized_content = self._standardize_content(content)

            # 4. 최종 텍스트 구성
            final_content = f"\n\n=== {title} ===\n\n{standardized_content}"

            return category, final_content

        except Exception as e:
            self.logger.error(f"Classification and standardization failed: {e}")
            return 'other_references', f"\n\n=== {title} ===\n\n{content}"

    def _classify_by_title(self, title: str) -> Optional[str]:
        """
        제목 기반 카테고리 분류
        """
        # DART 섹션 매핑
        section_mapping = {
            "사업의 개요": "business_overview",
            "사업개요": "business_overview",
            "주요 제품 및 서비스": "products_services",
            "주요제품 및 서비스": "products_services",
            "매출 및 수주상황": "revenue_orders",
            "원재료 및 생산설비": "revenue_orders",
            "주요계약 및 연구개발활동": "contracts_rnd",
            "기타 참고사항": "other_references",
            "위험관리 및 파생거래": "other_references"
        }

        # 정규화된 제목으로 매핑 시도
        normalized_title = re.sub(r'[\s\d\-\.︎️　]+', '', title.strip())

        # 직접 매칭
        if title in section_mapping:
            return section_mapping[title]
        if normalized_title in section_mapping:
            return section_mapping[normalized_title]

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

    async def _classify_with_llm(self, title: str, content: str) -> str:
        """
        LLM을 사용한 분류
        """
        if not self.ollama_client or not self.semaphore:
            return 'other_references'

        async with self.semaphore:
            try:
                prompt = f"""다음 공시 문서의 챕터를 분석하여 카테고리를 분류해주세요.

챕터 제목: {title}

챕터 내용:
{content[:1500]}

카테고리 분류 기준:
1. business_overview: 회사 개요, 사업 전반적인 설명
2. products_services: 제품/서비스 상세, 브랜드
3. revenue_orders: 매출 현황, 수주 실적, 원재료, 생산설비
4. contracts_rnd: 주요 계약, 연구개발 활동, 특허
5. other_references: 위험관리, 파생거래, 기타 참고사항

가장 적합한 카테고리 1개만 선택하여 답하세요:"""

                # 비동기 처리
                loop = asyncio.get_event_loop()
                response_text = await loop.run_in_executor(
                    self.executor,
                    self._call_ollama,
                    prompt
                )

                # 카테고리 추출
                response_text = response_text.strip().lower()
                valid_categories = [
                    'business_overview', 'products_services', 'revenue_orders',
                    'contracts_rnd', 'other_references'
                ]

                for category in valid_categories:
                    if category in response_text:
                        return category

                return 'other_references'

            except Exception as e:
                self.logger.error(f"LLM classification failed: {e}")
                return 'other_references'

    def _call_ollama(self, prompt: str) -> str:
        """Ollama API 동기 호출"""
        response = self.ollama_client.chat(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 2000
            }
        )
        return response['message']['content']

    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        base_status = super().get_status()
        base_status.update({
            "ollama_host": settings.OLLAMA_HOST,
            "model_name": settings.OLLAMA_MODEL,
            "max_workers": settings.MAX_WORKERS,
            "active_tasks": settings.MAX_WORKERS - (self.semaphore._value if self.semaphore else 0)
        })
        return base_status