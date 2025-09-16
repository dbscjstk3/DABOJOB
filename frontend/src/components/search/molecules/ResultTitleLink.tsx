import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';

interface ResultTitleLinkProps {
  title: string;
  url?: string;
  className?: string;
}

export default function ResultTitleLink({ title, url, className = '' }: ResultTitleLinkProps) {
  const handleClick = () => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  return (
    <Typography
      as="h3"
      variant="default"
      weight="semibold"
      className={cn('flex-1 cursor-pointer hover:text-daboja-default transition-colors', className)}
      onClick={handleClick}
    >
      {title}
    </Typography>
  );
}
