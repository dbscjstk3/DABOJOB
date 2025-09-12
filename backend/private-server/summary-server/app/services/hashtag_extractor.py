"""
해시태그 추출 서비스
요약된 텍스트에서 카테고리별 핵심 키워드를 추출
"""
import logging
import re
from typing import List, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class HashtagExtractor:
    def __init__(self, ollama_client, model_name: str = "qwen2.5:0.5b-instruct-fp16"):
        """
        해시태그 추출기 초기화
        
        Args:
            ollama_client: Ollama 클라이언트
            model_name: 사용할 모델명
        """
        self.ollama_client = ollama_client
        self.model_name = model_name
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def _extract_sync(self, text: str, category: str) -> List[str]:
        """동기 방식 해시태그 추출 (executor에서 실행용)"""
        
        # 카테고리별 추출 가이드
        category_guides = {
            'business_overview': "사업분야, 산업군, 기업특성 관련 키워드",
            'products_services': "주력제품명, 서비스명, 브랜드명",
            'revenue_orders': "재무지표, 성장성, 시장위치 관련 키워드",
            'contracts_rnd': "기술명, R&D분야, 혁신키워드",
            'other_references': "경영전략, ESG, 리스크관리 관련 키워드"
        }
        
        guide = category_guides.get(category, "핵심 비즈니스 키워드")
        
        prompt = f"""다음 기업분석 요약에서 {guide} 키워드를 정확히 3개 추출하세요.

엄격한 규칙:
1. 반드시 단어 또는 2단어 구문만 (예: "반도체", "스마트폰", "글로벌기업")
2. 번호 매기기 금지 (1., 2., 3. 사용 금지)
3. 줄바꿈 금지 (\n 사용 금지)
4. 쉼표(,)로만 구분
5. 불필요한 설명 금지
6. 한국어 단어만 사용

잘못된 예시: "1. TV\n2. DRAM", "- 제품혁신", "반도체 사업"
올바른 예시: "반도체, 스마트폰, 글로벌기업"

요약문:
{text[:500]}

3개 키워드:"""
        
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
            
            # 각 키워드를 더 정제
            cleaned_keywords = []
            for keyword in keywords:
                # 불필요한 접속사, 조사 제거
                keyword = re.sub(r'(이다|입니다|등|및|과|와|의|을|를|에서|에게|에)$', '', keyword)
                keyword = keyword.strip()
                if keyword and len(keyword) >= 2:  # 최소 2글자 이상
                    cleaned_keywords.append(keyword)
            
            keywords = cleaned_keywords[:3]  # 3개로 제한
            
            # 부족하면 기본값 추가
            if len(keywords) < 3:
                default_keywords = {
                    'business_overview': ['사업다각화', '글로벌기업', '종합기업'],
                    'products_services': ['제품혁신', '서비스확대', '기술개발'],
                    'revenue_orders': ['매출성장', '수익개선', '시장확대'],
                    'contracts_rnd': ['R&D투자', '기술혁신', '특허확보'],
                    'other_references': ['지속가능경영', '리스크관리', 'ESG경영']
                }
                defaults = default_keywords.get(category, ['기업분석', '비즈니스', '경영전략'])
                while len(keywords) < 3:
                    for default in defaults:
                        if default not in keywords:
                            keywords.append(default)
                            break
                    if len(keywords) >= 3:
                        break
            
            logger.info(f"Extracted hashtags for {category}: {keywords}")
            return keywords
            
        except Exception as e:
            logger.error(f"Failed to extract hashtags: {e}")
            # 실패 시 기본 키워드 반환
            default_map = {
                'business_overview': ['사업전략', '기업개요', '비즈니스모델'],
                'products_services': ['제품서비스', '주력상품', '기술력'],
                'revenue_orders': ['매출실적', '재무현황', '성장성'],
                'contracts_rnd': ['연구개발', '기술투자', '혁신'],
                'other_references': ['경영관리', '지속가능성', '기업가치']
            }
            return default_map.get(category, ['기업', '비즈니스', '분석'])[:3]
    
    async def extract_hashtags(self, summaries: Dict[str, str]) -> Dict[str, List[str]]:
        """
        각 카테고리별 요약에서 해시태그 추출
        
        Args:
            summaries: {카테고리: 요약문} 딕셔너리
            
        Returns:
            {카테고리: [해시태그 리스트]} 딕셔너리
        """
        hashtags = {}
        
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
        
        # 모든 태스크 완료 대기
        for category, task in tasks:
            try:
                result = await task
                hashtags[category] = result
            except Exception as e:
                logger.error(f"Failed to extract hashtags for {category}: {e}")
                hashtags[category] = []
        
        return hashtags
    
    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=False)
    
    def format_message(self, job_id: str, hashtags: Dict[str, List[str]]) -> List[Dict]:
        """
        Redis Streams로 전송할 메시지 포맷 생성
        
        Args:
            job_id: 작업 ID
            hashtags: {카테고리: [해시태그]} 딕셔너리
            
        Returns:
            전송할 메시지 리스트
        """
        messages = []
        for category, tags in hashtags.items():
            if tags:  # 해시태그가 있는 경우만
                message = {
                    'job_id': job_id,
                    'category': category,
                    'hashtags': tags
                }
                messages.append(message)
        return messages