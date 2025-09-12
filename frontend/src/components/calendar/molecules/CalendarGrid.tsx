import React from 'react';
import { CellBox } from '../atoms/CellBox';
import { Day } from '../atoms/Day';
import { generateCalendarCells, WEEK_DAYS } from '../../../lib/calendarUtils';
import { cn } from '../../../lib/utils';

export interface CalendarGridProps {
  viewDate: Date;
  getFilteredRecruits: (day: number) => {
    type: 'start' | 'end';
    company: string;
    employmentType: string;
    jobCategory: string;
  }[];
  expandedDays: Set<number>;
  onExpandedDaysChange: (days: Set<number>) => void;
  className?: string;
}

export const CalendarGrid: React.FC<CalendarGridProps> = ({
  viewDate,
  getFilteredRecruits,
  expandedDays,
  onExpandedDaysChange,
  className,
}) => {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  // 달력 셀 데이터 생성
  const calendarCells = generateCalendarCells(year, month);

  return (
    <div className={cn('w-full', className)}>
      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {WEEK_DAYS.map((day, index) => {
          const dayOfWeek = [
            'sunday',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
          ][index] as
            | 'sunday'
            | 'monday'
            | 'tuesday'
            | 'wednesday'
            | 'thursday'
            | 'friday'
            | 'saturday';
          return (
            <Day key={day} dayOfWeek={dayOfWeek}>
              {day}
            </Day>
          );
        })}
      </div>

      {/* 달력 그리드 */}
      <div className="grid grid-cols-7 gap-2">
        {calendarCells.map((cell, index) => (
          <CellBox
            key={index}
            tone={cell.isCurrentMonth ? 'default' : 'muted'}
            today={cell.isToday}
            interactive={cell.isCurrentMonth}
            day={cell.day}
            recruits={cell.day ? getFilteredRecruits(cell.day) : []}
            isExpanded={cell.day ? expandedDays.has(cell.day) : false}
            onToggleExpanded={(day) => {
              const next = new Set(expandedDays);
              if (next.has(day)) next.delete(day);
              else next.add(day);
              onExpandedDaysChange(next);
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default CalendarGrid;
