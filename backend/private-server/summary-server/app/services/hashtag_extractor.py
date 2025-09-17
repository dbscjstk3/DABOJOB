"""
해시태그 추출 서비스
요약된 텍스트에서 카테고리별 핵심 키워드를 추출
"""
import logging
import re
from typing import List, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logger = logging.getLogger(__name__)

class HashtagExtractor:
    def __init__(self, ollama_client, model_name: str = "llama3.2:1b-instruct-fp16"):
        """
        해시태그 추출기 초기화

        Args:
            ollama_client: Ollama 클라이언트
            model_name: 사용할 모델명
        """
        self.ollama_client = ollama_client
        self.model_name = model_name
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 제외할 일반적인 단어들
        self.common_words = {
            '기업', '회사', '사업', '제품', '서비스', '기술', '연구', '개발',
            '관리', '경영', '전략', '시장', '고객', '성장', '혁신', '투자',
            '매출', '수익', '실적', '현황', '분석', '평가', '계획', '목표',
            '글로벌', '국내', '해외', '세계', '지역', '산업', '분야', '부문',
            '주요', '핵심', '중요', '특별', '일반', '기본', '전체', '부분',
            '증가', '감소', '확대', '축소', '개선', '향상', '발전', '진화',
            'ESG', 'Environmental', 'Social', 'Governance', '지속가능',
            '리스크', '위험', '안전', '품질', '표준', '규정', '정책', '제도'
        }
    
    def _extract_sync(self, text: str, category: str) -> List[str]:
        """동기 방식 해시태그 추출 (executor에서 실행용)"""

        # 카테고리별 추출 가이드 - 더 구체적으로
        category_guides = {
            'business_overview': "구체적인 사업 영역, 특정 산업명, 고유한 비즈니스 모델",
            'products_services': "실제 제품명, 브랜드명, 특정 서비스명 (일반명사 제외)",
            'revenue_orders': "구체적인 수치, 특정 거래처, 계약 프로젝트명",
            'contracts_rnd': "특정 기술명, 특허명, 구체적인 R&D 프로젝트",
            'other_references': "특정 인증, 수상 내역, 구체적인 파트너십"
        }
        
        guide = category_guides.get(category, "핵심 비즈니스 키워드")
        
        prompt = f"""텍스트에서 뉴스 검색에 사용할 구체적이고 독특한 키워드를 추출하세요.
추출 기준: {guide}

엄격한 규칙:
1. 일반적인 단어 금지 (기업, 회사, 제품, 서비스, 기술, 관리 등)
2. 구체적인 고유명사, 제품명, 기술명 우선
3. 2-4단어 이내
4. 쉼표로 구분
5. 3개만 추출
6. 완전한 문장 금지

좋은 예: 갤럭시S24, 3나노공정, OLED패널
나쁜 예: 글로벌기업, 주요제품, 기술혁신

텍스트:
{text[:800]}

구체적 키워드 3개:"""
        
        try:
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 50
                }
            )
            
            # 응답에서 키워드 추출
            keywords_text = response['message']['content'].strip()

            # 불필요한 문자들 제거
            keywords_text = re.sub(r'\d+\.\s*', '', keywords_text)  # 숫자 번호 제거
            keywords_text = re.sub(r'[-•]\s*', '', keywords_text)   # 대시, 불릿 제거
            keywords_text = re.sub(r'\n+', ',', keywords_text)      # 줄바꿈을 쉼표로 변환
            keywords_text = re.sub(r'[#\[\]()]', '', keywords_text) # 특수문자 제거

            # 쉼표로 분리하고 정제
            keywords = [k.strip() for k in keywords_text.split(',')]
            keywords = [k for k in keywords if k and len(k) > 0]

            # 문장 형태 필터링 (5단어 이상은 제외)
            keywords = [k for k in keywords if len(k.split()) <= 4]
            
            # 각 키워드를 더 정제
            cleaned_keywords = []
            for keyword in keywords:
                # 불필요한 접속사, 조사 제거
                keyword = re.sub(r'(이다|입니다|등|및|과|와|의|을|를|에서|에게|에|은|는|이|가)$', '', keyword)
                keyword = keyword.strip()

                # 흔한 단어 필터링
                if self._is_too_common(keyword):
                    logger.debug(f"Filtered common word: {keyword}")
                    continue

                # 최소 2글자, 최대 20글자
                if keyword and 2 <= len(keyword) <= 20:
                    cleaned_keywords.append(keyword)

            keywords = cleaned_keywords[:3]  # 3개로 제한
            
            # 부족하면 텍스트에서 추가 추출 시도
            if len(keywords) < 3:
                additional = self._extract_specific_terms(text, category)
                for term in additional:
                    if term not in keywords and not self._is_too_common(term):
                        keywords.append(term)
                        if len(keywords) >= 3:
                            break
            
            logger.info(f"Extracted hashtags for {category}: {keywords}")
            return keywords
            
        except Exception as e:
            logger.error(f"Failed to extract hashtags: {e}")
            # 실패 시 텍스트에서 직접 추출 시도
            return self._extract_specific_terms(text[:500], category)[:3]
    
    async def extract_hashtags_streaming(self, job_id: str, summaries: Dict[str, str], redis_publisher=None) -> Dict[str, List[str]]:
        """
        각 카테고리별 요약에서 해시태그 추출하고 완료되는 대로 Redis로 전송

        Args:
            job_id: 작업 ID
            summaries: {카테고리: 요약문} 딕셔너리
            redis_publisher: Redis 발행자 (선택적)

        Returns:
            {카테고리: [해시태그 리스트]} 딕셔너리
        """
        hashtags = {}
        published_count = 0

        # 비동기 실행을 위한 태스크 생성
        loop = asyncio.get_event_loop()
        tasks = []

        for category, summary in summaries.items():
            if summary and summary.strip():
                task = loop.run_in_executor(
                    self.executor,
                    self._extract_sync,
                    summary,
                    category
                )
                tasks.append((category, task))
            else:
                hashtags[category] = []
                # 빈 카테고리도 Redis에 전송 (빈 태그 리스트로)
                if redis_publisher:
                    redis_publisher.publish_single_hashtag(job_id, category, [])

        # 더 안전한 방식: asyncio.wait() 사용
        pending_tasks = {task: category for category, task in tasks}

        while pending_tasks:
            done, pending = await asyncio.wait(
                pending_tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED
            )

            for completed_task in done:
                category = pending_tasks.get(completed_task, "unknown")
                try:
                    result = await completed_task
                    hashtags[category] = result

                    # 완료되는 즉시 Redis로 전송
                    if redis_publisher and result:
                        message_id = redis_publisher.publish_single_hashtag(job_id, category, result)
                        if message_id:
                            published_count += 1
                            logger.info(f"Hashtags for {category} published immediately: {result}")

                except Exception as e:
                    logger.error(f"Failed to extract hashtags for {category}: {e}")
                    hashtags[category] = []

                # 완료된 태스크를 딕셔너리에서 제거
                if completed_task in pending_tasks:
                    del pending_tasks[completed_task]

        # 완료 신호 전송
        if redis_publisher and published_count > 0:
            redis_publisher.publish_completion_signal(job_id, published_count)

        return hashtags

    async def extract_hashtags(self, summaries: Dict[str, str]) -> Dict[str, List[str]]:
        """
        기존 호환성을 위한 메서드 - 모든 추출 완료 후 일괄 반환

        Args:
            summaries: {카테고리: 요약문} 딕셔너리

        Returns:
            {카테고리: [해시태그 리스트]} 딕셔너리
        """
        return await self.extract_hashtags_streaming("temp", summaries, None)
    
    def _is_too_common(self, keyword: str) -> bool:
        """너무 일반적인 키워드인지 확인"""
        # 단어를 공백으로 분리
        words = keyword.split()

        # 모든 단어가 common_words에 있으면 True
        for word in words:
            if word in self.common_words:
                return True

        # 전체 키워드가 common_words에 있으면 True
        if keyword in self.common_words:
            return True

        return False

    def _extract_specific_terms(self, text: str, category: str) -> List[str]:
        """텍스트에서 구체적인 용어 추출"""
        import re

        # 영문+숫자 조합 (제품명, 모델명)
        product_pattern = r'\b[A-Z][A-Za-z0-9]+(?:[\s-][A-Z0-9]+)*\b'
        products = re.findall(product_pattern, text)

        # 숫자가 포함된 용어 (수치, 규모)
        number_pattern = r'\b\d+[가-힣]+|[가-힣]+\d+[가-힣]*\b'
        numbers = re.findall(number_pattern, text)

        # 괄호 안의 용어 (약어, 설명)
        bracket_pattern = r'[\(\[]([^\)\]]+)[\)\]]'
        brackets = re.findall(bracket_pattern, text)

        # 고유명사 패턴 (대문자로 시작하는 연속된 단어들)
        proper_pattern = r'\b[A-Z가-힣][A-Za-z가-힣]+(?:\s+[A-Z가-힣][A-Za-z가-힣]+)*\b'
        propers = re.findall(proper_pattern, text)

        # 모든 추출된 용어 합치기
        all_terms = products + numbers + brackets + propers

        # 정제 및 필터링
        specific_terms = []
        for term in all_terms:
            term = term.strip()
            if term and 2 <= len(term) <= 20 and not self._is_too_common(term):
                specific_terms.append(term)

        # 중복 제거하고 상위 5개 반환
        seen = set()
        unique_terms = []
        for term in specific_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms[:5] if unique_terms else []

    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=False)
    
    def format_message(self, job_id: str, category: str, hashtags: List[str]) -> Dict:
        """
        단일 카테고리 해시태그를 Redis Streams로 전송할 메시지 포맷 생성

        Args:
            job_id: 작업 ID
            category: 카테고리명
            hashtags: 해시태그 리스트

        Returns:
            전송할 메시지 딕셔너리
        """
        return {
            'job_id': job_id,
            'category': category,
            'hashtags': hashtags,
            'timestamp': datetime.now().isoformat(),
            'source': 'hashtag-extractor'
        }