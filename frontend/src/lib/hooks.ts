import { useQuery } from '@tanstack/react-query';
import {
  fetchSummaryDetail,
  fetchNewsBySummary,
  fetchNewsByHashtag,
  fetchJobPosting,
  type SummaryResponse,
  type NewsResponse,
  type JobPostingResponse,
} from './api';

// Summary Detail을 가져오는 커스텀 훅
export const useSummaryDetail = (summaryId: string | undefined) => {
  return useQuery<SummaryResponse, Error>({
    queryKey: ['summaryDetail', summaryId],
    queryFn: () => {
      if (!summaryId) throw new Error('Summary ID is required');
      return fetchSummaryDetail(summaryId);
    },
    enabled: !!summaryId, // summaryId가 있을 때만 쿼리 실행
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분 (구 cacheTime)
    retry: 1, // 실패 시 1번만 재시도
  });
};

// News를 가져오는 커스텀 훅
export const useNews = (summaryId: string | undefined) => {
  return useQuery<NewsResponse[], Error>({
    queryKey: ['news', summaryId],
    queryFn: () => {
      if (!summaryId) throw new Error('Summary ID is required for news');
      return fetchNewsBySummary(summaryId);
    },
    enabled: !!summaryId,
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 1,
  });
};

// 해시태그별 News를 가져오는 커스텀 훅
export const useNewsByHashtag = (
  summaryId: string | undefined,
  hashtagName: string | null | undefined,
) => {
  return useQuery<NewsResponse[], Error>({
    queryKey: ['news', summaryId, 'hashtag', hashtagName],
    queryFn: () => {
      if (!summaryId) throw new Error('Summary ID is required for news');
      if (!hashtagName) return []; // 해시태그가 없으면 빈 배열 반환
      return fetchNewsByHashtag(summaryId, hashtagName);
    },
    enabled: !!summaryId && !!hashtagName, // 둘 다 있을 때만 실행
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 1,
    // 빈 배열도 성공으로 처리
    select: (data) => data || [],
  });
};

// JobPosting을 가져오는 커스텀 훅
export const useJobPosting = (jobPostingId: string | undefined) => {
  return useQuery<JobPostingResponse, Error>({
    queryKey: ['jobPosting', jobPostingId],
    queryFn: () => {
      if (!jobPostingId) throw new Error('Job Posting ID is required');
      return fetchJobPosting(jobPostingId);
    },
    enabled: !!jobPostingId, // jobPostingId가 있을 때만 쿼리 실행
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 1,
  });
};
