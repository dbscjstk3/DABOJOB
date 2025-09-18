import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';

interface NewsCardProps {
  title: string;
  content: string;
  publishedDate: string;
  url?: string;
  className?: string;
}

export default function NewsCard({
  title,
  content,
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
    <article className={cn('border-b border-slate-200 pb-1 last:border-b-0', className)}>
      {/* 제목과 날짜 */}
      <Typography
        as="h3"
        variant="default"
        weight="semibold"
        className="flex-1 cursor-pointer mb-3 hover:text-blue-600 transition-colors"
        onClick={handleClick}
      >
        {title}
      </Typography>

      {/* 뉴스 내용 - 전체 표시 */}
      <Typography variant="default" color="gray" className="text-sm leading-6">
        {content}
      </Typography>
      <Typography
        variant="default"
        color="gray"
        align="right"
        className="mt-2 text-sm whitespace-nowrap"
      >
        {publishedDate}
      </Typography>
    </article>
  );
}
