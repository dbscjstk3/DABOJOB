import { useState, useMemo, useEffect } from 'react';
import { useSwipeable } from 'react-swipeable';
import { useNavigate } from '@tanstack/react-router';
import Typography from '@/components/common/atoms/Typography';
import { Button } from '@/components/common/atoms/Button';
import { IconButton } from '@/components/common/atoms/IconButton';
import NewsCard from '@/components/calendar-detail/molecules/NewsCard';
import PaginationDots from '@/components/calendar-detail/molecules/PaginationDots';
import { cn } from '@/lib/utils';
import { useResummaryTriggerMutation, useJobApproveMutation } from '@/lib/hooks';

export interface NewsItem {
  newsId: number;
  title: string;
  content: string;
  postingDate: string;
  url: string;
  summaryHashtagId?: number; // 필요시 사용
}

interface AdminNewsContainerProps {
  news: NewsItem[];
  filterTag?: string | null;
  itemsPerPage?: number;
  className?: string;
  jobId: string | number;
  companyId?: string | number;
  mappingId?: string | number;
}

export function AdminNewsContainer({
  news,
  filterTag,
  itemsPerPage = 3,
  className = '',
  jobId,
  companyId: _companyId,
  mappingId,
}: AdminNewsContainerProps) {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);

  // API Mutations
  const resummaryMutation = useResummaryTriggerMutation(mappingId);
  const approveMutation = useJobApproveMutation(jobId);

  // 페이지네이션 계산 (이미 필터링된 데이터를 받아옴)
  const totalPages = Math.ceil(news.length / itemsPerPage);
  const currentNews = useMemo(() => {
    const start = currentPage * itemsPerPage;
    const end = start + itemsPerPage;
    return news.slice(start, end);
  }, [news, currentPage, itemsPerPage]);

  // 태그 변경 시 첫 페이지로 리셋
  useEffect(() => {
    setCurrentPage(0);
  }, [filterTag]);

  // 스와이프 핸들러
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {
      if (currentPage < totalPages - 1) {
        setCurrentPage(currentPage + 1);
      }
    },
    onSwipedRight: () => {
      if (currentPage > 0) {
        setCurrentPage(currentPage - 1);
      }
    },
    trackMouse: false,
    trackTouch: true,
  });

  // 페이지 변경 핸들러
  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  // 재요약 요청 핸들러
  const handleReprocessing = async () => {
    try {
      await resummaryMutation.mutateAsync();
      alert('요청 완료! 재요약 완료까지 시간이 소요될 수 있습니다.');
      navigate({ to: '/admin' });
    } catch (error) {
      console.error('Resummary trigger failed:', error);
      alert('재요약 요청 중 오류가 발생했습니다.');
    }
  };

  // 승인 핸들러
  const handleApprove = async () => {
    try {
      await approveMutation.mutateAsync();
      alert('승인이 완료되었습니다!');
      navigate({ to: '/admin' });
    } catch (error) {
      console.error('Approval failed:', error);
      alert('승인 중 오류가 발생했습니다.');
    }
  };

  return (
    <article className={cn('rounded-xl bg-slate-50 p-4 md:p-6', className)}>
      {/* 헤더 */}
      <div className="mb-5">
        <div className="flex items-center justify-center gap-2 md:gap-3">
          <IconButton
            size="3xl"
            aria-label="previous page"
            onClick={handlePrevious}
            className="text-lg md:text-3xl"
            disabled={currentPage === 0}
          >
            ‹
          </IconButton>
          <Typography
            variant="subtitle"
            weight="bold"
            align="center"
            className="text-md md:text-lg"
          >
            {filterTag ? `# ${filterTag} 관련 뉴스` : '관련 뉴스'}
          </Typography>
          <IconButton
            size="3xl"
            aria-label="next page"
            onClick={handleNext}
            className="text-lg md:text-3xl"
            disabled={currentPage >= totalPages - 1}
          >
            ›
          </IconButton>
        </div>
      </div>

      {/* 뉴스 목록 */}
      {currentNews.length > 0 ? (
        <div className="space-y-6" {...swipeHandlers}>
          {currentNews.map((item) => (
            <NewsCard
              key={item.newsId}
              title={item.title}
              content={item.content}
              publishedDate={item.postingDate}
              url={item.url}
            />
          ))}
        </div>
      ) : (
        <div className="py-5 text-center">
          <Typography variant="default" color="gray" className="text-center mb-5">
            {filterTag ? `# ${filterTag} 관련 뉴스가 없습니다.😭` : '뉴스가 없습니다.'}
          </Typography>
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <PaginationDots total={totalPages} current={currentPage} onChange={setCurrentPage} />
      )}

      {/* 관리자 액션 버튼들 - 세로 배치 */}
      <div className="mt-6 space-y-3">
        <Button
          variant="outlined"
          size="md"
          className="w-full"
          onClick={handleReprocessing}
          disabled={resummaryMutation.isPending}
        >
          {resummaryMutation.isPending ? '처리 중...' : '🔄 재요약 요청'}
        </Button>

        <Button
          variant="contained"
          size="md"
          className="w-full"
          onClick={handleApprove}
          disabled={approveMutation.isPending}
        >
          {approveMutation.isPending ? '처리 중...' : '✅ 승인'}
        </Button>
      </div>
    </article>
  );
}
