"""
S3 업로드 서비스
reports/ 경로에 뉴스 리포트 업로드
"""
import boto3
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from ..config import config

logger = logging.getLogger(__name__)

class S3Service:
    """S3 업로드 서비스 (A2 프라이빗 EC2용)"""
    
    def __init__(self):
        self.bucket_name = config.S3_BUCKET
        self.region = config.AWS_REGION
        
        # A2 EC2에서는 daboja-bridge-private 프로필 사용
        try:
            # 세션 생성 (프로필 기반)
            session = boto3.Session(profile_name='daboja-bridge-private')
            self.s3_client = session.client('s3', region_name=self.region)
            logger.info("S3 client initialized with daboja-bridge-private profile")
        except Exception as e:
            logger.warning(f"Profile not found, using default credentials: {e}")
            # 프로필이 없으면 기본 credential provider 사용
            self.s3_client = boto3.client('s3', region_name=self.region)
    
    async def upload_news_report(self, mapping_id: int, report_data: Dict[str, Any]) -> Optional[str]:
        """
        뉴스 리포트를 S3에 업로드
        
        Args:
            mapping_id: 매핑 ID 
            report_data: 리포트 데이터
            
        Returns:
            S3 키 (업로드 성공 시) 또는 None (실패 시)
        """
        try:
            # S3 키 생성: reports/{YYYY-MM-DD}/news-report-{mapping_id}.json
            today = datetime.now().strftime('%Y-%m-%d')
            s3_key = f"reports/{today}/news-report-{mapping_id}.json"
            
            # JSON 문자열로 변환
            json_content = json.dumps(report_data, ensure_ascii=False, indent=2)
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'mapping-id': str(mapping_id),
                    'created-at': datetime.now().isoformat(),
                    'content-type': 'news-report'
                }
            )
            
            logger.info(f"Successfully uploaded news report to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return None
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return None
    
    async def upload_daily_summary(self, summary_data: Dict[str, Any]) -> Optional[str]:
        """
        일일 뉴스 요약을 S3에 업로드
        
        Args:
            summary_data: 일일 요약 데이터
            
        Returns:
            S3 키 (업로드 성공 시) 또는 None (실패 시)
        """
        try:
            # S3 키 생성: reports/{YYYY-MM-DD}/daily-news-summary.json
            today = datetime.now().strftime('%Y-%m-%d')
            s3_key = f"reports/{today}/daily-news-summary.json"
            
            # JSON 문자열로 변환
            json_content = json.dumps(summary_data, ensure_ascii=False, indent=2)
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'created-at': datetime.now().isoformat(),
                    'content-type': 'daily-summary'
                }
            )
            
            logger.info(f"Successfully uploaded daily summary to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Error uploading daily summary: {e}")
            return None
    
    def list_reports(self, date_str: str = None) -> List[str]:
        """
        특정 날짜의 리포트 목록 조회
        
        Args:
            date_str: 날짜 (YYYY-MM-DD), None이면 오늘
            
        Returns:
            S3 키 목록
        """
        try:
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d')
                
            prefix = f"reports/{date_str}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []
    
    def get_s3_url(self, s3_key: str) -> str:
        """S3 키를 URL로 변환"""
        return f"s3://{self.bucket_name}/{s3_key}"

# 전역 인스턴스
s3_service = S3Service()