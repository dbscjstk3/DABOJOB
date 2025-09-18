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

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: (provider: string) => `${API_BASE_URL}/api/auth/login/${provider}`,
    ME: `${API_BASE_URL}/api/auth/me`,
    REFRESH: `${API_BASE_URL}/api/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
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
