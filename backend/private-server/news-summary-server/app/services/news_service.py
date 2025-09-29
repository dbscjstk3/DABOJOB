"""
뉴스 검색 및 처리 서비스
Naver 뉴스 API → 크롤링 → AI 요약 → DB 저장
"""
import aiohttp
import asyncio
import logging
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote
from email.utils import parsedate_to_datetime
from ..config import config
from ..database import database

logger = logging.getLogger(__name__)

class NewsService:
    """뉴스 검색 및 처리 서비스"""
    
    def __init__(self):
        self.client_id = config.NAVER_CLIENT_ID
        self.client_secret = config.NAVER_CLIENT_SECRET
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        
        # 해시태그별 키워드 매핑
        self.hashtag_keywords = {
            '반도체': ['반도체', 'semiconductor', '메모리', 'dram', 'nand', '칩', 'chip'],
            'ai': ['ai', '인공지능', 'artificial intelligence', '머신러닝', '딥러닝'],
            '실적': ['실적', '매출', '영업이익', '순이익', '분기', '어닝'],
            '채용': ['채용', '인재', '신입', '경력', '모집', '입사', '대규모', '정기', '수시'],
            '플랫폼': ['플랫폼', 'platform', '서비스', '시스템', '솔루션', '기술', '개발'],
            '인재': ['인재', '채용', '모집', '신입', '경력', '인력', '직원', '사원', '취업'],
            '신사업': ['신사업', '새로운', '신규', '확장', '진출', '사업', '출시', '론칭']
        }
    
    async def search_and_process_news(self, mapping_id: int, hashtag_id: int, summary_id: int,
                                    hashtag: str, company_name: str = "") -> int:
        """
        해시태그로 뉴스 검색하고 처리

        Args:
            mapping_id: 매핑 ID
            hashtag_id: 해시태그 ID
            summary_id: 요약 ID
            hashtag: 검색할 해시태그
            company_name: 기업명

        Returns:
            처리된 뉴스 수
        """
        try:
            logger.info(f"Searching news for hashtag: {hashtag}, company: {company_name}")

            # 중복 처리 방지 체크
            existing_count = await self._check_existing_news(mapping_id, hashtag_id, hashtag)
            if existing_count > 0:
                logger.info(f"News already processed for hashtag: {hashtag} (count: {existing_count})")
                return existing_count

            # 1. Naver API로 뉴스 검색 (테스트용: 1개로 제한)
            raw_news_list = await self._search_naver_news(hashtag, company_name, target_articles=1)
            # 기존: target_articles=3 (운영용)

            if not raw_news_list:
                logger.warning(f"No news found for hashtag: {hashtag}")
                return 0

            # 2. Raw 뉴스를 DB에 저장 (status='raw')
            saved_count = await self._save_raw_news(mapping_id, hashtag_id, summary_id, raw_news_list)

            # 3. 즉시 크롤링 + 요약 처리 (백그라운드 아님)
            await self._process_news_content(mapping_id, hashtag_id, hashtag)

            return saved_count

        except Exception as e:
            logger.error(f"Error searching news for hashtag {hashtag}: {e}")
            return 0

    async def _check_existing_news(self, mapping_id: int, hashtag_id: int, hashtag: str) -> int:
        """해당 해시태그로 이미 처리된 뉴스가 있는지 확인"""
        try:
            query = """
            SELECT COUNT(*) as count
            FROM news_summaries
            WHERE mapping_id = %s AND hashtag_id = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (mapping_id, hashtag_id))
                result = await cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error checking existing news: {e}")
            return 0

    async def _search_naver_news(self, hashtag: str, company_name: str = "",
                               target_articles: int = 1) -> List[Dict[str, Any]]:  # 테스트용: 기본값 1개
        """Naver 뉴스 API 검색 (참고 코드 기반)"""
        try:
            hashtag_clean = hashtag.replace('#', '').lower()
            company_clean = company_name.replace('주', '').replace('(', '').replace(')', '').strip()
            
            # 검색 쿼리 생성
            search_queries = []
            if company_clean:
                search_queries = [
                    f"{company_clean} {hashtag_clean}",  # 기업명 + 해시태그
                ]
            else:
                search_queries = [hashtag_clean]
            
            collected_articles = []
            seen_urls = set()
            
            for query in search_queries:
                if len(collected_articles) >= target_articles:
                    break
                    
                logger.info(f"Searching with query: {query}")
                articles = await self._call_naver_api(query, display=30)
                
                for article in articles:
                    if len(collected_articles) >= target_articles:
                        break
                        
                    if article['url'] in seen_urls:
                        continue
                    seen_urls.add(article['url'])
                    
                    # 관련성 점수 계산
                    relevance_score = self._calculate_relevance_score(
                        article['title'], article['description'], hashtag, company_name
                    )

                    # 모든 뉴스의 점수 로그 출력 (임계값 통과 여부 관계없이)
                    logger.info(f"🔍 뉴스 점수: {relevance_score}점")
                    logger.info(f"📰 제목: {article['title']}")
                    logger.info(f"📝 내용: {article['description'][:100]}...")
                    logger.info(f"🔗 URL: {article['url']}")

                    if relevance_score >= 15:  # 임계값 (기업 관련성 강화에 따라 상향)
                        article['relevance_score'] = relevance_score

                        # 중복 체크
                        if not self._is_duplicate_content(article, collected_articles):
                            collected_articles.append(article)
                            logger.info(f"✅ 뉴스 선택됨: {relevance_score}점")
                        else:
                            logger.info(f"❌ 중복 뉴스로 제외")
                    else:
                        logger.info(f"❌ 점수 부족으로 제외 (최소 15점 필요)")
                    logger.info("─" * 80)
            
            # 점수 순으로 정렬하고 상위 articles 반환
            collected_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
            result = collected_articles[:target_articles]
            
            logger.info(f"Found {len(result)} relevant news items for hashtag: {hashtag}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching Naver news: {e}")
            return []
    
    async def _call_naver_api(self, query: str, display: int = 30) -> List[Dict[str, Any]]:
        """실제 Naver API 호출"""
        try:
            headers = {
                'X-Naver-Client-Id': self.client_id,
                'X-Naver-Client-Secret': self.client_secret
            }
            
            params = {
                'query': query,
                'display': min(display, 100),
                'start': 1,
                'sort': 'date'  # 날짜순
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        # 뉴스 데이터 정제
                        news_list = []
                        for item in items:
                            news_item = {
                                'title': self._clean_html_tags(item.get('title', '')),
                                'url': item.get('originallink', item.get('link', '')),
                                'description': self._clean_html_tags(item.get('description', '')),
                                'pub_date': self._parse_pub_date(item.get('pubDate', ''))
                            }
                            news_list.append(news_item)
                        
                        return news_list
                    else:
                        logger.error(f"Naver API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error calling Naver API: {e}")
            return []
    
    def _calculate_relevance_score(self, title: str, description: str, hashtag: str, company: str) -> int:
        """관련성 점수 계산 (참고 코드 기반)"""
        score = 0
        title_lower = title.lower()
        desc_lower = description.lower()
        hashtag_clean = hashtag.replace('#', '').lower()
        company_lower = company.lower()
        full_text = f"{title_lower} {desc_lower}"
        
        # 1. 기업명 체크 및 기업 관련성 강화
        if company_lower:
            # 기본 기업명과 괄호 제거된 버전만 체크
            company_variants = [
                company_lower,
                company_lower.replace('(주)', '').replace('㈜', '').strip(),
                company_lower.split('(')[0].strip() if '(' in company_lower else company_lower
            ]

            company_found = False
            company_in_title = False

            for variant in company_variants:
                if variant and variant in title_lower:
                    score += 50  # 제목에 기업명 있으면 높은 점수
                    company_found = True
                    company_in_title = True
                    break
                elif variant and variant in desc_lower:
                    score += 25  # 설명에 기업명 있으면 중간 점수
                    company_found = True
                    break

            # 기업 관련성 추가 체크
            if company_found:
                # 기업 활동 관련 키워드 체크
                corporate_activity_keywords = [
                    '발표', '출시', '계획', '투자', '사업', '서비스', '제품', '기술',
                    '실적', '매출', '영업이익', '순이익', '실적', '채용', '모집',
                    '개발', '생산', '공장', '확장', '진출', '협력', '제휴'
                ]

                corporate_activity_found = sum(1 for keyword in corporate_activity_keywords if keyword in full_text)
                if corporate_activity_found > 0:
                    score += corporate_activity_found * 5  # 기업 활동 키워드당 5점 추가

                # 제목에 기업명이 있으면서 기업 활동 키워드도 있으면 추가 보너스
                if company_in_title and corporate_activity_found > 0:
                    score += 20

            # 기업명이 없으면 큰 감점
            if not company_found:
                score -= 30
        
        # 2. 해시태그별 키워드 체크
        keywords = self.hashtag_keywords.get(hashtag_clean, [hashtag_clean])
        
        keyword_found = False
        for keyword in keywords:
            if keyword in title_lower:
                score += 20
                keyword_found = True
                break
            elif keyword in desc_lower:
                score += 10
                keyword_found = True
                break
        
        if not keyword_found:
            score -= 5
        
        # 3. 비즈니스 관련 키워드 보너스
        business_keywords = ['기업', '회사', '사업', '투자', '서비스', '출시', '발표', '채용']
        if any(keyword in full_text for keyword in business_keywords):
            score += 5
        
        # 4. 제외 키워드 체크
        exclude_keywords = ['개인', '사적', '연인', '부부', '외도', '싸움', '갈등', '스캔들', '루머', '가십']
        if any(keyword in full_text for keyword in exclude_keywords):
            score -= 30
        
        return max(0, score)
    
    def _is_duplicate_content(self, new_article: Dict[str, Any], existing_articles: List[Dict[str, Any]], 
                            similarity_threshold: float = 0.7) -> bool:
        """중복 컨텐츠 체크"""
        new_title = new_article['title'].lower()
        
        for existing in existing_articles:
            existing_title = existing['title'].lower()
            similarity = self._calculate_text_similarity(new_title, existing_title)
            
            if similarity >= similarity_threshold:
                return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """텍스트 유사도 계산 (Jaccard 유사도)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        return intersection / union
    
    async def _save_raw_news(self, mapping_id: int, hashtag_id: int, summary_id: int, 
                           news_list: List[Dict]) -> int:
        """Raw 뉴스를 DB에 저장"""
        insert_query = """
        INSERT INTO news_summaries (
            mapping_id, hashtag_id, summary_id,
            news_title, news_url, news_created_at, status
        ) VALUES (%s, %s, %s, %s, %s, %s, 'raw')
        ON DUPLICATE KEY UPDATE
            news_title = VALUES(news_title),
            updated_at = NOW()
        """
        
        saved_count = 0
        async with database.get_connection() as cursor:
            for news in news_list:
                try:
                    await cursor.execute(insert_query, (
                        mapping_id,
                        hashtag_id,
                        summary_id,
                        news['title'][:500],
                        news['url'][:1000],
                        news['pub_date']
                    ))
                    saved_count += cursor.rowcount
                except Exception as e:
                    logger.error(f"Error saving raw news: {e}")
        
        logger.info(f"Saved {saved_count} raw news items")
        return saved_count
    
    async def _process_news_content(self, mapping_id: int, hashtag_id: int, hashtag: str):
        """뉴스 크롤링 + 요약 처리 (순차 처리)"""
        try:
            # status='raw'인 뉴스들 조회
            raw_news = await self._get_raw_news(mapping_id, hashtag_id)

            # 순차적으로 하나씩 처리 (동시 처리하지 않음)
            for i, news in enumerate(raw_news):
                try:
                    # 이미 처리된 뉴스인지 확인
                    if news.get('status') == 'completed':
                        logger.info(f"News {news['news_id']} already processed, skipping")
                        continue

                    logger.info(f"Processing news {i+1}/{len(raw_news)}: {news['news_id']}")

                    # 크롤링 + 요약 (순차적으로)
                    content = await self._crawl_news_content(news['news_url'])
                    if content:
                        summary = await self._summarize_content(content, hashtag)
                        company_name = self._extract_company_name(content)

                        # DB 업데이트 (status='completed')
                        await self._update_news_summary(news['news_id'], summary, company_name)
                        logger.info(f"Completed processing news {news['news_id']}")

                        # 각 뉴스 처리 후 잠깐 대기 (서버 부하 분산)
                        await asyncio.sleep(0.5)
                    else:
                        logger.warning(f"Failed to crawl content for news {news['news_id']}")

                except Exception as e:
                    logger.error(f"Error processing news {news['news_id']}: {e}")
                    continue  # 에러가 나도 다음 뉴스 처리 계속

        except Exception as e:
            logger.error(f"Error in news processing: {e}")
    
    async def _get_raw_news(self, mapping_id: int, hashtag_id: int) -> List[Dict]:
        """Raw 상태의 뉴스 조회"""
        query = """
        SELECT news_id, news_url, news_title, status
        FROM news_summaries
        WHERE mapping_id = %s AND hashtag_id = %s AND status = 'raw'
        """

        async with database.get_connection() as cursor:
            await cursor.execute(query, (mapping_id, hashtag_id))
            rows = await cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    async def _crawl_news_content(self, url: str) -> Optional[str]:
        """뉴스 URL에서 본문 크롤링"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        # 간단한 텍스트 추출 (실제로는 BeautifulSoup 등 사용)
                        text = self._extract_text_from_html(html)
                        return text[:2000]  # 2000자 제한
                    return None
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    def _extract_text_from_html(self, html: str) -> str:
        """BeautifulSoup를 사용한 고품질 HTML 텍스트 추출"""
        try:
            from bs4 import BeautifulSoup

            # BeautifulSoup로 HTML 파싱
            soup = BeautifulSoup(html, 'html.parser')

            # 불필요한 태그들 완전 제거
            unwanted_tags = [
                'script', 'style', 'meta', 'link', 'noscript', 'iframe',
                'embed', 'object', 'head', 'header', 'footer', 'nav',
                'aside', 'form', 'input', 'button', 'select', 'textarea'
            ]

            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()

            # 광고나 불필요한 클래스/ID 제거
            unwanted_classes = [
                'advertisement', 'ad', 'ads', 'banner', 'popup', 'modal',
                'sidebar', 'menu', 'navigation', 'footer', 'header',
                'social', 'share', 'comment', 'related', 'recommend'
            ]

            for class_name in unwanted_classes:
                for element in soup.find_all(attrs={'class': re.compile(class_name, re.I)}):
                    element.decompose()
                for element in soup.find_all(attrs={'id': re.compile(class_name, re.I)}):
                    element.decompose()

            # 본문 텍스트만 추출 (우선순위: article > main > div.content > p)
            main_content = None

            # 1. article 태그 찾기
            article = soup.find('article')
            if article:
                main_content = article.get_text()

            # 2. main 태그 찾기
            if not main_content:
                main = soup.find('main')
                if main:
                    main_content = main.get_text()

            # 3. content 관련 div 찾기
            if not main_content:
                content_div = soup.find('div', attrs={'class': re.compile(r'content|article|body', re.I)})
                if content_div:
                    main_content = content_div.get_text()

            # 4. 전체에서 텍스트 추출
            if not main_content:
                main_content = soup.get_text()

            # 텍스트 정제
            text = main_content

            # 연속된 공백과 줄바꿈 정리
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n', text)

            # 불필요한 패턴 제거
            unwanted_patterns = [
                r'function\s*\([^)]*\)\s*\{.*?\}',  # JavaScript 함수
                r'var\s+\w+\s*=.*?;',  # JavaScript 변수
                r'\$\([^)]*\)',  # jQuery 선택자
                r'document\.\w+.*?;',  # DOM 조작
                r'window\.\w+.*?;',  # Window 객체
                r'console\.\w+.*?;',  # Console 로그
                r'gtm\.|gtag\(|ga\(',  # Google Analytics
                r'facebook|twitter|instagram|youtube',  # SNS 관련
                r'저작권|copyright|©|\(c\)',  # 저작권 표시
                r'구독|좋아요|공유|댓글',  # 소셜 액션
                r'더보기|펼치기|접기|토글',  # UI 요소
                r'로그인|회원가입|마이페이지',  # 계정 관련
            ]

            for pattern in unwanted_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)

            # HTML 엔티티 정리
            text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
            text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
            text = text.replace('&hellip;', '...').replace('&middot;', '·')

            # 최종 정리
            text = text.strip()

            # 너무 짧으면 원본 반환
            if len(text) < 50:
                # fallback: 정규식으로 간단 정제
                text = re.sub(r'<[^>]+>', '', html)
                text = re.sub(r'\s+', ' ', text).strip()

            return text

        except Exception as e:
            logger.warning(f"BeautifulSoup 파싱 실패, fallback 사용: {e}")
            # BeautifulSoup 실패 시 기존 방식 사용
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    
    async def _summarize_content(self, content: str, hashtag: str) -> str:
        """향상된 AI 뉴스 요약 (고품질 모델 사용)"""
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text_for_summary(content)

            # 텍스트가 너무 짧으면 그대로 반환
            if len(processed_text.strip()) < 50:
                return processed_text.strip() or "관련 뉴스입니다."

            # 향상된 프롬프트로 고품질 요약 생성
            summary = await self._generate_high_quality_summary(processed_text, hashtag)

            # 후처리로 완벽한 요약 완성
            final_summary = self._post_process_summary(summary, target_sentences=1)

            logger.info(f"High-quality summarizing for hashtag: {hashtag}")
            return final_summary

        except Exception as e:
            logger.error(f"Error in enhanced AI summarization: {e}")
            # 실패 시 기존 방식 사용
            return await self._fallback_summarize_content(content, hashtag)

    def _preprocess_text_for_summary(self, text: str) -> str:
        """요약을 위한 텍스트 전처리 (향상됨)"""
        # 사진 관련 정보 제거
        remove_patterns = [
            r'/사진제공=[^/\n]*',
            r'사진제공=[^/\n]*',
            r'▲[^▲]*▲[^.]*\.',
            r'<사진=[^>]*>',
            r'사진 확대[^.]*\.',
            r'[가-힣]+ 모습\.',
            r'본지와의 인터뷰[^.]*\.',
            r'인터뷰를 하고 있는[^.]*\.',
        ]

        for pattern in remove_patterns:
            text = re.sub(pattern, '', text)

        # 공백 정리
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    async def _generate_high_quality_summary(self, text: str, hashtag: str) -> str:
        """고품질 AI 요약 생성"""
        try:
            # Ollama 클라이언트 가져오기
            from ..main import ollama_client, MODEL_NAME

            if not ollama_client:
                logger.warning("Ollama client not available, using fallback")
                return text[:150] + ("..." if len(text) > 150 else "")

            # 대폭 개선된 프롬프트
            prompt = f"""다음 뉴스 기사의 핵심 내용을 한국어로 명확하게 요약하세요.

