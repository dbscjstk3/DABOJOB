import { useState, useMemo } from 'react';
import { useSwipeable } from 'react-swipeable';
import Typography from '@/components/common/atoms/Typography';
import { Button } from '@/components/common/atoms/Button';
import NewsCard from '../molecules/NewsCard';
import PaginationDots from '../molecules/PaginationDots';
import { cn } from '@/lib/utils';

export interface NewsItem {
  id: number;
  title: string;
  source: string;
  publishedDate: string;
  hashtags: string[];
  url?: string;
}

interface NewsContainerProps {
  news: NewsItem[];
  filterTag?: string | null;
  itemsPerPage?: number;
  className?: string;
}

export default function NewsContainer({
  news,
  filterTag,
  itemsPerPage = 3,
  className = '',
}: NewsContainerProps) {
  // const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);

  // 필터링된 뉴스
  const filteredNews = useMemo(() => {
    if (!filterTag) return news;
    return news.filter((item) => item.hashtags.includes(filterTag));
  }, [news, filterTag]);

  // 페이지네이션 계산
  const totalPages = Math.ceil(filteredNews.length / itemsPerPage);
  const currentNews = useMemo(() => {
    const start = currentPage * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredNews.slice(start, end);
  }, [filteredNews, currentPage, itemsPerPage]);

  // 태그 변경 시 첫 페이지로 리셋
  useMemo(() => {
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
    if (filterTag) {
      // TODO: /search 라우트 추가 후 주석 해제
      // 현재는 임시로 콘솔 로그만 출력
      console.log('Navigate to search with tag:', filterTag);

      // 나중에 search 라우트 추가 시 사용할 코드:
      // void navigate({
      //   to: '/search',
      //   search: { tag: filterTag.replace('#', '') }
      // });
    }
  };

  return (
    <article className={cn('rounded-xl border border-slate-200 bg-white p-4 md:p-6', className)}>
      {/* 헤더 */}
      <div className="mb-7">
        <Typography variant="subtitle" weight="bold">
          {filterTag ? `# ${filterTag} 관련 뉴스` : '관련 뉴스'}
        </Typography>
      </div>

      {/* 뉴스 목록 */}
      {currentNews.length > 0 ? (
        <div className="space-y-6" {...swipeHandlers}>
          {currentNews.map((item) => (
            <NewsCard
              key={item.id}
              title={item.title}
              source={item.source}
              publishedDate={item.publishedDate}
              url={item.url}
            />
          ))}
        </div>
      ) : (
        <div className="py-8 text-center">
          <Typography variant="default" color="gray">
            {filterTag ? `# ${filterTag} 관련 뉴스가 없습니다.` : '뉴스가 없습니다.'}
          </Typography>
        </div>
      )}

      {/* 채용공고 검색 버튼 - 태그 선택 시에만 표시 */}
      {filterTag && (
        <div className="mt-6 text-center">
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
