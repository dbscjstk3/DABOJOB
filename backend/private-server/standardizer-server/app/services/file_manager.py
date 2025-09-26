import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_data_path: str = "/app/data"):
        """
        파일 관리자 초기화
        
        Args:
            base_data_path (str): 데이터 저장 기본 경로
        """
        self.base_data_path = Path(base_data_path)
        self.base_data_path.mkdir(parents=True, exist_ok=True)
    
    def get_job_path(self, job_id: str) -> Path:
        """job_id에 해당하는 디렉토리 경로 반환"""
        return self.base_data_path / "mapping" / str(job_id)
    
    def create_job_directory(self, job_id: str) -> Path:
        """
        job_id에 해당하는 디렉토리 구조 생성
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            Path: 생성된 job 디렉토리 경로
        """
        job_path = self.get_job_path(job_id)
        
        # 디렉토리 구조 생성
        directories = [
            job_path,
            job_path / "raw",
            job_path / "standardized", 
            job_path / "summaries",
            job_path / "processed"
        ]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            else:
                logger.debug(f"Directory already exists: {directory}")
        
        return job_path
    
    def save_metadata(self, job_id: str, metadata: Dict) -> None:
        """
        메타데이터를 JSON 파일로 저장
        
        Args:
            job_id (str): 작업 ID
            metadata (dict): 저장할 메타데이터
        """
        job_path = self.get_job_path(job_id)
        job_path.mkdir(parents=True, exist_ok=True)
        
        metadata_file = job_path / "metadata.json"
        
        # 기존 메타데이터가 있으면 병합
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                existing_metadata.update(metadata)
                metadata = existing_metadata
            except Exception as e:
                logger.warning(f"Failed to load existing metadata: {e}")
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Saved metadata for job {job_id}")
    
    def load_metadata(self, job_id: str) -> Optional[Dict]:
        """
        메타데이터 로드
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            dict: 메타데이터 또는 None
        """
        metadata_file = self.get_job_path(job_id) / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata for job {job_id}: {e}")
            return None
    
    def save_raw_files(self, job_id: str, files: Dict[str, str]) -> None:
        """
        원본 파일들을 저장
        
        Args:
            job_id (str): 작업 ID
            files (dict): 파일명과 내용의 딕셔너리
        """
        job_path = self.create_job_directory(job_id)
        raw_path = job_path / "raw"
        
        for filename, content in files.items():
            file_path = raw_path / filename
            
            # 파일이 이미 존재하면 덮어쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved raw file: {file_path} ({len(content):,} characters)")
    
    def save_standardized_files(self, job_id: str, chapters: Dict[str, str]) -> None:
        """
        표준화된 챕터별 파일들을 저장
        
        Args:
            job_id (str): 작업 ID
            chapters (dict): 챕터명과 내용의 딕셔너리
        """
        job_path = self.create_job_directory(job_id)
        standardized_path = job_path / "standardized"
        
        chapter_mapping = {
            "1. 사업의 개요": "chapter_1_business.txt",
            "2. 주요 제품 및 서비스": "chapter_2_products.txt", 
            "3. 원재료 및 생산설비": "chapter_3_revenue.txt",
            "4. 매출 및 수주현황": "chapter_4_contracts.txt"
        }
        
        for chapter_title, content in chapters.items():
            # 챕터 매핑에서 파일명 찾기
            filename = chapter_mapping.get(chapter_title)
            
            if not filename:
                # 매핑에 없으면 제목을 파일명으로 변환
                safe_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"chapter_{safe_title.replace(' ', '_')}.txt"
            
            file_path = standardized_path / filename
            
            # 파일이 이미 존재하면 덮어쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved standardized file: {file_path} ({len(content):,} characters)")
    
    def save_categorized_files(self, job_id: str, categorized_chapters: Dict[str, List[str]]) -> None:
        """
        카테고리별로 분류된 챕터들을 파일에 저장 (append 방식)
        
        Args:
            job_id (str): 작업 ID
            categorized_chapters (dict): {카테고리명: [챕터 내용 리스트]}
        """
        job_path = self.create_job_directory(job_id)
        standardized_path = job_path / "standardized"
        
        # 5개 카테고리 파일명 매핑
        category_files = {
            'business_overview': 'business_overview.txt',
            'products_services': 'products_services.txt',
            'revenue_orders': 'revenue_orders.txt',
            'contracts_rnd': 'contracts_rnd.txt',
            'other_references': 'other_references.txt'
        }
        
        for category, contents in categorized_chapters.items():
            if category not in category_files:
                logger.warning(f"Unknown category: {category}, skipping")
                continue
            
            file_path = standardized_path / category_files[category]
            
            # 파일에 append (이미 존재하면 이어서 쓰기)
            mode = 'a' if file_path.exists() else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                for content in contents:
                    f.write(content)
                    # 각 챕터 사이에 구분선 추가
                    f.write('\n' + '='*80 + '\n')
            
            total_chars = sum(len(c) for c in contents)
            logger.info(f"Saved to {category} file: {file_path} ({len(contents)} chapters, {total_chars:,} total characters)")
    
    def append_to_category_file(self, job_id: str, category: str, title: str, content: str) -> None:
        """
        특정 카테고리 파일에 챕터 내용 추가
        
        Args:
            job_id (str): 작업 ID
            category (str): 카테고리명 (business_overview, products_services, ...)
            title (str): 챕터 제목
            content (str): 챕터 내용
        """
        job_path = self.create_job_directory(job_id)
        standardized_path = job_path / "standardized"
        
        # 카테고리별 파일명
        category_files = {
            'business_overview': 'business_overview.txt',
            'products_services': 'products_services.txt',
            'revenue_orders': 'revenue_orders.txt',
            'contracts_rnd': 'contracts_rnd.txt',
            'other_references': 'other_references.txt'
        }
        
        if category not in category_files:
            logger.warning(f"Unknown category: {category}, defaulting to other_references")
            category = 'other_references'
        
        file_path = standardized_path / category_files[category]
        
        # 파일에 append
        mode = 'a' if file_path.exists() else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            # 챕터 제목과 내용 작성
            f.write(f"\n\n=== {title} ===\n\n")
            f.write(content)
            f.write('\n' + '='*80 + '\n')
        
        logger.info(f"Appended chapter '{title}' to {category} file: {file_path} ({len(content):,} characters)")
    
    def save_summary_files(self, job_id: str, summaries: Dict[str, str]) -> None:
        """
        요약 파일들을 저장
        
        Args:
            job_id (str): 작업 ID
            summaries (dict): 챕터명과 요약 내용의 딕셔너리
        """
        job_path = self.create_job_directory(job_id)
        summaries_path = job_path / "summaries"
        
        for chapter_title, summary in summaries.items():
            # 파일명 생성
            safe_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"chapter_{safe_title.replace(' ', '_')}_summary.txt"
            
            file_path = summaries_path / filename
            
            # 파일이 이미 존재하면 덮어쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"Saved summary file: {file_path} ({len(summary):,} characters)")
    
    def job_exists(self, job_id: str) -> bool:
        """
        job_id에 해당하는 작업이 존재하는지 확인
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            bool: 작업 존재 여부
        """
        return self.get_job_path(job_id).exists()
    
    def list_jobs(self) -> List[str]:
        """
        모든 job_id 목록 반환
        
        Returns:
            list: job_id 목록
        """
        jobs_path = self.base_data_path / "mapping"
        if not jobs_path.exists():
            return []
        
        return [d.name for d in jobs_path.iterdir() if d.is_dir()]
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        작업 상태 조회
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            dict: 작업 상태 정보
        """
        if not self.job_exists(job_id):
            return None
        
        job_path = self.get_job_path(job_id)
        metadata = self.load_metadata(job_id)
        
        # 각 단계별 파일 존재 여부 확인
        status = {
            "job_id": job_id,
            "exists": True,
            "raw_files": len(list((job_path / "raw").glob("*"))) if (job_path / "raw").exists() else 0,
            "standardized_files": len(list((job_path / "standardized").glob("*"))) if (job_path / "standardized").exists() else 0,
            "summary_files": len(list((job_path / "summaries").glob("*"))) if (job_path / "summaries").exists() else 0,
            "metadata": metadata
        }
        
        return status
    
    def update_job_stage(self, job_id: str, stage: str, status: str = "completed") -> None:
        """
        작업 단계 상태 업데이트
        
        Args:
            job_id (str): 작업 ID
            stage (str): 단계명 (raw_extraction, standardization, summarization)
            status (str): 상태 (in_progress, completed, failed)
        """
        metadata = self.load_metadata(job_id) or {}
        
        if "stages" not in metadata:
            metadata["stages"] = {}
        
        metadata["stages"][stage] = {
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        self.save_metadata(job_id, metadata)
    
    def get_categorized_files(self, job_id: str) -> Dict[str, str]:
        """
        카테고리별 파일 내용 조회
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            dict: {카테고리명: 파일 내용}
        """
        job_path = self.get_job_path(job_id)
        standardized_path = job_path / "standardized"
        
        category_files = {
            'business_overview': 'business_overview.txt',
            'products_services': 'products_services.txt',
            'revenue_orders': 'revenue_orders.txt',
            'contracts_rnd': 'contracts_rnd.txt',
            'other_references': 'other_references.txt'
        }
        
        result = {}
        for category, filename in category_files.items():
            file_path = standardized_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        result[category] = f.read()
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
                    result[category] = None
            else:
                result[category] = None
        
        return result