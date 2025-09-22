import type { AutocompleteJobPosting, AutocompleteResponse } from '@/lib/api';

// 모든 채용공고 목 데이터
export const mockJobPostings: AutocompleteJobPosting[] = [
  // 삼성전자
  {
    jobPostingId: 1,
    companyId: 1,
    companyName: '삼성전자',
    title: 'AI 반도체 개발 엔지니어',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123456',
    jobSectorId: 100,
    jobSectorName: '반도체 설계',
    jobSectorCategory: 'IT/하드웨어',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-15',
    deadlineDate: '2025-12-31',
  },
  {
    jobPostingId: 2,
    companyId: 123,
    companyName: '삼성전자',
    title: '메모리 반도체 연구원',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123457',
    jobSectorId: 101,
    jobSectorName: '연구개발',
    jobSectorCategory: '연구/R&D',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-10',
    deadlineDate: '2025-02-15',
  },
  {
    jobPostingId: 3,
    companyId: 123,
    companyName: '삼성전자',
    title: 'HBM 메모리 설계 엔지니어',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123458',
    jobSectorId: 100,
    jobSectorName: '반도체 설계',
    jobSectorCategory: 'IT/하드웨어',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-20',
    deadlineDate: '2025-03-31',
  },

  // 삼성SDI
  {
    jobPostingId: 4,
    companyId: 124,
    companyName: '삼성SDI',
    title: '배터리 연구개발 엔지니어',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=124456',
    jobSectorId: 102,
    jobSectorName: '배터리 기술',
    jobSectorCategory: '연구/R&D',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-18',
    deadlineDate: '2025-01-20',
  },
  {
    jobPostingId: 5,
    companyId: 124,
    companyName: '삼성SDI',
    title: '전기차 배터리 품질관리',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=124457',
    jobSectorId: 103,
    jobSectorName: '품질관리',
    jobSectorCategory: '제조/생산',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-12',
    deadlineDate: '2024-12-28',
  },

  // LG전자
  {
    jobPostingId: 6,
    companyId: 456,
    companyName: 'LG전자',
    title: '전기차 SW 개발자',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=456789',
    jobSectorId: 200,
    jobSectorName: '소프트웨어 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-10',
    deadlineDate: '2024-12-25',
  },
  {
    jobPostingId: 7,
    companyId: 456,
    companyName: 'LG전자',
    title: '스마트홈 IoT 개발자',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=456790',
    jobSectorId: 200,
    jobSectorName: 'IoT 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-14',
    deadlineDate: '2025-01-10',
  },

  // SK하이닉스
  {
    jobPostingId: 8,
    companyId: 789,
    companyName: 'SK하이닉스',
    title: '메모리 반도체 연구원',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=789012',
    jobSectorId: 300,
    jobSectorName: '반도체 연구',
    jobSectorCategory: '연구/R&D',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-20',
    deadlineDate: '2025-02-28',
  },
  {
    jobPostingId: 9,
    companyId: 789,
    companyName: 'SK하이닉스',
    title: 'DRAM 설계 엔지니어',
    url: 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=789013',
    jobSectorId: 301,
    jobSectorName: 'DRAM 설계',
    jobSectorCategory: 'IT/하드웨어',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-16',
    deadlineDate: '2025-01-25',
  },

  // 네이버
  {
    jobPostingId: 10,
    companyId: 1001,
    companyName: '네이버',
    title: '프론트엔드 개발자',
    url: 'https://career.navercorp.com/jobs/12345',
    jobSectorId: 400,
    jobSectorName: '웹 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-22',
    deadlineDate: '2025-01-15',
  },
  {
    jobPostingId: 11,
    companyId: 1001,
    companyName: '네이버',
    title: '백엔드 개발자 (Java/Spring)',
    url: 'https://career.navercorp.com/jobs/12346',
    jobSectorId: 401,
    jobSectorName: '서버 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-19',
    deadlineDate: '2025-02-10',
  },
  {
    jobPostingId: 12,
    companyId: 1001,
    companyName: '네이버',
    title: 'AI 연구 엔지니어',
    url: 'https://career.navercorp.com/jobs/12347',
    jobSectorId: 402,
    jobSectorName: 'AI/ML',
    jobSectorCategory: '연구/R&D',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-17',
    deadlineDate: '2025-01-28',
  },

  // 카카오
  {
    jobPostingId: 13,
    companyId: 1002,
    companyName: '카카오',
    title: '모바일 앱 개발자 (iOS)',
    url: 'https://careers.kakao.com/jobs/P-13456',
    jobSectorId: 500,
    jobSectorName: '모바일 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-21',
    deadlineDate: '2025-01-18',
  },
  {
    jobPostingId: 14,
    companyId: 1002,
    companyName: '카카오',
    title: '데이터 분석가',
    url: 'https://careers.kakao.com/jobs/P-13457',
    jobSectorId: 501,
    jobSectorName: '데이터 분석',
    jobSectorCategory: 'IT/데이터',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-13',
    deadlineDate: '2025-01-05',
  },

  // 현대자동차
  {
    jobPostingId: 15,
    companyId: 2001,
    companyName: '현대자동차',
    title: '전기차 배터리 엔지니어',
    url: 'https://recruit.hyundai.com/jobs/15001',
    jobSectorId: 600,
    jobSectorName: '자동차 엔지니어링',
    jobSectorCategory: '자동차/기계',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-14',
    deadlineDate: '2025-02-14',
  },
  {
    jobPostingId: 16,
    companyId: 2001,
    companyName: '현대자동차',
    title: '자율주행 SW 개발자',
    url: 'https://recruit.hyundai.com/jobs/15002',
    jobSectorId: 601,
    jobSectorName: '자율주행',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-11',
    deadlineDate: '2025-01-22',
  },

  // 배달의민족 (우아한형제들)
  {
    jobPostingId: 17,
    companyId: 3001,
    companyName: '우아한형제들',
    title: '백엔드 개발자',
    url: 'https://www.woowahan.com/jobs/backend-001',
    jobSectorId: 700,
    jobSectorName: '서버 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-23',
    deadlineDate: '2025-01-30',
  },
  {
    jobPostingId: 18,
    companyId: 3001,
    companyName: '우아한형제들',
    title: '프론트엔드 개발자 (React)',
    url: 'https://www.woowahan.com/jobs/frontend-001',
    jobSectorId: 701,
    jobSectorName: '웹 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'JUNIOR',
    postingDate: '2024-12-20',
    deadlineDate: '2025-01-27',
  },

  // 당근마켓
  {
    jobPostingId: 19,
    companyId: 4001,
    companyName: '당근마켓',
    title: '안드로이드 개발자',
    url: 'https://team.daangn.com/jobs/android-001',
    jobSectorId: 800,
    jobSectorName: '모바일 개발',
    jobSectorCategory: 'IT/소프트웨어',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-06',
    deadlineDate: '2024-12-30',
  },
  {
    jobPostingId: 20,
    companyId: 4001,
    companyName: '당근마켓',
    title: 'DevOps 엔지니어',
    url: 'https://team.daangn.com/jobs/devops-001',
    jobSectorId: 801,
    jobSectorName: 'DevOps',
    jobSectorCategory: 'IT/인프라',
    careerInfo: 'EXPERIENCED',
    postingDate: '2024-12-08',
    deadlineDate: '2025-10-12',
  },
];

