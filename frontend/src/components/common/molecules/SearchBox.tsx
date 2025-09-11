// components/search/SearchBox.tsx
import * as React from 'react';
import { SearchBar } from './SearchBar';
import { SearchResult, type SearchItem } from './SearchResult';

/** 디바운스 훅 (간단 버전) */
function useDebouncedValue<T>(value: T, delay = 250) {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

type SearchBoxProps = {
  /** 자동완성 API: query를 받아 SearchItem[] 반환 */
  fetchSuggestions: (query: string, signal?: AbortSignal) => Promise<SearchItem[]>;
  /** 입력 placeholder */
  placeholder?: string;
  /** 최소 글자 수 (이상일 때만 호출) */
  minChars?: number;
  /** 디바운스 ms */
  debounceMs?: number;
  /** 컨테이너 스타일 */
  className?: string;
  /** 아이템 선택 시 */
  onSelect?: (item: SearchItem) => void;
  /** 제출(엔터/돋보기 클릭) 시 */
  onSubmit?: (query: string) => void;
};

export function SearchBox({
  fetchSuggestions,
  placeholder = '기업명 / 키워드 검색',
  minChars = 1,
  debounceMs = 250,
  className,
  onSelect,
  onSubmit,
}: SearchBoxProps) {
  const wrapperRef = React.useRef<HTMLDivElement>(null);
  const formRef = React.useRef<HTMLFormElement>(null);

  const [query, setQuery] = React.useState('');
  const debounced = useDebouncedValue(query, debounceMs);

  const [items, setItems] = React.useState<SearchItem[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(-1);

  // 바깥 클릭 시 닫기
  React.useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (!wrapperRef.current) return;
      if (!wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  // ESC 닫기
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  // 디바운스된 쿼리로 자동완성 호출
  React.useEffect(() => {
    let aborter: AbortController | undefined;
    async function run() {
      const q = debounced.trim();
      if (q.length < minChars) {
        setItems([]);
        setLoading(false);
        setOpen(false);
        setActiveIndex(-1);
        return;
      }
      aborter = new AbortController();
      setLoading(true);
      try {
        const data = await fetchSuggestions(q, aborter.signal);
        setItems(data);
        setOpen(true); // 결과 생길 때 오픈
        setActiveIndex(-1);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === 'AbortError')) {
          // 에러 로깅 정도만
          console.error(err);
          setItems([]);
          setOpen(false);
        }
      } finally {
        setLoading(false);
      }
    }
    run();
    return () => aborter?.abort();
  }, [debounced, minChars, fetchSuggestions]);

  // 제출(엔터/아이콘 클릭)
  const handleSubmit = React.useCallback(() => {
    const q = query.trim();
    if (!q) return;
    onSubmit?.(q);
    // 제출 시 자동완성 닫기 (필요시 유지하도록 바꿔도 됩니다)
    setOpen(false);
    setActiveIndex(-1);
  }, [onSubmit, query]);

  // 아이템 선택
  const handleSelect = React.useCallback(
    (item: SearchItem) => {
      onSelect?.(item);
      setQuery(item.label); // 선택한 항목을 입력창에 반영
      setOpen(false);
      setActiveIndex(-1);
      // 선택 즉시 검색까지 트리거하고 싶으면 아래 주석 해제
      // onSubmit?.(item.label);
    },
    [onSelect],
  );

  return (
    <div
      ref={wrapperRef}
      className={[
        // 한 박스로 보이도록 래퍼가 border/round/shadow를 관리
        'w-full max-w-3xl bg-white border border-slate-300 shadow-sm',
        open ? 'rounded-2xl' : 'rounded-full',
        'overflow-hidden',
        className ?? '',
      ].join(' ')}
    >
      {/* 상단 입력 줄 */}
      <SearchBar
        value={query}
        onChange={(v) => {
          setQuery(v);
          // 입력 시 즉시 열지 않고, API 응답이 오면 열리도록(깜빡임 방지)
          // setOpen(true); // 필요 시 포커스 즉시 열리게 하려면 사용
        }}
        onSubmit={handleSubmit}
        isLoading={loading}
        placeholder={placeholder}
        ariaControlsId="search-suggestions"
        formRef={formRef}
      />

      {/* 결과 리스트 (같은 래퍼 내부에 렌더 → 한 박스처럼 아래로 확장) */}
      {open && (
        <SearchResult
          id="search-suggestions"
          items={items}
          activeIndex={activeIndex}
          onHover={setActiveIndex}
          onSelect={handleSelect}
          loading={loading}
          className="w-full"
        />
      )}
    </div>
  );
}
