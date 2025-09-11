import { CellBox } from '../components/calendar/atoms/CellBox';
import { Typography } from '../components/common/atoms/Typography';

export default function CalendarPage() {
  // 2024년 1월 달력 데이터 (예시)
  const currentDate = new Date(2025, 8); // 2024년 1월
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // 해당 월의 첫 번째 날과 마지막 날
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const firstDayOfWeek = firstDay.getDay(); // 0 = 일요일
  const daysInMonth = lastDay.getDate();

  // 요일 헤더
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  // 달력 셀 데이터 생성
  const calendarCells = [];

  // 이전 달의 빈 셀들 (첫 번째 주의 앞부분)
  for (let i = 0; i < firstDayOfWeek; i++) {
    calendarCells.push({
      day: null,
      isCurrentMonth: false,
      isToday: false,
    });
  }

  // 현재 달의 날짜들
  const today = new Date();
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday =
      today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;

    calendarCells.push({
      day,
      isCurrentMonth: true,
      isToday,
    });
  }

  // 다음 달의 빈 셀들 (마지막 주의 뒷부분)
  const totalCells = 38; // 7주 x 6일
  const remainingCells = totalCells - calendarCells.length;
  for (let i = 0; i < remainingCells; i++) {
    calendarCells.push({
      day: null,
      isCurrentMonth: false,
      isToday: false,
    });
  }

  return (
    <div className="p-6 w-full">
      {/* 달력 헤더 */}
      <div className="mb-6">
        <Typography variant="default" color="dabojob" weight="bold" align="center">
          {year}년 {month + 1}월
        </Typography>
      </div>

      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map((day) => (
          <div key={day} className="p-2">
            <Typography variant="default" weight="bold" color="gray" align="center">
              {day}
            </Typography>
          </div>
        ))}
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
              <div className="flex flex-col h-full mt-2">
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
                {/* 여기에 일정이나 이벤트를 추가할 수 있습니다 */}
              </div>
            )}
          </CellBox>
        ))}
      </div>
    </div>
  );
}
