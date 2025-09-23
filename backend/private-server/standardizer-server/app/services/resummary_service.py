"""
재요약 서비스 - 핵심 비즈니스 로직
완료된 보고서의 품질 관리 및 재요약 처리
"""
import logging
import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from ..database import SessionLocal, get_redis_client
from ..models.resummary_models import (
    SummaryVersion, ResummaryRequest, VersionComparison,
    CompanyAnalysisSummary, SummaryHashtag, NewsSummary
)
from ..models.crawler_models import Company, CompanyDartMapping
from ..shared.status_integration import standardizer_status
from ..shared.status_manager import JobStatus

logger = logging.getLogger(__name__)

class ResummaryService:
    """재요약 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()

    # ==========================================
    # Dashboard & Overview
    # ==========================================

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """관리자 대시보드 요약 정보"""
        try:
            # 전체 완료된 보고서 수
            total_completed = self.db.query(SummaryVersion).filter(
                SummaryVersion.status == 'completed'
            ).count()

            # 검토 필요한 보고서 (quality_score가 null)
            needs_review = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.status == 'completed',
                    SummaryVersion.quality_score.is_(None)
                )
            ).count()

            # 품질 불량 보고서 (quality_score <= 2)
            poor_quality = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.status == 'completed',
                    SummaryVersion.quality_score <= 2
                )
            ).count()

            # 재요약 진행 중
            in_resummary = self.db.query(ResummaryRequest).filter(
                ResummaryRequest.status.in_(['requested', 'processing'])
            ).count()

            # 최근 완료된 보고서 (10개)
            recent_completions = self.db.query(
                SummaryVersion.mapping_id,
                SummaryVersion.version_number,
                SummaryVersion.completed_at,
                SummaryVersion.quality_score,
                SummaryVersion.total_news_count
            ).filter(
                SummaryVersion.status == 'completed'
            ).order_by(desc(SummaryVersion.completed_at)).limit(10).all()

            return {
                "total_completed": total_completed,
                "needs_review": needs_review,
                "poor_quality": poor_quality,
                "in_resummary": in_resummary,
                "recent_completions": [
                    {
                        "mapping_id": r.mapping_id,
                        "version": r.version_number,
                        "completed_at": r.completed_at,
                        "quality_score": r.quality_score,
                        "news_count": r.total_news_count
                    } for r in recent_completions
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            raise

    async def get_completed_reports(
        self,
        quality_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """완료된 보고서 목록 조회"""
        try:
            query = self.db.query(
                SummaryVersion,
                CompanyDartMapping.crawled_company_name,
                CompanyDartMapping.dart_corp_name
            ).join(
                CompanyDartMapping,
                SummaryVersion.mapping_id == CompanyDartMapping.mapping_id
            ).filter(
                SummaryVersion.status == 'completed'
            )

            # 품질 필터 적용
            if quality_filter == "needs_review":
                query = query.filter(SummaryVersion.quality_score.is_(None))
            elif quality_filter == "poor_quality":
                query = query.filter(SummaryVersion.quality_score <= 2)
            elif quality_filter == "good_quality":
                query = query.filter(SummaryVersion.quality_score >= 4)

            # 최신 버전만 조회 (서브쿼리)
            latest_versions = self.db.query(
                SummaryVersion.mapping_id,
                func.max(SummaryVersion.version_number).label('max_version')
            ).filter(
                SummaryVersion.status == 'completed'
            ).group_by(SummaryVersion.mapping_id).subquery()

            query = query.join(
                latest_versions,
                and_(
                    SummaryVersion.mapping_id == latest_versions.c.mapping_id,
                    SummaryVersion.version_number == latest_versions.c.max_version
                )
            )

            results = query.order_by(desc(SummaryVersion.completed_at)).offset(offset).limit(limit).all()

            reports = []
            for sv, company_name, dart_corp_name in results:
                # 재요약 횟수 계산
                resummary_count = self.db.query(ResummaryRequest).filter(
                    ResummaryRequest.mapping_id == sv.mapping_id
                ).count()

                # 품질 상태 결정
                quality_status = self._determine_quality_status(sv.quality_score)

                # 챕터 정보 조회
                chapters = await self._get_chapter_summary(sv.mapping_id, sv.version_number)

                reports.append({
                    "mapping_id": sv.mapping_id,
                    "version_number": sv.version_number,
                    "company_name": company_name,
                    "dart_corp_name": dart_corp_name,
                    "status": sv.status,
                    "quality_score": sv.quality_score,
                    "quality_status": quality_status,
                    "completed_at": sv.completed_at,
                    "total_news_count": sv.total_news_count,
                    "resummary_count": resummary_count,
                    "chapters": chapters
                })

            return reports

        except Exception as e:
            logger.error(f"Failed to get completed reports: {e}")
            raise

    async def get_report_detail(self, mapping_id: int, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """보고서 상세 정보 조회"""
        try:
            # 버전이 지정되지 않으면 최신 버전 사용
            if version is None:
                latest_version = self.db.query(func.max(SummaryVersion.version_number)).filter(
                    and_(
                        SummaryVersion.mapping_id == mapping_id,
                        SummaryVersion.status == 'completed'
                    )
                ).scalar()
                version = latest_version

            if version is None:
                return None

            # 요약 버전 정보 조회
            summary_version = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.mapping_id == mapping_id,
                    SummaryVersion.version_number == version
                )
            ).first()

            if not summary_version:
                return None

            # 회사 정보 조회
            mapping = self.db.query(CompanyDartMapping).filter(
                CompanyDartMapping.mapping_id == mapping_id
            ).first()

            # 상세 요약 내용 조회
            summary_content = self.db.query(CompanyAnalysisSummary).filter(
                CompanyAnalysisSummary.version_id == summary_version.version_id
            ).first()

            # 챕터별 통계
            chapters = await self._get_detailed_chapter_info(mapping_id, version)

            return {
                "mapping_id": mapping_id,
                "version_number": version,
                "company_name": mapping.crawled_company_name if mapping else "Unknown",
                "dart_corp_name": mapping.dart_corp_name if mapping else None,
                "status": summary_version.status,
                "quality_score": summary_version.quality_score,
                "quality_issues": summary_version.quality_issues,
                "admin_notes": summary_version.admin_notes,
                "completed_at": summary_version.completed_at,
                "total_news_count": summary_version.total_news_count,
                "chapters": chapters,
                "summary_content": {
                    "business_overview": summary_content.business_overview if summary_content else None,
                    "products_service": summary_content.products_service if summary_content else None,
                    "sales_contracts": summary_content.sales_contracts if summary_content else None,
                    "rnd_activities": summary_content.rnd_activities if summary_content else None,
                    "other_notes": summary_content.other_notes if summary_content else None,
                } if summary_content else None
            }

        except Exception as e:
            logger.error(f"Failed to get report detail: {e}")
            raise

    # ==========================================
    # Quality Review
    # ==========================================

    async def review_report_quality(
        self,
        mapping_id: int,
        version: Optional[int] = None,
        quality_score: int = None,
        quality_issues: List[str] = None,
        admin_notes: Optional[str] = None,
        action: str = "approve"
    ) -> Dict[str, Any]:
        """보고서 품질 검토"""
        try:
            # 최신 버전 가져오기
            if version is None:
                version = self.db.query(func.max(SummaryVersion.version_number)).filter(
                    SummaryVersion.mapping_id == mapping_id
                ).scalar()

            summary_version = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.mapping_id == mapping_id,
                    SummaryVersion.version_number == version
                )
            ).first()

            if not summary_version:
                raise ValueError(f"Summary version not found: {mapping_id} v{version}")

            # 품질 정보 업데이트
            summary_version.quality_score = quality_score
            summary_version.quality_issues = quality_issues
            summary_version.admin_notes = admin_notes

            # 액션별 처리
            if action == "approve":
                # 승인: 상태 유지, 품질 점수만 기록
                pass
            elif action == "archive":
                # 아카이브: 상태 변경
                summary_version.status = 'archived'
            elif action == "resummary":
                # 재요약: 별도 프로세스에서 처리
                pass

            self.db.commit()

            return {
                "version_id": summary_version.version_id,
                "version": version,
                "action": action,
                "quality_score": quality_score
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to review report quality: {e}")
            raise

    async def get_reports_needing_review(self, limit: int = 20) -> List[Dict[str, Any]]:
        """검토가 필요한 보고서 목록"""
        try:
            # quality_score가 null인 완료된 최신 버전 보고서들
            results = self.db.query(
                SummaryVersion,
                CompanyDartMapping.crawled_company_name,
                CompanyDartMapping.dart_corp_name
            ).join(
                CompanyDartMapping,
                SummaryVersion.mapping_id == CompanyDartMapping.mapping_id
            ).filter(
                and_(
                    SummaryVersion.status == 'completed',
                    SummaryVersion.quality_score.is_(None)
                )
            ).order_by(desc(SummaryVersion.completed_at)).limit(limit).all()

            reports = []
            for sv, company_name, dart_corp_name in results:
                chapters = await self._get_chapter_summary(sv.mapping_id, sv.version_number)
                reports.append({
                    "mapping_id": sv.mapping_id,
                    "version_number": sv.version_number,
                    "company_name": company_name,
                    "dart_corp_name": dart_corp_name,
                    "completed_at": sv.completed_at,
                    "total_news_count": sv.total_news_count,
                    "chapters": chapters
                })

            return reports

        except Exception as e:
            logger.error(f"Failed to get reports needing review: {e}")
            raise

    # ==========================================
    # Re-summarization
    # ==========================================

    async def trigger_resummary(
        self,
        mapping_id: int,
        reason: str,
        requested_by: str,
        priority: str = "normal",
        quality_issues: List[str] = None
    ) -> Dict[str, Any]:
        """재요약 요청 트리거"""
        try:
            # 현재 최신 버전 확인
            current_version = self.db.query(func.max(SummaryVersion.version_number)).filter(
                SummaryVersion.mapping_id == mapping_id
            ).scalar()

            if current_version is None:
                raise ValueError(f"No existing summary found for mapping_id: {mapping_id}")

            new_version = current_version + 1

            # 재요약 요청 생성
            resummary_request = ResummaryRequest(
                mapping_id=mapping_id,
                from_version=current_version,
                to_version=new_version,
                requested_by=requested_by,
                request_reason=reason,
                quality_issues=quality_issues,
                status='requested'
            )
            self.db.add(resummary_request)

            # 새 버전 레코드 생성
            new_summary_version = SummaryVersion(
                mapping_id=mapping_id,
                version_number=new_version,
                status='processing',
                requested_by=requested_by,
                request_reason=reason
            )
            self.db.add(new_summary_version)

            self.db.commit()

            # Redis에 재요약 활성 플래그 설정
            await self._set_resummary_active_flag(mapping_id, new_version)

            # 상태 관리자 업데이트
            await standardizer_status.update_mapping_status(
                mapping_id=mapping_id,
                status=JobStatus.MAPPING_VERIFIED  # 재요약을 위해 verified 상태로 롤백
            )

            # 재요약 큐에 추가
            await self._add_to_resummary_queue(mapping_id, new_version, priority)

            # 예상 완료 시간 계산 (평균 처리 시간 기반)
            estimated_completion = await self._calculate_estimated_completion()

            return {
                "request_id": resummary_request.request_id,
                "new_version": new_version,
                "estimated_completion": estimated_completion
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to trigger resummary: {e}")
            raise

    async def get_resummary_status(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """재요약 진행 상태 조회"""
        try:
            # Redis에서 활성 재요약 확인
            active_version = await self.redis_client.get(f"resummary:active:{mapping_id}")
            if not active_version:
                return None

            version = int(active_version.replace('v', ''))

            # DB에서 요청 정보 조회
            resummary_request = self.db.query(ResummaryRequest).filter(
                and_(
                    ResummaryRequest.mapping_id == mapping_id,
                    ResummaryRequest.to_version == version
                )
            ).first()

            if not resummary_request:
                return None

            # 진행률 조회
            progress = await self._get_resummary_progress(mapping_id, version)

            return {
                "mapping_id": mapping_id,
                "current_version": version,
                "status": resummary_request.status,
                "started_at": resummary_request.started_at,
                "progress": progress,
                "estimated_completion": await self._calculate_estimated_completion()
            }

        except Exception as e:
            logger.error(f"Failed to get resummary status: {e}")
            raise

    async def get_resummary_queue(self, status_filter: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """재요약 큐 조회"""
        try:
            query = self.db.query(ResummaryRequest)

            if status_filter:
                query = query.filter(ResummaryRequest.status == status_filter)
            else:
                query = query.filter(ResummaryRequest.status.in_(['requested', 'processing']))

            requests = query.order_by(ResummaryRequest.created_at).limit(limit).all()

            queue = []
            for req in requests:
                queue.append({
                    "request_id": req.request_id,
                    "mapping_id": req.mapping_id,
                    "from_version": req.from_version,
                    "to_version": req.to_version,
                    "status": req.status,
                    "requested_by": req.requested_by,
                    "request_reason": req.request_reason,
                    "created_at": req.created_at,
                    "started_at": req.started_at
                })

            return queue

        except Exception as e:
            logger.error(f"Failed to get resummary queue: {e}")
            raise

    # ==========================================
    # Version Management
    # ==========================================

    async def get_version_history(self, mapping_id: int) -> List[Dict[str, Any]]:
        """버전 이력 조회"""
        try:
            versions = self.db.query(SummaryVersion).filter(
                SummaryVersion.mapping_id == mapping_id
            ).order_by(desc(SummaryVersion.version_number)).all()

            history = []
            for version in versions:
                # 각 버전의 통계 정보
                stats = await self._get_version_statistics(mapping_id, version.version_number)

                history.append({
                    "version_number": version.version_number,
                    "status": version.status,
                    "quality_score": version.quality_score,
                    "created_at": version.created_at,
                    "completed_at": version.completed_at,
                    "requested_by": version.requested_by,
                    "request_reason": version.request_reason,
                    "statistics": stats
                })

            return history

        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            raise

    async def compare_versions(self, mapping_id: int, version1: int, version2: int) -> Dict[str, Any]:
        """버전 간 비교"""
        try:
            # 두 버전의 상세 정보 조회
            v1_info = await self.get_report_detail(mapping_id, version1)
            v2_info = await self.get_report_detail(mapping_id, version2)

            if not v1_info or not v2_info:
                raise ValueError("One or both versions not found")

            # 비교 결과 계산
            comparison = {
                "mapping_id": mapping_id,
                "version_1": version1,
                "version_2": version2,
                "quality_improvement": self._calculate_quality_improvement(v1_info, v2_info),
                "summary_length_diff": self._calculate_summary_length_diff(v1_info, v2_info),
                "news_count_diff": v2_info["total_news_count"] - v1_info["total_news_count"],
                "chapter_improvements": self._compare_chapters(v1_info["chapters"], v2_info["chapters"]),
                "compared_at": datetime.utcnow()
            }

            # 비교 로그 저장
            await self._save_comparison_log(comparison)

            return comparison

        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            raise

    # ==========================================
    # Statistics
    # ==========================================

    async def get_quality_statistics(self, days: int = 30) -> Dict[str, Any]:
        """품질 통계"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 기간 내 완료된 보고서
            completed_reports = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.status == 'completed',
                    SummaryVersion.completed_at >= start_date
                )
            ).all()

            total_reports = len(completed_reports)
            if total_reports == 0:
                return {"message": "No completed reports in the specified period"}

            # 품질 점수 분포
            quality_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "unreviewed": 0}
            quality_scores = []

            for report in completed_reports:
                if report.quality_score is None:
                    quality_distribution["unreviewed"] += 1
                else:
                    quality_distribution[str(report.quality_score)] += 1
                    quality_scores.append(report.quality_score)

            # 평균 품질 점수
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            return {
                "period_days": days,
                "total_reports": total_reports,
                "quality_distribution": quality_distribution,
                "average_quality_score": round(avg_quality, 2),
                "reviewed_percentage": round((len(quality_scores) / total_reports) * 100, 1),
                "high_quality_percentage": round((len([s for s in quality_scores if s >= 4]) / total_reports) * 100, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get quality statistics: {e}")
            raise

    async def get_resummary_statistics(self, days: int = 30) -> Dict[str, Any]:
        """재요약 통계"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 기간 내 재요약 요청
            resummary_requests = self.db.query(ResummaryRequest).filter(
                ResummaryRequest.created_at >= start_date
            ).all()

            total_requests = len(resummary_requests)
            if total_requests == 0:
                return {"message": "No resummary requests in the specified period"}

            # 상태별 분포
            status_distribution = {}
            for req in resummary_requests:
                status_distribution[req.status] = status_distribution.get(req.status, 0) + 1

            # 성공률 계산
            completed_requests = len([r for r in resummary_requests if r.status == 'completed'])
            success_rate = (completed_requests / total_requests) * 100

            # 평균 처리 시간 계산
            processing_times = []
            for req in resummary_requests:
                if req.started_at and req.completed_at:
                    duration = (req.completed_at - req.started_at).total_seconds() / 60  # 분 단위
                    processing_times.append(duration)

            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

            return {
                "period_days": days,
                "total_requests": total_requests,
                "status_distribution": status_distribution,
                "success_rate": round(success_rate, 1),
                "average_processing_time_minutes": round(avg_processing_time, 1),
                "completed_requests": completed_requests
            }

        except Exception as e:
            logger.error(f"Failed to get resummary statistics: {e}")
            raise

    # ==========================================
    # Helper Methods
    # ==========================================

    def _determine_quality_status(self, quality_score: Optional[int]) -> str:
        """품질 상태 결정"""
        if quality_score is None:
            return "needs_review"
        elif quality_score <= 2:
            return "poor_quality"
        elif quality_score <= 3:
            return "needs_improvement"
        else:
            return "good_quality"

    async def _get_chapter_summary(self, mapping_id: int, version: int) -> List[Dict[str, Any]]:
        """챕터별 요약 정보"""
        try:
            # version_id 조회
            summary_version = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.mapping_id == mapping_id,
                    SummaryVersion.version_number == version
                )
            ).first()

            if not summary_version:
                return []

            # 챕터별 해시태그와 뉴스 개수 조회
            chapters = self.db.query(
                SummaryHashtag.chapter,
                func.count(SummaryHashtag.hashtag_id).label('hashtag_count')
            ).filter(
                SummaryHashtag.version_id == summary_version.version_id
            ).group_by(SummaryHashtag.chapter).all()

            chapter_info = []
            for chapter, hashtag_count in chapters:
                # 해당 챕터의 뉴스 개수
                news_count = self.db.query(func.count(NewsSummary.news_id)).join(
                    SummaryHashtag,
                    NewsSummary.hashtag_id == SummaryHashtag.hashtag_id
                ).filter(
                    and_(
                        SummaryHashtag.version_id == summary_version.version_id,
                        SummaryHashtag.chapter == chapter
                    )
                ).scalar() or 0

                chapter_info.append({
                    "chapter": chapter,
                    "hashtag_count": hashtag_count,
                    "news_count": news_count
                })

            return chapter_info

        except Exception as e:
            logger.error(f"Failed to get chapter summary: {e}")
            return []

    async def _get_detailed_chapter_info(self, mapping_id: int, version: int) -> List[Dict[str, Any]]:
        """상세 챕터 정보"""
        # 기본 챕터 정보에 요약 길이 등 추가 정보 포함
        basic_info = await self._get_chapter_summary(mapping_id, version)

        # 요약 내용 길이 정보 추가
        summary_version = self.db.query(SummaryVersion).filter(
            and_(
                SummaryVersion.mapping_id == mapping_id,
                SummaryVersion.version_number == version
            )
        ).first()

        if summary_version:
            summary_content = self.db.query(CompanyAnalysisSummary).filter(
                CompanyAnalysisSummary.version_id == summary_version.version_id
            ).first()

            if summary_content:
                chapter_mapping = {
                    "business_overview": "1",
                    "products_service": "2",
                    "sales_contracts": "4",
                    "rnd_activities": "6",
                    "other_notes": "7"
                }

                for chapter_info in basic_info:
                    chapter = chapter_info["chapter"]
                    for field, chapter_num in chapter_mapping.items():
                        if chapter == chapter_num:
                            content = getattr(summary_content, field, "")
                            chapter_info["summary_length"] = len(content) if content else 0
                            break

        return basic_info

    async def _set_resummary_active_flag(self, mapping_id: int, version: int):
        """재요약 활성 플래그 설정"""
        await self.redis_client.set(f"resummary:active:{mapping_id}", f"v{version}", ex=86400)

    async def _add_to_resummary_queue(self, mapping_id: int, version: int, priority: str):
        """재요약 큐에 추가"""
        queue_data = {
            "mapping_id": mapping_id,
            "version": version,
            "priority": priority,
            "queued_at": datetime.utcnow().isoformat()
        }
        await self.redis_client.lpush("resummary:queue", json.dumps(queue_data))

    async def _calculate_estimated_completion(self) -> datetime:
        """예상 완료 시간 계산"""
        # 간단한 추정: 현재 시간 + 30분
        return datetime.utcnow() + timedelta(minutes=30)

    async def _get_resummary_progress(self, mapping_id: int, version: int) -> Dict[str, Any]:
        """재요약 진행률 조회"""
        try:
            # Redis에서 진행률 정보 조회
            summary_progress = await self.redis_client.get(f"summary:progress:{mapping_id}:v{version}")
            news_progress = await self.redis_client.get(f"completed:{mapping_id}:v{version}")

            return {
                "summary_progress": summary_progress or "0/5",
                "news_chapters_completed": int(news_progress) if news_progress else 0,
                "total_chapters": 5
            }
        except Exception as e:
            logger.error(f"Failed to get resummary progress: {e}")
            return {"summary_progress": "0/5", "news_chapters_completed": 0, "total_chapters": 5}

    async def _get_version_statistics(self, mapping_id: int, version: int) -> Dict[str, Any]:
        """버전별 통계"""
        try:
            summary_version = self.db.query(SummaryVersion).filter(
                and_(
                    SummaryVersion.mapping_id == mapping_id,
                    SummaryVersion.version_number == version
                )
            ).first()

            if not summary_version:
                return {}

            return {
                "total_news_count": summary_version.total_news_count,
                "completed_chapters": summary_version.completed_chapters,
                "processing_duration": self._calculate_processing_duration(summary_version)
            }

        except Exception as e:
            logger.error(f"Failed to get version statistics: {e}")
            return {}

    def _calculate_processing_duration(self, summary_version: SummaryVersion) -> Optional[int]:
        """처리 시간 계산 (분 단위)"""
        if summary_version.created_at and summary_version.completed_at:
            duration = summary_version.completed_at - summary_version.created_at
            return int(duration.total_seconds() / 60)
        return None

    def _calculate_quality_improvement(self, v1_info: Dict, v2_info: Dict) -> Optional[float]:
        """품질 개선도 계산"""
        if v1_info.get("quality_score") and v2_info.get("quality_score"):
            return v2_info["quality_score"] - v1_info["quality_score"]
        return None

    def _calculate_summary_length_diff(self, v1_info: Dict, v2_info: Dict) -> Dict[str, int]:
        """요약 길이 차이 계산"""
        diff = {}
        if v1_info.get("summary_content") and v2_info.get("summary_content"):
            for field in ["business_overview", "products_service", "sales_contracts", "rnd_activities", "other_notes"]:
                v1_len = len(v1_info["summary_content"].get(field, "") or "")
                v2_len = len(v2_info["summary_content"].get(field, "") or "")
                diff[field] = v2_len - v1_len
        return diff

    def _compare_chapters(self, v1_chapters: List[Dict], v2_chapters: List[Dict]) -> Dict[str, Any]:
        """챕터별 비교"""
        comparison = {}

        # 챕터별 뉴스 개수 비교
        for v1_ch in v1_chapters:
            chapter = v1_ch["chapter"]
            v2_ch = next((ch for ch in v2_chapters if ch["chapter"] == chapter), None)
            if v2_ch:
                comparison[f"chapter_{chapter}"] = {
                    "news_count_diff": v2_ch["news_count"] - v1_ch["news_count"],
                    "hashtag_count_diff": v2_ch["hashtag_count"] - v1_ch["hashtag_count"]
                }

        return comparison

    async def _save_comparison_log(self, comparison: Dict[str, Any]):
        """비교 로그 저장"""
        try:
            comparison_log = VersionComparison(
                mapping_id=comparison["mapping_id"],
                version_1=comparison["version_1"],
                version_2=comparison["version_2"],
                summary_length_diff=comparison["summary_length_diff"],
                news_count_diff=comparison["news_count_diff"],
                quality_improvement=comparison["quality_improvement"],
                compared_at=comparison["compared_at"]
            )
            self.db.add(comparison_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save comparison log: {e}")
            # 로그 저장 실패는 무시