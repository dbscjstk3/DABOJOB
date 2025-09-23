package com.dabojob.jobposting.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class ViewCountService {

    @Qualifier("customStringRedisTemplate")
    private final RedisTemplate<String, String> stringRedisTemplate;

    // Redis 키 패턴
    private static final String VIEW_COUNT_KEY = "views:%s"; // views:{jobPostingId}
    private static final String USER_VIEW_KEY = "user_view:%s:%s"; // user_view:{userId}:{jobPostingId}
    private static final String HOT_JOBS_KEY = "hot_jobs"; // Sorted Set for hot jobs

    // TTL 설정
    private static final Duration VIEW_COUNT_TTL = Duration.ofDays(7); // 7일
    private static final Duration USER_VIEW_TTL = Duration.ofHours(1); // 1시간

    // 조회수 증가 (사용자별 1시간 중복 체크). 증가 여부 반환
    public void incrementViewCount(String jobPostingId, String userId) {
        String userViewKey = String.format(USER_VIEW_KEY, userId, jobPostingId);
        String viewCountKey = String.format(VIEW_COUNT_KEY, jobPostingId);

        // 1시간 내 동일한 사용자의 조회 기록이 있는지 확인
        Boolean hasViewed = stringRedisTemplate.hasKey(userViewKey);

        if (hasViewed) {
            log.debug("User {} already viewed job {} within 1 hour", userId, jobPostingId);
            return;
        }

        // 사용자 조회 기록 저장 (1시간 TTL)
        stringRedisTemplate.opsForValue().set(userViewKey, "1", USER_VIEW_TTL);

        // 조회수 증가
        Long newCount = stringRedisTemplate.opsForValue().increment(viewCountKey);

        // 조회수 키에 TTL 설정 (처음 생성될 때만)
        if (newCount == 1) {
            stringRedisTemplate.expire(viewCountKey, VIEW_COUNT_TTL);
        }

        // 인기 공고 점수 업데이트 (Sorted Set)
        stringRedisTemplate.opsForZSet().incrementScore(HOT_JOBS_KEY, jobPostingId, 1.0);
        stringRedisTemplate.expire(HOT_JOBS_KEY, VIEW_COUNT_TTL);

        log.debug("View count incremented for job {} by user {}. New count: {}",
                jobPostingId, userId, newCount);
    }

    // 특정 채용공고의 조회수 조회
    public long getViewCount(String jobPostingId) {
        String viewCountKey = String.format(VIEW_COUNT_KEY, jobPostingId);
        String countStr = stringRedisTemplate.opsForValue().get(viewCountKey);

        if (countStr == null) {
            return 0L;
        }

        try {
            return Long.parseLong(countStr);
        } catch (NumberFormatException e) {
            log.warn("Invalid view count format for job {}: {}", jobPostingId, countStr);
            return 0L;
        }
    }

    // 인기 채용공고 ID 목록 조회 (조회수 기준 상위 N개)
    public Set<String> getHotJobPostings(int limit) {
        // Sorted Set에서 점수가 높은 순으로 조회
        return stringRedisTemplate.opsForZSet().reverseRange(HOT_JOBS_KEY, 0, limit - 1);
    }

    // 사용자가 특정 공고를 조회했는지 확인
    public boolean hasUserViewedRecently(String jobPostingId, String userId) {
        String userViewKey = String.format(USER_VIEW_KEY, userId, jobPostingId);
        return stringRedisTemplate.hasKey(userViewKey);
    }

    // 특정 채용공고의 모든 조회 데이터 삭제 (관리자용)
    public void clearViewData(String jobPostingId) {
        String viewCountKey = String.format(VIEW_COUNT_KEY, jobPostingId);

        // 조회수 삭제
        stringRedisTemplate.delete(viewCountKey);

        // 인기 공고에서 제거
        stringRedisTemplate.opsForZSet().remove(HOT_JOBS_KEY, jobPostingId);

        log.info("Cleared view data for job {}", jobPostingId);
    }
}