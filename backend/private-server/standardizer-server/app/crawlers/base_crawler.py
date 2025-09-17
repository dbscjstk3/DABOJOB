from abc import ABC, abstractmethod
import time
import random
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os
from datetime import datetime


class BaseCrawler(ABC):
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self.driver: Optional[webdriver.Chrome] = None
        self.logger = self._setup_logger()
        os.makedirs(output_dir, exist_ok=True)
    
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
    
    def _setup_driver(self) -> webdriver.Chrome:
        options = Options()
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-web-security')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--lang=ko_KR')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')  # Docker 환경에서는 헤드리스 모드
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_settings.popups': 0
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Docker 환경에서는 ChromeDriverManager 대신 시스템 설치된 크롬 사용
        try:
            # Docker 환경 체크
            if os.path.exists('/usr/bin/google-chrome'):
                options.binary_location = '/usr/bin/google-chrome'
                # chromium-driver 경로 찾기
                chromedriver_path = None
                possible_paths = ['/usr/bin/chromedriver', '/usr/lib/chromium/chromedriver']
                for path in possible_paths:
                    if os.path.exists(path):
                        chromedriver_path = path
                        break
                
                if chromedriver_path:
                    from selenium.webdriver.chrome.service import Service as ChromeService
                    service = ChromeService(executable_path=chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    # chromedriver 경로를 지정하지 않고 시도
                    driver = webdriver.Chrome(options=options)
            else:
                # 로컬 환경에서는 ChromeDriverManager 사용
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self.logger.error(f"Chrome 드라이버 초기화 실패: {e}")
            raise
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(30)
        
        return driver
    
    def initialize(self):
        self.driver = self._setup_driver()
        self.logger.info("크롤러 초기화 완료")
        
    def cleanup(self):
        if self.driver:
            self.driver.quit()
            self.logger.info("크롤러 리소스 정리 완료")
    
    def natural_scroll(self):
        if not self.driver:
            return
            
        scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        
        while current_position < scroll_height:
            scroll_amount = random.randint(300, 800)
            current_position += scroll_amount
            
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            self.wait_random(0.5, 1.5)
            
            new_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_scroll_height > scroll_height:
                scroll_height = new_scroll_height
    
    def wait_random(self, min_seconds: float = 1, max_seconds: float = 3):
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)
    
    def wait_for_element(self, by: By, selector: str, timeout: int = 10) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            return False
    
    def get_page_soup(self) -> BeautifulSoup:
        if not self.driver:
            raise RuntimeError("Driver not initialized")
        return BeautifulSoup(self.driver.page_source, 'html.parser')
    
    @abstractmethod
    def crawl(self, **kwargs) -> Dict[str, Any]:
        pass