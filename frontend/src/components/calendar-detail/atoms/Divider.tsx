import { cn } from '@/lib/utils';

interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  thickness?: 1 | 2 | 4 | 8;
  color?: string;
  className?: string;
}

export function Divider({
  orientation = 'horizontal',
  thickness = 1,
  color = 'bg-gray-200',
  className = '',
}: DividerProps) {
  const isVertical = orientation === 'vertical';

  const thicknessMap = {
    1: isVertical ? 'w-px' : 'h-px',
    2: isVertical ? 'w-0.5' : 'h-0.5',
    4: isVertical ? 'w-1' : 'h-1',
    8: isVertical ? 'w-2' : 'h-2',
  };

  return (
    <div
      className={cn(color, thicknessMap[thickness], isVertical ? 'h-full' : 'w-full', className)}
      role="separator"
      aria-orientation={orientation}
    />
  );
}
