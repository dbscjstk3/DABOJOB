package com.dabojob.jobposting.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.List;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class SearchHistoryService {

    @Qualifier("customStringRedisTemplate")
    private final RedisTemplate<String, String> stringRedisTemplate;

    // Redis 키 패턴
    private static final String USER_SEARCH_HISTORY_KEY = "search_history:%s"; // search_history:{userId}
    private static final String POPULAR_SEARCHES_KEY = "popular_searches"; // 전체 인기 검색어

    // TTL 설정
    private static final Duration USER_HISTORY_TTL = Duration.ofDays(30); // 개인 검색어 30일
    private static final Duration POPULAR_SEARCHES_TTL = Duration.ofDays(7); // 인기 검색어 7일

    // 개인 검색어 최대 저장 개수
    private static final int MAX_USER_SEARCH_HISTORY = 20;

    // 사용자 검색어 기록 저장
    public void addSearchHistory(String userId, String searchKeyword) {
        if (searchKeyword == null || searchKeyword.trim().isEmpty()) {
            return;
        }

        String trimmedKeyword = searchKeyword.trim();
        String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

        // 현재 시간을 점수로 사용 (최신 검색어가 높은 점수)
        double score = System.currentTimeMillis();

        // 개인 검색어 기록 저장 (Sorted Set - 시간순 정렬)
        stringRedisTemplate.opsForZSet().add(userHistoryKey, trimmedKeyword, score);

        // 개인 검색어 기록 개수 제한 (오래된 것부터 삭제)
        Long count = stringRedisTemplate.opsForZSet().count(userHistoryKey, Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY);
        if (count != null && count > MAX_USER_SEARCH_HISTORY) {
            long removeCount = count - MAX_USER_SEARCH_HISTORY;
            stringRedisTemplate.opsForZSet().removeRange(userHistoryKey, 0, removeCount - 1);
        }

        // TTL 설정
        stringRedisTemplate.expire(userHistoryKey, USER_HISTORY_TTL);

        // 전체 인기 검색어 집계 (검색 빈도로 점수 증가)
        stringRedisTemplate.opsForZSet().incrementScore(POPULAR_SEARCHES_KEY, trimmedKeyword, 1.0);
        stringRedisTemplate.expire(POPULAR_SEARCHES_KEY, POPULAR_SEARCHES_TTL);

        log.debug("Added search history for user {}: {}", userId, trimmedKeyword);
    }

    // 사용자의 최근 검색어 조회
    public List<String> getUserRecentSearches(String userId, int limit) {
        String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

        // 점수가 높은 순으로 조회 (최신순)
        Set<String> searches = stringRedisTemplate.opsForZSet().reverseRange(userHistoryKey, 0, limit - 1);

        return searches != null ? List.copyOf(searches) : List.of();
    }

    //전체 인기 검색어 조회
    public List<String> getPopularSearches(int limit) {
        // 점수가 높은 순으로 조회 (인기순)
        Set<String> searches = stringRedisTemplate.opsForZSet().reverseRange(POPULAR_SEARCHES_KEY, 0, limit - 1);

        return searches != null ? List.copyOf(searches) : List.of();
    }

    // 사용자의 특정 검색어 삭제
    public void removeUserSearchHistory(String userId, String searchKeyword) {
        String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

        Long removed = stringRedisTemplate.opsForZSet().remove(userHistoryKey, searchKeyword);

        if (removed != null && removed > 0) {
            log.debug("Removed search history for user {}: {}", userId, searchKeyword);
        }
    }

    // 사용자의 모든 검색어 기록 삭제
    public void clearUserSearchHistory(String userId) {
        String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

        Boolean deleted = stringRedisTemplate.delete(userHistoryKey);

        if (deleted) {
            log.info("Cleared all search history for user {}", userId);
        }
    }

    // 특정 검색어의 검색 빈도 조회
    public Double getSearchFrequency(String searchKeyword) {
        return stringRedisTemplate.opsForZSet().score(POPULAR_SEARCHES_KEY, searchKeyword);
    }


}