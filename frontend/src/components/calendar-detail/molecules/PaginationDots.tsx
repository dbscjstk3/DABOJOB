import { cn } from '@/lib/utils';

interface PaginationDotsProps {
  total: number;
  current: number;
  onChange: (page: number) => void;
  className?: string;
}

export default function PaginationDots({
  total,
  current,
  onChange,
  className = '',
}: PaginationDotsProps) {
  if (total <= 1) return null;

  return (
    <div className={cn('flex justify-center gap-2 mt-4', className)}>
      {Array.from({ length: total }).map((_, index) => (
        <button
          key={index}
          onClick={() => onChange(index)}
          className={cn(
            'w-2 h-2 rounded-full transition-colors',
            index === current ? 'bg-gray-800' : 'bg-gray-300 hover:bg-gray-400',
          )}
          aria-label={`페이지 ${index + 1}`}
          aria-current={index === current ? 'page' : undefined}
        />
      ))}
    </div>
  );
}
