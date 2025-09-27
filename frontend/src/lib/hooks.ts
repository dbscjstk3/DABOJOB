import { useQuery, useMutation, keepPreviousData } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { queryClient } from './queryClient';
import {
  fetchSummaryDetail,
  fetchNewsBySummary,
  fetchNewsByHashtag,
  fetchJobPosting,
  fetchAutocomplete,
  fetchSearchJobPostings,
  fetchRecentSearches,
  fetchAdminMappingData,
  updateAdminMapping,
  fetchAdminJobCompleteData,
  requestJobReprocessing,
  approveJob,
  type SummaryResponse,
  type NewsResponse,
  type JobPostingResponse,
  type AutocompleteResponse,
  type SearchJobPostingResponse,
  type AdminMappingResponse,
  type AdminMappingUpdateRequest,
  type AdminMappingUpdateResponse,
  type AdminJobCompleteResponse,
  type AdminJobReprocessingResponse,
  type AdminJobApproveResponse,
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

// 디바운싱 훅
export const useDebouncedValue = <T>(value: T, delay: number = 300): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

// 자동완성을 위한 커스텀 훅
export const useAutocomplete = (searchQuery: string) => {
  const debouncedQuery = useDebouncedValue(searchQuery, 300);

  return useQuery<AutocompleteResponse, Error>({
    queryKey: ['autocomplete', debouncedQuery],
    queryFn: () => fetchAutocomplete(debouncedQuery),
    enabled: debouncedQuery.length > 0, // 검색어가 있을 때만 실행
    staleTime: 30 * 1000, // 30초
    gcTime: 60 * 1000, // 1분
    retry: 0, // 자동완성은 재시도 안함
  });
};

// 최근 검색어를 가져오는 커스텀 훅
export const useRecentSearches = (limit: number = 5) => {
  return useQuery<string[], Error>({
    queryKey: ['recentSearches', limit],
    queryFn: () => fetchRecentSearches(limit),
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 0, // 실패 시 재시도 안함
  });
};

// 검색을 위한 커스텀 훅
export const useSearchJobPostings = (search: string, page?: number, size?: number) => {
  return useQuery<SearchJobPostingResponse, Error>({
    queryKey: ['searchJobPostings', search, page, size],
    queryFn: () => fetchSearchJobPostings(search, page, size),
    enabled: search.length > 0, // 검색어가 있을 때만 실행
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 1, // 실패 시 1번만 재시도
    placeholderData: keepPreviousData, // 페이지 전환 시 이전 데이터 유지
  });
};

// 관리자 매핑 데이터를 가져오는 커스텀 훅
export const useAdminMappingData = (companyId: number | undefined, year: number, month: number) => {
  return useQuery<AdminMappingResponse, Error>({
    queryKey: ['adminMapping', companyId, year, month],
    queryFn: () => {
      if (!companyId) throw new Error('Company ID is required');
      return fetchAdminMappingData(companyId, year, month);
    },
    enabled: !!companyId, // companyId가 있을 때만 쿼리 실행
    staleTime: 2 * 60 * 1000, // 2분 (관리자 데이터는 짧게)
    gcTime: 5 * 60 * 1000, // 5분
    retry: 1, // 실패 시 1번만 재시도
  });
};

// 관리자 매핑 업데이트를 위한 커스텀 훅
export const useAdminMappingUpdate = (companyId: number, year: number, month: number) => {
  return useMutation<AdminMappingUpdateResponse, Error, AdminMappingUpdateRequest>({
    mutationFn: (data) => updateAdminMapping(companyId, data),
    onSuccess: () => {
      // 성공 시 관련 쿼리 캐시 무효화
      queryClient.invalidateQueries({ queryKey: ['adminMapping', companyId, year, month] });
    },
    onError: (error) => {
      console.error('Admin mapping update failed:', error);
    },
  });
};

// 관리자 Job Complete 데이터를 가져오는 커스텀 훅
export const useAdminJobCompleteData = (jobId: string | number | undefined) => {
  return useQuery<AdminJobCompleteResponse, Error>({
    queryKey: ['adminJobComplete', jobId],
    queryFn: () => {
      if (!jobId) throw new Error('Job ID is required');
      return fetchAdminJobCompleteData(jobId);
    },
    enabled: !!jobId,
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 1,
  });
};

// Job 재요약 요청을 위한 커스텀 훅
export const useJobReprocessingMutation = (jobId: string | number) => {
  return useMutation<AdminJobReprocessingResponse, Error>({
    mutationFn: () => requestJobReprocessing(jobId),
    onSuccess: (data) => {
      console.log('Job reprocessing requested:', data);
      // 성공 시 관련 쿼리 캐시 무효화
      queryClient.invalidateQueries({ queryKey: ['adminJobComplete', jobId] });
    },
    onError: (error) => {
      console.error('Job reprocessing failed:', error);
    },
  });
};

// Job 승인을 위한 커스텀 훅
export const useJobApproveMutation = (jobId: string | number) => {
  return useMutation<AdminJobApproveResponse, Error>({
    mutationFn: () => approveJob(jobId),
    onSuccess: (data) => {
      console.log('Job approved:', data);
      // 성공 시 관련 쿼리 캐시 무효화
      queryClient.invalidateQueries({ queryKey: ['adminJobComplete', jobId] });
    },
    onError: (error) => {
      console.error('Job approval failed:', error);
    },
  });
};
