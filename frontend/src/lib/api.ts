// API 관련 상수 및 유틸리티 함수
// MSW 사용 시에는 상대 경로로, 실제 API 사용 시에는 전체 URL 사용
export const API_BASE_URL =
  import.meta.env.VITE_USE_MSW === 'true' ? '' : import.meta.env.VITE_API_BASE_URL;

// Summary API 응답 타입 정의
export interface SummaryResponse {
  summaryId: number;
  companyId: number;
  companyName: string;
  businessOverview: string;
  productsService: string;
  salesContracts: string;
  rndActivities: string;
  otherNotes: string;
  chapterHashtags: {
    BUSINESS_OVERVIEW: string[];
    PRODUCTS_SERVICE: string[];
    SALES_CONTRACTS: string[];
    RND_ACTIVITIES: string[];
    OTHER_NOTES: string[];
  };
}

// News API 응답 타입 정의
export interface NewsResponse {
  newsId: number;
  summaryHashtagId: number;
  newsUrl: string;
  newsTitle: string;
  newsContent: string;
  newsCreateDate: string;
}

// JobPosting API 응답 타입 정의
export interface JobPostingResponse {
  jobPostingId: number;
  companyId: number;
  companyName: string;
  title: string;
  url: string;
  jobSectorName: string;
  jobSectorCategory: string;
  careerInfo: string;
  postingDate: string;
  deadlineDate: string;
}

// 자동완성 API 응답 타입 정의
export interface AutocompleteJobPosting {
  jobPostingId: number;
  companyId: number;
  companyName: string;
  title: string;
  url: string;
  jobSectorId: number;
  jobSectorName: string;
  jobSectorCategory: string;
  careerInfo: string;
  postingDate: string;
  deadlineDate: string;
}

export interface AutocompleteResponse {
  content: AutocompleteJobPosting[];
  pageable: {
    pageNumber: number;
    pageSize: number;
    sort: {
      empty: boolean;
      sorted: boolean;
      unsorted: boolean;
    };
    offset: number;
    paged: boolean;
    unpaged: boolean;
  };
  last: boolean;
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
  sort: {
    empty: boolean;
    sorted: boolean;
    unsorted: boolean;
  };
  first: boolean;
  numberOfElements: number;
  empty: boolean;
}

// 검색 API 응답 타입 정의 (AutocompleteResponse와 동일한 구조)
export type SearchJobPostingResponse = AutocompleteResponse;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: (provider: string) => `${import.meta.env.VITE_API_BASE_URL}/api/auth/login/${provider}`,
    ME: `${import.meta.env.VITE_API_BASE_URL}/api/auth/me`,
    REFRESH: `${import.meta.env.VITE_API_BASE_URL}/api/auth/refresh`,
    LOGOUT: `${import.meta.env.VITE_API_BASE_URL}/api/auth/logout`,
  },
  SUMMARY: {
    DETAIL: (summaryId: string) => `${API_BASE_URL}/api/summary/${summaryId}`,
  },
  NEWS: {
    BY_SUMMARY: (summaryId: string) => `${API_BASE_URL}/api/summary/${summaryId}/news`,
    BY_HASHTAG: (summaryId: string | number, hashtagName: string) =>
      `${API_BASE_URL}/api/summary/${summaryId}/news/${encodeURIComponent(hashtagName)}`,
  },
  JOB_POSTING: {
    DETAIL: (jobPostingId: string | number) => `${API_BASE_URL}/api/job-posting/${jobPostingId}`,
    AUTOCOMPLETE: (prefix: string) =>
      `${API_BASE_URL}/api/job-postings/suggestions?prefix=${encodeURIComponent(prefix)}`,
    SEARCH: (search: string, page?: number, size?: number) => {
      let url = `${API_BASE_URL}/api/job-postings?search=${encodeURIComponent(search)}`;
      if (page !== undefined) url += `&page=${page}`;
      if (size !== undefined) url += `&size=${size}`;
      return url;
    },
  },
} as const;

// API 호출 함수
export const fetchSummaryDetail = async (summaryId: string): Promise<SummaryResponse> => {
  const response = await fetch(API_ENDPOINTS.SUMMARY.DETAIL(summaryId), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch summary detail: ${response.status}`);
  }

  return response.json();
};

// News API 호출 함수
export const fetchNewsBySummary = async (summaryId: string): Promise<NewsResponse[]> => {
  const response = await fetch(API_ENDPOINTS.NEWS.BY_SUMMARY(summaryId), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch news: ${response.status}`);
  }

  return response.json();
};

// 해시태그별 News API 호출 함수
export const fetchNewsByHashtag = async (
  summaryId: string | number,
  hashtagName: string,
): Promise<NewsResponse[]> => {
  const response = await fetch(API_ENDPOINTS.NEWS.BY_HASHTAG(summaryId, hashtagName), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
      // Access Token이 필요한 경우 여기에 추가
      // 'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  if (!response.ok) {
    // 404나 빈 결과는 빈 배열 반환
    if (response.status === 404) {
      return [];
    }
    throw new Error(`Failed to fetch news by hashtag: ${response.status}`);
  }

  const data = await response.json();
  // 빈 배열이거나 null인 경우 빈 배열 반환
  return data || [];
};

// JobPosting API 호출 함수
export const fetchJobPosting = async (
  jobPostingId: string | number,
): Promise<JobPostingResponse> => {
  const response = await fetch(API_ENDPOINTS.JOB_POSTING.DETAIL(jobPostingId), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch job posting: ${response.status}`);
  }

  return response.json();
};

// 자동완성 API 호출 함수
export const fetchAutocomplete = async (prefix: string): Promise<AutocompleteResponse> => {
  // prefix가 비어있으면 빈 결과 반환
  if (!prefix || prefix.trim().length === 0) {
    return {
      content: [],
      pageable: {
        pageNumber: 0,
        pageSize: 10,
        sort: { empty: true, sorted: false, unsorted: true },
        offset: 0,
        paged: true,
        unpaged: false,
      },
      last: true,
      totalElements: 0,
      totalPages: 0,
      size: 10,
      number: 0,
      sort: { empty: true, sorted: false, unsorted: true },
      first: true,
      numberOfElements: 0,
      empty: true,
    };
  }

  const response = await fetch(API_ENDPOINTS.JOB_POSTING.AUTOCOMPLETE(prefix), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch autocomplete results: ${response.status}`);
  }

  return response.json();
};

// 검색 API 호출 함수
export const fetchSearchJobPostings = async (
  search: string,
  page?: number,
  size?: number,
): Promise<SearchJobPostingResponse> => {
  const response = await fetch(API_ENDPOINTS.JOB_POSTING.SEARCH(search, page, size), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch search results: ${response.status}`);
  }

  return response.json();
};
