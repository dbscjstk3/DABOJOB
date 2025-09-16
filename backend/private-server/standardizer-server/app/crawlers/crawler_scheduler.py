import schedule
import time
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .saramin_crawler import SaraminCrawler
from threading import Thread
import signal
import sys


class CrawlerScheduler:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.logger = self._setup_logger()
        self.is_running = False
        self.scheduler_thread = None
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_daily_crawl(self, max_pages: int = 10):
        """일일 크롤링 실행"""
        try:
            self.logger.info(f"일일 크롤링 시작 - {datetime.now()}")
            crawler = SaraminCrawler(db_session=self.db_session)
            result = crawler.crawl(max_pages=max_pages)
            
            if result['status'] == 'success':
                self.logger.info(
                    f"일일 크롤링 완료: {result['total_found']}개 발견, "
                    f"{result['total_saved']}개 저장"
                )
            else:
                self.logger.error(f"일일 크롤링 실패: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"일일 크롤링 실행 중 오류: {str(e)}")
    
    def run_weekly_full_crawl(self, max_pages: int = 50):
        """주간 전체 크롤링 실행"""
        try:
            self.logger.info(f"주간 전체 크롤링 시작 - {datetime.now()}")
            crawler = SaraminCrawler(db_session=self.db_session)
            result = crawler.crawl(max_pages=max_pages)
            
            if result['status'] == 'success':
                self.logger.info(
                    f"주간 전체 크롤링 완료: {result['total_found']}개 발견, "
                    f"{result['total_saved']}개 저장"
                )
            else:
                self.logger.error(f"주간 전체 크롤링 실패: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"주간 전체 크롤링 실행 중 오류: {str(e)}")
    
    def run_immediate_crawl(self, max_pages: int = 5):
        """즉시 크롤링 실행"""
        try:
            self.logger.info(f"즉시 크롤링 시작 - {datetime.now()}")
            crawler = SaraminCrawler(db_session=self.db_session)
            result = crawler.crawl(max_pages=max_pages)
            
            if result['status'] == 'success':
                self.logger.info(
                    f"즉시 크롤링 완료: {result['total_found']}개 발견, "
                    f"{result['total_saved']}개 저장"
                )
                return result
            else:
                self.logger.error(f"즉시 크롤링 실패: {result.get('error')}")
                return result
                
        except Exception as e:
            self.logger.error(f"즉시 크롤링 실행 중 오류: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'jobs': []
            }
    
    def setup_schedule(self):
        """스케줄 설정"""
        schedule.clear()
        
        # 매일 오전 9시에 일일 크롤링 (10페이지)
        schedule.every().day.at("09:00").do(
            lambda: self.run_daily_crawl(max_pages=10)
        )
        
        # 매일 오후 6시에 추가 크롤링 (5페이지)
        schedule.every().day.at("18:00").do(
            lambda: self.run_daily_crawl(max_pages=5)
        )
        
        # 매주 일요일 오전 6시에 전체 크롤링 (50페이지)
        schedule.every().sunday.at("06:00").do(
            lambda: self.run_weekly_full_crawl(max_pages=50)
        )
        
        self.logger.info("크롤링 스케줄 설정 완료")
        self.logger.info("- 일일 크롤링: 매일 09:00, 18:00")
        self.logger.info("- 주간 전체 크롤링: 매주 일요일 06:00")
    
    def _run_scheduler(self):
        """스케줄러 실행 (별도 스레드)"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
            except Exception as e:
                self.logger.error(f"스케줄러 실행 중 오류: {str(e)}")
                time.sleep(60)
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            self.logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.setup_schedule()
        
        # 스케줄러를 별도 스레드에서 실행
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("크롤링 스케줄러가 시작되었습니다.")
    
    def stop(self):
        """스케줄러 중지"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        self.logger.info("크롤링 스케줄러가 중지되었습니다.")
    
    def get_next_jobs(self):
        """다음 예정된 작업 조회"""
        jobs = []
        for job in schedule.get_jobs():
            next_run = job.next_run
            if next_run:
                jobs.append({
                    'job': str(job),
                    'next_run': next_run.isoformat()
                })
        return jobs
    
    def run_blocking(self):
        """블로킹 모드로 스케줄러 실행 (메인 프로세스용)"""
        def signal_handler(sig, frame):
            self.logger.info("종료 신호를 받았습니다. 스케줄러를 중지합니다.")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self.setup_schedule()
        self.is_running = True
        
        self.logger.info("크롤링 스케줄러가 블로킹 모드로 시작되었습니다. (Ctrl+C로 종료)")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                self.logger.info("키보드 인터럽트를 받았습니다.")
                break
            except Exception as e:
                self.logger.error(f"스케줄러 실행 중 오류: {str(e)}")
                time.sleep(60)
        
        self.stop()


# 독립 실행 스크립트
if __name__ == "__main__":
    import sys
    import os
    
    # 상위 디렉토리를 Python 경로에 추가
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from app.database import SessionLocal
    
    # 데이터베이스 세션 생성
    db = SessionLocal()
    
    try:
        # 스케줄러 생성 및 실행
        scheduler = CrawlerScheduler(db_session=db)
        
        # 인자 확인
        if len(sys.argv) > 1:
            if sys.argv[1] == "immediate":
                # 즉시 크롤링 실행
                pages = int(sys.argv[2]) if len(sys.argv) > 2 else 5
                result = scheduler.run_immediate_crawl(max_pages=pages)
                print(f"크롤링 결과: {result}")
            elif sys.argv[1] == "daily":
                # 일일 크롤링 실행
                scheduler.run_daily_crawl()
            elif sys.argv[1] == "weekly":
                # 주간 크롤링 실행
                scheduler.run_weekly_full_crawl()
            else:
                print("사용법: python crawler_scheduler.py [immediate|daily|weekly|schedule]")
                print("  immediate [pages] - 즉시 크롤링 실행")
                print("  daily - 일일 크롤링 실행")
                print("  weekly - 주간 전체 크롤링 실행")
                print("  schedule - 스케줄러 시작 (기본)")
        else:
            # 스케줄러 실행
            scheduler.run_blocking()
            
    finally:
        db.close()