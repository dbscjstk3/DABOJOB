import { useState, useEffect } from 'react';
import ReportContainer from '@/components/calendar-detail/organisms/ReportContainer';
import NewsContainer from '@/components/calendar-detail/organisms/NewsContainer';
import { Link, useNavigate, useParams, useSearch } from '@tanstack/react-router';
import { ChevronsLeft, SquareArrowOutUpRight } from 'lucide-react';
import Typography from '@/components/common/atoms/Typography';
import { Button } from '@/components/common/atoms/Button';
import { cn } from '@/lib/utils';
import { useSummaryDetail, useNews, useNewsByHashtag, useJobPosting } from '@/lib/hooks';

export default function CalendarDetailPage() {
  const navigate = useNavigate();
  const { id: summaryId } = useParams({ from: '/calendar/$id' });
  const { jobPostingId } = useSearch({ from: '/calendar/$id' });
  const [newsFilter, setNewsFilter] = useState<string | null>(null);
  const [newsItemsPerPage, setNewsItemsPerPage] = useState(1);

  // 화면 크기에 따라 itemsPerPage 설정
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setNewsItemsPerPage(3);
      } else {
        setNewsItemsPerPage(1);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // API 호출
  const { data, isLoading, error } = useSummaryDetail(summaryId);
  const { data: allNewsData } = useNews(summaryId);
  const { data: hashtagNewsData } = useNewsByHashtag(summaryId, newsFilter);
  const { data: jobData } = useJobPosting(jobPostingId);

  // 표시할 뉴스 데이터 결정 (태그가 선택되면 태그별 뉴스, 아니면 전체 뉴스)
  const newsData = newsFilter ? hashtagNewsData : allNewsData;

  // 날짜 기반 상태 계산
  const getJobStatus = (): 'recruiting' | 'ended' => {
    if (!jobData) return 'ended';
    const today = new Date();
    const deadline = new Date(jobData.deadlineDate);
    return deadline >= today ? 'recruiting' : 'ended';
  };

  // 마감일 포맷팅 (예: ~02.28 (금))
  const formatDeadline = (dateString: string): string => {
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    const weekday = weekdays[date.getDay()];
    return `~${month}.${day} (${weekday})`;
  };

  // 태그 클릭 시 검색 페이지로 이동하는 함수
  const handleTagSearch = (tag: string) => {
    navigate({
      to: '/search',
      search: {
        q: tag,
        page: 1,
      },
    });
  };

  // API 데이터를 ReportContainer 형식으로 변환
  const reportData = data
    ? {
        title: data.companyName,
        sections: [
          {
            title: '사업 개요',
            items: [
              {
                summary: data.businessOverview,
              },
            ],
            tags: data.chapterHashtags.BUSINESS_OVERVIEW || [],
          },
          {
            title: '제품 및 서비스',
            items: [
              {
                summary: data.productsService,
              },
            ],
            tags: data.chapterHashtags.PRODUCTS_SERVICE || [],
          },
          {
            title: '판매 및 계약',
            items: [
              {
                summary: data.salesContracts,
              },
            ],
            tags: data.chapterHashtags.SALES_CONTRACTS || [],
          },
          {
            title: '연구개발 활동',
            items: [
              {
                summary: data.rndActivities,
              },
            ],
            tags: data.chapterHashtags.RND_ACTIVITIES || [],
          },
          {
            title: '기타 사항',
            items: [
              {
                summary: data.otherNotes,
              },
            ],
            tags: data.chapterHashtags.OTHER_NOTES || [],
          },
        ],
      }
    : { title: '', sections: [] };

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
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm mb-1 mt-5">
        <ChevronsLeft className="h-4 w-4 text-daboja-default" />
        <span>캘린더로 돌아가기</span>
      </Link>

      {/* 채용공고 섹션 */}
      {jobData && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
          <div className="flex flex-col md:flex-row md:justify-between gap-3">
            <div className="flex items-center justify-center md:justify-start gap-4">
              {/* 상태 */}
              <Typography
                variant="default"
                weight="semibold"
                className={cn(
                  'text-md',
                  getJobStatus() === 'recruiting' ? 'text-daboja-default' : 'text-red-600',
                )}
              >
                {getJobStatus() === 'recruiting' ? '시작' : '마감'}
              </Typography>

              {/* 마감일 */}
              <Typography variant="default" color="gray" weight="medium">
                {formatDeadline(jobData.deadlineDate)}
              </Typography>

              {/* 공고명 */}
              <Typography variant="subtitle" weight="bold">
                {jobData.title}
              </Typography>
            </div>

            <div className="w-full md:w-auto md:flex md:justify-end">
              {/* 버튼 */}
              <Button
                size="md"
                className="w-full md:w-auto"
                onClick={() => window.open(jobData.url, '_blank')}
                endIcon={<SquareArrowOutUpRight className="h-4 w-4" />}
              >
                지원공고 보러가기
              </Button>
            </div>
          </div>
        </div>
      )}
      {/* 리포트와 뉴스 나란히 배치 (3:2 비율) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <ReportContainer
            title={reportData.title}
            sections={reportData.sections}
            onTagSelect={(tag) => {
              setNewsFilter(tag); // 뉴스 필터링용
              // if(tag)
              //   handleTagSearch(tag); // 검색 페이지 이동용
            }}
          />
        </div>

        <div className="lg:col-span-2">
          <div className="sticky top-20 lg:top-24">
            <NewsContainer
              news={newsData || []}
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
