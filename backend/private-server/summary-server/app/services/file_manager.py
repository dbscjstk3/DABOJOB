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
    
    def _extract_mapping_id_from_job_id(self, job_id: str) -> int:
        """
        job_id에서 mapping_id 추출

        Args:
            job_id (str): 예: "summary_2_20250925_150658"

        Returns:
            int: mapping_id (예: 2)
        """
        try:
            if job_id.startswith('summary_'):
                return int(job_id.split('_')[1])
            else:
                # fallback: 전체를 숫자로 파싱 시도
                return int(job_id)
        except (ValueError, IndexError) as e:
            logger.error(f"Failed to extract mapping_id from job_id '{job_id}': {e}")
            raise ValueError(f"Invalid job_id format: {job_id}")

    def create_mapping_directory(self, mapping_id: int) -> Path:
        """
        mapping_id 기반으로 standardizer와 동일한 디렉토리 구조 생성

        Args:
            mapping_id (int): 매핑 ID

        Returns:
            Path: 생성된 디렉토리 경로
        """
        try:
            job_path = self.data_root / f"mapping_{mapping_id}"

            # 하위 디렉토리들 생성
            directories = ["raw", "standardized", "summaries", "processed"]

            for dir_name in directories:
                dir_path = job_path / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")

            return job_path

        except Exception as e:
            logger.error(f"Failed to create mapping directory for {mapping_id}: {e}")
            raise

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
            job_id (str): 작업 ID (예: "summary_2_20250925_150658")
            category (str): 카테고리명
            summary (str): 요약 내용
        """
        try:
            # job_id에서 mapping_id 추출 (summary_2_20250925_150658 -> 2)
            mapping_id = self._extract_mapping_id_from_job_id(job_id)

            # standardizer와 동일한 경로 사용: /app/data/jobs/mapping_2/
            job_path = self.create_mapping_directory(mapping_id)
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
    
    def get_summary_results(self, job_id_or_mapping_id: str) -> Dict[str, str]:
        """
        저장된 요약 결과들 조회
        
        Args:
            job_id (str): 작업 ID
            
        Returns:
            dict: {카테고리명: 요약내용}
        """
        try:
            # job_id인지 mapping_id인지 판단해서 경로 결정
            if job_id_or_mapping_id.startswith('summary_') or job_id_or_mapping_id.startswith('test_'):
                # job_id 형태인 경우
                mapping_id = self._extract_mapping_id_from_job_id(job_id_or_mapping_id)
                job_path = self.data_root / f"mapping_{mapping_id}"
            else:
                # 단순 mapping_id인 경우
                job_path = self.data_root / f"mapping_{job_id_or_mapping_id}"

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
            logger.error(f"Failed to get summary results for {job_id_or_mapping_id}: {e}")
            return {}
    
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
    
    def save_summary_files(self, job_id: str, summaries: Dict[str, str]) -> None:
        """
        요약 파일들을 저장
        
        Args:
            job_id (str): 작업 ID
            summaries (dict): 카테고리명과 요약 내용의 딕셔너리
        """
        try:
            job_path = self.create_job_directory(job_id)
            summaries_path = job_path / "summaries"
            
            for category, summary in summaries.items():
                filename = f"{category}_summary.txt"
                file_path = summaries_path / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                
                logger.info(f"Saved summary: {file_path} ({len(summary):,} characters)")
                
        except Exception as e:
            logger.error(f"Failed to save summary files: {e}")
            raise
    
    def update_job_stage(self, job_id: str, stage: str, status: str = "completed") -> None:
        """
        작업 단계 상태 업데이트
        
        Args:
            job_id (str): 작업 ID
            stage (str): 단계명 (raw_extraction, standardization, summarization, re_summarization)
            status (str): 상태 (in_progress, completed, failed)
        """
        try:
            job_path = self.get_job_path(job_id)
            metadata_file = job_path / "summary_metadata.json"
            
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load existing metadata: {e}")
            
            if "stages" not in metadata:
                metadata["stages"] = {}
            
            metadata["stages"][stage] = {
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            job_path.mkdir(parents=True, exist_ok=True)
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Updated job stage for {job_id}: {stage}={status}")
            
        except Exception as e:
            logger.error(f"Failed to update job stage: {e}")
            raise