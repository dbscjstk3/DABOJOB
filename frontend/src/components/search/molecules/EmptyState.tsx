import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';
import searchImage from '@/assets/img/search.png?format=webp&quality=80';

interface EmptyStateProps {
  searchTerm?: string;
  className?: string;
}

export default function EmptyState({ searchTerm, className = '' }: EmptyStateProps) {
  return (
    <div className={cn('py-16 text-center', className)}>
      <div className="flex justify-center mb-4">
        <img src={searchImage} alt="검색" className="h-24 w-24 object-contain" />
      </div>

      <Typography variant="subtitle" weight="semibold" className="mb-2 text-center">
        {searchTerm ? `"${searchTerm}"에 대한 검색 결과가 없습니다` : '검색 결과가 없습니다'}
      </Typography>

      <Typography variant="default" color="gray" className="text-center">
        다른 기업명 / 공고명 으로 시도해보세요!
      </Typography>
    </div>
  );
}
