package com.dabojob.jobposting.service;

import com.dabojob.global.exception.RedisServiceException;
import java.util.Collections;
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

    private static final String USER_SEARCH_HISTORY_KEY = "search_history:%s"; // search_history:{userId}
    private static final String POPULAR_SEARCHES_KEY = "popular_searches"; // 전체 인기 검색어

    private static final Duration USER_HISTORY_TTL = Duration.ofDays(30); // 개인 검색어 30일
    private static final Duration POPULAR_SEARCHES_TTL = Duration.ofDays(7); // 인기 검색어 7일

    // 개인 검색어 최대 저장 개수
    private static final int MAX_USER_SEARCH_HISTORY = 20;

    // 사용자 검색어 기록 저장
    public void addSearchHistory(String userId, String searchKeyword) {
        try {
            if (searchKeyword == null || searchKeyword.trim().isEmpty()) {
                log.debug("Empty search keyword provided for user {}", userId);
                return;
            }

            String trimmedKeyword = searchKeyword.trim();
            String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

            // 현재 시간을 점수로 사용 (최신 검색어가 높은 점수)
            double score = System.currentTimeMillis();

            // 개인 검색어 기록 저장 (Sorted Set - 시간순 정렬)
            stringRedisTemplate.opsForZSet().add(userHistoryKey, trimmedKeyword, score);
            Long count = stringRedisTemplate.opsForZSet().count(userHistoryKey, Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY);
            if (count != null && count > MAX_USER_SEARCH_HISTORY) {
                long removeCount = count - MAX_USER_SEARCH_HISTORY;
                stringRedisTemplate.opsForZSet().removeRange(userHistoryKey, 0, removeCount - 1);
            }

            stringRedisTemplate.expire(userHistoryKey, USER_HISTORY_TTL);

            // 전체 인기 검색어 집계 (검색 빈도로 점수 증가)
            stringRedisTemplate.opsForZSet().incrementScore(POPULAR_SEARCHES_KEY, trimmedKeyword, 1.0);
            stringRedisTemplate.expire(POPULAR_SEARCHES_KEY, POPULAR_SEARCHES_TTL);

            log.info("Added search history for user {}: {}", userId, trimmedKeyword);

        } catch (Exception e) {
            log.error("Failed to add search history for user {} with keyword '{}'", userId, searchKeyword, e);
            // 예외 던지지 않음 - 검색 기능 자체는 계속 작동
        }
    }

    // 사용자의 최근 검색어 조회
    public List<String> getUserRecentSearches(String userId, int limit) {
        try {
            if (limit <= 0) {
                throw new IllegalArgumentException("Limit must be positive");
            }

            String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);
            Set<String> searches = stringRedisTemplate.opsForZSet().reverseRange(userHistoryKey, 0, limit - 1);

            return  searches != null ? List.copyOf(searches) : Collections.emptyList();

        } catch (IllegalArgumentException e) {
            throw e; // 파라미터 검증 예외는 그대로 전파
        } catch (Exception e) {
            log.error("Failed to get recent searches for user {} with limit {}", userId, limit, e);
            throw new RedisServiceException("Failed to retrieve recent search history", e);
        }
    }

    //전체 인기 검색어 조회
    public List<String> getPopularSearches(int limit) {
        try {
            if (limit <= 0) {
                throw new IllegalArgumentException("Limit must be positive");
            }

            Set<String> searches = stringRedisTemplate.opsForZSet().reverseRange(POPULAR_SEARCHES_KEY, 0, limit - 1);
            return searches != null ? List.copyOf(searches) : Collections.emptyList();

        } catch (IllegalArgumentException e) {
            throw e; // 파라미터 검증 예외는 그대로 전파
        } catch (Exception e) {
            log.error("Failed to get popular searches with limit {}", limit, e);
            throw new RedisServiceException("Failed to retrieve popular searches", e);
        }
    }

    // 사용자의 특정 검색어 삭제
    public void removeUserSearchHistory(String userId, String searchKeyword) {
        try {
            if (searchKeyword == null || searchKeyword.trim().isEmpty()) {
                throw new IllegalArgumentException("Search keyword cannot be empty");
            }

            String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

            Long removed = stringRedisTemplate.opsForZSet().remove(userHistoryKey, searchKeyword.trim());

            if (removed != null && removed > 0) {
                log.debug("Removed search history for user {}: {}", userId, searchKeyword);
            } else {
                log.debug("No search history found to remove for user {}: {}", userId, searchKeyword);
            }

        } catch (IllegalArgumentException e) {
            throw e; // 파라미터 검증 예외는 그대로 전파
        } catch (Exception e) {
            log.error("Failed to remove search history for user {} with keyword '{}'", userId, searchKeyword, e);
            throw new RedisServiceException("Failed to remove search history", e);
        }
    }

    // 사용자의 모든 검색어 기록 삭제
    public void clearUserSearchHistory(String userId) {
        try {
            String userHistoryKey = String.format(USER_SEARCH_HISTORY_KEY, userId);

            Boolean deleted = stringRedisTemplate.delete(userHistoryKey);

            if (deleted) {
                log.debug("Cleared all search history for user {}", userId);
            } else {
                log.debug("No search history found to clear for user {}", userId);
            }

        } catch (Exception e) {
            log.error("Failed to clear search history for user {}", userId, e);
            throw new RedisServiceException("Failed to clear search history", e);
        }
    }




}