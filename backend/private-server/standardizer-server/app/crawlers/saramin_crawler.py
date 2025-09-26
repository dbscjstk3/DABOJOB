#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
from .base_crawler import BaseCrawler
from ..models.crawler_models import (
    Company, JobPosting, JobSector, Region,
    JobPostingSector, JobPostingRegion, CrawlingLog, CompanyDartMapping, MappingStatus
)
from ..services.company_mapper import CompanyMappingService
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import redis
import json as json_lib


def parse_job_item(job_item_element):
    """
    개별 채용공고 아이템을 파싱하여 구조화된 데이터로 변환
    - 실제 HTML 구조에 맞게 개선된 파싱 로직
    """
    if not job_item_element:
        return None

    job_data = {}

    # 디버깅을 위한 요소 ID 저장
    element_id = job_item_element.get('id', 'unknown')
    job_data['debug_element_id'] = element_id

    try:
        # box_item 찾기 (list_item 안에 있을 수 있음)
        box_item = job_item_element.find('div', class_='box_item')
        if not box_item:
            box_item = job_item_element  # 이미 box_item일 경우

        # 1. 회사 정보 파싱 (개선된 로직)
        company_section = box_item.find('div', class_='col company_nm')
        if company_section:
            # 회사명 추출 (더 강건한 방식)
            company_link = company_section.find('a', class_='str_tit')
            if not company_link:
                company_link = company_section.find('a')

            company_name = None
            company_url = None

            if company_link:
                company_name = company_link.get_text(strip=True)
                company_url = company_link.get('href')

                # 빈 텍스트 처리
                if not company_name or company_name == '':
                    # title 속성에서 회사명 추출 시도
                    company_name = company_link.get('title', '').strip()

            if not company_name:
                # 링크가 없거나 텍스트가 비어있으면 전체 텍스트에서 추출
                all_text = company_section.get_text(separator=' ', strip=True)
                if all_text:
                    # 첫 번째 의미있는 단어를 회사명으로 사용
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    if lines:
                        company_name = lines[0]

            job_data['company_name'] = company_name
            job_data['company_url'] = company_url

            # 계열사 정보
            main_corp = company_section.find('span', class_='main_corp')
            if main_corp:
                group_name = main_corp.get_text(strip=True)
                if group_name:
                    job_data['company_group'] = group_name

            # 기업 규모
            stock_info = company_section.find('span', class_='info_stock')
            if stock_info:
                size_info = stock_info.get_text(strip=True)
                if size_info:
                    job_data['company_size'] = size_info

        # 2. 채용공고 정보 파싱 (개선된 로직)
        notification_section = box_item.find('div', class_='col notification_info')
        if notification_section:
            # 공고 제목 및 URL (더 정확한 선택자)
            job_title_link = None

            # 첫 번째 방법: 직접 찾기
            job_title_link = notification_section.find('a', class_='str_tit')

            # 두 번째 방법: job_tit 안에서 찾기
            if not job_title_link:
                job_tit_section = notification_section.find('div', class_='job_tit')
                if job_tit_section:
                    job_title_link = job_tit_section.find('a')

            # 세 번째 방법: 모든 a 태그 중 href가 있는 것 찾기
            if not job_title_link:
                all_links = notification_section.find_all('a')
                for link in all_links:
                    if link.get('href') and ('jobs' in link.get('href', '') or 'rec_idx' in link.get('href', '')):
                        job_title_link = link
                        break

            if job_title_link:
                # 제목 추출
                title_text = job_title_link.get_text(strip=True)
                if title_text:
                    job_data['job_title'] = title_text

                # URL 추출
                job_url = job_title_link.get('href')
                if job_url:
                    job_data['job_url'] = job_url

                    # rec_idx 추출 (더 강건한 방식)
                    rec_idx = None
                    # 1. 직접 속성에서
                    rec_idx = job_title_link.get('rec_idx')
                    # 2. href에서 rec_idx 파라미터
                    if not rec_idx:
                        rec_match = re.search(r'rec_idx=(\d+)', job_url)
                        if rec_match:
                            rec_idx = rec_match.group(1)
                    # 3. id 속성에서 (rec_link_숫자 형태)
                    if not rec_idx:
                        link_id = job_title_link.get('id', '')
                        id_match = re.search(r'rec_link_(\d+)', link_id)
                        if id_match:
                            rec_idx = id_match.group(1)

                    job_data['job_id'] = rec_idx

            # 직무 분야 (개선된 파싱)
            job_sectors_section = notification_section.find('div', class_='job_meta')
            if job_sectors_section:
                job_sectors_span = job_sectors_section.find('span', class_='job_sector')
                if job_sectors_span:
                    # 모든 span 태그에서 텍스트 추출
                    sectors = []
                    sector_spans = job_sectors_span.find_all('span')
                    for span in sector_spans:
                        sector_text = span.get_text(strip=True)
                        if sector_text and sector_text != '외':
                            sectors.append(sector_text)

                    if sectors:
                        job_data['job_sectors'] = sectors

            # NEW, HOT 등 뱃지 확인
            badges = []
            if job_title_link and 'new' in job_title_link.get('class', []):
                badges.append('NEW')

            # HOT 뱃지 별도 확인
            hot_elements = notification_section.find_all(class_=re.compile(r'hot', re.I))
            if hot_elements:
                badges.append('HOT')

            if badges:
                job_data['badges'] = badges

        # 3. 채용 조건 파싱 (개선된 로직)
        recruit_section = box_item.find('div', class_='col recruit_info')
        if recruit_section:
            recruit_items = recruit_section.find('ul')
            if recruit_items:
                li_elements = recruit_items.find_all('li')

                for li in li_elements:
                    # 근무지
                    work_place = li.find('p', class_='work_place')
                    if work_place:
                        location_text = work_place.get_text(strip=True)
                        if location_text:
                            job_data['work_location'] = location_text

                    # 경력 및 고용형태
                    career = li.find('p', class_='career')
                    if career:
                        career_text = career.get_text(strip=True)
                        if career_text:
                            job_data['career_requirement'] = career_text

                            # 경력과 고용형태 분리 (· 기준)
                            if '·' in career_text:
                                parts = [part.strip() for part in career_text.split('·')]
                                if len(parts) >= 2:
                                    job_data['career'] = parts[0]
                                    job_data['employment_type'] = parts[1]

                    # 학력
                    education = li.find('p', class_='education')
                    if education:
                        edu_text = education.get_text(strip=True)
                        if edu_text:
                            job_data['education_requirement'] = edu_text

                    # 급여
                    salary = li.find('p', class_='salary')
                    if salary:
                        salary_text = salary.get_text(strip=True)
                        if salary_text:
                            job_data['salary'] = salary_text

        # 4. 지원 정보 파싱 (개선된 로직)
        support_section = box_item.find('div', class_='col support_info')
        if support_section:
            # 지원 버튼 타입 확인
            apply_button = support_section.find('button', class_='sri_btn_md')
            if apply_button:
                job_data['apply_type'] = '즉시지원'
            else:
                homepage_apply = support_section.find('a', class_='sri_btn_sm')
                if homepage_apply:
                    job_data['apply_type'] = '홈페이지지원'

            # 자소서 문항 확인
            cover_letter_btn = support_section.find('span', class_='coverLetterLayerBtn')
            if cover_letter_btn:
                job_data['has_cover_letter'] = True
                cover_letter_id = cover_letter_btn.get('data-id')
                if cover_letter_id:
                    job_data['cover_letter_id'] = cover_letter_id
            else:
                job_data['has_cover_letter'] = False

            # 지원 상세 정보 (마감일, 등록시간)
            support_detail = support_section.find('p', class_='support_detail')
            if support_detail:
                # 마감일 정보
                date_span = support_detail.find('span', class_='date')
                if date_span:
                    deadline_text = date_span.get_text(strip=True)
                    if deadline_text:
                        job_data['deadline'] = deadline_text

                # 등록 시간 정보
                deadlines_span = support_detail.find('span', class_='deadlines')
                if deadlines_span:
                    reg_time_text = deadlines_span.get_text(strip=True)
                    if reg_time_text:
                        job_data['registration_time'] = reg_time_text

        return job_data

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Job item parsing failed for {element_id}: {str(e)}")
        return None


