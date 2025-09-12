import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';
import { Typography, type TypographyProps } from '../../common/atoms/Typography';

const monthTitleVariants = cva('w-full flex items-baseline gap-2', {
  variants: {
    align: {
      left: 'justify-start text-left',
      center: 'justify-center text-center',
      right: 'justify-end text-right',
    },
  },
  defaultVariants: {
    align: 'center',
  },
});

export interface MonthTitleProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'align'>,
    VariantProps<typeof monthTitleVariants> {
  year: number;
  month: number; // 0-based (0=Jan)
  yearWeight?: TypographyProps['weight'];
  monthWeight?: TypographyProps['weight'];
}

export const MonthTitle: React.FC<MonthTitleProps> = ({
  year,
  month,
  align,
  yearWeight = 'regular',
  monthWeight = 'bold',
  className,
  ...props
}) => {
  return (
    <div className={cn(monthTitleVariants({ align }), className)} {...props}>
      <Typography variant="calendarNavigation" color="black" weight={yearWeight} align={align}>
        {year}년
      </Typography>
      <Typography variant="calendarNavigation" color="black" weight={monthWeight} align={align}>
        {month + 1}월
      </Typography>
    </div>
  );
};

export default MonthTitle;
