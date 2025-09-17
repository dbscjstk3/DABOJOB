"""
최종 뉴스 리포트 생성기
5개 txt 파일 + 공고 정보 + DB 뉴스 데이터를 종합해서 JSON 리포트 생성
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..file_manager import FileManager
from ..database import database

logger = logging.getLogger(__name__)

class ReportGenerator:
    """최종 뉴스 리포트 생성기"""
    
    def __init__(self):
        self.chapter_names = {
            1: "사업의 개요",
            2: "주요 제품 및 서비스", 
            3: "매출 및 수주 상황",
            4: "주요 계약 및 연구 개발 활동",
            5: "기타 참고사항"
        }
    
    async def generate_final_report(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """
        최종 뉴스 리포트 생성
        
        Args:
            mapping_id: 매핑 ID
            
        Returns:
            완성된 리포트 데이터 또는 None
        """
        try:
            logger.info(f"Generating final report for mapping_id={mapping_id}")
            
            # 1. 파일 시스템에서 기업 분석 데이터 읽기
            file_manager = FileManager(mapping_id)
            company_summaries = file_manager.read_all_summaries()
            
            if not company_summaries:
                logger.error(f"No company summaries found for mapping_id={mapping_id}")
                return None
            
            # 2. DB에서 기업 분석 데이터 읽기
            company_analysis = await database.get_company_analysis(mapping_id)
            
            # 3. DB에서 해시태그 데이터 읽기
            hashtags_data = await database.get_hashtags_by_mapping(mapping_id)
            
            # 4. DB에서 뉴스 데이터 읽기
            news_data = await database.get_news_by_mapping_id(mapping_id)
            
            # 5. 통계 정보 생성
            stats = await self._generate_statistics(mapping_id, news_data, hashtags_data)
            
            # 6. 최종 리포트 구성
            report = {
                "metadata": {
                    "mapping_id": mapping_id,
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "source": "news-summary-server"
                },
                "company_analysis": {
                    "summary_id": company_analysis.get('summary_id') if company_analysis else 0,
                    "chapters": self._format_company_chapters(company_summaries, company_analysis),
                    "file_sources": self._get_file_sources(file_manager)
                },
                "hashtags": self._format_hashtags_data(hashtags_data),
                "news": {
                    "total_count": len(news_data),
                    "completed_count": len([n for n in news_data if n.get('status') == 'completed']),
                    "by_hashtag": self._group_news_by_hashtag(news_data, hashtags_data),
                    "articles": self._format_news_articles(news_data)
                },
                "statistics": stats
            }
            
            logger.info(f"Successfully generated report for mapping_id={mapping_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report for mapping_id={mapping_id}: {e}")
            return None
    
    def _format_company_chapters(self, summaries: Dict[int, str], 
                                analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """기업 분석 챕터 데이터 포맷팅"""
        chapters = {}
        
        for chapter_num, content in summaries.items():
            chapter_name = self.chapter_names.get(chapter_num, f"Chapter {chapter_num}")
            
            chapters[str(chapter_num)] = {
                "name": chapter_name,
                "content": content,
                "word_count": len(content),
                "has_content": bool(content.strip())
            }
        
        # DB 분석 데이터 추가 (있다면)
        if analysis:
            db_mapping = {
                1: analysis.get('business_overview', ''),
                2: analysis.get('products_service', ''),
                3: analysis.get('sales_contracts', ''),
                4: analysis.get('rnd_activities', ''),
                5: analysis.get('other_notes', '')
            }
            
            for chapter_num, db_content in db_mapping.items():
                if str(chapter_num) in chapters and db_content:
                    chapters[str(chapter_num)]['db_content'] = db_content
        
        return chapters
    
    def _get_file_sources(self, file_manager: FileManager) -> Dict[str, Any]:
        """파일 소스 정보"""
        files = file_manager.list_files()
        return {
            "base_path": str(file_manager.base_path),
            "files": files,
            "total_files": sum(len(file_list) for file_list in files.values())
        }
    
    def _format_hashtags_data(self, hashtags_data: List[Dict]) -> Dict[str, Any]:
        """해시태그 데이터 포맷팅"""
        # 챕터별로 그룹화
        by_chapter = {}
        all_hashtags = []
        
        for hashtag_item in hashtags_data:
            chapter = str(hashtag_item.get('chapter', 'unknown'))
            hashtag = hashtag_item.get('hashtag', '')
            
            if chapter not in by_chapter:
                by_chapter[chapter] = []
            
            by_chapter[chapter].append({
                "hashtag_id": hashtag_item.get('hashtag_id'),
                "hashtag": hashtag,
                "created_at": hashtag_item.get('created_at').isoformat() if hashtag_item.get('created_at') else None
            })
            
            all_hashtags.append(hashtag)
        
        return {
            "total_count": len(hashtags_data),
            "unique_hashtags": len(set(all_hashtags)),
            "by_chapter": by_chapter,
            "all_hashtags": list(set(all_hashtags))
        }
    
    def _group_news_by_hashtag(self, news_data: List[Dict], hashtags_data: List[Dict]) -> Dict[str, Any]:
        """해시태그별 뉴스 그룹화"""
        # hashtag_id로 해시태그 이름 매핑
        hashtag_map = {h.get('hashtag_id'): h.get('hashtag') for h in hashtags_data}
        
        by_hashtag = {}
        
        for news_item in news_data:
            hashtag_id = news_item.get('hashtag_id')
            hashtag_name = hashtag_map.get(hashtag_id, f"hashtag_{hashtag_id}")
            
            if hashtag_name not in by_hashtag:
                by_hashtag[hashtag_name] = {
                    "hashtag_id": hashtag_id,
                    "total_count": 0,
                    "completed_count": 0,
                    "articles": []
                }
            
            by_hashtag[hashtag_name]["total_count"] += 1
            
            if news_item.get('status') == 'completed':
                by_hashtag[hashtag_name]["completed_count"] += 1
            
            by_hashtag[hashtag_name]["articles"].append({
                "news_id": news_item.get('news_id'),
                "title": news_item.get('news_title'),
                "url": news_item.get('news_url'),
                "status": news_item.get('status'),
                "created_at": news_item.get('created_at').isoformat() if news_item.get('created_at') else None
            })
        
        return by_hashtag
    
    def _format_news_articles(self, news_data: List[Dict]) -> List[Dict[str, Any]]:
        """뉴스 기사 데이터 포맷팅"""
        articles = []
        
        for news_item in news_data:
            article = {
                "news_id": news_item.get('news_id'),
                "title": news_item.get('news_title'),
                "url": news_item.get('news_url'),
                "pub_date": news_item.get('news_created_at').isoformat() if news_item.get('news_created_at') else None,
                "content": news_item.get('news_content'),
                "company_name": news_item.get('company_name'),
                "status": news_item.get('status'),
                "hashtag_id": news_item.get('hashtag_id'),
                "created_at": news_item.get('created_at').isoformat() if news_item.get('created_at') else None,
                "updated_at": news_item.get('updated_at').isoformat() if news_item.get('updated_at') else None
            }
            articles.append(article)
        
        # 최신순으로 정렬
        articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return articles
    
    async def _generate_statistics(self, mapping_id: int, news_data: List[Dict], 
                                 hashtags_data: List[Dict]) -> Dict[str, Any]:
        """통계 정보 생성"""
        return {
            "mapping_id": mapping_id,
            "total_chapters": 5,
            "total_hashtags": len(hashtags_data),
            "unique_hashtags": len(set(h.get('hashtag') for h in hashtags_data)),
            "total_news": len(news_data),
            "completed_news": len([n for n in news_data if n.get('status') == 'completed']),
            "raw_news": len([n for n in news_data if n.get('status') == 'raw']),
            "completion_rate": round(
                len([n for n in news_data if n.get('status') == 'completed']) / len(news_data) * 100, 2
            ) if news_data else 0,
            "news_by_chapter": self._get_news_by_chapter_stats(news_data, hashtags_data),
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_news_by_chapter_stats(self, news_data: List[Dict], hashtags_data: List[Dict]) -> Dict[str, int]:
        """챕터별 뉴스 통계"""
        # hashtag_id -> chapter 매핑
        hashtag_chapter_map = {h.get('hashtag_id'): h.get('chapter') for h in hashtags_data}
        
        chapter_stats = {}
        
        for news_item in news_data:
            hashtag_id = news_item.get('hashtag_id')
            chapter = hashtag_chapter_map.get(hashtag_id, 'unknown')
            
            if chapter not in chapter_stats:
                chapter_stats[chapter] = 0
            
            chapter_stats[chapter] += 1
        
        return chapter_stats

# 전역 인스턴스
report_generator = ReportGenerator()