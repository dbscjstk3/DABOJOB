import { useState, useRef, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Search } from 'lucide-react';
import { useAutocomplete } from '@/lib/hooks';
import AutocompleteDropdown from './AutocompleteDropdown';
import { cn } from '@/lib/utils';

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
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  // React Query 훅 사용
  const { data, isLoading } = useAutocomplete(query);
  const items = data?.content || [];

  // 검색 제출 처리
  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    if (onSubmit) {
      onSubmit(trimmedQuery);
    } else {
      // 기본 동작: 검색 페이지로 이동
      navigate({
        to: '/search',
        search: { q: trimmedQuery, page: 1 },
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
    if (query.trim().length > 0 && items.length > 0) {
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

  // 자동완성 아이템이 있을 때만 드롭다운 표시
  useEffect(() => {
    if (items.length > 0 && query.trim().length > 0) {
      setIsOpen(true);
    }
  }, [items, query]);

  return (
    <div className={cn('relative w-full', className)}>
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
              isOpen && items.length > 0 ? 'rounded-t-lg' : 'rounded-full',
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
        isOpen={isOpen && items.length > 0}
        onClose={() => setIsOpen(false)}
        className={isOpen && items.length > 0 ? 'rounded-t-none rounded-b-lg' : ''}
      />
    </div>
  );
}
