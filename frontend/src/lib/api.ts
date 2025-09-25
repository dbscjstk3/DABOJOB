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
  url: string;
  title: string;
  content: string;
  postingDate: string;
}

// JobPosting API 응답 타입 정의
export interface JobPostingResponse {
  jobPostingId: number;
  companyId: number;
  companyName: string;
  companyType: string;
  title: string;
  url: string;
  jobSectorName: string;
  jobSectorCategory: string;
  careerInfo: 'junior' | 'experienced' | 'senior';
  postingDate: string;
  deadlineDate: string;
}

// 인기 공고 API 응답 타입 정의
export interface HotJobPostingResponse {
  jobPostingId: string;
  title: string;
}

// 관리자용 캘린더 채용공고 API 응답 타입 정의
export interface AdminCalendarJobPosting {
  job_id: number;
  job_title: string;
  posting_date: string;
  application_deadline: string | null;
  job_url: string;
}

export interface AdminCalendarCompany {
  company_id: number;
  company_name: string;
  mapping_status: 'pending' | 'processing' | 'suggested' | 'verified' | 'rejected' | 'failed';
  mapping_id: number;
  first_posting_date: string;
  last_posting_date: string;
  job_count: number;
  mapping_created_at: string;
  can_remap: boolean;
  job_postings: AdminCalendarJobPosting[];
}

