import Typography from '@/components/common/atoms/Typography';
import { cn } from '@/lib/utils';

interface ResultMetaRowProps {
  category: string; // "IT 직무"
  experienceLevel: string; // "신입"
  period: string; // "09/05~09/12"
  className?: string;
}

export default function ResultMetaRow({
  category,
  experienceLevel,
  period,
  className = '',
}: ResultMetaRowProps) {
  return (
    <div className={cn('flex items-center gap-4 flex-wrap', className)}>
      {/* 직무 카테고리 */}
      <Typography variant="default" color="gray" className="text-sm">
        {category}
      </Typography>

      {/* 경력 레벨 */}
      <Typography variant="default" className="text-sm font-medium">
        {experienceLevel}
      </Typography>

      {/* 기간 */}
      <Typography variant="default" color="gray" className="text-sm">
        {period}
      </Typography>
    </div>
  );
}
