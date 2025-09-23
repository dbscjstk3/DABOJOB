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

            # 1. Naver API로 뉴스 검색 (3개로 제한)
            raw_news_list = await self._search_naver_news(hashtag, company_name, target_articles=3)

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
                               target_articles: int = 3) -> List[Dict[str, Any]]:
        """Naver 뉴스 API 검색 (참고 코드 기반)"""
        try:
            hashtag_clean = hashtag.replace('#', '').lower()
            company_clean = company_name.replace('주', '').replace('(', '').replace(')', '').strip()
            
            # 검색 쿼리 생성
            search_queries = []
            if company_clean:
                search_queries = [
                    company_clean,  # 기업명만
                    hashtag_clean,  # 해시태그만
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
                    
                    if relevance_score >= 10:  # 임계값
                        article['relevance_score'] = relevance_score
                        
                        # 중복 체크
                        if not self._is_duplicate_content(article, collected_articles):
                            collected_articles.append(article)
                            logger.info(f"Added news: {article['title'][:50]}... (score: {relevance_score})")
            
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
        
        # 1. 기업명 체크
        if company_lower:
            company_variants = [
                company_lower,
                company_lower.replace('주', '').replace('(', '').replace(')', '').strip(),
                company_lower.split('(')[0].strip() if '(' in company_lower else company_lower
            ]
            
            company_found = False
            for variant in company_variants:
                if variant and variant in title_lower:
                    score += 30
                    company_found = True
                    break
                elif variant and variant in desc_lower:
                    score += 15
                    company_found = True
                    break
            
            if not company_found:
                score -= 10
        
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
        """뉴스 크롤링 + 요약 처리"""
        try:
            # status='raw'인 뉴스들 조회
            raw_news = await self._get_raw_news(mapping_id, hashtag_id)

            for news in raw_news:
                try:
                    # 이미 처리된 뉴스인지 확인
                    if news.get('status') == 'completed':
                        logger.info(f"News {news['news_id']} already processed, skipping")
                        continue

                    # 크롤링 + 요약
                    content = await self._crawl_news_content(news['news_url'])
                    if content:
                        summary = await self._summarize_content(content, hashtag)
                        company_name = self._extract_company_name(content)

                        # DB 업데이트 (status='completed')
                        await self._update_news_summary(news['news_id'], summary, company_name)

                except Exception as e:
                    logger.error(f"Error processing news {news['news_id']}: {e}")

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
        """HTML에서 텍스트 추출 (간단한 버전)"""
        # HTML 태그 제거
        text = re.sub('<[^<]+?>', '', html)
        # 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    async def _summarize_content(self, content: str, hashtag: str) -> str:
        """AI로 뉴스 내용 요약"""
        # TODO: 실제 AI 요약 로직 구현 (OpenAI, Ollama 등)
        summary = f"{hashtag} 관련 뉴스 요약: {content[:200]}..."
        logger.info(f"Summarizing content for hashtag: {hashtag}")
        return summary
    
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