import React from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Typography } from '../../common/atoms/Typography';
import { RecruitBadge } from '../atoms/RecruitBadge';
import { Button } from '../../common/atoms/Button';
import { CalendarHeader } from '../molecules/CalendarHeader';
import type { JobPostingResponse } from '@/lib/api';

export interface RecruitModalProps {
  isOpen: boolean;
  onClose: () => void;
  recruits: JobPostingResponse[];
  selectedDate: number;
  selectedMonth: number;
  selectedYear: number;
  onDateChange?: (date: Date) => void;
}

export const RecruitModal: React.FC<RecruitModalProps> = ({
  isOpen,
  onClose,
  recruits,
  selectedDate,
  selectedMonth,
  selectedYear,
  onDateChange,
}) => {
  const navigate = useNavigate();

  if (!isOpen) return null;

  // 기업 상세페이지로 이동하는 함수 (companyId를 summaryId로 사용)
  const handleCompanyClick = (companyId: number, jobPostingId: number) => {
    navigate({
      to: '/calendar/$id',
      params: { id: companyId.toString() },
      search: { jobPostingId: jobPostingId.toString() },
    });
  };

  const getCompanyTypeClass = (companyType: string) => {
    switch (companyType) {
      case '대기업':
        return 'bg-purple-100 text-purple-800';
      case '중견기업':
        return 'bg-amber-100 text-amber-800';
      case '중소기업':
        return 'bg-emerald-100 text-emerald-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 시작 공고와 종료 공고를 분리
  // 공고를 공고일/마감일로 분류
  const postingRecruits = recruits.filter((recruit) => {
    // 날짜 문자열을 직접 비교 (YYYY-MM-DD 형식)
    const expectedDate = `${selectedYear}-${String(selectedMonth + 1).padStart(2, '0')}-${String(selectedDate).padStart(2, '0')}`;
    const matches = recruit.postingDate === expectedDate;

    return matches;
  });

  const expirationRecruits = recruits.filter((recruit) => {
    // 날짜 문자열을 직접 비교 (YYYY-MM-DD 형식)
    const expectedDate = `${selectedYear}-${String(selectedMonth + 1).padStart(2, '0')}-${String(selectedDate).padStart(2, '0')}`;
    const matches = recruit.deadlineDate === expectedDate;

    return matches;
  });

  // 만약 공고일/마감일 필터링에서 아무것도 찾지 못했다면,
  // 해당 날짜에 있는 모든 공고를 "공고일"로 표시
  const allRecruits =
    postingRecruits.length === 0 && expirationRecruits.length === 0
      ? recruits
      : [...postingRecruits, ...expirationRecruits];

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date
      .toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      })
      .replace(/\.$/, ''); // 마지막 점 제거
  };

  // 마감일용 날짜+시간 포맷팅 함수
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date
      .toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
      .replace(/\.$/, ''); // 마지막 점 제거
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 배경 오버레이 */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      {/* 모달 컨테이너 */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* 모달 헤더 */}
        <div className="pt-4">
          <CalendarHeader
            viewDate={new Date(selectedYear, selectedMonth, selectedDate)}
            onViewDateChange={onDateChange || (() => {})}
            showDay={true}
            dayOnly={true}
            showPopularDropdown={false}
          />
        </div>

        {/* 모달 내용 */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* 공고일 공고 섹션 */}
          {postingRecruits.length > 0 && (
            <div className="mb-6">
              <Typography
                as="h3"
                variant="title"
                weight="bold"
                color="dabojob"
                className="mb-3 text-lg"
              >
                오늘 올라온 공고 ({postingRecruits.length}개)
              </Typography>
              <div className="space-y-3">
                {postingRecruits.map((recruit, index) => (
                  <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <Typography
                          variant="default"
                          weight="bold"
                          color="black"
                          className="mb-1 cursor-pointer hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
                          onClick={() =>
                            handleCompanyClick(recruit.companyId, recruit.jobPostingId)
                          }
                        >
                          {recruit.companyName}
                        </Typography>
                        <Typography variant="recruits" color="black" className="mb-2">
                          {recruit.title}
                        </Typography>
                      </div>
                      <RecruitBadge type="start" company="" />
                    </div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      <span
                        className={`px-2 py-1 text-xs rounded ${getCompanyTypeClass(recruit.companyType)}`}
                      >
                        {recruit.companyType}
                      </span>
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {recruit.careerInfo}
                      </span>
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        {recruit.jobSectorName}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      <div>
                        📅 {formatDate(recruit.postingDate)} ~{' '}
                        {formatDateTime(recruit.deadlineDate)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 마감일 공고 섹션 */}
          {expirationRecruits.length > 0 && (
            <div>
              <Typography
                as="h3"
                variant="title"
                weight="bold"
                color="red"
                className="mb-3 text-lg"
              >
                오늘 마감인 공고 ({expirationRecruits.length}개)
              </Typography>
              <div className="space-y-3">
                {expirationRecruits.map((recruit, index) => (
                  <div key={index} className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <Typography
                          variant="default"
                          weight="bold"
                          color="black"
                          className="mb-1 cursor-pointer hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
                          onClick={() =>
                            handleCompanyClick(recruit.companyId, recruit.jobPostingId)
                          }
                        >
                          {recruit.companyName}
                        </Typography>
                        <Typography variant="recruits" color="black" className="mb-2">
                          {recruit.title}
                        </Typography>
                      </div>
                      <RecruitBadge type="end" company="" />
                    </div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      <span
                        className={`px-2 py-1 text-xs rounded ${getCompanyTypeClass(recruit.companyType)}`}
                      >
                        {recruit.companyType}
                      </span>
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                        {recruit.careerInfo}
                      </span>
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        {recruit.jobSectorName}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      <div>
                        📅 {formatDate(recruit.postingDate)} ~{' '}
                        {formatDateTime(recruit.deadlineDate)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 공고일/마감일 필터링에서 아무것도 찾지 못한 경우, 모든 공고를 표시 */}
          {postingRecruits.length === 0 &&
            expirationRecruits.length === 0 &&
            allRecruits.length > 0 && (
              <div>
                <Typography
                  as="h3"
                  variant="title"
                  weight="bold"
                  color="dabojob"
                  className="mb-3 text-lg"
                >
                  채용 공고 ({allRecruits.length}개)
                </Typography>
                <div className="space-y-3">
                  {allRecruits.map((recruit, index) => (
                    <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <Typography
                            variant="default"
                            weight="bold"
                            color="black"
                            className="mb-1 cursor-pointer hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
                            onClick={() =>
                              handleCompanyClick(recruit.companyId, recruit.jobPostingId)
                            }
                          >
                            {recruit.companyName}
                          </Typography>
                          <Typography variant="recruits" color="black" className="mb-2">
                            {recruit.title}
                          </Typography>
                        </div>
                        <RecruitBadge type="start" company="" />
                      </div>
                      <div className="flex flex-wrap gap-2 mb-2">
                        <span
                          className={`px-2 py-1 text-xs rounded ${getCompanyTypeClass(recruit.companyType)}`}
                        >
                          {recruit.companyType}
                        </span>
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          {recruit.careerInfo}
                        </span>
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                          {recruit.jobSectorName}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600">
                        <div>
                          📅 {formatDate(recruit.postingDate)} ~{' '}
                          {formatDateTime(recruit.deadlineDate)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* 공고가 없는 경우 */}
          {allRecruits.length === 0 && (
            <div className="text-center py-8">
              <Typography variant="default" color="gray">
                해당 날짜에 채용 공고가 없습니다.
              </Typography>
            </div>
          )}
        </div>

        {/* 모달 푸터 */}
        <div className="flex justify-end p-6 border-t border-gray-200">
          <Button variant="contained" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
};

export default RecruitModal;
