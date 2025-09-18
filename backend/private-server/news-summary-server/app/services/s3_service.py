"""
S3 업로드 서비스
reports/ 경로에 뉴스 리포트 업로드
"""
import boto3
import json
import logging
import os
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
        
        # AWS 자격증명 초기화
        try:
            # 환경변수에서 자격증명 확인
            if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
                # 환경변수로 세션 생성
                session = boto3.Session(
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
                self.s3_client = session.client('s3')
                logger.info("S3 client initialized with environment variables")
            else:
                # 프로필 기반 시도
                try:
                    session = boto3.Session(profile_name='daboja-bridge-private')
                    self.s3_client = session.client('s3', region_name=self.region)
                    logger.info("S3 client initialized with daboja-bridge-private profile")
                except Exception:
                    # 기본 credential provider 사용
                    self.s3_client = boto3.client('s3', region_name=self.region)
                    logger.info("S3 client initialized with default credentials")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {e}")
            self.s3_client = None  # S3 기능 비활성화
    
    async def upload_job_completion_data(self, job_id: int) -> Dict[str, str]:
        """
        job_id 완료 시 4개 JSON 파일을 S3에 업로드

        Args:
            job_id: 작업 ID

        Returns:
            업로드된 파일들의 S3 키 딕셔너리
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available, skipping upload")
                return {}

            # 데이터 수집
            from ..database import database

            companies_data = await self._get_companies_data(job_id)
            job_postings_data = await self._get_job_postings_data(job_id)
            job_sectors_data = await self._get_job_sectors_data(job_id)
            dart_data = await self._get_dart_data(job_id)

            # S3 업로드
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            today = datetime.now().strftime('%Y-%m-%d')
            uploaded_files = {}

            # 4개 파일 업로드
            files_to_upload = [
                ("companies", f"reports/{today}/{job_id}/companies_{timestamp}.json", companies_data),
                ("job_postings", f"reports/{today}/{job_id}/job_postings_{timestamp}.json", job_postings_data),
                ("job_sectors", f"reports/{today}/{job_id}/job_sectors_{timestamp}.json", job_sectors_data),
                ("Dart", f"reports/{today}/{job_id}/Dart_{timestamp}.json", dart_data)
            ]

            for file_type, s3_key, data in files_to_upload:
                uploaded_key = await self._upload_json_to_s3(s3_key, data, job_id)
                if uploaded_key:
                    uploaded_files[file_type] = uploaded_key

            logger.info(f"Successfully uploaded {len(uploaded_files)} files for job {job_id} to S3")
            return uploaded_files

        except Exception as e:
            logger.error(f"Failed to upload job completion data for {job_id}: {e}")
            return {}
    
    async def _get_companies_data(self, job_id: int) -> Dict[str, Any]:
        """회사 정보 조회 (job_postings → companies)"""
        try:
            from ..database import database

            query = """
            SELECT DISTINCT c.company_id, c.company_name, c.company_code
            FROM companies c
            JOIN job_postings jp ON c.company_id = jp.company_id
            WHERE jp.job_id = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                results = await cursor.fetchall()

                companies = []
                for row in results:
                    companies.append({
                        "company_id": row[0],
                        "company_name": row[1],
                        "company_code": row[2]
                    })

                return {
                    "job_id": job_id,
                    "companies": companies,
                    "total_count": len(companies)
                }

        except Exception as e:
            logger.error(f"Error getting companies data for job {job_id}: {e}")
            return {"job_id": job_id, "companies": [], "total_count": 0}

    async def _get_job_postings_data(self, job_id: int) -> Dict[str, Any]:
        """채용공고 정보 조회"""
        try:
            from ..database import database

            query = """
            SELECT job_id, company_id, sector_id, saramin_job_title, saramin_job_url,
                   career_info, posting_date, application_deadline
            FROM job_postings
            WHERE job_id = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                results = await cursor.fetchall()

                postings = []
                for row in results:
                    postings.append({
                        "job_id": row[0],
                        "company_id": row[1],
                        "sector_id": row[2],
                        "saramin_job_title": row[3],
                        "saramin_job_url": row[4],
                        "career_info": row[5],
                        "posting_date": row[6].isoformat() if row[6] else None,
                        "application_deadline": row[7].isoformat() if row[7] else None
                    })

                return {
                    "job_id": job_id,
                    "postings": postings,
                    "total_count": len(postings)
                }

        except Exception as e:
            logger.error(f"Error getting job_postings data for job {job_id}: {e}")
            return {"job_id": job_id, "postings": [], "total_count": 0}

    async def _get_job_sectors_data(self, job_id: int) -> Dict[str, Any]:
        """직무 분야 정보 조회"""
        try:
            from ..database import database

            query = """
            SELECT DISTINCT js.sector_id, js.sector_name, js.sector_category
            FROM job_sectors js
            JOIN job_postings jp ON js.sector_id = jp.sector_id
            WHERE jp.job_id = %s
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                results = await cursor.fetchall()

                sectors = []
                for row in results:
                    sectors.append({
                        "sector_id": row[0],
                        "sector_name": row[1],
                        "sector_category": row[2]
                    })

                return {
                    "job_id": job_id,
                    "sectors": sectors,
                    "total_count": len(sectors)
                }

        except Exception as e:
            logger.error(f"Error getting job_sectors data for job {job_id}: {e}")
            return {"job_id": job_id, "sectors": [], "total_count": 0}

    async def _get_dart_data(self, job_id: int) -> Dict[str, Any]:
        """DART 보고서 요약 + 뉴스 + 해시태그 데이터 조회"""
        try:
            # 1. 로컬 요약 파일들 읽기
            summaries = await self._read_summary_files(job_id)

            # 2. 뉴스 데이터 조회
            news_data = await self._get_news_data(job_id)

            # 3. 해시태그 데이터 조회
            hashtags_data = await self._get_hashtags_data(job_id)

            return {
                "job_id": job_id,
                "dart_summaries": summaries,
                "news": news_data,
                "hashtags": hashtags_data,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting DART data for job {job_id}: {e}")
            return {
                "job_id": job_id,
                "dart_summaries": {},
                "news": {"items": [], "total_count": 0},
                "hashtags": {"categories": [], "total_categories": 0},
                "generated_at": datetime.now().isoformat()
            }

    async def _read_summary_files(self, job_id: int) -> Dict[str, str]:
        """로컬 파일시스템에서 요약 파일들 읽기"""
        summaries = {}
        summary_files = [
            "business_overview_summary.txt",
            "products_services_summary.txt",
            "revenue_orders_summary.txt",
            "contracts_rnd_summary.txt",
            "others_summary.txt"
        ]

        for filename in summary_files:
            try:
                file_path = f"/app/data/jobs/{job_id}/summaries/{filename}"
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        chapter_name = filename.replace('_summary.txt', '')
                        summaries[chapter_name] = content
                else:
                    logger.warning(f"Summary file not found: {file_path}")
                    chapter_name = filename.replace('_summary.txt', '')
                    summaries[chapter_name] = "Summary file not found"
            except Exception as e:
                logger.error(f"Error reading summary file {filename}: {e}")
                chapter_name = filename.replace('_summary.txt', '')
                summaries[chapter_name] = f"Error reading file: {e}"

        return summaries

    async def _get_news_data(self, job_id: int) -> Dict[str, Any]:
        """뉴스 데이터 조회"""
        try:
            from ..database import database

            # 원본 뉴스 조회
            news_query = """
            SELECT rn.news_id, rn.hashtag_id, rn.title, rn.url, rn.published_date,
                   sh.chapter, sh.hashtag
            FROM raw_news rn
            JOIN summary_hashtags sh ON rn.hashtag_id = sh.hashtag_id
            WHERE rn.job_id = %s
            ORDER BY rn.published_date DESC
            """

            # 뉴스 요약 조회
            summary_query = """
            SELECT news_id, summary_content
            FROM news_summaries
            WHERE job_id = %s
            """

            async with database.get_connection() as cursor:
                # 뉴스 데이터 조회
                await cursor.execute(news_query, (job_id,))
                news_results = await cursor.fetchall()

                # 요약 데이터 조회
                await cursor.execute(summary_query, (job_id,))
                summary_results = await cursor.fetchall()

                # 요약 데이터를 딕셔너리로 변환
                summaries = {news_id: summary for news_id, summary in summary_results}

                # 뉴스 아이템 생성
                items = []
                for news_id, hashtag_id, title, url, published_date, chapter, hashtag in news_results:
                    items.append({
                        "news_id": news_id,
                        "hashtag_id": hashtag_id,
                        "title": title,
                        "url": url,
                        "published_date": published_date.isoformat() if published_date else None,
                        "chapter": chapter,
                        "hashtag": hashtag,
                        "summary": summaries.get(news_id, None)
                    })

                return {
                    "items": items,
                    "total_count": len(items)
                }

        except Exception as e:
            logger.error(f"Error getting news data for job {job_id}: {e}")
            return {"items": [], "total_count": 0}

    async def _get_hashtags_data(self, job_id: int) -> Dict[str, Any]:
        """해시태그 데이터 조회"""
        try:
            from ..database import database

            query = """
            SELECT hashtag_id, chapter, hashtag
            FROM summary_hashtags
            WHERE job_id = %s
            ORDER BY chapter, hashtag_id
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                results = await cursor.fetchall()

                # 카테고리별로 그룹화
                categories = {}
                for hashtag_id, chapter, hashtag in results:
                    if chapter not in categories:
                        categories[chapter] = {"category": chapter, "hashtags": []}
                    categories[chapter]["hashtags"].append({
                        "hashtag_id": hashtag_id,
                        "hashtag": hashtag
                    })

                return {
                    "categories": list(categories.values()),
                    "total_categories": len(categories)
                }

        except Exception as e:
            logger.error(f"Error getting hashtags data for job {job_id}: {e}")
            return {"categories": [], "total_categories": 0}

    async def _upload_json_to_s3(self, s3_key: str, data: Dict[str, Any], job_id: int) -> Optional[str]:
        """JSON 데이터를 S3에 업로드"""
        try:
            json_content = json.dumps(data, ensure_ascii=False, indent=2)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'job-id': str(job_id),
                    'created-at': datetime.now().isoformat(),
                    'content-type': 'job-completion-data'
                }
            )

            logger.info(f"Successfully uploaded {s3_key} to S3")
            return s3_key

        except Exception as e:
            logger.error(f"Failed to upload {s3_key} to S3: {e}")
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
            if not self.s3_client:
                logger.warning("S3 client not available, skipping upload")
                return None

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
    
    def list_reports(self, date_str: Optional[str] = None) -> List[str]:
        """
        특정 날짜의 리포트 목록 조회
        
        Args:
            date_str: 날짜 (YYYY-MM-DD), None이면 오늘
            
        Returns:
            S3 키 목록
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available, returning empty list")
                return []

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