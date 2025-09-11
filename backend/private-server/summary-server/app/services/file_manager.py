"""
파일 관리자 - Summary Server용
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

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
        return self.base_data_path / "jobs" / str(job_id)
    
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
            job_path / "summaries"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        return job_path
    
    def read_categorized_file(self, file_path: str) -> Optional[str]:
        """
        카테고리별 파일 읽기
        
        Args:
            file_path (str): 파일 경로
            
        Returns:
            str: 파일 내용 또는 None
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Read file: {file_path} ({len(content):,} characters)")
            return content
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def save_summary(self, job_id: str, category: str, summary: str) -> None:
        """
        카테고리별 요약 결과 저장
        
        Args:
            job_id (str): 작업 ID
            category (str): 카테고리명
            summary (str): 요약 내용
        """
        try:
            job_path = self.create_job_directory(job_id)
            summaries_path = job_path / "summaries"
            
            # 카테고리별 요약 파일명
            filename = f"{category}_summary.txt"
            file_path = summaries_path / filename
            
            # 요약 결과 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"Saved summary: {file_path} ({len(summary):,} characters)")
            
        except Exception as e:
            logger.error(f"Failed to save summary for {category}: {e}")
            raise
    
    def save_metadata(self, job_id: str, metadata: Dict) -> None:
        """
        메타데이터를 JSON 파일로 저장
        
        Args:
            job_id (str): 작업 ID
            metadata (dict): 저장할 메타데이터
        """
        try:
            job_path = self.get_job_path(job_id)
            job_path.mkdir(parents=True, exist_ok=True)
            
            metadata_file = job_path / "summary_metadata.json"
            
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
            
            logger.info(f"Saved summary metadata for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise
    
    def get_summary_results(self, job_id: str) -> Dict[str, str]:
        """
        저장된 요약 결과들 조회
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            dict: {카테고리명: 요약내용}
        """
        try:
            job_path = self.get_job_path(job_id)
            summaries_path = job_path / "summaries"
            
            if not summaries_path.exists():
                return {}
            
            results = {}
            for file_path in summaries_path.glob("*_summary.txt"):
                category = file_path.stem.replace("_summary", "")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    results[category] = content
                except Exception as e:
                    logger.warning(f"Failed to read summary file {file_path}: {e}")
                    results[category] = f"Error reading file: {e}"
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get summary results for {job_id}: {e}")
            return {}