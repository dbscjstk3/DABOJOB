import React from 'react';
import { IconButton } from '../../common/atoms/IconButton';
import { Typography } from '../../common/atoms/Typography';
import { cn } from '../../../lib/utils';

export interface CalendarHeaderProps {
  viewDate: Date;
  onViewDateChange: (date: Date) => void;
  showDay?: boolean;
  dayOnly?: boolean;
  className?: string;
}

export const CalendarHeader: React.FC<CalendarHeaderProps> = ({
  viewDate,
  onViewDateChange,
  showDay = false,
  dayOnly = false,
  className,
}) => {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const day = viewDate.getDate();

  const handlePrevious = () => {
    if (dayOnly) {
      // 일만 변경 (같은 달 내에서)
      onViewDateChange(new Date(year, month, day - 1));
    } else {
      // 월 변경
      onViewDateChange(new Date(year, month - 1, 1));
    }
  };

  const handleNext = () => {
    if (dayOnly) {
      // 일만 변경 (같은 달 내에서)
      onViewDateChange(new Date(year, month, day + 1));
    } else {
      // 월 변경
      onViewDateChange(new Date(year, month + 1, 1));
    }
  };

  return (
    <div className={cn('mb-6 flex items-center justify-center', className)}>
      <div className="flex items-center gap-3">
        <IconButton
          size="3xl"
          aria-label={dayOnly ? 'previous day' : 'previous month'}
          onClick={handlePrevious}
        >
          ‹
        </IconButton>
        <div className="flex items-baseline gap-2">
          <Typography variant="calendarNavigation" color="black" weight="regular">
            {year}년
          </Typography>
          <Typography variant="calendarNavigation" color="black" weight="bold">
            {month + 1}월
          </Typography>
          {showDay && (
            <Typography variant="calendarNavigation" color="black" weight="bold">
              {day}일
            </Typography>
          )}
        </div>
        <IconButton
          size="3xl"
          aria-label={dayOnly ? 'next day' : 'next month'}
          onClick={handleNext}
        >
          ›
        </IconButton>
      </div>
    </div>
  );
};

export default CalendarHeader;