**필수 조건:**
1. 정확히 1개의 완전한 문장으로 작성
2. 80자 이내로 간결하게
3. "{hashtag}"와 직접 관련된 구체적 내용만 포함
4. 완전한 주어-서술어 구조의 문장
5. 숫자나 고유명사는 정확히 기재
6. 불필요한 수식어나 반복 금지

**금지사항:**
- 문장이 끊어지거나 미완성
- "등", "관련", "발표" 같은 모호한 표현 남발
- 여러 기업/사건을 나열하지 말고 핵심만
- 중국어, 일본어, 특수문자 사용 금지

기사 내용:
{text[:1200]}

핵심 요약(80자 이내 1문장):"""

            response = ollama_client.chat(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.2,  # 더 일관성 있는 결과를 위해 낮춤
                    "top_p": 0.7,
                    "num_predict": 100,  # 짧은 요약을 위해 줄임
                    "stop": ["\n", ".", "。"]  # 첫 번째 문장에서 멈춤
                }
            )

            return response['message']['content'].strip()

        except Exception as e:
            logger.error(f"Error in high-quality summary generation: {e}")
            return text[:150] + ("..." if len(text) > 150 else "")

    def _post_process_summary(self, summary: str, target_sentences: int = 1) -> str:
        """요약 텍스트 후처리 (대폭 개선됨)"""
        logger.debug(f"[원본 요약 결과]\n{summary}\n")

        # 1. 기본 정리
        summary = summary.strip()

        # 2. 불필요한 prefix/suffix 제거
        unwanted_prefixes = [
            r'^.*?요약\s*[:：]?\s*',
            r'^.*?정리\s*[:：]?\s*',
            r'^.*?결론\s*[:：]?\s*',
            r'^.*?핵심\s*[:：]?\s*',
            r'^.*?내용\s*[:：]?\s*',
        ]

        for pattern in unwanted_prefixes:
            summary = re.sub(pattern, '', summary, flags=re.IGNORECASE)

        # 3. 불필요한 기호와 패턴 제거
        summary = re.sub(r'[•\-\*]\s*', '', summary)  # 불릿 포인트
        summary = re.sub(r'\[\s*\]\s*', '', summary)  # 빈 대괄호
        summary = re.sub(r'\d+\.\s*', '', summary)     # 번호 매기기
        summary = re.sub(r'\d+\)\s*', '', summary)     # 번호 매기기
        summary = re.sub(r'Answer\s*:?\s*', '', summary, flags=re.IGNORECASE)

        # 4. 중국어, 일본어, 이상한 문자 제거
        summary = re.sub(r'[ぁ-んァ-ヶー一-龯。，]', '', summary)
        summary = re.sub(r'[^\w\s가-힣0-9.,!?]', ' ', summary)

        # 5. 공백 정리
        summary = re.sub(r'\s+', ' ', summary)
        summary = summary.strip()

        logger.debug(f"[1차 정리된 요약]\n{summary}\n")

        # 6. 빈 문자열 체크
        if not summary or len(summary.strip()) < 5:
            logger.warning("⚠️  요약 결과가 너무 짧습니다.")
            return "요약 생성에 실패했습니다."

        # 7. 문장 완성도 검증 및 보완
        summary = self._ensure_complete_sentence(summary)

        # 8. 최대 길이 제한
        if len(summary) > 80:
            # 마지막 완전한 문장까지만 자르기
            sentences = re.split(r'[.!?]', summary)
            if len(sentences) > 1:
                # 첫 번째 완전한 문장만 사용
                summary = sentences[0].strip() + '.'
            else:
                summary = summary[:77] + "..."

        logger.debug(f"[최종 요약]\n{summary}\n")
        return summary

    def _ensure_complete_sentence(self, text: str) -> str:
        """문장의 완성도를 보장"""
        text = text.strip()

        # 한국어 문장의 기본 패턴 확인
        korean_words = re.findall(r'[가-힣]+', text)

        if len(korean_words) < 2:
            return "관련 뉴스입니다."

        # 문장 끝 처리
        if not text.endswith(('.', '!', '?')):
            # 한국어 어미로 끝나는지 확인
            if re.search(r'[가-힣][다음습니까요]$', text):
                text += '.'
            elif re.search(r'[가-힣]$', text):
                text += '다.'
            else:
                text += '.'

        # 너무 짧은 문장 보완
        if len(text) < 15:
            return "관련 뉴스입니다."

        return text

    async def _fallback_summarize_content(self, content: str, hashtag: str) -> str:
        """기존 방식의 폴백 요약"""
        try:
            # utils.py의 clean_text 함수 사용
            from ..utils import clean_text

            # 텍스트 정제
            cleaned_content = clean_text(content)

            # 텍스트가 너무 짧으면 그대로 반환
            if len(cleaned_content.strip()) < 50:
                return cleaned_content.strip() or "관련 뉴스입니다."

            # Ollama 클라이언트 가져오기
            from ..main import ollama_client, MODEL_NAME

            if not ollama_client:
                logger.warning("Ollama client not available, using text truncation")
                return cleaned_content[:150] + ("..." if len(cleaned_content) > 150 else "")

            # 기존 프롬프트
            prompt = f"""다음 뉴스 기사를 {hashtag} 해시태그와 관련된 핵심 내용 중심으로 정확히 2개의 완전한 한국어 문장으로 요약하세요.