def parse_multiple_jobs(html_content):
    """
    여러 개의 채용공고가 포함된 HTML을 파싱
    - 실제 HTML 구조에 맞게 개선된 선택자 사용
    - 광고성 콘텐츠와 실제 채용공고 구분
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []

    try:
        # 1. 메인 채용공고 섹션 찾기 (더 구체적인 경로)
        recruiting_section = soup.find('section', class_='list_recruiting')
        if recruiting_section:
            # list_body 찾기
            list_body = recruiting_section.find('div', class_='list_body')
            if list_body:
                # ID 패턴을 이용한 정확한 채용공고 아이템 선택
                # rec-숫자 형태의 ID를 가진 list_item만 선택
                job_items = list_body.find_all('div', class_='list_item', id=re.compile(r'^rec-\d+$'))

                for item in job_items:
                    # 광고성 콘텐츠 제외 (더 포괄적인 체크)
                    if (item.find('div', class_='list_curation_wrap') or
                        item.find('div', class_='theme_jobs_container') or
                        item.find('div', class_='list_recommend') or
                        item.find('div', class_='newcomer_sub_bottom')):
                        continue

                    # box_item이 있는지 확인
                    if not item.find('div', class_='box_item'):
                        continue

                    job_data = parse_job_item(item)
                    if job_data and job_data.get('job_title') and job_data.get('company_name'):
                        jobs.append(job_data)

        # 2. 대안 방법: common_recruilt_list에서 직접 찾기
        if not jobs:
            common_list = soup.find('div', class_='common_recruilt_list')
            if common_list:
                # list_item들을 직접 찾되, ID가 rec-로 시작하는 것만
                job_items = common_list.find_all('div', class_='list_item', id=re.compile(r'^rec-\d+$'))

                for item in job_items:
                    # 광고성 콘텐츠 제외
                    if (item.find('div', class_='list_curation_wrap') or
                        item.find('div', class_='theme_jobs_container')):
                        continue

                    job_data = parse_job_item(item)
                    if job_data and job_data.get('job_title') and job_data.get('company_name'):
                        jobs.append(job_data)

        # 3. 최후 수단: 모든 box_item 직접 검색
        if not jobs:
            all_box_items = soup.find_all('div', class_='box_item')
            for box_item in all_box_items:
                # 부모가 list_item이고 ID가 rec-로 시작하는 경우만
                parent = box_item.parent
                if (parent and
                    parent.get('class') and
                    'list_item' in parent.get('class') and
                    parent.get('id') and
                    parent.get('id').startswith('rec-')):

                    job_data = parse_job_item(parent)
                    if job_data and job_data.get('job_title') and job_data.get('company_name'):
                        jobs.append(job_data)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Multiple jobs parsing failed: {str(e)}")

    return jobs


def parse_recommendation_jobs(html_content):
    """
    추천 공고 섹션 파싱 (테마별 공고)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    recommendations = {}

    # 테마 추천 공고 찾기
    theme_container = soup.find('div', class_='theme_jobs_container')
    if not theme_container:
        return recommendations

    # 탭 버튼들에서 테마 정보 추출
    tab_buttons = theme_container.find_all('button', class_='btn_curation')

    for button in tab_buttons:
        theme_key = button.get('data-key')
        theme_name = button.get_text(strip=True)

        if theme_key:
            # 해당 테마의 패널 찾기
            panel_id = f"keyword_tab_panel{button.get('data-index')}"
            panel = theme_container.find('div', id=panel_id)

            if panel:
                theme_jobs = []
                job_slides = panel.find_all('li', class_='swiper-slide')

                for slide in job_slides:
                    job_link = slide.find('a', class_='newcomer_link_view')
                    if job_link:
                        job_info = {}

                        # 공고 제목
                        announcement = slide.find('span', class_='announcement')
                        if announcement:
                            job_info['title'] = announcement.get_text(strip=True)

                        # 회사명
                        company = slide.find('span', class_='company_name')
                        if company:
                            job_info['company'] = company.get_text(strip=True)

                        # 위치 및 기타 정보
                        info_spans = slide.find_all('span')
                        job_info['details'] = [span.get_text(strip=True) for span in info_spans if span.get_text(strip=True)]

                        # 마감일
                        day_span = slide.find('span', class_='day')
                        if day_span:
                            job_info['deadline'] = day_span.get_text(strip=True)

                        # URL
                        job_info['url'] = job_link.get('href')

                        theme_jobs.append(job_info)

                recommendations[theme_name] = theme_jobs

    return recommendations


