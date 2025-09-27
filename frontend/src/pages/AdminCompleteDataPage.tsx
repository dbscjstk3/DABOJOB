import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate, Link } from '@tanstack/react-router';
import Typography from '@/components/common/atoms/Typography';
import { Button } from '@/components/common/atoms/Button';
import { ChevronsLeft, SquareArrowOutUpRight } from 'lucide-react';
import ReportContainer from '@/components/calendar-detail/organisms/ReportContainer';
import NewsContainer from '@/components/calendar-detail/organisms/NewsContainer';
import { cn } from '@/lib/utils';
import { fetchAdminJobCompleteData, type AdminJobCompleteResponse } from '@/lib/api';

export default function AdminCompleteDataPage() {
  const navigate = useNavigate();
  const { jobId } = useParams({ from: '/admin/jobs/$jobId/complete' });
  const [data, setData] = useState<AdminJobCompleteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsFilter, setNewsFilter] = useState<string | null>(null);
  const [newsItemsPerPage, setNewsItemsPerPage] = useState(1);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) setNewsItemsPerPage(3);
      else setNewsItemsPerPage(1);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const res = await fetchAdminJobCompleteData(Number(jobId));
        setData(res);
      } catch (e) {
        setError(e instanceof Error ? e.message : '데이터를 불러오기에 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [jobId]);

  const reportData = useMemo(() => {
    if (!data) return { title: '', sections: [] };
    return {
      title: data.company_info.company_name,
      sections: [
        {
          title: '사업 개요',
          items: [{ summary: data.summary_reports.business_overview }],
          tags: [],
        },
        {
          title: '제품 및 서비스',
          items: [{ summary: data.summary_reports.products_services }],
          tags: [],
        },
        {
          title: '판매 및 계약',
          items: [{ summary: data.summary_reports.revenue_orders }],
          tags: [],
        },
        {
          title: '연구개발 활동',
          items: [{ summary: data.summary_reports.contracts_rnd }],
          tags: [],
        },
        {
          title: '기타 사항',
          items: [{ summary: data.summary_reports.other_references }],
          tags: [],
        },
      ],
    };
  }, [data]);

  const newsData = useMemo(() => {
    if (!data)
      return [] as import('@/components/calendar-detail/organisms/NewsContainer').NewsItem[];
    const items: import('@/components/calendar-detail/organisms/NewsContainer').NewsItem[] = [];
    Object.values(data.news_data).forEach((topics) => {
      Object.values(topics).forEach((info) => {
        info.news_items.forEach((n) => {
          items.push({
            newsId: n.news_id,
            title: n.title,
            content: n.summary || '요약 데이터 없음',
            postingDate: n.published_date,
            url: n.url,
            summaryHashtagId: info.hashtag_id,
          });
        });
      });
    });
    return items;
  }, [data]);

  const handleTagSearch = (tag: string) => {
    navigate({ to: '/search', search: { q: tag, page: 1 } });
  };

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

  if (error || !data) {
    return (
      <div className="max-w-5xl mx-auto p-4 space-y-4">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-lg text-red-600 mb-4">데이터를 불러오는데 실패했습니다.</p>
            <p className="text-sm text-gray-500">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-4/5 mx-auto p-4 space-y-4">
      <Link to="/admin" className="inline-flex items-center gap-1.5 text-sm mb-1 mt-5">
        <ChevronsLeft className="h-4 w-4 text-daboja-default" />
        <span>캘린더로 돌아가기</span>
      </Link>

      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="hidden md:flex md:flex-row md:justify-between gap-3">
          <div className="flex items-center gap-4">
            <Typography
              variant="default"
              weight="semibold"
              className={cn('text-md', 'text-daboja-default')}
            >
              완료
            </Typography>
            <Typography variant="default" color="gray" weight="medium" className="text-base">
              {new Date(data.generated_at).toLocaleString('ko-KR')}
            </Typography>
            <Typography variant="subtitle" weight="bold" className="text-lg">
              {data.company_info.company_name} ({data.company_info.company_scale})
            </Typography>
          </div>
          <Button
            size="md"
            onClick={() => navigate({ to: '/admin' })}
            endIcon={<SquareArrowOutUpRight className="h-4 w-4" />}
          >
            관리자 캘린더로
          </Button>
        </div>

        <div className="flex flex-col gap-2 md:hidden">
          <div className="flex items-center gap-3">
            <Typography
              variant="default"
              weight="semibold"
              className={cn('text-sm', 'text-daboja-default')}
            >
              완료
            </Typography>
            <Typography variant="default" color="gray" weight="medium" className="text-sm">
              {new Date(data.generated_at).toLocaleString('ko-KR')}
            </Typography>
          </div>
          <Typography variant="subtitle" weight="bold" className="text-base">
            {data.company_info.company_name} ({data.company_info.company_scale})
          </Typography>
          <Button
            size="md"
            className="w-full"
            onClick={() => navigate({ to: '/admin' })}
            endIcon={<SquareArrowOutUpRight className="h-4 w-4" />}
          >
            관리자 캘린더로
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <ReportContainer
            title={reportData.title}
            sections={reportData.sections}
            onTagSelect={(tag) => setNewsFilter(tag)}
          />
        </div>
        <div className="lg:col-span-2">
          <div className="sticky top-20 lg:top-24">
            <NewsContainer
              news={newsData}
              filterTag={newsFilter}
              itemsPerPage={newsItemsPerPage}
              onTagSearch={handleTagSearch}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
