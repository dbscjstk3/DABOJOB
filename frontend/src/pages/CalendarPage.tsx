import { useState } from 'react';
import { CellBox } from '../components/calendar/atoms/CellBox';
import { RecruitBadge } from '../components/calendar/atoms/RecruitBadge';
import { MonthTitle } from '../components/calendar/molecules/MonthTitle';
import { Day } from '../components/calendar/atoms/Day';
import { Typography } from '../components/common/atoms/Typography';
import { IconButton } from '../components/common/atoms/IconButton';
import { generateCalendarCells, WEEK_DAYS } from '../lib/calendarUtils';

export default function CalendarPage() {
  // 더보기(확장) 상태: 날짜 번호 Set
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());
  // 현재 보이는 연/월 상태
  const [viewDate, setViewDate] = useState(new Date());
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  // 달력 셀 데이터 생성
  const calendarCells = generateCalendarCells(year, month);

  // 샘플 공고 데이터 (날짜별 시작/종료 이벤트)
  const recruitMap: Record<number, { type: 'start' | 'end'; company: string }[]> = {
    2: [
      { type: 'start', company: '삼성전자' },
      { type: 'start', company: '삼성SDS' },
      { type: 'start', company: '삼성생명' },
      { type: 'start', company: '삼성SDI' },
      { type: 'start', company: '삼성디스플레이' },
      { type: 'start', company: '삼성물산' },
      { type: 'start', company: '삼성화재' },
      { type: 'start', company: '삼성바이오' },
      { type: 'start', company: '삼성전기' },
      { type: 'start', company: '삼성중공업' },
      { type: 'start', company: '삼성카드' },
      { type: 'start', company: '삼성증권' },
      { type: 'start', company: '삼성E&A' },
      { type: 'end', company: '현대자동차' },
    ],
    3: [{ type: 'start', company: 'KB국민은행' }],
    4: [{ type: 'end', company: '멀티캠퍼스' }],
    5: [
      { type: 'start', company: '비바리퍼블리카' },
      { type: 'start', company: '카카오' },
    ],
  };

  return (
    <div className="p-6 w-full">
      {/* 달력 헤더 */}
      <div className="mb-6 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <IconButton
            size="3xl"
            aria-label="previous month"
            onClick={() => setViewDate((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1))}
          >
            ‹
          </IconButton>
          <MonthTitle year={year} month={month} />
          <IconButton
            size="3xl"
            aria-label="next month"
            onClick={() => setViewDate((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1))}
          >
            ›
          </IconButton>
        </div>
      </div>

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
                    if (!cell.isCurrentMonth || !Array.isArray(recruitMap[cell.day])) return null;
                    const items = recruitMap[cell.day] as {
                      type: 'start' | 'end';
                      company: string;
                    }[];
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
}
