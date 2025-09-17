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
    JobPostingSector, JobPostingRegion, CrawlingLog
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


def parse_job_item(job_item_element):
    """
    개별 채용공고 아이템을 파싱하여 구조화된 데이터로 변환
    """
    if not job_item_element:
        return None

    job_data = {}

    # box_item 찾기 (list_item 안에 있을 수 있음)
    box_item = job_item_element.find('div', class_='box_item')
    if not box_item:
        box_item = job_item_element  # 이미 box_item일 경우

    # 1. 회사 정보 파싱
    company_section = box_item.find('div', class_='col company_nm')
    if company_section:
        # 회사명 (여러 방법으로 시도)
        company_link = company_section.find('a', class_='str_tit')
        if not company_link:
            # 다른 선택자로 시도
            company_link = company_section.find('a')

        company_name = None
        company_url = None

        if company_link:
            company_name = company_link.get_text(strip=True)
            company_url = company_link.get('href')
        else:
            # 링크가 없으면 텍스트만 추출 시도
            company_text = company_section.get_text(strip=True)
            if company_text:
                # 첫 번째 줄만 회사명으로 사용
                company_name = company_text.split('\n')[0].strip()

        job_data['company_name'] = company_name
        job_data['company_url'] = company_url

        # 계열사 정보
        main_corp = company_section.find('span', class_='main_corp')
        job_data['company_group'] = main_corp.get_text(strip=True) if main_corp else None

        # 기업 규모
        stock_info = company_section.find('span', class_='info_stock')
        job_data['company_size'] = stock_info.get_text(strip=True) if stock_info else None

        # company_name이 비어있으면 company_group를 사용 (임시 해결책)
        if not job_data['company_name'] and job_data['company_group']:
            job_data['company_name'] = job_data['company_group']
            job_data['company_group'] = None  # 중복 방지

    # 2. 채용공고 정보 파싱
    notification_section = box_item.find('div', class_='col notification_info')
    if notification_section:
        # 공고 제목
        job_title_link = notification_section.find('a', class_='str_tit')
        if not job_title_link:
            # 다른 구조에서 찾기 (.job_tit a 구조)
            job_tit_section = notification_section.find('div', class_='job_tit')
            if job_tit_section:
                job_title_link = job_tit_section.find('a')

        if job_title_link:
            job_data['job_title'] = job_title_link.get_text(strip=True)
            job_data['job_url'] = job_title_link.get('href')

            # rec_idx 추출 (여러 방법으로 시도)
            rec_idx = job_title_link.get('rec_idx')
            if not rec_idx:
                # href에서 rec_idx 추출
                href = job_title_link.get('href', '')
                rec_match = re.search(r'rec_idx=(\d+)', href)
                if rec_match:
                    rec_idx = rec_match.group(1)
            job_data['job_id'] = rec_idx

        # 직무 분야
        job_sectors = notification_section.find('span', class_='job_sector')
        if job_sectors:
            sectors = [span.get_text(strip=True) for span in job_sectors.find_all('span')]
            # "외" 제거
            sectors = [s for s in sectors if s != '외']
            job_data['job_sectors'] = sectors

        # 특별 태그 (HOT, NEW 등)
        job_badge = notification_section.find('div', class_='job_badge')
        if job_badge:
            badges = []
            hot_badge = job_badge.find('span', class_='hot')
            if hot_badge:
                badges.append('HOT')
            job_data['badges'] = badges

    # 3. 채용 조건 파싱
    recruit_section = box_item.find('div', class_='col recruit_info')
    if recruit_section:
        recruit_items = recruit_section.find_all('li')

        for item in recruit_items:
            # 근무지
            work_place = item.find('p', class_='work_place')
            if work_place:
                job_data['work_location'] = work_place.get_text(strip=True)

            # 경력 및 고용형태
            career = item.find('p', class_='career')
            if career:
                career_text = career.get_text(strip=True)
                job_data['career_requirement'] = career_text

                # 경력과 고용형태 분리
                if '·' in career_text:
                    parts = career_text.split('·')
                    job_data['career'] = parts[0].strip()
                    job_data['employment_type'] = parts[1].strip()

            # 학력
            education = item.find('p', class_='education')
            if education:
                job_data['education_requirement'] = education.get_text(strip=True)

            # 급여
            salary = item.find('p', class_='salary')
            if salary:
                job_data['salary'] = salary.get_text(strip=True)

    # 4. 지원 정보 파싱
    support_section = box_item.find('div', class_='col support_info')
    if support_section:
        # 지원 버튼 정보
        apply_button = support_section.find('button', class_='sri_btn_md')
        if apply_button:
            job_data['apply_type'] = '즉시지원'
        else:
            homepage_apply = support_section.find('a', class_='sri_btn_sm')
            if homepage_apply:
                job_data['apply_type'] = '홈페이지지원'

        # 자소서 문항 버튼
        cover_letter_btn = support_section.find('span', class_='coverLetterLayerBtn')
        if cover_letter_btn:
            job_data['has_cover_letter'] = True
            job_data['cover_letter_id'] = cover_letter_btn.get('data-id')
        else:
            job_data['has_cover_letter'] = False

        support_detail = support_section.find('p', class_='support_detail')
        if support_detail:
            # 마감일
            date_span = support_detail.find('span', class_='date')
            if date_span:
                job_data['deadline'] = date_span.get_text(strip=True)

            # 등록 시간
            deadlines_span = support_detail.find('span', class_='deadlines')
            if deadlines_span:
                job_data['registration_time'] = deadlines_span.get_text(strip=True)

    return job_data


