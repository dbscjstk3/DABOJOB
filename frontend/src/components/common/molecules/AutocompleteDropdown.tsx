import { useState, useRef, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import Typography from '@/components/common/atoms/Typography';
import type { AutocompleteJobPosting } from '@/lib/api';

interface AutocompleteDropdownProps {
  items: AutocompleteJobPosting[];
  recentSearches?: string[];
  isOpen: boolean;
  onClose: () => void;
  onItemClick?: (item: AutocompleteJobPosting) => void;
  onRecentSearchClick?: (search: string) => void;
  containerRef?: React.RefObject<HTMLDivElement>;
  className?: string;
}

export default function AutocompleteDropdown({
  items,
  recentSearches = [],
  isOpen,
  onClose,
  onItemClick,
  onRecentSearchClick,
  className,
}: AutocompleteDropdownProps) {
  const navigate = useNavigate();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  // 드롭다운이 열릴 때마다 selectedIndex 초기화
  useEffect(() => {
    if (isOpen) {
      setSelectedIndex(-1);
    }
  }, [isOpen]);

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // 키보드 네비게이션
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      const totalItems = recentSearches.length + items.length;
      if (totalItems === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev < totalItems - 1 ? prev + 1 : 0));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : totalItems - 1));
          break;
        case 'Enter':
          if (selectedIndex >= 0) {
            e.preventDefault();
            // 최근 검색어 섹션
            if (selectedIndex < recentSearches.length) {
              handleRecentSearchClick(recentSearches[selectedIndex]);
            }
            // 자동완성 섹션
            else if (selectedIndex < totalItems) {
              const autocompleteIndex = selectedIndex - recentSearches.length;
              handleItemClick(items[autocompleteIndex]);
            }
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, items, recentSearches, selectedIndex, onClose]);

  const handleItemClick = (item: AutocompleteJobPosting) => {
    if (onItemClick) {
      onItemClick(item);
    } else {
      // 기본 동작: 캘린더 상세 페이지로 이동
      // companyId를 summaryId로 사용
      // 실제로는 API 수정이 필요할 수 있음
      navigate({
        to: '/calendar/$id',
        params: { id: String(item.companyId) },
        search: { jobPostingId: String(item.jobPostingId) },
      });
    }
    onClose();
  };

  const handleRecentSearchClick = (search: string) => {
    if (onRecentSearchClick) {
      onRecentSearchClick(search);
    } else {
      // 기본 동작: 검색 페이지로 이동
      navigate({
        to: '/search',
        search: { q: search, page: 1 },
      });
    }
    onClose();
  };

  const formatDeadline = (dateString: string): string => {
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `~${month}.${day}`;
  };

  const getJobStatus = (deadlineDate: string): 'started' | 'ended' => {
    const today = new Date();
    const deadline = new Date(deadlineDate);
    return deadline >= today ? 'started' : 'ended';
  };

  if (!isOpen || (items.length === 0 && recentSearches.length === 0)) return null;

  return (
    <>
      {/* 모바일에서만 더 강조된 그림자 효과 */}

      <div className="relative">
        {/* 드롭다운 리스트 */}
        <div
          ref={dropdownRef}
          className={cn(
            'bg-white border border-slate-200 overflow-hidden z-50',
            // 모바일에서 더 강한 그림자, 데스크톱에서 기본 그림자
            'shadow-2xl sm:shadow-lg',
            // 기본 위치 설정
            'absolute top-full left-0 w-full mt-1',
            // 높이 제한
            'max-h-[50vh] sm:max-h-[400px]',
            // 모바일에서 더 둥근 모서리
            'rounded-xl sm:rounded-lg',
            className,
          )}
        >
          {/* 모바일에서 드래그 핸들 */}
          <div className="sm:hidden flex justify-center py-2">
            <div className="w-8 h-1 bg-gray-300 rounded-full"></div>
          </div>

          <div className="overflow-y-auto h-full pb-safe">
            {/* 최근 검색어 섹션 - 자동완성과 동일한 스타일 */}
            {recentSearches.length > 0 && (
              <>
                {recentSearches.map((search, index) => (
                  <div
                    key={`recent-${index}`}
                    className={cn(
                      // 모바일: 더 큰 터치 영역, 데스크톱: 컴팩트
                      'px-4 py-4 sm:px-4 sm:py-3',
                      'hover:bg-slate-50 cursor-pointer transition-colors border-b border-slate-100',
                      selectedIndex === index && 'bg-slate-50',
                    )}
                    onClick={() => handleRecentSearchClick(search)}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="flex items-center gap-3">
                      {/* 시계 아이콘 */}
                      <Clock className="h-5 w-5 sm:h-4 sm:w-4 text-slate-400" />

                      {/* 검색어 텍스트 - 모바일에서 더 큰 글자 */}
                      <Typography
                        variant="default"
                        weight="medium"
                        className="flex-1 text-base sm:text-sm"
                      >
                        {search}
                      </Typography>
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* 자동완성 결과 섹션 */}
            {items.map((item, index) => (
              <div
                key={item.jobPostingId}
                className={cn(
                  // 모바일: 더 큰 터치 영역, 데스크톱: 컴팩트
                  'px-4 py-4 sm:px-4 sm:py-3',
                  'hover:bg-slate-50 cursor-pointer transition-colors border-b border-slate-100 last:border-b-0',
                  selectedIndex === recentSearches.length + index && 'bg-slate-50',
                )}
                onClick={() => handleItemClick(item)}
                onMouseEnter={() => {
                  setSelectedIndex(recentSearches.length + index);
                }}
              >
                <div className="flex items-center gap-3">
                  {/* 상태 */}
                  <Typography
                    variant="default"
                    weight="medium"
                    className={cn(
                      'text-base sm:text-sm', // 모바일에서 더 큰 글자
                      getJobStatus(item.deadlineDate) === 'started'
                        ? 'text-daboja-default'
                        : 'text-red-500',
                    )}
                  >
                    {getJobStatus(item.deadlineDate) === 'started' ? '시작' : '마감'}
                  </Typography>

                  {/* 회사명 - 직무명 */}
                  <Typography
                    variant="default"
                    weight="medium"
                    className="flex-1 text-base sm:text-sm truncate" // 모바일, 데스크톱 모두 1줄로 제한
                  >
                    {item.companyName} - {item.title}
                  </Typography>

                  {/* 마감일 */}
                  <Typography
                    variant="default"
                    color="gray"
                    className="text-base sm:text-sm" // 모바일에서 더 큰 글자
                  >
                    {formatDeadline(item.deadlineDate)}
                  </Typography>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