export interface AdminJobPostingsResponse {
  year: number;
  month: number;
  total_companies: number;
  companies: AdminCalendarCompany[];
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
  careerInfo: 'junior' | 'experienced' | 'senior';
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

// Admin Mapping API 타입 정의
export interface AdminCompany {
  company_id: number;
  company_name: string;
  company_url: string | null;
  company_scale: string;
  company_group: string;
  created_at: string;
}

export interface AdminMapping {
  mapping_id: number;
  mapping_status: 'suggested' | 'failed' | 'rejected';
  dart_corp_name: string;
  dart_corp_code: string;
  dart_stock_code: string;
  confidence_score: number;
  gpt_response: string;
  manual_notes: string;
  processed_at: string | null;
  verified_at: string | null;
  verified_by: string | null;
  can_remap: boolean;
}

export interface AdminPeriod {
  year: number;
  month: number;
  first_posting_date: string;
  last_posting_date: string;
}

export interface AdminJobPosting {
  job_id: number;
  job_title: string;
  work_location: string;
  salary_info: string;
  career_info: string;
  education_requirement: string;
  posting_date: string;
  application_deadline: string;
  job_url: string;
  status: string;
  is_hot: boolean;
  registration_info: string;
}

export interface AdminMappingResponse {
  company: AdminCompany;
  mapping: AdminMapping;
  period: AdminPeriod;
  job_postings: AdminJobPosting[];
  job_postings_count: number;
}

export interface AdminMappingUpdateRequest {
  dart_corp_name: string;
  dart_corp_code: string;
  dart_stock_code: string;
  manual_notes?: string;
}

export interface AdminMappingUpdateResponse {
  status: 'success' | 'error';
  message: string;
  mapping: {
    company_id: number;
    company_name: string;
    dart_corp_name: string;
    dart_corp_code: string;
    dart_stock_code: string;
    job_count: number;
    confidence_score: number;
    verified_by: string;
    verified_at: string;
  };
}

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: (provider: string) => `${import.meta.env.VITE_API_BASE_URL}/api/auth/login/${provider}`,
    ME: `${import.meta.env.VITE_API_BASE_URL}/api/auth/me`,
    REFRESH: `${import.meta.env.VITE_API_BASE_URL}/api/auth/refresh`,
    LOGOUT: `${import.meta.env.VITE_API_BASE_URL}/api/auth/logout`,
  },
  SUMMARY: {
    DETAIL: (summaryId: string) => `${API_BASE_URL}/api/summaries/${summaryId}`,
  },
  NEWS: {
    BY_SUMMARY: (summaryId: string) => `${API_BASE_URL}/api/summaries/${summaryId}/news`,
    BY_HASHTAG: (summaryId: string | number, hashtagName: string) =>
      `${API_BASE_URL}/api/summaries/${summaryId}/news/${encodeURIComponent(hashtagName)}`,
  },
  JOB_POSTING: {
    DETAIL: (jobPostingId: string | number) => `${API_BASE_URL}/api/job-postings/${jobPostingId}`,
    AUTOCOMPLETE: (prefix: string) =>
      `${API_BASE_URL}/api/job-postings/suggestions?prefix=${encodeURIComponent(prefix)}`,
    SEARCH: (search: string, page?: number, size?: number) => {
      let url = `${API_BASE_URL}/api/job-postings?search=${encodeURIComponent(search)}`;
      if (page !== undefined) url += `&page=${page}`;
      if (size !== undefined) url += `&size=${size}`;
      return url;
    },
    CALENDAR: (startDate: string, endDate: string) =>
      `${API_BASE_URL}/api/job-postings/calendar?startDate=${startDate}&endDate=${endDate}`,
    HOT: `${API_BASE_URL}/api/job-postings/hot`,
    ADMIN: (year: number, month: number) =>
      `${API_BASE_URL}/api/admin/job-postings/calendar?year=${year}&month=${month}`,
  },
  ADMIN: {
    MAPPING: (companyId: number, year: number, month: number) =>
      `${API_BASE_URL}/api/admin/calendar/companies/${companyId}?year=${year}&month=${month}`,
    REMAP: (companyId: number) =>
      `${import.meta.env.VITE_ADMIN_API_BASE_URL}/api/admin/calendar/companies/${companyId}/remap`,
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

// 기간별 채용공고 조회 API 호출 함수
export const fetchJobPostingsByDateRange = async (
  startDate: string,
  endDate: string,
): Promise<JobPostingResponse[]> => {
  const url = API_ENDPOINTS.JOB_POSTING.CALENDAR(startDate, endDate);

  const response = await fetch(url, {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch job postings by date range: ${response.status}`);
  }

  const data = await response.json();
  return data;
};

// 인기 공고 API 호출 함수
export const fetchHotJobPostings = async (): Promise<HotJobPostingResponse[]> => {
  const response = await fetch(API_ENDPOINTS.JOB_POSTING.HOT, {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch hot job postings: ${response.status}`);
  }

  const data = await response.json();
  return data;
};

// 관리자 캘린더 채용공고 조회 API 호출 함수
export const fetchAdminJobPostings = async (
  year: number,
  month: number,
): Promise<AdminJobPostingsResponse> => {
  const response = await fetch(API_ENDPOINTS.JOB_POSTING.ADMIN(year, month), {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch admin job postings: ${response.status}`);
  }

  return response.json();
};

// 관리자 매핑 데이터 조회 API 호출 함수
export const fetchAdminMappingData = async (
  companyId: number,
  year: number,
  month: number,
): Promise<AdminMappingResponse> => {
  const response = await fetch(API_ENDPOINTS.ADMIN.MAPPING(companyId, year, month), {
    method: 'GET',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch admin mapping data: ${response.status}`);
  }

  return response.json();
};

// 관리자 매핑 업데이트 API 호출 함수
export const updateAdminMapping = async (
  companyId: number,
  data: AdminMappingUpdateRequest,
): Promise<AdminMappingUpdateResponse> => {
  const response = await fetch(API_ENDPOINTS.ADMIN.REMAP(companyId), {
    method: 'POST',
    credentials: 'include', // Cookie 포함
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to update admin mapping: ${response.status}`);
  }

  return response.json();
};

// 관리자용 완료 데이터 타입
export interface AdminJobCompleteDataResponse {
  job_id: number;
  status: 'completed';
  company_info: {
    company_name: string;
    company_scale: string;
  };
  summary_reports: {
    business_overview: string;
    products_services: string;
    revenue_orders: string;
    contracts_rnd: string;
    others: string;
  };
  news_data: Record<
    string,
    Record<
      string,
      {
        hashtag_id: number;
        news_items: Array<{
          news_id: number;
          title: string;
          url: string;
          published_date: string;
          summary: string;
          company_name: string;
          status: 'completed' | 'processing' | 'finished';
        }>;
      }
    >
  >;
  generated_at: string;
}

// 관리자용 완료 데이터 조회
export const fetchAdminJobCompleteData = async (
  jobId: number,
): Promise<AdminJobCompleteDataResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/admin/jobs/${jobId}/complete-data`, {
    method: 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch admin complete data: ${response.status}`);
  }
  return response.json();
};