def parse_multiple_jobs(html_content):
    """
    여러 개의 채용공고가 포함된 HTML을 파싱
    list_body 구조와 추천 공고 등 다양한 형태 지원
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []

    # 메인 채용공고 리스트 찾기
    list_body = soup.find('div', class_='list_body')
    if list_body:
        # list_item 찾기
        job_items = list_body.find_all('div', class_='list_item')

        for item in job_items:
            # 추천 공고나 광고 섹션 건너뛰기
            if item.find('div', class_='list_curation_wrap') or item.find('div', class_='theme_jobs_container'):
                continue

            job_data = parse_job_item(item)
            if job_data and job_data.get('job_title'):  # 유효한 채용공고만 추가
                jobs.append(job_data)
    else:
        # 단일 box_item 또는 다른 구조 처리
        job_items = soup.find_all('div', class_='box_item')
        for item in job_items:
            job_data = parse_job_item(item)
            if job_data and job_data.get('job_title'):
                jobs.append(job_data)

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

    def crawl(self, max_pages: int = 5) -> Dict[str, Any]:
        """
        특정 조건으로 사람인 크롤링 (봇 탐지 방지를 위한 Selenium 사용)
        - 대기업 + 코스닥 기업
        - 정규직
        - 국내 기업
        - 페이지당 100개 항목
        """
        try:
            self.initialize()

            self.crawl_log_id = self._log_crawl_start('job_list', self.base_url)

            all_jobs = []
            all_recommendations = {}

            for page in range(1, max_pages + 1):
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

            return {
                'status': 'success',
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
        """채용공고 리스트 로딩 대기"""
        selectors = [
            (By.CLASS_NAME, "box_item"),
            (By.CLASS_NAME, "list_item"),
            (By.CSS_SELECTOR, "div.list_body"),
            (By.CSS_SELECTOR, "[class*='recruit']"),
        ]

        for by, selector in selectors:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                self.logger.info(f"채용공고 요소 발견: {selector}")
                return True
            except TimeoutException:
                continue

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
        """개선된 파싱을 사용한 페이지 크롤링"""
        try:
            # BeautifulSoup으로 파싱
            soup = self.get_page_soup()
            jobs = parse_multiple_jobs(str(soup))

            # 데이터 매핑
            mapped_jobs = []
            for job_data in jobs:
                mapped_data = self._map_job_data(job_data)
                if mapped_data and mapped_data.get('saramin_job_title'):
                    mapped_jobs.append(mapped_data)

            return mapped_jobs

        except Exception as e:
            self.logger.error(f"페이지 파싱 실패: {e}")
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
        """마감일 텍스트를 datetime으로 변환"""
        try:
            if not deadline_text:
                return None

            if '상시' in deadline_text:
                return None

            # ~10.10(금) 또는 ~09.29(월) 형태에서 월.일 추출
            if '~' in deadline_text:
                date_part = deadline_text.split('~')[-1].strip()

                # 정규식으로 월.일 패턴 추출 (요일 정보 무시)
                import re
                match = re.search(r'(\d{1,2})\.(\d{1,2})', date_part)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
                    year = datetime.now().year

                    # 유효한 날짜인지 확인
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        try:
                            return datetime(year, month, day)
                        except ValueError:
                            # 잘못된 날짜 조합 (예: 2월 30일)
                            self.logger.warning(f"잘못된 날짜: {year}-{month}-{day}")
                            return None

        except Exception as e:
            self.logger.warning(f"마감일 파싱 실패: {deadline_text} - {e}")
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