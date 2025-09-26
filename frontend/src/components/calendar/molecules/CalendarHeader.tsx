import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { IconButton } from '../../common/atoms/IconButton';
import { Typography } from '../../common/atoms/Typography';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { fetchHotJobPostings } from '../../../lib/api';
import type { HotJobPostingResponse } from '../../../lib/api';
import searchIcon from '@/assets/img/search.png?format=webp&quality=80';

// 실시간 인기 드롭다운 컴포넌트
const PopularDropdown: React.FC = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [hotJobPostings, setHotJobPostings] = useState<HotJobPostingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 인기 공고 데이터 가져오기
  useEffect(() => {
    const fetchHotData = async () => {
      try {
        setLoading(true);
        const hotJobPostings = await fetchHotJobPostings();
        setHotJobPostings(hotJobPostings);

        // 백엔드에서 이미 companyName과 title을 제공하므로 추가 API 호출 불필요
        console.log('🔍 인기 공고 데이터 (companyName 포함):', hotJobPostings);
      } catch (error) {
        console.error('Failed to fetch hot job postings:', error);
        // 에러 시 기본 데이터 사용
        setHotJobPostings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHotData();
  }, []);

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 자동 순환 기능
  useEffect(() => {
    if (hotJobPostings.length === 0) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % hotJobPostings.length);
    }, 3000); // 3초마다 변경

    return () => clearInterval(interval);
  }, [hotJobPostings.length]);

  // 인기 공고 클릭 핸들러
  const handleHotJobPostingClick = (jobPosting: HotJobPostingResponse) => {
    const searchQuery = `${jobPosting.companyName} ${jobPosting.title}`.trim();
    navigate({
      to: '/search',
      search: {
        q: searchQuery,
        page: 1,
      },
    });
    setIsOpen(false);
  };

  const getCurrentJobPosting = () => {
    if (hotJobPostings.length === 0) return null;
    return hotJobPostings[currentIndex];
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 sm:gap-1.5 md:gap-2 lg:gap-3 text-xs sm:text-sm md:text-base border border-daboja-default text-gray-600 hover:text-gray-800 transition-colors py-1 px-1.5 sm:px-2 sm:py-1.5 md:px-3 md:py-2 lg:px-5 lg:py-5 lg:mr-4 rounded-lg hover:bg-gray-50 w-fit min-w-0"
      >
        <img
          src={searchIcon}
          alt="검색"
          className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 lg:w-8 lg:h-8 xl:w-10 xl:h-10"
        />
        <span className="font-bold text-xs sm:text-sm md:text-base">실시간 인기</span>
        <span className="text-gray-500 text-xs sm:text-sm md:text-base hidden sm:inline transition-opacity duration-500 w-10 sm:w-12 md:w-16 lg:w-20 xl:w-24 text-center truncate">
          {loading
            ? '로딩중...'
            : (() => {
                const current = getCurrentJobPosting();
                if (!current) return '인기 공고';
                return current.companyName || current.title;
              })()}
        </span>
        <ChevronDown
          className={cn(
            'h-3 w-3 sm:h-3 sm:w-3 md:h-4 md:w-4 text-gray-400 transition-transform duration-200',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 sm:right-0 md:right-0 lg:right-2 xl:right-4 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 w-[10rem] sm:w-[12rem] md:w-[14rem] lg:w-[18rem] xl:w-[24rem] 2xl:w-[30rem] max-h-60 overflow-y-auto">
          <div className="py-1 sm:py-1 md:py-1.5 lg:py-2">
            {loading ? (
              <div className="px-2 py-1 sm:px-2.5 sm:py-1.5 md:px-3 md:py-2 lg:px-4 lg:py-3 text-xs sm:text-sm md:text-sm text-gray-500 text-center">
                로딩중...
              </div>
            ) : hotJobPostings.length === 0 ? (
              <div className="px-2 py-1 sm:px-2.5 sm:py-1.5 md:px-3 md:py-2 lg:px-4 lg:py-3 text-xs sm:text-sm md:text-sm text-gray-500 text-center">
                인기 공고가 없습니다
              </div>
            ) : (
              hotJobPostings.map((jobPosting, index) => {
                return (
                  <div
                    key={jobPosting.jobPostingId}
                    onClick={() => handleHotJobPostingClick(jobPosting)}
                    className="px-2 py-1 sm:px-2.5 sm:py-1.5 md:px-3 md:py-2 lg:px-4 lg:py-3 text-xs sm:text-sm md:text-sm hover:bg-gray-100 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-1 sm:gap-1.5 md:gap-2 lg:gap-3">
                      <span className="font-bold text-red-500 w-3 sm:w-4 md:w-5 lg:w-6 xl:w-8 text-xs sm:text-sm md:text-base flex-shrink-0">
                        {index + 1}위
                      </span>
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <div className="text-gray-700 text-xs sm:text-sm md:text-base font-medium truncate">
                          {jobPosting.companyName || jobPosting.title}
                        </div>
                        {jobPosting.companyName && (
                          <div className="text-gray-500 text-xs truncate">{jobPosting.title}</div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export interface CalendarHeaderProps {
  viewDate: Date;
  onViewDateChange: (date: Date) => void;
  showDay?: boolean;
  dayOnly?: boolean;
  showPopularDropdown?: boolean;
  className?: string;
}

export const CalendarHeader: React.FC<CalendarHeaderProps> = ({
  viewDate,
  onViewDateChange,
  showDay = false,
  dayOnly = false,
  showPopularDropdown = true,
  className,
}) => {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const day = viewDate.getDate();

  const handlePrevious = () => {
    if (dayOnly) {
      // 일만 변경 (같은 달 내에서)
      onViewDateChange(new Date(year, month, day - 1));
    } else {
      // 월 변경
      onViewDateChange(new Date(year, month - 1, 1));
    }
  };

  const handleNext = () => {
    if (dayOnly) {
      // 일만 변경 (같은 달 내에서)
      onViewDateChange(new Date(year, month, day + 1));
    } else {
      // 월 변경
      onViewDateChange(new Date(year, month + 1, 1));
    }
  };

  return (
    <div className={cn('mb-4 md:mb-6 relative', className)}>
      {/* 중앙 달력 네비게이션 */}
      <div className="flex items-center justify-center gap-2 md:gap-3">
        <IconButton
          size="3xl"
          aria-label={dayOnly ? 'previous day' : 'previous month'}
          onClick={handlePrevious}
          className="text-lg md:text-3xl"
        >
          ‹
        </IconButton>
        <div className="flex items-baseline gap-1 md:gap-2 whitespace-nowrap">
          <Typography variant="calendarNavigation" color="black" weight="regular">
            {year}년
          </Typography>
          <Typography variant="calendarNavigation" color="black" weight="bold">
            {month + 1}월
          </Typography>
          {showDay && (
            <Typography variant="calendarNavigation" color="black" weight="bold">
              {day}일
            </Typography>
          )}
        </div>
        <IconButton
          size="3xl"
          aria-label={dayOnly ? 'next day' : 'next month'}
          onClick={handleNext}
          className="text-lg md:text-3xl"
        >
          ›
        </IconButton>
      </div>

      {/* 우측 실시간 인기 드롭다운 */}
      {showPopularDropdown && (
        <div className="absolute top-0 right-0 sm:right-0 md:right-0 lg:right-2 xl:right-4 flex items-center h-full">
          <PopularDropdown />
        </div>
      )}
    </div>
  );
};

export default CalendarHeader;
