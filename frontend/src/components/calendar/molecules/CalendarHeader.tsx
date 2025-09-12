import React from 'react';
import { IconButton } from '../../common/atoms/IconButton';
import { Typography } from '../../common/atoms/Typography';
import { cn } from '../../../lib/utils';

export interface CalendarHeaderProps {
  viewDate: Date;
  onViewDateChange: (date: Date) => void;
  className?: string;
}

export const CalendarHeader: React.FC<CalendarHeaderProps> = ({
  viewDate,
  onViewDateChange,
  className,
}) => {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  const handlePreviousMonth = () => {
    onViewDateChange(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    onViewDateChange(new Date(year, month + 1, 1));
  };

  return (
    <div className={cn('mb-6 flex items-center justify-center', className)}>
      <div className="flex items-center gap-3">
        <IconButton size="3xl" aria-label="previous month" onClick={handlePreviousMonth}>
          ‹
        </IconButton>
        <div className="flex items-baseline gap-2">
          <Typography variant="calendarNavigation" color="black" weight="regular">
            {year}년
          </Typography>
          <Typography variant="calendarNavigation" color="black" weight="bold">
            {month + 1}월
          </Typography>
        </div>
        <IconButton size="3xl" aria-label="next month" onClick={handleNextMonth}>
          ›
        </IconButton>
      </div>
    </div>
  );
};

export default CalendarHeader;
