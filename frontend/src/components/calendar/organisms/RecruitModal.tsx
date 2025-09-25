import React, { useState, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Typography } from '../../common/atoms/Typography';
import { RecruitBadge } from '../atoms/RecruitBadge';
import { Button } from '../../common/atoms/Button';
import { CalendarHeader } from '../molecules/CalendarHeader';
import type { JobPostingResponse, AdminCalendarCompany } from '@/lib/api';
import { groupCompaniesByGroup } from '@/lib/companyUtils';
// import { fetchAdminJobStatus } from '@/lib/api';

export interface RecruitModalProps {
  isOpen: boolean;
  onClose: () => void;
  recruits: JobPostingResponse[];
  selectedDate: number;
  selectedMonth: number;
  selectedYear: number;
  onDateChange?: (date: Date) => void;
  // 관리자용 props
  adminCompanies?: AdminCalendarCompany[];
  onAdminCalendarCompanyClick?: (company: AdminCalendarCompany) => void;
}

export const RecruitModal: React.FC<RecruitModalProps> = ({
  isOpen,
  onClose,
  recruits,
  selectedDate,
  selectedMonth,
  selectedYear,
  onDateChange,
  adminCompanies = [],
  onAdminCalendarCompanyClick,
}) => {
  const navigate = useNavigate();

  // 작업 상태 관리
  const [jobStatuses] = useState<Record<number, 'processing' | 'finished' | 'completed'>>({});
  const [loadingStatuses, setLoadingStatuses] = useState<Set<number>>(new Set());

  // verified 상태인 회사들의 작업 상태 조회
  useEffect(() => {
    const fetchJobStatuses = async () => {
      const verifiedCompanies = adminCompanies.filter(
        (company) => company.mapping_status === 'verified',
      );

      for (const company of verifiedCompanies) {
        for (const job of company.job_postings) {
          if (!jobStatuses[job.job_id] && !loadingStatuses.has(job.job_id)) {
            setLoadingStatuses((prev) => new Set(prev).add(job.job_id));

            try {
              // TODO: fetchAdminJobStatus API 구현 필요
              // const statusData = await fetchAdminJobStatus(job.job_id);
              // setJobStatuses((prev) => ({
              //   ...prev,
              //   [job.job_id]: statusData.status,
              // }));
            } catch (error) {
              console.error(`작업 상태 조회 실패 (job_id: ${job.job_id}):`, error);
            } finally {
              setLoadingStatuses((prev) => {
                const newSet = new Set(prev);
                newSet.delete(job.job_id);
                return newSet;
              });
            }
          }
        }
      }
    };

    if (isOpen && adminCompanies.length > 0) {
      fetchJobStatuses();
    }
  }, [isOpen, adminCompanies, jobStatuses, loadingStatuses]);

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
  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '상시채용';
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

  // 작업 상태 텍스트와 색상 반환
  const getJobStatusInfo = (status: 'processing' | 'finished' | 'completed') => {
    switch (status) {
      case 'processing':
        return { text: '처리중', color: 'dabojob' as const };
      case 'finished':
        return { text: '최종완료', color: 'red' as const };
      case 'completed':
        return { text: '완료', color: 'green' as const };
      default:
        return { text: '알 수 없음', color: 'gray' as const };
    }
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
                  <div
                    key={index}
                    className="p-4 bg-blue-50 rounded-lg border border-blue-200 cursor-pointer hover:bg-blue-100 hover:shadow-md transition-all duration-200 ease-in-out"
                    onClick={() => handleCompanyClick(recruit.companyId, recruit.jobPostingId)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <Typography
                          variant="default"
                          weight="bold"
                          color="black"
                          className="mb-1 hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
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
                        {recruit.careerInfo === 'junior'
                          ? '신입'
                          : recruit.careerInfo === 'experienced'
                            ? '경력'
                            : recruit.careerInfo === 'senior'
                              ? '시니어'
                              : recruit.careerInfo}
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
                  <div
                    key={index}
                    className="p-4 bg-red-50 rounded-lg border border-red-200 cursor-pointer hover:bg-red-100 hover:shadow-md transition-all duration-200 ease-in-out"
                    onClick={() => handleCompanyClick(recruit.companyId, recruit.jobPostingId)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <Typography
                          variant="default"
                          weight="bold"
                          color="black"
                          className="mb-1 hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
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
                        {recruit.careerInfo === 'junior'
                          ? '신입'
                          : recruit.careerInfo === 'experienced'
                            ? '경력'
                            : recruit.careerInfo === 'senior'
                              ? '시니어'
                              : recruit.careerInfo}
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
                    <div
                      key={index}
                      className="p-4 bg-blue-50 rounded-lg border border-blue-200 cursor-pointer hover:bg-blue-100 hover:shadow-md transition-all duration-200 ease-in-out"
                      onClick={() => handleCompanyClick(recruit.companyId, recruit.jobPostingId)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <Typography
                            variant="default"
                            weight="bold"
                            color="black"
                            className="mb-1 hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
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
                          {recruit.careerInfo === 'junior'
                            ? '신입'
                            : recruit.careerInfo === 'experienced'
                              ? '경력'
                              : recruit.careerInfo === 'senior'
                                ? '시니어'
                                : recruit.careerInfo}
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

          {/* 관리자용 회사 섹션 */}
          {adminCompanies.length > 0 && (
            <div className="mb-6">
              <Typography
                as="h3"
                variant="title"
                weight="bold"
                color="dabojob"
                className="mb-3 text-lg"
              >
                관리자 - 회사 매핑 상태 ({adminCompanies.length}개)
              </Typography>
              {(() => {
                const groupedCompanies = groupCompaniesByGroup(adminCompanies);

                return (
                  <div className="space-y-4">
                    {Object.entries(groupedCompanies).map(([groupName, groupCompanies]) => (
                      <div key={groupName} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <Typography
                            as="h4"
                            variant="default"
                            weight="bold"
                            color="black"
                            className="text-base"
                          >
                            {groupName} 그룹
                          </Typography>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">
                              총 {groupCompanies.length}개 회사
                            </span>
                            <span className="text-sm text-green-600">
                              확인됨:{' '}
                              {groupCompanies.filter((c) => c.mapping_status === 'verified').length}
                            </span>
                            <span className="text-sm text-red-600">
                              실패:{' '}
                              {groupCompanies.filter((c) => c.mapping_status === 'failed').length}
                            </span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          {groupCompanies.map((company, index) => (
                            <div
                              key={index}
                              className={`p-3 rounded-lg border cursor-pointer hover:shadow-md transition-all duration-200 ease-in-out ${
                                company.mapping_status === 'verified'
                                  ? 'bg-green-50 border-green-200 hover:bg-green-100'
                                  : 'bg-red-50 border-red-200 hover:bg-red-100'
                              }`}
                              onClick={() => onAdminCalendarCompanyClick?.(company)}
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex-1">
                                  <Typography
                                    variant="recruits"
                                    weight="bold"
                                    color="black"
                                    className="mb-1 hover:text-blue-600 hover:underline transition-all duration-200 ease-in-out"
                                  >
                                    {company.company_name}
                                  </Typography>
                                  <div className="flex items-center gap-2 mb-2">
                                    <RecruitBadge
                                      type={
                                        company.mapping_status as
                                          | 'pending'
                                          | 'processing'
                                          | 'suggested'
                                          | 'verified'
                                          | 'rejected'
                                          | 'failed'
                                      }
                                      company=""
                                    />
                                    <span className="text-sm text-gray-600">
                                      채용공고 {company.job_count}개
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* 채용공고 목록 */}
                              <div className="space-y-1">
                                {company.job_postings.map((job, jobIndex) => (
                                  <div
                                    key={jobIndex}
                                    className="p-2 bg-white rounded border border-gray-100"
                                  >
                                    <div className="flex items-start justify-between mb-1">
                                      <Typography
                                        variant="recruits"
                                        weight="medium"
                                        color="black"
                                        className="text-sm flex-1"
                                      >
                                        {job.job_title}
                                      </Typography>

                                      {/* 작업 상태 표시 (verified 상태일 때만) */}
                                      {company.mapping_status === 'verified' && (
                                        <div className="ml-2">
                                          {loadingStatuses.has(job.job_id) ? (
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                          ) : jobStatuses[job.job_id] ? (
                                            <span
                                              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                getJobStatusInfo(jobStatuses[job.job_id]).color ===
                                                'dabojob'
                                                  ? 'bg-blue-100 text-blue-800'
                                                  : getJobStatusInfo(jobStatuses[job.job_id])
                                                        .color === 'green'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-200 text-gray-800'
                                              }`}
                                            >
                                              {getJobStatusInfo(jobStatuses[job.job_id]).text}
                                            </span>
                                          ) : null}
                                        </div>
                                      )}
                                    </div>

                                    <div className="text-xs text-gray-600">
                                      <div>
                                        📅 {formatDate(job.posting_date)} ~{' '}
                                        {formatDateTime(job.application_deadline)}
                                      </div>
                                      <div className="mt-1">
                                        <a
                                          href={job.job_url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:underline"
                                          onClick={(e) => e.stopPropagation()}
                                        >
                                          공고 보기 →
                                        </a>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          )}

          {/* 공고가 없는 경우 */}
          {allRecruits.length === 0 && adminCompanies.length === 0 && (
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
