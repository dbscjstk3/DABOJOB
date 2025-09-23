import { useState, useMemo, useEffect } from 'react';
import { useSwipeable } from 'react-swipeable';
import Typography from '@/components/common/atoms/Typography';
import { Button } from '@/components/common/atoms/Button';
import { IconButton } from '@/components/common/atoms/IconButton';
import NewsCard from '../molecules/NewsCard';
import PaginationDots from '../molecules/PaginationDots';
import { cn } from '@/lib/utils';

export interface NewsItem {
  newsId: number;
  newsTitle: string;
  newsContent: string;
  newsCreateDate: string;
  newsUrl: string;
  summaryHashtagId?: number; // 필요시 사용
}

interface NewsContainerProps {
  news: NewsItem[];
  filterTag?: string | null;
  itemsPerPage?: number;
  className?: string;
  onTagSearch?: (tag: string) => void;
}

export default function NewsContainer({
  news,
  filterTag,
  itemsPerPage = 3,
  className = '',
  onTagSearch,
}: NewsContainerProps) {
  // const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);

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

  // 전체보기 버튼 클릭 핸들러
  const handleViewAll = () => {
    if (filterTag && onTagSearch) {
      onTagSearch(filterTag);
    }
  };

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

  return (
    <article className={cn('rounded-xl border border-slate-200 bg-white p-4 md:p-6', className)}>
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
          <Typography variant="subtitle" weight="bold" align="center">
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
              title={item.newsTitle}
              content={item.newsContent}
              publishedDate={item.newsCreateDate}
              url={item.newsUrl}
            />
          ))}
        </div>
      ) : (
        <div className="py-5 text-center">
          <Typography variant="default" color="gray" className="text-center">
            {filterTag ? `# ${filterTag} 관련 뉴스가 없습니다.😭` : '뉴스가 없습니다.'}
          </Typography>
        </div>
      )}

      {/* 채용공고 검색 버튼 - 태그 선택 시에만 표시 */}
      {filterTag && (
        <div className="text-center mt-5">
          <Button variant="outlined" size="md" onClick={handleViewAll}>
            # {filterTag} 채용공고 검색하기
          </Button>
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <PaginationDots total={totalPages} current={currentPage} onChange={setCurrentPage} />
      )}
    </article>
  );
}