필수 조건:
1. 반드시 150자 이내로 작성한다.
2. 정확히 2개의 완전한 한국어 문장으로만 구성한다.
3. {hashtag}와 관련된 핵심 내용만 포함한다.
4. 중국어, 영어 등 다른 언어 사용 금지한다.
5. 사진이나 이미지 관련 내용은 제외한다.
6. "..."과 ":" 같은 생략 표시는 사용하지 않는다.
7. 순수한 뉴스 내용만 요약해서 응답한다.

기사 내용:
{cleaned_content[:1500]}

150자 이내 2문장 요약:"""

            response = ollama_client.chat(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 150
                }
            )

            summary = response['message']['content'].strip()

            # 기존 후처리 로직 유지
            prefix_patterns = [
                rf"^{re.escape(hashtag)}\s*관련\s*뉴스\s*요약\s*[:：]?\s*",
                r"^뉴스\s*요약\s*[:：]?\s*",
                r"^요약\s*[:：]?\s*",
            ]

            for pattern in prefix_patterns:
                summary = re.sub(pattern, "", summary, flags=re.IGNORECASE).strip()

            if ':' in summary:
                parts = summary.split(':', 1)
                if len(parts) > 1 and len(parts[1].strip()) > 10:
                    summary = parts[1].strip()

            summary = summary.strip()

            if len(summary) > 150:
                summary = summary[:147] + "..."

            if not summary:
                summary = cleaned_content[:150] + ("..." if len(cleaned_content) > 150 else "")

            return summary

        except Exception as e:
            logger.error(f"Error in fallback summarization: {e}")
            cleaned_content = content[:150].strip()
            return cleaned_content + ("..." if len(content) > 150 else "")
    
    def _extract_company_name(self, content: str) -> str:
        """본문에서 기업명 추출"""
        # TODO: 실제 기업명 추출 로직 구현
        # 간단한 패턴 매칭으로 (주), 주식회사 등 찾기
        company_pattern = r'([가-힣a-zA-Z0-9]+(?:\([주]\)|주식회사|㈜))'
        matches = re.findall(company_pattern, content)
        return matches[0] if matches else ""
    
    async def _update_news_summary(self, news_id: int, summary: str, company_name: str):
        """뉴스 요약 업데이트"""
        update_query = """
        UPDATE news_summaries 
        SET news_content = %s, company_name = %s, status = 'completed', updated_at = NOW()
        WHERE news_id = %s
        """
        
        async with database.get_connection() as cursor:
            await cursor.execute(update_query, (summary, company_name, news_id))
            logger.info(f"Updated news summary for news_id: {news_id}")
    
    def _clean_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        clean = re.sub('<.*?>', '', text)
        return clean.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    
    def _parse_pub_date(self, pub_date_str: str) -> datetime:
        """발행일 파싱"""
        try:
            return parsedate_to_datetime(pub_date_str)
        except:
            return datetime.now()

    async def search_and_process_news_versioned(
        self,
        mapping_id: int,
        version: int,
        hashtag_id: int,
        summary_id: int,
        hashtag: str,
        company_name: str = "",
        limit: int = 50
    ) -> int:
        """버전별 뉴스 검색 및 처리 (재요약용)"""
        try:
            logger.info(f"Starting versioned news search for hashtag: {hashtag} (v{version})")

            # 기존 로직과 동일하지만 version_id 추가해서 저장
            relevant_articles = await self._search_news_api(hashtag, limit=limit)

            if not relevant_articles:
                logger.warning(f"No news found for hashtag: {hashtag} (v{version})")
                return 0

            # 버전별 저장
            saved_count = await self._save_raw_news_versioned(
                mapping_id=mapping_id,
                version=version,
                hashtag_id=hashtag_id,
                summary_id=summary_id,
                news_list=relevant_articles
            )

            logger.info(f"Processed {saved_count} news articles for hashtag: {hashtag} (v{version})")
            return saved_count

        except Exception as e:
            logger.error(f"Error in versioned news search for {hashtag} (v{version}): {e}")
            return 0

    async def _save_raw_news_versioned(self, mapping_id: int, version: int, hashtag_id: int, summary_id: int,
                                     news_list: List[Dict]) -> int:
        """버전별 Raw 뉴스 저장"""
        insert_query = """
        INSERT INTO news_summaries (
            version_id, mapping_id, hashtag_id, summary_id,
            news_title, news_url, news_created_at, status
        ) SELECT sv.version_id, %s, %s, %s, %s, %s, %s, 'raw'
        FROM summary_versions sv
        WHERE sv.mapping_id = %s AND sv.version_number = %s
        ON DUPLICATE KEY UPDATE
            news_title = VALUES(news_title),
            updated_at = NOW()
        """

        saved_count = 0
        async with database.get_connection() as cursor:
            for news in news_list:
                try:
                    await cursor.execute(insert_query, (
                        mapping_id,
                        hashtag_id,
                        summary_id,
                        news['title'][:500],
                        news['url'][:1000],
                        news['pub_date'],
                        mapping_id,
                        version
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving versioned news: {e}")

        return saved_count

# 전역 인스턴스
news_service = NewsService()