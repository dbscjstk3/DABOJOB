import { useState, useEffect } from 'react';
import { Button } from '@/components/common/atoms/Button';
import { cn } from '@/lib/utils';

interface HashtagListProps {
  tags: string[];
  defaultSelected?: string | null;
  selectedTag?: string | null;
  onFilterChange?: (tag: string | null) => void;
  onTagClick?: (tag: string | null) => void;
  className?: string;
  loading?: boolean;
}

export function HashtagList({
  tags,
  defaultSelected = null,
  selectedTag,
  onFilterChange,
  onTagClick,
  className = '',
  loading = false,
}: HashtagListProps) {
  const isControlled = selectedTag !== undefined;
  const [internalSelected, setInternalSelected] = useState<string | null>(defaultSelected);

  const selected = isControlled ? selectedTag : internalSelected;

  const handleClick = (tag: string | null) => {
    const newSelected = selected === tag ? null : tag;

    if (isControlled) {
      onTagClick?.(newSelected);
    } else {
      setInternalSelected(newSelected);
      onFilterChange?.(newSelected);
    }
  };

  useEffect(() => {
    if (!isControlled) {
      setInternalSelected(defaultSelected);
    }
  }, [defaultSelected, isControlled]);

  return (
    <div className={cn('flex flex-wrap gap-2', className)} role="group" aria-label="뉴스 필터 태그">
      {tags.map((tag) => (
        <Button
          key={tag}
          variant="tag"
          selected={selected === tag}
          onClick={() => handleClick(tag)}
          disabled={loading}
          aria-pressed={selected === tag}
        >
          # {tag}
        </Button>
      ))}
    </div>
  );
}
