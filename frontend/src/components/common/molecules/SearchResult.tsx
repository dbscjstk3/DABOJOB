import * as React from 'react';
import { ArrowUpLeft } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { IconButton } from '../atoms/IconButton';

export type SearchItem = {
  id: string | number;
  label: string;
  // 필요 시 추가 필드(예: subtitle, icon 등)
};

type SearchResultProps = {
  id?: string; // aria 연결용 (listbox id)
  items: SearchItem[];
  activeIndex?: number;
  loading?: boolean;
  emptyText?: string;

  onHover?: (index: number) => void;
  onSelect?: (item: SearchItem) => void;
  onRemove?: (item: SearchItem) => void;

  /** SearchBox 내부에서 한 박스로 보이도록 사용하는 외부 클래스 */
  className?: string;
};

export function SearchResult({
  id = 'search-suggestions',
  items,
  activeIndex = -1,
  loading = false,
  emptyText = '결과가 없습니다',
  onHover,
  onSelect,
  className,
}: SearchResultProps) {
  return (
    <div className={cn('w-full', className)}>
      {/* 상단 구분선: 한 박스 내부에서 input 아래에 자연스럽게 붙음 */}
      <div className="border-t border-slate-200" />

      {/* 리스트 영역 */}
      <ul
        id={id}
        role="listbox"
        className="max-h-64 overflow-auto py-5"
        aria-busy={loading || undefined}
      >
        {/* 로딩 상태 */}
        {loading && <li className="px-4 py-2 text-sm text-slate-400">불러오는 중…</li>}

        {/* 빈 상태 */}
        {!loading && items.length === 0 && (
          <li className="px-4 py-2 text-sm text-slate-400">{emptyText}</li>
        )}

        {/* 결과 아이템 */}
        {!loading &&
          items.map((item, i) => {
            const isActive = i === activeIndex;
            return (
              <li
                key={item.id}
                role="option"
                aria-selected={isActive}
                className={cn(
                  'group relative flex items-center',
                  'px-4 py-2.5 text-sm cursor-pointer select-none',
                  'hover:bg-slate-100',
                  isActive && 'bg-slate-100',
                )}
                onMouseEnter={() => onHover?.(i)}
                onMouseDown={(e) => {
                  // input blur로 닫히기 전에 선택 처리되도록
                  e.preventDefault();
                  onSelect?.(item);
                }}
              >
                <span className="flex-1 pr-10">{item.label}</span>
                {onSelect && (
                  <div className="absolute right-2 top-1/2 -translate-y-1/2">
                    <IconButton
                      variant="plain"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        onSelect(item);
                      }}
                      onMouseDown={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                      }}
                      className={cn(isActive ? 'opacity-100' : 'opacity-0')}
                      aria-label={`${item.label} 선택`}
                    >
                      <ArrowUpLeft className="h-4 w-4" />
                    </IconButton>
                  </div>
                )}
              </li>
            );
          })}
      </ul>
    </div>
  );
}
