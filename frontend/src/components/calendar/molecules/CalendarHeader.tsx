import React, { useState, useRef, useEffect } from 'react';
import { IconButton } from '../../common/atoms/IconButton';
import { Typography } from '../../common/atoms/Typography';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../../lib/utils';

// 실시간 인기 옵션
const popularOptions = [
  { value: '1', label: '1위 - 삼성전자' },
  { value: '2', label: '2위 - 네이버' },
  { value: '3', label: '3위 - 카카오' },
  { value: '4', label: '4위 - LG전자' },
  { value: '5', label: '5위 - 현대자동차' },
  { value: '6', label: '6위 - SK하이닉스' },
  { value: '7', label: '7위 - 쿠팡' },
  { value: '8', label: '8위 - 토스' },
  { value: '9', label: '9위 - 배달의민족' },
  { value: '10', label: '10위 - 당근마켓' },
];

// 실시간 인기 드롭다운 컴포넌트
const PopularDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

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
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % popularOptions.length);
    }, 3000); // 3초마다 변경

    return () => clearInterval(interval);
  }, []);

  const handleRankSelect = (rank: string) => {
    setCurrentIndex(parseInt(rank) - 1);
    setIsOpen(false);
  };

  const getCurrentOption = () => {
    return popularOptions[currentIndex];
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 md:gap-3 text-sm md:text-base text-gray-600 hover:text-gray-800 transition-colors px-2 py-1 md:px-3 md:py-2 rounded-lg hover:bg-gray-50"
      >
        <span className="font-semibold text-xs md:text-base">실시간 인기</span>
        <span className="text-gray-500 text-xs md:text-sm hidden sm:inline transition-opacity duration-500 w-20 text-center">
          {getCurrentOption()?.label.split(' - ')[1] || '삼성전자'}
        </span>
        <ChevronDown
          className={cn(
            'h-3 w-3 md:h-4 md:w-4 text-gray-400 transition-transform duration-200',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 w-48 md:w-56 max-h-60 overflow-y-auto">
          <div className="py-1 md:py-2">
            {popularOptions.map((option) => (
              <div
                key={option.value}
                onClick={() => handleRankSelect(option.value)}
                className="px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm hover:bg-gray-100 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-2 md:gap-3">
                  <span className="font-bold text-red-500 w-6 md:w-8 text-sm md:text-base">
                    {option.value}위
                  </span>
                  <span className="text-gray-700 text-sm md:text-base">
                    {option.label.split(' - ')[1]}
                  </span>
                </div>
              </div>
            ))}
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
        <div className="absolute top-0 right-0 flex items-center h-full">
          <PopularDropdown />
        </div>
      )}
    </div>
  );
};

export default CalendarHeader;
