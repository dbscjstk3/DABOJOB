import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from '@tanstack/react-router';
import { Search } from 'lucide-react';
import { useAutocomplete, useRecentSearches } from '@/lib/hooks';
import AutocompleteDropdown from './AutocompleteDropdown';
import { cn } from '@/lib/utils';
import type { AutocompleteJobPosting } from '@/lib/api';

interface SearchBoxWithAutocompleteProps {
  placeholder?: string;
  className?: string;
  onSubmit?: (query: string) => void;
}

export default function SearchBoxWithAutocomplete({
  placeholder = '기업명 / 채용공고 검색',
  className,
  onSubmit,
}: SearchBoxWithAutocompleteProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  // React Query 훅 사용
  const { data, isLoading } = useAutocomplete(query);
  const { data: recentSearches = [] } = useRecentSearches(5);
  const items = data?.content || [];

  // 검색 제출 처리
  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    // "회사명 - 제목" 형식인 경우 제목만 추출, 아니면 전체 사용
    const searchQuery = trimmedQuery.includes(' - ')
      ? trimmedQuery.split(' - ').slice(1).join(' - ') // " - " 뒤의 모든 부분
      : trimmedQuery;

    if (onSubmit) {
      onSubmit(searchQuery);
    } else {
      // 기본 동작: 검색 페이지로 이동
      navigate({
        to: '/search',
        search: { q: searchQuery, page: 1 },
      });
    }
    setIsOpen(false);
  };

  // 입력 변경 처리
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setIsOpen(value.trim().length > 0);
  };

  // 포커스 처리
  const handleFocus = () => {
    // 검색어가 없어도 최근 검색어가 있으면 드롭다운 열기
    if (recentSearches.length > 0) {
      setIsOpen(true);
    } else if (query.trim().length > 0 && items.length > 0) {
      setIsOpen(true);
    }
  };

  // ESC 키 처리
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        inputRef.current?.blur();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 홈으로 이동 시 검색바 초기화
  useEffect(() => {
    if (location.pathname === '/') {
      setQuery('');
      setIsOpen(false);
    }
  }, [location.pathname]);

  // 자동완성 아이템이 있을 때만 드롭다운 표시
  useEffect(() => {
    if (query.trim().length > 0 && items.length > 0) {
      setIsOpen(true);
    }
  }, [items, query]);

  // 자동완성 아이템 선택 처리
  const handleItemClick = (item: AutocompleteJobPosting) => {
    setQuery(`${item.companyName} - ${item.title}`); // 검색바에 회사명과 제목 형식으로 설정
    setIsOpen(false); // 드롭다운 닫기

    // 달력 상세 페이지로 이동 (companyId를 summaryId로 사용)
    navigate({
      to: '/calendar/$id',
      params: { id: String(item.companyId) },
      search: { jobPostingId: String(item.jobPostingId) },
    });
  };

  // 최근 검색어 선택 처리
  const handleRecentSearchClick = (search: string) => {
    setQuery(search); // 검색바에 선택한 검색어 설정
    setIsOpen(false); // 드롭다운 닫기

    // 검색 페이지로 이동
    navigate({
      to: '/search',
      search: { q: search, page: 1 },
    });
  };

  return (
    <div className={cn('relative w-full', className)} ref={containerRef}>
      <form onSubmit={handleSubmit} className="w-full">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={handleFocus}
            placeholder={placeholder}
            className={cn(
              'w-full h-10 pl-4 pr-10 text-sm border border-slate-300 focus:outline-none focus:ring-1 focus:ring-daboja-default focus:border-transparent transition-all',
              isOpen && (items.length > 0 || recentSearches.length > 0)
                ? 'rounded-t-lg'
                : 'rounded-full',
            )}
          />

          {/* 검색 버튼 */}
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-slate-100 rounded-full transition-colors"
            aria-label="검색"
          >
            <Search className={cn('h-4 w-4', isLoading ? 'animate-pulse' : '')} />
          </button>
        </div>
      </form>

      {/* 자동완성 드롭다운 */}
      <AutocompleteDropdown
        items={items}
        recentSearches={query.trim() === '' ? recentSearches : undefined}
        isOpen={isOpen && (items.length > 0 || (query.trim() === '' && recentSearches.length > 0))}
        onClose={() => setIsOpen(false)}
        onItemClick={handleItemClick}
        onRecentSearchClick={handleRecentSearchClick}
        // containerRef={containerRef}
        className={
          isOpen && (items.length > 0 || (query.trim() === '' && recentSearches.length > 0))
            ? 'rounded-t-none rounded-b-lg'
            : ''
        }
      />
    </div>
  );
}