class SaraminCrawler(BaseCrawler):
    def __init__(self, base_url: str = "https://www.saramin.co.kr/zf_user/jobs/public/list", db_session: Optional[Session] = None):
        super().__init__()
        self.base_url = base_url
        self.db_session = db_session
        self.crawl_log_id = None

        # 매핑 서비스 초기화
        self.mapping_service = CompanyMappingService() if db_session else None

        # 매핑 캐시 (한 번 확인한 회사는 재확인 방지)
        self.mapping_cache = {}  # {company_name: is_mappable}

        # Redis 클라이언트 초기화
        try:
            self.redis_client = redis.from_url(
                "redis://redis:6379",
                decode_responses=True
            )
            self.redis_client.ping()
            self.logger.info("Redis 연결 성공: 크롤링 재시작 기능 활성화")
        except Exception as e:
            self.redis_client = None
            self.logger.warning(f"Redis 연결 실패: 크롤링 재시작 기능 비활성화 - {e}")

    def crawl(self, max_pages: int = 5, crawl_id: str = None, resume: bool = False) -> Dict[str, Any]:
        """
        특정 조건으로 사람인 크롤링 (봇 탐지 방지를 위한 Selenium 사용)
        - 대기업 + 코스닥 기업
        - 정규직
        - 국내 기업
        - 페이지당 100개 항목

        Args:
            max_pages: 크롤링할 최대 페이지 수
            crawl_id: 크롤링 작업 ID (재시작용)
            resume: 이전 크롤링을 이어서 할지 여부
        """
        try:
            self.initialize()

            # Redis에서 상태 복원 또는 새로 시작
            if resume and crawl_id and self.redis_client:
                state = self._load_crawl_state(crawl_id)
                if state:
                    start_page = state.get('last_page', 0) + 1
                    all_jobs = state.get('collected_jobs', [])
                    all_recommendations = state.get('recommendations', {})
                    self.crawl_log_id = state.get('log_id')
                    self.logger.info(f"크롤링 재개: {crawl_id}, 페이지 {start_page}부터 시작")
                else:
                    start_page = 1
                    all_jobs = []
                    all_recommendations = {}
                    self.crawl_log_id = self._log_crawl_start('job_list', self.base_url)
            else:
                start_page = 1
                all_jobs = []
                all_recommendations = {}
                self.crawl_log_id = self._log_crawl_start('job_list', self.base_url)
                if not crawl_id:
                    crawl_id = f"saramin_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            for page in range(start_page, max_pages + 1):
                try:
                    self.logger.info(f"페이지 {page} 크롤링 시작")

                    # 특정 조건으로 URL 구성
                    page_url = self._build_url_with_conditions(page)

                    if page == 1:
                        self.driver.get(page_url)
                        # 초기 로딩 대기
                        self._wait_for_page_load()
                    else:
                        # 페이지네이션 처리
                        if not self._navigate_to_next_page(page):
                            self.driver.get(page_url)
                            self._wait_for_page_load()

                    # 페이지 로딩 완료 대기
                    if not self._wait_for_job_listings():
                        self.logger.warning(f"페이지 {page}: 채용공고를 찾을 수 없음")
                        continue

                    # 자연스러운 스크롤
                    self.natural_scroll()

                    # 개선된 파싱 사용
                    page_jobs = self._crawl_page_jobs_improved()
                    all_jobs.extend(page_jobs)

                    # 첫 페이지에서만 추천 공고 수집
                    if page == 1:
                        all_recommendations = self._parse_recommendations()

                    self.logger.info(f"페이지 {page}: {len(page_jobs)}개 공고 수집")

                    # 진행 상태를 Redis에 저장 (매 페이지마다)
                    if crawl_id and self.redis_client:
                        self._save_crawl_state(crawl_id, {
                            'last_page': page,
                            'max_pages': max_pages,
                            'collected_jobs': all_jobs,
                            'recommendations': all_recommendations,
                            'log_id': self.crawl_log_id,
                            'updated_at': datetime.now().isoformat()
                        })

                    if len(page_jobs) == 0:
                        self.logger.info(f"페이지 {page}에서 더 이상 데이터가 없습니다.")
                        break

                    # 랜덤 대기 (봇 탐지 방지)
                    self.wait_random(3, 8)

                except Exception as e:
                    self.logger.error(f"페이지 {page} 크롤링 실패: {str(e)}")
                    continue

            # 데이터베이스 저장
            saved_count = self._save_jobs_to_database(all_jobs) if self.db_session else 0

            self._log_crawl_complete(self.crawl_log_id, 'success', len(all_jobs), saved_count)

            # 크롤링 완료 시 Redis에서 상태 삭제
            if crawl_id and self.redis_client:
                self._delete_crawl_state(crawl_id)

            return {
                'status': 'completed',
                'total_jobs': saved_count,
                'pages_processed': max_pages,
                'total_found': len(all_jobs),
                'total_saved': saved_count,
                'jobs': all_jobs,
                'recommendations': all_recommendations,
                'conditions': {
                    'company_type': '대기업 + 코스닥',
                    'job_type': '정규직',
                    'panel_type': '국내기업',
                    'page_count': '100개/페이지'
                }
            }

        except Exception as e:
            self.logger.error(f"크롤링 실패: {str(e)}")
            self._log_crawl_complete(self.crawl_log_id, 'failed', 0, 0, str(e))
            return {
                'status': 'failed',
                'error': str(e),
                'jobs': []
            }
        finally:
            self.cleanup()

    def _build_url_with_conditions(self, page: int) -> str:
        """특정 조건으로 URL 구성"""
        params = [
            f"recruitPage={page}",
            "recruitPageCount=100",
            "company_type=scale001,kosdaq",  # 대기업 + 코스닥
            "job_type=1",                   # 정규직
            "panel_type=domestic",          # 국내기업
            "search_optional_item=y",
            "search_done=y"
        ]
        return f"{self.base_url}?{'&'.join(params)}"

    def _wait_for_page_load(self):
        """페이지 로딩 대기"""
        try:
            # 여러 가지 요소 중 하나라도 로드되면 성공
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # 추가 대기
            time.sleep(2)
        except TimeoutException:
            self.logger.warning("페이지 로딩 대기 시간 초과")

    def _wait_for_job_listings(self) -> bool:
        """
        채용공고 리스트 로딩 대기 (개선된 로직)
        - 실제 HTML 구조에 맞는 선택자 사용
        - 요소의 존재 뿐만 아니라 가시성도 확인
        """
        # 우선순위별로 선택자 정의
        primary_selectors = [
            (By.CSS_SELECTOR, "section.list_recruiting .list_body .list_item[id^='rec-']"),
            (By.CSS_SELECTOR, ".common_recruilt_list .list_item[id^='rec-']"),
        ]

        secondary_selectors = [
            (By.CSS_SELECTOR, "section.list_recruiting"),
            (By.CSS_SELECTOR, "div.list_body"),
            (By.CLASS_NAME, "box_item"),
        ]

        # 1차: 실제 채용공고 아이템이 있는지 확인 (우선순위)
        for by, selector in primary_selectors:
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((by, selector))
                )
                # 추가로 요소가 실제로 보이는지 확인
                WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((by, selector))
                )
                self.logger.info(f"채용공고 아이템 발견: {selector}")
                return True
            except TimeoutException:
                continue

        # 2차: 기본적인 구조 요소들이 있는지 확인
        for by, selector in secondary_selectors:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                self.logger.info(f"기본 구조 요소 발견: {selector}")

                # 추가 대기 후 실제 채용공고가 로드되었는지 재확인
                time.sleep(3)
                soup = self.get_page_soup()
                if soup:
                    # rec-로 시작하는 ID를 가진 요소가 있는지 확인
                    job_items = soup.find_all('div', class_='list_item', id=re.compile(r'^rec-\d+$'))
                    if job_items:
                        self.logger.info(f"채용공고 {len(job_items)}개 발견")
                        return True

                return True  # 기본 구조는 있으니 시도
            except TimeoutException:
                continue

        self.logger.warning("채용공고 리스트를 찾을 수 없음")
        return False

    def _navigate_to_next_page(self, page: int) -> bool:
        """다음 페이지로 이동"""
        try:
            # 페이지네이션 버튼 찾기
            pagination_selectors = [
                f"a[onclick*='recruitPage={page}']",
                f"a[data-page='{page}']",
                f"button[onclick*='recruitPage={page}']"
            ]

            for selector in pagination_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed() and element.is_enabled():
                        # 자연스러운 클릭을 위해 스크롤
                        self.driver.execute_script("arguments[0].scrollIntoView();", element)
                        time.sleep(1)
                        element.click()
                        self.wait_random(2, 4)
                        return True
                except NoSuchElementException:
                    continue

            # JavaScript로 직접 이동 시도
            script = f"window.location.href = window.location.href.replace(/recruitPage=\\d+/, 'recruitPage={page}');"
            self.driver.execute_script(script)
            self.wait_random(2, 4)
            return True

        except Exception as e:
            self.logger.warning(f"페이지네이션 실패: {e}")
            return False

    def _crawl_page_jobs_improved(self) -> List[Dict[str, Any]]:
        """
        개선된 파싱을 사용한 페이지 크롤링
        - 강화된 에러 처리 및 로깅
        - 디버깅 정보 수집
        """
        try:
            # 페이지 소스 획득
            soup = self.get_page_soup()
            if not soup:
                self.logger.error("페이지 소스를 가져올 수 없음")
                return []

            # HTML 파싱
            jobs = parse_multiple_jobs(str(soup))
            self.logger.info(f"원시 파싱 결과: {len(jobs)}개 채용공고")

            if not jobs:
                # 디버깅을 위한 추가 정보 수집
                page_title = soup.find('title')
                title_text = page_title.get_text() if page_title else "제목 없음"

                # 주요 요소들이 있는지 확인
                recruiting_section = soup.find('section', class_='list_recruiting')
                list_body = soup.find('div', class_='list_body')
                list_items = soup.find_all('div', class_='list_item')

                self.logger.warning(f"채용공고를 찾을 수 없음 - 페이지: {title_text}")
                self.logger.warning(f"디버그 정보 - recruiting_section: {'있음' if recruiting_section else '없음'}")
                self.logger.warning(f"디버그 정보 - list_body: {'있음' if list_body else '없음'}")
                self.logger.warning(f"디버그 정보 - list_items: {len(list_items)}개")

            # 데이터 매핑
            mapped_jobs = []
            mapping_errors = 0

            for idx, job_data in enumerate(jobs):
                try:
                    mapped_data = self._map_job_data(job_data)
                    if mapped_data and mapped_data.get('saramin_job_title') and mapped_data.get('company_name'):
                        mapped_jobs.append(mapped_data)
                    else:
                        # 매핑 실패 원인 로깅
                        missing_fields = []
                        if not mapped_data:
                            missing_fields.append("전체 매핑 실패")
                        else:
                            if not mapped_data.get('saramin_job_title'):
                                missing_fields.append("job_title")
                            if not mapped_data.get('company_name'):
                                missing_fields.append("company_name")

                        debug_id = job_data.get('debug_element_id', f'item_{idx}')
                        self.logger.warning(f"매핑 실패 [{debug_id}]: {', '.join(missing_fields)} 누락")
                        mapping_errors += 1

                except Exception as e:
                    mapping_errors += 1
                    debug_id = job_data.get('debug_element_id', f'item_{idx}')
                    self.logger.error(f"개별 아이템 매핑 실패 [{debug_id}]: {str(e)}")

            success_rate = (len(mapped_jobs) / len(jobs) * 100) if jobs else 0
            self.logger.info(f"페이지 파싱 완료: {len(mapped_jobs)}/{len(jobs)} 성공 ({success_rate:.1f}%)")

            if mapping_errors > 0:
                self.logger.warning(f"매핑 오류 {mapping_errors}건 발생")

            return mapped_jobs

        except Exception as e:
            self.logger.error(f"페이지 크롤링 전체 실패: {str(e)}", exc_info=True)
            return []

    def _parse_recommendations(self) -> Dict[str, Any]:
        """추천 공고 파싱"""
        try:
            soup = self.get_page_soup()
            return parse_recommendation_jobs(str(soup))
        except Exception as e:
            self.logger.error(f"추천 공고 파싱 실패: {e}")
            return {}

    def _map_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """새로운 크롤링 데이터를 기존 데이터베이스 스키마에 맞게 매핑"""
        mapped = {
            'company_name': job_data.get('company_name'),
            'csn': self._extract_csn_from_url(job_data.get('company_url', '')),
            'company_group': job_data.get('company_group'),
            'company_scale': job_data.get('company_size'),
            'saramin_job_id': job_data.get('job_id'),
            'saramin_job_title': job_data.get('job_title'),
            'saramin_job_url': self._ensure_absolute_url(job_data.get('job_url')),
            'job_sectors': job_data.get('job_sectors', []),
            'is_hot': 'HOT' in job_data.get('badges', []),
            'work_location': job_data.get('work_location'),
            'career_info': job_data.get('career_requirement'),
            'education_requirement': job_data.get('education_requirement'),
            'salary_info': job_data.get('salary'),
            'application_deadline': self._parse_deadline_date(job_data.get('deadline', '')),
            'registration_info': job_data.get('registration_time'),
            'posting_date': self._parse_posting_date(job_data.get('registration_time', '')),
            'crawled_at': datetime.now()
        }
        return mapped

    def _ensure_absolute_url(self, url: str) -> str:
        """URL을 절대 경로로 변환"""
        if not url:
            return ""
        if not url.startswith('http'):
            return f"https://www.saramin.co.kr{url}"
        return url

    def _extract_csn_from_url(self, url: str) -> Optional[str]:
        """URL에서 CSN 추출"""
        if not url:
            return None
        match = re.search(r'csn=([^&]+)', url)
        return match.group(1) if match else None

    def _parse_deadline_date(self, deadline_text: str) -> Optional[datetime]:
        """
        마감일 텍스트를 datetime으로 변환
        - D-숫자, 오늘마감, 내일마감, ~월.일(요일) 등 다양한 형태 지원
        """
        try:
            if not deadline_text:
                return None

            deadline_text = deadline_text.strip()

            # 상시채용 또는 채용시마감
            if any(keyword in deadline_text for keyword in ['상시', '채용시마감', '채용시', '수시']):
                return None

            # D-숫자 형태 (D-4, D-21 등) - 가장 일반적인 형태
            d_match = re.search(r'D-(\d+)', deadline_text)
            if d_match:
                days_left = int(d_match.group(1))
                return datetime.now() + timedelta(days=days_left)

            # 오늘마감
            if '오늘마감' in deadline_text or '오늘' in deadline_text:
                return datetime.now().replace(hour=23, minute=59, second=59)

            # 내일마감
            if '내일마감' in deadline_text or '내일' in deadline_text:
                tomorrow = datetime.now() + timedelta(days=1)
                return tomorrow.replace(hour=23, minute=59, second=59)

            # ~10.10(금) 또는 ~09.29(월) 형태
            if '~' in deadline_text:
                date_part = deadline_text.split('~')[-1].strip()

                # 월.일 패턴 추출 (요일 정보 무시)
                match = re.search(r'(\d{1,2})\.(\d{1,2})', date_part)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
                    year = datetime.now().year
                    current_date = datetime.now()

                    # 유효한 날짜인지 확인
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        try:
                            target_date = datetime(year, month, day, 23, 59, 59)

                            # 현재 날짜보다 이전이면 내년으로 설정
                            if target_date < current_date:
                                target_date = datetime(year + 1, month, day, 23, 59, 59)

                            return target_date
                        except ValueError:
                            # 잘못된 날짜 조합 (예: 2월 30일)
                            self.logger.warning(f"잘못된 날짜: {year}-{month}-{day}")
                            return None

            # 숫자일 패턴 (1일 후, 2일 후 등)
            days_match = re.search(r'(\d+)일', deadline_text)
            if days_match:
                days_left = int(days_match.group(1))
                if days_left <= 365:  # 합리적인 범위 내에서만
                    return datetime.now() + timedelta(days=days_left)

            # 마감 임박 키워드들
            if any(keyword in deadline_text for keyword in ['마감임박', '곧마감', '마감직전']):
                # 마감임박은 1일 후로 설정
                return datetime.now() + timedelta(days=1)

            # 기타 알 수 없는 형태는 None 반환
            self.logger.info(f"알 수 없는 마감일 형태: {deadline_text}")
            return None

        except Exception as e:
            self.logger.warning(f"마감일 파싱 실패: {deadline_text} - {str(e)}")
            return None

    def _parse_posting_date(self, reg_info: str) -> Optional[datetime]:
        """등록 정보에서 게시일 추출"""
        try:
            if not reg_info:
                return None
            if '일 전' in reg_info:
                days_ago = int(re.search(r'(\d+)일 전', reg_info).group(1))
                return datetime.now() - timedelta(days=days_ago)
            elif '시간 전' in reg_info:
                hours_ago = int(re.search(r'(\d+)시간 전', reg_info).group(1))
                return datetime.now() - timedelta(hours=hours_ago)
        except Exception as e:
            self.logger.warning(f"게시일 파싱 실패: {reg_info} - {e}")
        return None

    # 기존 데이터베이스 저장 메서드들 유지
    def _save_jobs_to_database(self, jobs_data: List[Dict[str, Any]]) -> int:
        if not self.db_session:
            return 0

        saved_count = 0

        for job_data in jobs_data:
            try:
                # 회사명이 없으면 건너뛰기
                if not job_data.get('company_name'):
                    self.logger.warning(f"회사명이 없어 건너뜁니다: job_title={job_data.get('job_title')}")
                    continue

                # 모든 회사 저장 (나중에 자동 매핑에서 처리)
                # 크롤링 단계에서는 필터링하지 않음

                company_id = self._save_or_update_company(job_data)
                if not company_id:
                    continue

                job_id = self._save_job_posting(company_id, job_data)

                if job_id:
                    self._save_job_sectors_mapping(job_id, job_data.get('job_sectors', []))
                    if job_data.get('work_location'):
                        self._save_job_regions_mapping(job_id, job_data['work_location'])
                    saved_count += 1

            except Exception as e:
                self.logger.error(f"데이터 저장 실패 ({job_data.get('company_name')}): {str(e)}")
                self.db_session.rollback()
                continue

        return saved_count

    def _save_or_update_company(self, job_data: Dict[str, Any]) -> Optional[int]:
        try:
            # 회사명이 없으면 저장 불가
            if not job_data.get('company_name'):
                self.logger.warning(f"회사명이 없어 저장을 건너뜁니다: {job_data}")
                return None

            company = self.db_session.query(Company).filter_by(
                csn=job_data.get('csn')
            ).first() if job_data.get('csn') else None

            if not company:
                company = self.db_session.query(Company).filter_by(
                    company_name=job_data['company_name']
                ).first()

            if not company:
                company = Company(
                    company_name=job_data['company_name'],
                    csn=job_data.get('csn'),
                    company_group=job_data.get('company_group'),
                    company_scale=job_data.get('company_scale')
                )
                self.db_session.add(company)
            else:
                if job_data.get('csn'):
                    company.csn = job_data['csn']
                if job_data.get('company_group'):
                    company.company_group = job_data['company_group']
                if job_data.get('company_scale'):
                    company.company_scale = job_data['company_scale']

            self.db_session.flush()
            return company.company_id

        except Exception as e:
            self.logger.error(f"회사 정보 저장 실패: {e}")
            raise

    def _is_company_mappable(self, company_name: str) -> bool:
        """
        회사가 DART 매핑 가능한지 실시간 확인

        Args:
            company_name: 회사명

        Returns:
            bool: 매핑 가능 여부
        """
        if not self.mapping_service or not company_name:
            return False

        # 캐시에서 먼저 확인
        if company_name in self.mapping_cache:
            return self.mapping_cache[company_name]

        try:
            # 1. 이미 매핑된 회사인지 확인
            existing_mapping = self.db_session.query(CompanyDartMapping)\
                .join(Company)\
                .filter(Company.company_name == company_name)\
                .first()

            if existing_mapping:
                # 이미 검증된 매핑이 있으면 OK
                if existing_mapping.mapping_status == MappingStatus.verified:
                    self.mapping_cache[company_name] = True
                    return True
                # 제안된 매핑이 있으면 OK (검증 대기 중)
                elif existing_mapping.mapping_status == MappingStatus.suggested:
                    self.mapping_cache[company_name] = True
                    return True
                # 실패한 매핑이면 NO
                elif existing_mapping.mapping_status == MappingStatus.failed:
                    self.mapping_cache[company_name] = False
                    return False

            # 2. 새로운 회사라면 간단한 휴리스틱 검사
            is_mappable = self._quick_mapping_check(company_name)
            self.mapping_cache[company_name] = is_mappable

            if is_mappable:
                self.logger.info(f"새 회사 매핑 가능 예상: {company_name}")
            else:
                self.logger.info(f"새 회사 매핑 불가능 예상: {company_name}")

            return is_mappable

        except Exception as e:
            self.logger.error(f"매핑 확인 실패 {company_name}: {e}")
            self.mapping_cache[company_name] = False
            return False

    def _quick_mapping_check(self, company_name: str) -> bool:
        """
        간단한 휴리스틱으로 매핑 가능성 예측
        """
        # 너무 짧은 회사명은 매핑 어려움
        if len(company_name) < 2:
            return False

        # 숫자만 있는 회사명은 매핑 어려움
        if company_name.isdigit():
            return False

        # 특수문자만 있는 경우
        import re
        if not re.search(r'[가-힣A-Za-z]', company_name):
            return False

        # 일반적인 대기업, 중견기업 키워드
        big_company_keywords = [
            '삼성', 'LG', '현대', '기아', 'SK', 'KT', '롯데', '포스코',
            '한화', 'GS', 'CJ', '아모레', '카카오', '네이버', '쿠팡',
            '주식회사', '(주)', '㈜', '그룹', '홀딩스'
        ]

        for keyword in big_company_keywords:
            if keyword in company_name:
                return True

        # 기본적으로 시도해볼 가치가 있다고 판단
        return True

    def get_mapping_stats(self) -> Dict[str, int]:
        """
        크롤링 중 매핑 통계 반환
        """
        mappable_count = sum(1 for is_mappable in self.mapping_cache.values() if is_mappable)
        unmappable_count = len(self.mapping_cache) - mappable_count

        return {
            "total_companies_checked": len(self.mapping_cache),
            "mappable_companies": mappable_count,
            "unmappable_companies": unmappable_count,
            "mapping_rate": round(mappable_count / len(self.mapping_cache) * 100, 2) if self.mapping_cache else 0
        }

    def _save_job_posting(self, company_id: int, job_data: Dict[str, Any]) -> Optional[int]:
        try:
            existing_job = self.db_session.query(JobPosting).filter_by(
                saramin_job_id=job_data['saramin_job_id']
            ).first()

            if existing_job:
                existing_job.saramin_job_title = job_data['saramin_job_title']
                existing_job.work_location = job_data.get('work_location')
                existing_job.career_info = job_data.get('career_info')
                existing_job.education_requirement = job_data.get('education_requirement')
                existing_job.salary_info = job_data.get('salary_info')
                existing_job.application_deadline = job_data.get('application_deadline')
                existing_job.is_hot = job_data.get('is_hot', False)
                existing_job.updated_at = datetime.now()

                self.db_session.flush()
                return existing_job.job_id
            else:
                job_posting = JobPosting(
                    company_id=company_id,
                    saramin_job_id=job_data['saramin_job_id'],
                    saramin_job_title=job_data['saramin_job_title'],
                    saramin_job_url=job_data['saramin_job_url'],
                    work_location=job_data.get('work_location'),
                    career_info=job_data.get('career_info'),
                    education_requirement=job_data.get('education_requirement'),
                    salary_info=job_data.get('salary_info'),
                    posting_date=job_data.get('posting_date'),
                    application_deadline=job_data.get('application_deadline'),
                    registration_info=job_data.get('registration_info'),
                    is_hot=job_data.get('is_hot', False)
                )
                self.db_session.add(job_posting)
                self.db_session.flush()
                return job_posting.job_id

        except IntegrityError as e:
            self.logger.warning(f"중복된 채용공고: {job_data['saramin_job_id']}")
            self.db_session.rollback()
            return None
        except Exception as e:
            self.logger.error(f"채용공고 저장 실패: {e}")
            raise

    def _save_job_sectors_mapping(self, job_id: int, sectors: List[str]):
        try:
            for idx, sector_name in enumerate(sectors):
                if not sector_name:
                    continue

                sector = self.db_session.query(JobSector).filter_by(
                    sector_name=sector_name
                ).first()

                if not sector:
                    sector = JobSector(sector_name=sector_name)
                    self.db_session.add(sector)
                    self.db_session.flush()

                existing_mapping = self.db_session.query(JobPostingSector).filter_by(
                    job_id=job_id,
                    sector_id=sector.sector_id
                ).first()

                if not existing_mapping:
                    mapping = JobPostingSector(
                        job_id=job_id,
                        sector_id=sector.sector_id,
                        is_primary=(idx == 0)
                    )
                    self.db_session.add(mapping)

            self.db_session.flush()

        except Exception as e:
            self.logger.error(f"직무분야 매핑 저장 실패: {e}")

    def _save_job_regions_mapping(self, job_id: int, location: str):
        try:
            locations = location.split()

            parent_region = None
            for idx, loc_name in enumerate(locations):
                if not loc_name:
                    continue

                region = self.db_session.query(Region).filter_by(
                    region_name=loc_name,
                    parent_region_id=parent_region.region_id if parent_region else None
                ).first()

                if not region:
                    region = Region(
                        region_name=loc_name,
                        parent_region_id=parent_region.region_id if parent_region else None,
                        region_level=idx + 1
                    )
                    self.db_session.add(region)
                    self.db_session.flush()

                parent_region = region

                existing_mapping = self.db_session.query(JobPostingRegion).filter_by(
                    job_id=job_id,
                    region_id=region.region_id
                ).first()

                if not existing_mapping:
                    mapping = JobPostingRegion(
                        job_id=job_id,
                        region_id=region.region_id
                    )
                    self.db_session.add(mapping)

            self.db_session.flush()

        except Exception as e:
            self.logger.error(f"지역 매핑 저장 실패: {e}")

    def _log_crawl_start(self, crawl_type: str, crawl_url: str) -> Optional[int]:
        if not self.db_session:
            return None

        try:
            log = CrawlingLog(
                crawl_type=crawl_type,
                crawl_url=crawl_url,
                crawl_status='running',
                started_at=datetime.now()
            )
            self.db_session.add(log)
            self.db_session.commit()
            return log.log_id
        except Exception as e:
            self.logger.error(f"크롤링 로그 시작 기록 실패: {e}")
            return None

    def _log_crawl_complete(self, log_id: Optional[int], status: str, items_found: int, items_saved: int, error_message: str = None):
        if not self.db_session or not log_id:
            return

        try:
            log = self.db_session.query(CrawlingLog).filter_by(log_id=log_id).first()
            if log:
                log.crawl_status = status
                log.items_found = items_found
                log.items_saved = items_saved
                log.error_message = error_message
                log.completed_at = datetime.now()
                if log.started_at:
                    log.crawl_duration_seconds = int((log.completed_at - log.started_at).total_seconds())
                self.db_session.commit()
        except Exception as e:
            self.logger.error(f"크롤링 로그 완료 기록 실패: {e}")

    def _save_crawl_state(self, crawl_id: str, state: Dict[str, Any]) -> None:
        """크롤링 상태를 Redis에 저장"""
        if not self.redis_client:
            return
        try:
            # 큰 데이터는 제외하고 중요 정보만 저장
            saved_state = {
                'last_page': state.get('last_page'),
                'max_pages': state.get('max_pages'),
                'log_id': state.get('log_id'),
                'updated_at': state.get('updated_at'),
                'job_count': len(state.get('collected_jobs', [])),
                'collected_job_ids': [job.get('saramin_job_id') for job in state.get('collected_jobs', [])[:1000]]  # 최대 1000개만
            }
            self.redis_client.setex(
                f"crawl_state:{crawl_id}",
                86400,  # 24시간 TTL
                json_lib.dumps(saved_state, ensure_ascii=False)
            )
            self.logger.debug(f"크롤링 상태 저장: {crawl_id}, 페이지 {state.get('last_page')}")
        except Exception as e:
            self.logger.warning(f"크롤링 상태 저장 실패: {e}")

    def _load_crawl_state(self, crawl_id: str) -> Optional[Dict[str, Any]]:
        """Redis에서 크롤링 상태 로드"""
        if not self.redis_client:
            return None
        try:
            state_data = self.redis_client.get(f"crawl_state:{crawl_id}")
            if state_data:
                state = json_lib.loads(state_data)
                self.logger.info(f"크롤링 상태 복원: {crawl_id}, 마지막 페이지: {state.get('last_page')}")
                # 이미 수집된 job_id들로 기존 작업 필터링
                state['collected_jobs'] = []  # 실제 jobs는 DB에서 복원
                return state
            return None
        except Exception as e:
            self.logger.warning(f"크롤링 상태 로드 실패: {e}")
            return None

    def _delete_crawl_state(self, crawl_id: str) -> None:
        """Redis에서 크롤링 상태 삭제"""
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(f"crawl_state:{crawl_id}")
            self.logger.debug(f"크롤링 상태 삭제: {crawl_id}")
        except Exception as e:
            self.logger.warning(f"크롤링 상태 삭제 실패: {e}")


# 호환성을 위한 래퍼 함수들
def crawl_saramin_by_conditions(page=1):
    """특정 조건으로 사람인 크롤링"""
    crawler = SaraminCrawler()
    result = crawler.crawl(max_pages=1)

    return {
        'jobs': result.get('jobs', []),
        'recommendations': result.get('recommendations', {}),
        'total_jobs': result.get('total_found', 0),
        'conditions': result.get('conditions', {}),
        'page': page,
        'error': result.get('error') if result.get('status') == 'failed' else None
    }


def crawl_multiple_pages(max_pages=5):
    """여러 페이지를 연속으로 크롤링"""
    crawler = SaraminCrawler()
    result = crawler.crawl(max_pages=max_pages)

    return {
        'jobs': result.get('jobs', []),
        'recommendations': result.get('recommendations', {}),
        'total_jobs': result.get('total_found', 0),
        'pages_crawled': max_pages if result.get('status') == 'success' else 0
    }