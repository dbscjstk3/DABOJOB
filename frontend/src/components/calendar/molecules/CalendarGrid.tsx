import React, { useState } from 'react';
import { CellBox } from '../atoms/CellBox';
import { RecruitBadge } from '../atoms/RecruitBadge';
import { Day } from '../atoms/Day';
import { Typography } from '../../common/atoms/Typography';
import { generateCalendarCells, WEEK_DAYS } from '../../../lib/calendarUtils';
import { cn } from '../../../lib/utils';

export interface CalendarGridProps {
  viewDate: Date;
  employmentTypeFilter: string[];
  jobCategoryFilter: string[];
  className?: string;
}

// 샘플 공고 데이터 (날짜별 시작/종료 이벤트)
const recruitMap: Record<
  number,
  {
    type: 'start' | 'end';
    company: string;
    employmentType: string;
    jobCategory: string;
  }[]
> = {
  2: [
    {
      type: 'start',
      company: '삼성전자',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성SDS',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    { type: 'start', company: '삼성생명', employmentType: 'contract', jobCategory: 'finance' },
    {
      type: 'start',
      company: '삼성SDI',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성디스플레이',
      employmentType: 'full-time',
      jobCategory: 'design',
    },
    { type: 'start', company: '삼성물산', employmentType: 'contract', jobCategory: 'management' },
    { type: 'start', company: '삼성화재', employmentType: 'full-time', jobCategory: 'finance' },
    {
      type: 'start',
      company: '삼성바이오',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성전기',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    {
      type: 'start',
      company: '삼성중공업',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    { type: 'start', company: '삼성카드', employmentType: 'full-time', jobCategory: 'finance' },
    { type: 'start', company: '삼성증권', employmentType: 'full-time', jobCategory: 'finance' },
    { type: 'start', company: '삼성E&A', employmentType: 'contract', jobCategory: 'development' },
    {
      type: 'end',
      company: '현대자동차',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
  ],
  3: [
    { type: 'start', company: 'KB국민은행', employmentType: 'full-time', jobCategory: 'finance' },
  ],
  4: [{ type: 'end', company: '멀티캠퍼스', employmentType: 'contract', jobCategory: 'education' }],
  5: [
    {
      type: 'start',
      company: '비바리퍼블리카',
      employmentType: 'full-time',
      jobCategory: 'development',
    },
    { type: 'start', company: '카카오', employmentType: 'full-time', jobCategory: 'development' },
  ],
};

export const CalendarGrid: React.FC<CalendarGridProps> = ({
  viewDate,
  employmentTypeFilter,
  jobCategoryFilter,
  className,
}) => {
  // 더보기(확장) 상태: 날짜 번호 Set
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  // 달력 셀 데이터 생성
  const calendarCells = generateCalendarCells(year, month);

  // 필터링된 공고 데이터
  const getFilteredRecruits = (day: number) => {
    const recruits = recruitMap[day] || [];
    return recruits.filter((recruit) => {
      const employmentTypeMatch =
        employmentTypeFilter.length === 0 || employmentTypeFilter.includes(recruit.employmentType);
      const jobCategoryMatch =
        jobCategoryFilter.length === 0 || jobCategoryFilter.includes(recruit.jobCategory);
      return employmentTypeMatch && jobCategoryMatch;
    });
  };

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
          >
            {cell.day && (
              <div className="flex flex-col h-full mt-2 gap-2">
                <div className="flex items-center justify-start">
                  {cell.isToday ? (
                    <div className="w-7 h-7 bg-[#099AEE] rounded-full flex items-center justify-center">
                      <Typography variant="dayNumber" color="white" weight="bold" align="center">
                        {cell.day}
                      </Typography>
                    </div>
                  ) : (
                    <Typography
                      variant="dayNumber"
                      color={cell.isCurrentMonth ? 'black' : 'gray'}
                      weight="regular"
                      align="left"
                    >
                      {cell.day}
                    </Typography>
                  )}
                </div>
                {/* 공고 배지 렌더링 */}
                <div className="flex flex-col gap-1">
                  {(() => {
                    if (!cell.isCurrentMonth || !cell.day) return null;
                    const items = getFilteredRecruits(cell.day);
                    const isExpanded = expandedDays.has(cell.day as number);
                    const visible = isExpanded ? items : items.slice(0, 8);
                    return (
                      <>
                        {visible.map((item, idx) => (
                          <RecruitBadge key={idx} type={item.type} company={item.company} />
                        ))}
                        {items.length > 8 && (
                          <button
                            type="button"
                            className="text-left"
                            onClick={() => {
                              setExpandedDays((prev) => {
                                const next = new Set(prev);
                                const dayNum = cell.day as number;
                                if (next.has(dayNum)) next.delete(dayNum);
                                else next.add(dayNum);
                                return next;
                              });
                            }}
                          >
                            <Typography variant="recruits" color="gray">
                              {isExpanded ? '접기' : `+${items.length - 8} 더보기`}
                            </Typography>
                          </button>
                        )}
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </CellBox>
        ))}
      </div>
    </div>
  );
};

export default CalendarGrid;
