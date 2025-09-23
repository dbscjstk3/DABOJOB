"""
기업 분석 데이터 처리 서비스
Redis에서 해시태그 수신 시 EC2 로컬 파일을 읽어서 DB에 저장 + S3 업로드
"""
import logging
from typing import Dict, Any, Optional
from ..file_manager import FileManager
from ..database import database
from .s3_service import s3_service
from .report_generator import report_generator

logger = logging.getLogger(__name__)

class CompanyProcessor:
    """기업 분석 데이터 처리 클래스"""
    
    async def process_hashtag_completion(self, job_id: int, category: str, hashtags: list) -> bool:
        """
        해시태그 추출 완료 시 기업 분석 데이터 처리
        
        Args:
            job_id: 작업 ID (mapping_id와 동일)
            category: 카테고리 
            hashtags: 해시태그 목록
            
        Returns:
            처리 성공 여부
        """
        try:
            logger.info(f"Processing company analysis for job_id={job_id}, category={category}")
            
            # FileManager로 해당 job_id의 파일 읽기
            file_manager = FileManager(mapping_id=job_id)
            
            # 기업 분석 데이터 추출
            analysis_data = file_manager.get_company_analysis_data()
            
            if not analysis_data:
                logger.warning(f"No analysis data found for job_id={job_id}")
                return False
            
            # DB에 저장
            summary_id = await database.save_company_analysis(job_id, analysis_data)
            
            if summary_id:
                logger.info(f"Successfully saved company analysis for job_id={job_id}, summary_id={summary_id}")
                
                # 해시태그의 summary_id 업데이트
                updated_count = await database.update_hashtags_summary_id(job_id, summary_id)
                logger.info(f"Updated {updated_count} hashtags with summary_id={summary_id}")
                
                # 최종 리포트 생성 및 S3 업로드
                await self._generate_and_upload_report(job_id)
                
                return True
            else:
                logger.error(f"Failed to save company analysis for job_id={job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing company analysis for job_id={job_id}: {e}")
            return False
    
    async def get_company_analysis(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """기업 분석 데이터 조회"""
        try:
            return await database.get_company_analysis(mapping_id)
        except Exception as e:
            logger.error(f"Error getting company analysis for mapping_id={mapping_id}: {e}")
            return None
    
    async def _generate_and_upload_report(self, mapping_id: int):
        """최종 리포트 생성 및 S3 업로드"""
        try:
            logger.info(f"Generating final report for mapping_id={mapping_id}")
            
            # 1. 최종 리포트 생성
            report_data = await report_generator.generate_final_report(mapping_id)
            
            if not report_data:
                logger.error(f"Failed to generate report for mapping_id={mapping_id}")
                return
            
            # 2. S3에 업로드
            s3_key = await s3_service.upload_news_report(mapping_id, report_data)
            
            if s3_key:
                logger.info(f"Successfully uploaded report to S3: {s3_key}")
                
                # 3. 업로드 정보를 DB에 기록 (선택사항)
                # await self._save_upload_info(mapping_id, s3_key)
                
            else:
                logger.error(f"Failed to upload report to S3 for mapping_id={mapping_id}")
                
        except Exception as e:
            logger.error(f"Error generating and uploading report for mapping_id={mapping_id}: {e}")
    
    async def _save_upload_info(self, mapping_id: int, s3_key: str):
        """S3 업로드 정보를 DB에 기록 (선택사항)"""
        # TODO: 필요하다면 업로드 이력 테이블에 기록
        # upload_info = {
        #     'mapping_id': mapping_id,
        #     's3_key': s3_key,
        #     'uploaded_at': datetime.now(),
        #     'status': 'completed'
        # }
        pass

    async def process_hashtag_completion_versioned(self, mapping_id: int, version: int, category: str, hashtags: List[str]):
        """버전별 해시태그 완료 처리 (재요약용)"""
        try:
            logger.info(f"Processing hashtag completion for mapping_id: {mapping_id} v{version}, category: {category}")

            # 버전별 기업 분석 데이터 생성
            analysis_summary = await self._create_versioned_analysis_summary(mapping_id, version)

            if analysis_summary:
                logger.info(f"Successfully created versioned analysis summary for mapping_id: {mapping_id} v{version}")

                # 필요시 S3 업로드 (버전별)
                s3_key = f"analysis_summaries/v{version}/{mapping_id}_analysis.json"
                await self._upload_to_s3(analysis_summary, s3_key)

            else:
                logger.warning(f"Failed to create analysis summary for mapping_id: {mapping_id} v{version}")

        except Exception as e:
            logger.error(f"Error processing versioned hashtag completion: {e}")

    async def _create_versioned_analysis_summary(self, mapping_id: int, version: int) -> Optional[Dict[str, Any]]:
        """버전별 분석 요약 생성"""
        try:
            # 버전별 데이터 조회
            version_data_query = """
            SELECT
                sv.mapping_id,
                sv.version_number,
                cas.business_overview,
                cas.products_service,
                cas.sales_contracts,
                cas.rnd_activities,
                cas.other_notes,
                COUNT(DISTINCT sh.hashtag_id) as total_hashtags,
                COUNT(DISTINCT ns.news_id) as total_news
            FROM summary_versions sv
            LEFT JOIN company_analysis_summaries cas ON sv.version_id = cas.version_id
            LEFT JOIN summary_hashtags sh ON sv.version_id = sh.version_id
            LEFT JOIN news_summaries ns ON sv.version_id = ns.version_id
            WHERE sv.mapping_id = %s AND sv.version_number = %s
            GROUP BY sv.version_id
            """

            async with database.get_connection() as cursor:
                await cursor.execute(version_data_query, (mapping_id, version))
                result = await cursor.fetchone()

                if not result:
                    logger.warning(f"No versioned data found for mapping_id: {mapping_id} v{version}")
                    return None

                # 분석 요약 데이터 구성
                analysis_summary = {
                    "mapping_id": mapping_id,
                    "version": version,
                    "generated_at": datetime.now().isoformat(),
                    "total_hashtags": result[7],
                    "total_news": result[8],
                    "analysis": {
                        "business_overview": result[2] or "No data available",
                        "products_service": result[3] or "No data available",
                        "sales_contracts": result[4] or "No data available",
                        "rnd_activities": result[5] or "No data available",
                        "other_notes": result[6] or "No data available"
                    }
                }

                return analysis_summary

        except Exception as e:
            logger.error(f"Failed to create versioned analysis summary: {e}")
            return None

# 전역 인스턴스
company_processor = CompanyProcessor()