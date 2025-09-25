"""
S3 업로드 서비스
reports/ 경로에 뉴스/분석 리포트 업로드
- companies.json: flat 단일 객체
- job_postings.json: flat 단일 객체
- job_sectors.json: flat 단일 객체
- Dart.json: 요약 파일 + 뉴스(요약/해시태그 정합) + 해시태그
"""
import boto3
import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from ..config import config
from ..database import database

logger = logging.getLogger(__name__)

class S3Service:
    """S3 업로드 서비스 (A2 프라이빗 EC2용)"""
    
    CHAPTER_MAP: Dict[str, Tuple[str, str]] = {
        "business_overview": ("1", "사업의 개요"),
        "products_services": ("2", "주요 제품 및 서비스"),
        "revenue_orders": ("3", "매출 및 수주 상황"),
        "contracts_rnd": ("4", "주요 계약 및 연구 개발 활동"),
        "others": ("5", "기타 참고사항"),
    }
    
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
    
    # ----------------------------------------------------------------------
    # 메인: 기존처럼 4개의 JSON 업로드 (companies/job_postings/job_sectors/Dart)
    # ----------------------------------------------------------------------
    async def upload_job_completion_data(self, job_id: int) -> Dict[str, str]:
        """
        job_id 완료 시 4개 JSON 파일을 S3에 업로드
        - companies: 평평한(flat) 단일 객체 (배열 아님)
        - job_postings: 공고 목록
        - job_sectors: 직무/분야 목록
        - Dart: 파일 요약 + 뉴스 + 해시태그
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
    
    # ----------------------------------------------------------------------
    # 개별 데이터 수집 함수들
    # ----------------------------------------------------------------------
    async def _get_companies_data(self, job_id: int) -> Dict[str, Any]:
        """
        회사 정보 조회 (job_postings → companies)
        - 과거 배열 구조 대신 flat 단일 객체 반환
        {
          "job_id": 1,
          "company_id": 1,
          "company_name": "...",
          "company_scale": "대기업"
        }
        """
        try:
            from ..database import database

            query = """
            SELECT DISTINCT c.company_id,
                            c.company_name,
                            COALESCE(c.company_scale, '') AS company_scale
            FROM companies c
            JOIN job_postings jp ON c.company_id = jp.company_id
            WHERE jp.job_id = %s
            LIMIT 1
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                row = await cursor.fetchone()

                if row:
                    return {
                        "job_id": job_id,
                        "company_id": row[0],
                        "company_name": row[1],
                        "company_scale": row[2]
                    }

                return {
                    "job_id": job_id,
                    "company_id": None,
                    "company_name": "",
                    "company_scale": "",
                }

        except Exception as e:
            logger.error(f"Error getting companies data for job {job_id}: {e}")
            return {
                "job_id": job_id,
                "company_id": None,
                "company_name": "",
                "company_scale": "",
            }


    async def _get_job_postings_data(self, job_id: int) -> Dict[str, Any]:
        """채용공고 정보 조회"""
        try:
            from ..database import database

            # sector_id가 job_postings에 직접 없을 수 있어 안전하게 NULL 허용
            query = """
            SELECT job_id, company_id,
                IFNULL((SELECT sector_id FROM job_posting_sectors jps
                        WHERE jps.job_id = jp.job_id LIMIT 1), NULL) AS sector_id,
                saramin_job_title, saramin_job_url,
                career_info, posting_date, application_deadline
            FROM job_postings jp
            WHERE job_id = %s
            LIMIT 1
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                row = await cursor.fetchone()

                if row:
                    return {
                        "job_id": row[0],
                        "company_id": row[1],
                        "sector_id": row[2],
                        "saramin_job_title": row[3],
                        "saramin_job_url": row[4],
                        "career_info": row[5],
                        "posting_date": row[6].isoformat() if row[6] else None,
                        "application_deadline": row[7].isoformat() if row[7] else None,
                    }

                # 결과가 없으면 빈 값 반환
                return {
                    "job_id": job_id,
                    "company_id": None,
                    "sector_id": None,
                    "saramin_job_title": "",
                    "saramin_job_url": "",
                    "career_info": "",
                    "posting_date": None,
                    "application_deadline": None,
                }

        except Exception as e:
            logger.error(f"Error getting job_postings data for job {job_id}: {e}")
            return {
                "job_id": job_id,
                "company_id": None,
                "sector_id": None,
                "saramin_job_title": "",
                "saramin_job_url": "",
                "career_info": "",
                "posting_date": None,
                "application_deadline": None,
            }

    async def _get_job_sectors_data(self, job_id: int) -> Dict[str, Any]:
        """직무 분야 정보 조회"""
        try:
            from ..database import database

            query = """
            SELECT DISTINCT js.sector_id, js.sector_name, js.sector_category
            FROM job_sectors js
            JOIN job_posting_sectors jps ON js.sector_id = jps.sector_id
            WHERE jps.job_id = %s
            LIMIT 1
            """

            async with database.get_connection() as cursor:
                await cursor.execute(query, (job_id,))
                row = await cursor.fetchone()

            if row:
                return {
                    "job_id": job_id,
                    "sector_id": row[0],
                    "sector_name": row[1],
                    "sector_category": row[2]
                }

            # 결과 없을 때 기본 값
            return {
                "job_id": job_id,
                "sector_id": None,
                "sector_name": "",
                "sector_category": ""
            }

        except Exception as e:
            logger.error(f"Error getting job_sectors data for job {job_id}: {e}")
            return {
                "job_id": job_id,
                "sector_id": None,
                "sector_name": "",
                "sector_category": ""
            }

    async def _get_dart_data(self, job_id: int) -> Dict[str, Any]:
        """DART 보고서 요약 + 뉴스 + 해시태그 데이터 조회"""
        try:
            # 1. 로컬 요약 파일들 읽기
            summaries = await self._read_summary_files(job_id)

            # 2. 뉴스 데이터 조회
            news_data = await self._get_news_data_integrated(job_id)

            # 3. 해시태그 데이터 조회
            hashtags_data = await self._get_hashtags_data(job_id)

            return {
                "job_id": job_id,
                "company_id": news_data.get("company_id"),
                "dart_summaries": summaries,
                "news": news_data["news"],
                "hashtags": hashtags_data,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting DART data for job {job_id}: {e}")
            return {
                "job_id": job_id,
                "company_id": None,
                "dart_summaries": {},
                "news": {"items": [], "total_count": 0, "completed_count": 0, "by_hashtag": {}},
                "hashtags": {"categories": [], "total_categories": 0},
                "generated_at": datetime.now().isoformat(),
            }
    
    # ----------------------------------------------------------------------
    # 내부 헬퍼: 파일/뉴스/해시태그
    # ----------------------------------------------------------------------        
    async def _read_summary_files(self, job_id: int) -> Dict[str, str]:
        """로컬 파일시스템에서 요약 파일들 읽기"""
        summaries: Dict[str, str] = {}
        summary_files = [
            "business_overview_summary.txt",
            "products_services_summary.txt",
            "revenue_orders_summary.txt",
            "contracts_rnd_summary.txt",
            "others_summary.txt",
        ]

        for filename in summary_files:
            try:
                mapping_id = await database.get_mapping_id_by_job_id(job_id)
                file_path = f"/app/data/mapping/{mapping_id}/summaries/{filename}"
                chapter_name = filename.replace("_summary.txt", "")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        summaries[chapter_name] = f.read()
                else:
                    logger.warning(f"Summary file not found: {file_path}")
                    summaries[chapter_name] = "Summary file not found"
            except Exception as e:
                logger.error(f"Error reading summary file {filename}: {e}")
                summaries[chapter_name] = f"Error reading file: {e}"

        return summaries

    async def _get_news_data_integrated(self, job_id: int) -> Dict[str, Any]:
        """
        raw_news 없이 news_summaries만으로 뉴스/요약/카운트/태그별 묶기 생성
        반환:
        {
          "company_id": 1 or None,
          "news": {
            "items": [...],
            "total_count": N,
            "completed_count": M,
            "by_hashtag": {
              "#태그": { "hashtag_id": x, "total_count": n, "completed_count": m, "articles": [...] }
            }
          }
        }
        """
        from ..database import database

        # company_id 추출
        company_q = """
        SELECT c.company_id
        FROM companies c
        JOIN job_postings jp ON c.company_id = jp.company_id
        WHERE jp.job_id = %s
        LIMIT 1
        """
        company_id = None
        async with database.get_connection() as cur:
            await cur.execute(company_q, (job_id,))
            r = await cur.fetchone()
            if r:
                company_id = r[0]

        # 뉴스 본문/요약/상태
        news_q = """
        SELECT
        n.news_id, n.hashtag_id, n.news_title, n.news_url, n.news_created_at,
        n.news_content, n.company_name, n.status,
        sh.hashtag, sh.chapter
        FROM news_summaries n
        JOIN summary_hashtags sh
        ON sh.hashtag_id = n.hashtag_id
        AND sh.mapping_id = n.mapping_id    -- ✅ 같은 mapping 범위 보장
        WHERE n.mapping_id = (
            SELECT mapping_id FROM job_processing WHERE job_id = %s
        )
        ORDER BY FIELD(sh.chapter,'business_overview','products_services','revenue_orders','contracts_rnd','others'),
                sh.hashtag_id,
                n.news_created_at DESC, n.news_id DESC
        """

        items: List[Dict[str, Any]] = []
        total_count = 0
        completed_count = 0
        by_hashtag: Dict[str, Dict[str, Any]] = {}

        async with database.get_connection() as cur:
            await cur.execute(news_q, (job_id,))
            rows = await cur.fetchall()
            for (news_id, hid, title, url, created_at,
                 content, comp_name, status, hash_text, chapter) in rows:
                total_count += 1
                if status == "completed":
                    completed_count += 1

                # 정규화된 태그 키 (# 접두사 보장)
                tag_key = hash_text if hash_text.startswith("#") else f"#{hash_text}"

                if tag_key not in by_hashtag:
                    by_hashtag[tag_key] = {
                        "hashtag_id": int(hid),
                        "total_count": 0,
                        "completed_count": 0,
                        "articles": [],
                    }

                by_hashtag[tag_key]["total_count"] += 1
                if status == "completed":
                    by_hashtag[tag_key]["completed_count"] += 1

                item = {
                    "news_id": int(news_id),
                    "hashtag_id": int(hid),
                    "title": title,
                    "url": url,
                    "published_date": created_at.isoformat() if created_at else None,
                    "chapter": chapter,
                    "hashtag": hash_text,
                    "summary": content,            # news_content를 요약으로 사용
                    "company_name": comp_name,
                    "status": status,
                }
                items.append(item)

        news_block = {
            "items": items,
            "total_count": total_count,
            "completed_count": completed_count,
            "by_hashtag": by_hashtag,
        }
        
        return {"company_id": company_id, "news": news_block}
    
    
    
    async def _get_hashtags_data(self, job_id: int) -> Dict[str, Any]:
        """해시태그 데이터 조회 (카테고리=chapter별 그룹)"""
        try:
            from ..database import database

            query = """
            SELECT hashtag_id, chapter, hashtag
            FROM summary_hashtags
            WHERE job_id = %s
            ORDER BY FIELD(chapter,'business_overview','products_services','revenue_orders','contracts_rnd','others'),
         hashtag_id
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