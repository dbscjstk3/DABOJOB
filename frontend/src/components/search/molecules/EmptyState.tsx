import Typography from '@/components/common/atoms/Typography';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  searchTerm?: string;
  className?: string;
}

export default function EmptyState({ searchTerm, className = '' }: EmptyStateProps) {
  return (
    <div className={cn('py-16 text-center', className)}>
      <div className="flex justify-center mb-4">
        <Search className="h-12 w-12 text-gray-400" />
      </div>

      <Typography variant="subtitle" weight="semibold" className="mb-2 text-center">
        {searchTerm ? `"${searchTerm}"에 대한 검색 결과가 없습니다` : '검색 결과가 없습니다'}
      </Typography>

      <Typography variant="default" color="gray" className="text-center">
        다른 검색어로 시도해보시거나 검색 조건을 변경해주세요
      </Typography>
    </div>
  );
}
