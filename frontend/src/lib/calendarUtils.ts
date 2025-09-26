/**
 * 달력 관련 유틸리티 함수들
 */

export interface CalendarCell {
  day: number | null;
  isCurrentMonth: boolean;
  isToday: boolean;
  dayOfWeek?: number;
}

/**
 * 특정 년월의 달력 데이터를 생성합니다
 * @param year 년도
 * @param month 월 (0-11, 0이 1월)
 * @returns 달력 셀 배열
 */
export function generateCalendarCells(year: number, month: number): CalendarCell[] {
  const calendarCells: CalendarCell[] = [];

  // 해당 월의 첫 번째 날과 마지막 날
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const firstDayOfWeek = firstDay.getDay(); // 0 = 일요일
  const daysInMonth = lastDay.getDate();

  // 오늘 날짜
  const today = new Date();

  // 이전 달의 빈 셀들 (첫 번째 주의 앞부분)
  for (let i = 0; i < firstDayOfWeek; i++) {
    calendarCells.push({
      day: null,
      isCurrentMonth: false,
      isToday: false,
    });
  }

  // 현재 달의 날짜들
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday =
      today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;
    const dayOfWeek = new Date(year, month, day).getDay();

    calendarCells.push({
      day,
      isCurrentMonth: true,
      isToday,
      dayOfWeek,
    });
  }

  // 필요한 주 수 계산 (최소 4주, 최대 6주)
  const totalDays = calendarCells.length;
  const weeksNeeded = Math.ceil(totalDays / 7);
  const totalCells = weeksNeeded * 7;
  const remainingCells = totalCells - calendarCells.length;

  // 다음 달의 빈 셀들 (마지막 주의 뒷부분)
  for (let i = 0; i < remainingCells; i++) {
    calendarCells.push({
      day: null,
      isCurrentMonth: false,
      isToday: false,
    });
  }

  return calendarCells;
}

/**
 * 요일 배열을 반환합니다
 */
export const WEEK_DAYS = ['일', '월', '화', '수', '목', '금', '토'] as const;

/**
 * 현재 날짜를 반환합니다
 */
export function getCurrentDate() {
  return new Date();
}

/**
 * 특정 년월의 첫 번째 날을 반환합니다
 */
export function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1);
}

/**
 * 특정 년월의 마지막 날을 반환합니다
 */
export function getLastDayOfMonth(year: number, month: number) {
  return new Date(year, month + 1, 0);
}
