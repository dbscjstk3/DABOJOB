"""
EC2 파일 시스템 관리
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .config import config

logger = logging.getLogger(__name__)

class FileManager:
    """파일 시스템 관리 클래스"""
    
    def __init__(self, mapping_id: int):
        self.mapping_id = mapping_id
        self.base_path = Path(config.DATA_ROOT) / str(mapping_id)
        
        # 디렉토리 구조
        self.raw_dir = self.base_path / "raw"
        self.standardized_dir = self.base_path / "standardized" 
        self.summaries_dir = self.base_path / "summaries"
        
        # 디렉토리 생성
        self._create_directories()
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        for directory in [self.raw_dir, self.standardized_dir, self.summaries_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")

    def _get_summary_filename(self, chapter: str) -> str:
        """챕터명을 올바른 요약 파일명으로 변환"""
        chapter_mapping = {
            "business_overview": "business_overview_summary.txt",
            "products_services": "products_services_summary.txt",
            "revenue_orders": "revenue_orders_summary.txt",
            "contracts_rnd": "contracts_rnd_summary.txt",
            "others": "others_summary.txt"
        }
        return chapter_mapping.get(chapter, f"{chapter}_summary.txt")
    
    def save_raw_data(self, filename: str, data: str | Dict):
        """원본 데이터 저장"""
        file_path = self.raw_dir / filename
        
        if isinstance(data, dict):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)
                
        logger.info(f"Saved raw data: {file_path}")
        return str(file_path)
    
    def save_standardized_chapter(self, chapter: int, chapter_name: str, content: str) -> str:
        """표준화된 챕터 저장"""
        filename = f"chapter_{chapter}_{chapter_name}.txt"
        file_path = self.standardized_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Saved standardized chapter {chapter}: {file_path}")
        return str(file_path)
    
    def save_summary(self, chapter: str, summary_text: str) -> str:
        """요약 저장"""
        filename = self._get_summary_filename(chapter)
        file_path = self.summaries_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        logger.info(f"Saved summary for chapter {chapter}: {file_path}")
        return str(file_path)
    
    def read_standardized_chapter(self, chapter: int) -> Optional[str]:
        """표준화된 챕터 읽기"""
        # 파일명 패턴 찾기 (chapter_name이 다를 수 있음)
        pattern = f"chapter_{chapter}_*.txt"
        matching_files = list(self.standardized_dir.glob(pattern))
        
        if not matching_files:
            logger.error(f"No standardized file found for chapter {chapter}")
            return None
            
        file_path = matching_files[0]  # 첫 번째 매칭 파일 사용
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Read standardized chapter {chapter}: {file_path}")
                return content
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None
    
    def read_summary(self, chapter: str) -> Optional[str]:
        """요약 읽기"""
        filename = self._get_summary_filename(chapter)
        file_path = self.summaries_dir / filename

        if not file_path.exists():
            logger.error(f"Summary file not found: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Read summary for chapter {chapter}")
                return content
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None
    
    def read_all_summaries(self) -> Dict[str, str]:
        """모든 요약 읽기"""
        summaries = {}

        chapters = ["business_overview", "products_services", "revenue_orders", "contracts_rnd", "other_references"]
        for chapter in chapters:
            summary = self.read_summary(chapter)
            if summary:
                summaries[chapter] = summary

        logger.info(f"Read {len(summaries)} summaries for mapping_id={self.mapping_id}")
        return summaries
    
    def get_company_analysis_data(self) -> Optional[Dict[str, str]]:
        """기업 분석 데이터를 읽어서 DB 저장 형태로 변환"""
        summaries = self.read_all_summaries()
        
        if not summaries:
            logger.warning(f"No summaries found for mapping_id={self.mapping_id}")
            return None
        
        # 챕터별 매핑
        analysis_data = {
            'business_overview': summaries.get('business_overview', ''),    # 1. 사업의 개요
            'products_service': summaries.get('products_services', ''),     # 2. 주요 제품 및 서비스
            'sales_contracts': summaries.get('revenue_orders', ''),         # 4. 매출 및 수주 상황
            'rnd_activities': summaries.get('contracts_rnd', ''),           # 6. 주요 계약 및 연구 개발 활동
            'other_notes': summaries.get('others', '')                      # 7. 기타 참고사항
        }
        
        # 빈 데이터 체크
        has_data = any(data.strip() for data in analysis_data.values())
        if not has_data:
            logger.warning(f"All summary data is empty for mapping_id={self.mapping_id}")
            return None
            
        logger.info(f"Extracted company analysis data for mapping_id={self.mapping_id}")
        return analysis_data
    
    def get_standardized_file_path(self, chapter: int) -> Optional[str]:
        """표준화된 파일 경로 반환"""
        pattern = f"chapter_{chapter}_*.txt"
        matching_files = list(self.standardized_dir.glob(pattern))
        
        if matching_files:
            return str(matching_files[0])
        return None
    
    def list_files(self) -> Dict[str, List[str]]:
        """모든 파일 목록 반환"""
        files = {
            'raw': [f.name for f in self.raw_dir.glob('*') if f.is_file()],
            'standardized': [f.name for f in self.standardized_dir.glob('*') if f.is_file()],
            'summaries': [f.name for f in self.summaries_dir.glob('*') if f.is_file()]
        }
        return files
    
    def cleanup(self):
        """파일 정리 (테스트용)"""
        import shutil
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
            logger.info(f"Cleaned up files for mapping_id={self.mapping_id}")
    
    @classmethod
    def ensure_data_root(cls):
        """데이터 루트 디렉토리 생성"""
        Path(config.DATA_ROOT).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured data root directory: {config.DATA_ROOT}")

# 챕터명 매핑
CHAPTER_NAMES = {
    1: "business",      # 사업의 개요
    2: "products",      # 주요 제품 및 서비스
    3: "revenue",       # 매출 및 수주 상황
    4: "contracts",     # 주요계약 및 연구개발
    5: "other_references"  # 기타 참고사항 (standardizer, summary와 일치)
}