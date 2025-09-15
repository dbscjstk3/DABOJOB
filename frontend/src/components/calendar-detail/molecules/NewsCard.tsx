import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';

interface NewsCardProps {
  title: string;
  source: string;
  publishedDate: string;
  url?: string;
  className?: string;
}

export default function NewsCard({
  title,
  source,
  publishedDate,
  url,
  className = '',
}: NewsCardProps) {
  const handleClick = () => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  return (
    <article className={cn('border-b border-slate-200 pb-6 last:border-b-0', className)}>
      {/* 제목과 날짜 */}
      <div className="flex justify-between items-start mb-2">
        <Typography
          as="h3"
          variant="default"
          weight="semibold"
          className="flex-1 cursor-pointer hover:text-blue-600 transition-colors"
          onClick={handleClick}
        >
          {title}
        </Typography>
        <Typography variant="default" color="gray" className="ml-4 text-sm whitespace-nowrap">
          {publishedDate}
        </Typography>
      </div>

      {/* 출처/요약 - 전체 표시 */}
      <Typography variant="default" color="gray" className="text-sm">
        {source}
      </Typography>
    </article>
  );
}
