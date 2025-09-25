import type { AutocompleteJobPosting } from '@/lib/api';

// 검색용 전체 채용공고 mock 데이터
export const mockJobPostings: AutocompleteJobPosting[] = [
  // 삼성전자
  {
    jobPostingId: 2,
    companyId: 1,
    companyName: '삼성전자',
    title: '백엔드 개발자 채용',
    url: 'https://example.com/job/1',
    jobSectorId: 100,
    jobSectorName: '서버/백엔드 개발',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'senior',
    postingDate: '2024-09-16',
    deadlineDate: '2024-10-16',
  },
  {
    jobPostingId: 1,
    companyId: 1,
    companyName: '삼성전자',
    title: 'AI 반도체 개발 엔지니어',
    url: 'https://example.com/job/2',
    jobSectorId: 101,
    jobSectorName: '반도체 설계',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'junior',
    postingDate: '2024-12-15',
    deadlineDate: '2025-12-31',
  },
  {
    jobPostingId: 3,
    companyId: 1,
    companyName: '삼성전자',
    title: '프론트엔드 개발자 모집',
    url: 'https://example.com/job/3',
    jobSectorId: 102,
    jobSectorName: '웹 프론트엔드',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'junior',
    postingDate: '2024-12-20',
    deadlineDate: '2025-01-20',
  },

  // LG전자
  {
    jobPostingId: 4,
    companyId: 2,
    companyName: 'LG전자',
    title: '전기차 SW 개발자',
    url: 'https://example.com/job/4',
    jobSectorId: 103,
    jobSectorName: '소프트웨어 개발',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'junior',
    postingDate: '2024-12-10',
    deadlineDate: '2024-12-25',
  },
  {
    jobPostingId: 5,
    companyId: 2,
    companyName: 'LG전자',
    title: 'IoT 플랫폼 개발자',
    url: 'https://example.com/job/5',
    jobSectorId: 104,
    jobSectorName: 'IoT',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'junior',
    postingDate: '2024-12-18',
    deadlineDate: '2025-02-28',
  },

  // SK하이닉스
  {
    jobPostingId: 6,
    companyId: 3,
    companyName: 'SK하이닉스',
    title: '메모리 반도체 연구원',
    url: 'https://example.com/job/6',
    jobSectorId: 105,
    jobSectorName: '연구개발',
    jobSectorCategory: '연구·R&D',
    careerInfo: 'senior',
    postingDate: '2024-12-20',
    deadlineDate: '2025-02-28',
  },
  {
    jobPostingId: 7,
    companyId: 3,
    companyName: 'SK하이닉스',
    title: 'HBM 공정 엔지니어',
    url: 'https://example.com/job/7',
    jobSectorId: 106,
    jobSectorName: '공정 개발',
    jobSectorCategory: '엔지니어링·설계',
    careerInfo: 'junior',
    postingDate: '2024-12-22',
    deadlineDate: '2025-01-15',
  },

  // 네이버
  {
    jobPostingId: 8,
    companyId: 4,
    companyName: '네이버',
    title: '클라우드 플랫폼 개발자',
    url: 'https://example.com/job/8',
    jobSectorId: 107,
    jobSectorName: '클라우드',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'senior',
    postingDate: '2024-12-01',
    deadlineDate: '2025-01-10',
  },
  {
    jobPostingId: 9,
    companyId: 4,
    companyName: '네이버',
    title: 'AI 연구원',
    url: 'https://example.com/job/9',
    jobSectorId: 108,
    jobSectorName: 'AI/ML',
    jobSectorCategory: '연구·R&D',
    careerInfo: 'junior',
    postingDate: '2024-12-05',
    deadlineDate: '2025-01-25',
  },

  // 카카오
  {
    jobPostingId: 10,
    companyId: 5,
    companyName: '카카오',
    title: '백엔드 개발자 (Java/Kotlin)',
    url: 'https://example.com/job/10',
    jobSectorId: 109,
    jobSectorName: '서버/백엔드 개발',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'junior',
    postingDate: '2024-12-08',
    deadlineDate: '2025-01-30',
  },
  {
    jobPostingId: 11,
    companyId: 5,
    companyName: '카카오',
    title: '데이터 엔지니어',
    url: 'https://example.com/job/11',
    jobSectorId: 110,
    jobSectorName: '데이터 엔지니어링',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'senior',
    postingDate: '2024-12-12',
    deadlineDate: '2025-02-10',
  },

  // 교보문고
  {
    jobPostingId: 12,
    companyId: 12,
    companyName: '교보문고',
    title: '전자책 플랫폼 개발자',
    url: 'https://example.com/job/12',
    jobSectorId: 400,
    jobSectorName: '웹 개발',
    jobSectorCategory: '미디어·문화·스포츠',
    careerInfo: 'junior',
    postingDate: '2024-08-31',
    deadlineDate: '2024-09-30',
  },

  // 현대자동차
  {
    jobPostingId: 13,
    companyId: 6,
    companyName: '현대자동차',
    title: '자율주행 SW 개발자',
    url: 'https://example.com/job/13',
    jobSectorId: 111,
    jobSectorName: '자율주행',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'senior',
    postingDate: '2024-12-14',
    deadlineDate: '2025-02-20',
  },
  {
    jobPostingId: 14,
    companyId: 6,
    companyName: '현대자동차',
    title: '모빌리티 플랫폼 개발자',
    url: 'https://example.com/job/14',
    jobSectorId: 112,
    jobSectorName: '플랫폼 개발',
    jobSectorCategory: 'IT개발·데이터',
    careerInfo: 'junior',
    postingDate: '2024-12-16',
    deadlineDate: '2025-01-31',
  },
];

// 검색 함수
export function searchJobPostings(searchQuery: string, page: number = 0, size: number = 20) {
  const query = searchQuery.toLowerCase().trim();

  // 검색어로 필터링
  let filtered = mockJobPostings;
  if (query) {
    filtered = mockJobPostings.filter(
      (job) =>
        job.companyName.toLowerCase().includes(query) ||
        job.title.toLowerCase().includes(query) ||
        job.jobSectorName.toLowerCase().includes(query) ||
        job.jobSectorCategory.toLowerCase().includes(query),
    );
  }

  // 페이지네이션
  const totalElements = filtered.length;
  const totalPages = Math.ceil(totalElements / size);
  const start = page * size;
  const end = start + size;
  const content = filtered.slice(start, end);

  return {
    content,
    pageable: {
      pageNumber: page,
      pageSize: size,
      sort: {
        empty: false,
        sorted: true,
        unsorted: false,
      },
      offset: start,
      paged: true,
      unpaged: false,
    },
    last: page >= totalPages - 1,
    totalElements,
    totalPages,
    size,
    number: page,
    sort: {
      empty: false,
      sorted: true,
      unsorted: false,
    },
    first: page === 0,
    numberOfElements: content.length,
    empty: content.length === 0,
  };
}