// 검색어에 따라 필터링된 결과를 반환하는 함수
export function getFilteredJobPostings(prefix: string): AutocompleteJobPosting[] {
  if (!prefix || prefix.trim().length === 0) {
    return [];
  }

  const searchTerm = prefix.toLowerCase().trim();

  return mockJobPostings
    .filter(
      (job) =>
        job.companyName.toLowerCase().includes(searchTerm) ||
        job.title.toLowerCase().includes(searchTerm) ||
        job.jobSectorName.toLowerCase().includes(searchTerm) ||
        job.jobSectorCategory.toLowerCase().includes(searchTerm),
    )
    .slice(0, 10); // 최대 10개까지만 반환
}

// MSW용 자동완성 응답 생성 함수
export function createAutocompleteResponse(
  filteredJobs: AutocompleteJobPosting[],
): AutocompleteResponse {
  return {
    content: filteredJobs,
    pageable: {
      pageNumber: 0,
      pageSize: 10,
      sort: {
        empty: true,
        sorted: false,
        unsorted: true,
      },
      offset: 0,
      paged: true,
      unpaged: false,
    },
    last: true,
    totalElements: filteredJobs.length,
    totalPages: filteredJobs.length > 0 ? 1 : 0,
    size: 10,
    number: 0,
    sort: {
      empty: true,
      sorted: false,
      unsorted: true,
    },
    first: true,
    numberOfElements: filteredJobs.length,
    empty: filteredJobs.length === 0,
  };
}
