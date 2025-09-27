import { useState, useEffect } from 'react';
import ReportContainer from '@/components/calendar-detail/organisms/ReportContainer';
import { Link, useParams } from '@tanstack/react-router';
import { ChevronsLeft } from 'lucide-react';
import { useAdminJobCompleteData } from '@/lib/hooks';
import { AdminNewsContainer } from '@/components/admin/organisms/AdminNewsContainer';
import type { NewsItem } from '@/components/calendar-detail/organisms/NewsContainer';
import type { AdminJobCompleteResponse, AdminNewsItem } from '@/lib/api';

export default function AdminCompletedPage() {
  const { jobId } = useParams({ from: '/admin/jobs/$jobId/complete' });
  const [newsFilter, setNewsFilter] = useState<string | null>(null);
  const [newsItemsPerPage, setNewsItemsPerPage] = useState(3);

  // 화면 크기에 따라 itemsPerPage 설정
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setNewsItemsPerPage(1);
      } else {
        setNewsItemsPerPage(3);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // API 호출
  const { data, isLoading, error } = useAdminJobCompleteData(jobId);

  // AdminJobCompleteResponse를 ReportContainer 형식으로 변환
  const reportData = data
    ? {
        title: `${data.company_info.company_name} (${data.company_info.company_scale})`,
        sections: [
          {
            title: '사업 개요',
            items: [
              {
                summary: data.summary_reports.business_overview,
              },
            ],
            tags: extractHashtagsFromSection(data, 'business_overview'),
          },
          {
            title: '제품 및 서비스',
            items: [
              {
                summary: data.summary_reports.products_services,
              },
            ],
            tags: extractHashtagsFromSection(data, 'products_services'),
          },
          {
            title: '판매 및 계약',
            items: [
              {
                summary: data.summary_reports.revenue_orders,
              },
            ],
            tags: extractHashtagsFromSection(data, 'revenue_orders'),
          },
          {
            title: '연구개발 활동',
            items: [
              {
                summary: data.summary_reports.contracts_rnd,
              },
            ],
            tags: extractHashtagsFromSection(data, 'contracts_rnd'),
          },
          {
            title: '기타 사항',
            items: [
              {
                summary: data.summary_reports.other_references,
              },
            ],
            tags: extractHashtagsFromSection(data, 'other_references'),
          },
        ],
      }
    : { title: '', sections: [] };

  // news_data를 flat한 NewsItem[] 배열로 변환
  const newsData: NewsItem[] = data ? convertNewsData(data, newsFilter) : [];

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto p-4 space-y-4">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-daboja-default mx-auto mb-4"></div>
            <p className="text-lg text-gray-600">데이터를 불러오는 중...</p>
          </div>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="max-w-5xl mx-auto p-4 space-y-4">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-lg text-red-600 mb-4">데이터를 불러오는데 실패했습니다.</p>
            <p className="text-sm text-gray-500">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우
  if (!data) {
    return (
      <div className="max-w-5xl mx-auto p-4 space-y-4">
        <div className="flex items-center justify-center min-h-[400px]">
          <p className="text-lg text-gray-600">데이터가 없습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-4/5 mx-auto p-4 space-y-4">
      <Link to="/admin" className="inline-flex items-center gap-1.5 text-sm mb-1 mt-5">
        <ChevronsLeft className="h-4 w-4 text-daboja-default" />
        <span>관리자 페이지로 돌아가기</span>
      </Link>

      {/* 리포트와 뉴스 나란히 배치 (3:2 비율) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <ReportContainer
            title={reportData.title}
            sections={reportData.sections}
            onTagSelect={(tag) => {
              setNewsFilter(tag); // 뉴스 필터링용
            }}
          />
        </div>

        <div className="lg:col-span-2">
          <div className="sticky top-20 lg:top-24">
            <AdminNewsContainer
              news={newsData}
              filterTag={newsFilter}
              itemsPerPage={newsItemsPerPage}
              jobId={jobId}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// 섹션별로 해시태그를 추출하는 헬퍼 함수
function extractHashtagsFromSection(
  data: AdminJobCompleteResponse,
  sectionKey: keyof AdminJobCompleteResponse['news_data'],
): string[] {
  const sectionData = data.news_data[sectionKey];
  if (!sectionData) return [];

  return Object.keys(sectionData);
}

// news_data를 NewsItem[] 형식으로 변환하는 헬퍼 함수
function convertNewsData(data: AdminJobCompleteResponse, filterTag?: string | null): NewsItem[] {
  const newsItems: NewsItem[] = [];

  // 모든 섹션을 순회
  Object.values(data.news_data).forEach((sectionData) => {
    if (!sectionData) return;

    // 각 섹션의 해시태그를 순회
    Object.entries(sectionData).forEach(([hashtag, hashtagGroup]) => {
      // 필터가 있으면 해당 태그만 포함
      if (filterTag && hashtag !== filterTag) return;

      // news_items을 NewsItem 형식으로 변환
      hashtagGroup.news_items.forEach((item: AdminNewsItem) => {
        newsItems.push({
          newsId: item.news_id,
          title: item.title,
          content: item.summary || '요약 데이터 없음',
          postingDate: item.published_date,
          url: item.url,
          summaryHashtagId: hashtagGroup.hashtag_id,
        });
      });
    });
  });

  return newsItems;
}
