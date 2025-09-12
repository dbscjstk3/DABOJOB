import * as React from 'react';
import { Search } from 'lucide-react';
import { IconButton } from '../atoms/IconButton';

type SearchBarProps = {
  /** 제어형 입력 값 */
  value: string;
  /** 입력 변경 핸들러 */
  onChange: (value: string) => void;
  /** 엔터/아이콘 클릭 시 호출 (컨테이너에서 API 호출) */
  onSubmit?: () => void;

  placeholder?: string;
  isLoading?: boolean;
  autoFocus?: boolean;

  /** 자동완성 리스트의 id를 연결해 접근성 강화 (ul[role="listbox"] id) */
  ariaControlsId?: string;

  /** 레이아웃/너비 제어용 */
  className?: string;

  /** React 19: ref를 일반 prop으로 (form 요소 참조용) */
  formRef?: React.Ref<HTMLFormElement>;
};

export function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = '기업명 / 키워드 검색',
  isLoading = false,
  autoFocus,
  ariaControlsId,
  className,
  formRef,
}: SearchBarProps) {
  const [isComposing, setIsComposing] = React.useState(false);
  const [isFocused, setIsFocused] = React.useState(false);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim() || isComposing) return;
    onSubmit?.();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (isComposing) {
        e.preventDefault(); // IME 조합 중 제출 방지
      } else {
        e.preventDefault();
        onSubmit?.();
      }
    }
  };

  return (
    <form
      ref={formRef}
      onSubmit={handleFormSubmit}
      role="search"
      aria-label="사이트 검색"
      className={['relative flex w-full items-center', 'px-4 py-3', className ?? ''].join(' ')}
    >
      {/* 시각적으로 숨긴 라벨 */}
      <label htmlFor="global-search" className="sr-only">
        기업명 검색
      </label>

      <input
        id="global-search"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder={isFocused ? '' : placeholder}
        autoFocus={autoFocus}
        aria-label="기업명 입력"
        aria-controls={ariaControlsId} // SearchResult의 id와 연결
        className="w-full bg-transparent text-base text-slate-900 placeholder:text-slate-400 outline-none border-none pr-10"
      />

      {/* 우측 돋보기 아이콘 = 제출 */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2">
        <IconButton
          type="submit"
          variant="plain"
          size="sm"
          aria-label="검색"
          title="검색"
          loading={isLoading}
        >
          <Search className="h-4 w-4" aria-hidden="true" />
        </IconButton>
      </div>
    </form>
  );
}
