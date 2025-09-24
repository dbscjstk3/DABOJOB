package com.dabojob.jobposting.service;

import com.dabojob.global.exception.RedisServiceException;
import com.dabojob.jobposting.dto.HotJobPostingResponse;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

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
    private static final String JOB_TITLES_KEY = "job_titles"; // Hash for job titles

    // TTL 설정
    private static final Duration VIEW_COUNT_TTL = Duration.ofDays(7); // 7일
    private static final Duration USER_VIEW_TTL = Duration.ofHours(1); // 1시간
    private static final Duration JOB_TITLES_TTL = Duration.ofDays(7); // 7일

    // 조회수 증가 (사용자별 1시간 중복 체크). 제목 정보도 함께 저장
    public void incrementViewCount(String jobPostingId, String userId, String jobTitle) {
        try {
            // 입력 검증
            if (jobPostingId == null || jobPostingId.trim().isEmpty()) {
                log.debug("Empty job posting ID provided");
                return;
            }
            if (userId == null || userId.trim().isEmpty()) {
                log.debug("Empty user ID provided");
                return;
            }
            if (jobTitle == null || jobTitle.trim().isEmpty()) {
                log.debug("Empty job title provided");
                return;
            }

            String cleanJobId = jobPostingId.trim();
            String cleanUserId = userId.trim();
            String cleanJobTitle = jobTitle.trim();

            String userViewKey = String.format(USER_VIEW_KEY, cleanUserId, cleanJobId);
            String viewCountKey = String.format(VIEW_COUNT_KEY, cleanJobId);

            // 1시간 내 동일한 사용자의 조회 기록이 있는지 확인
            Boolean hasViewed = stringRedisTemplate.hasKey(userViewKey);

            if (hasViewed) {
                log.debug("User {} already viewed job {} within 1 hour", cleanUserId, cleanJobId);
                return; // 이미 조회한 사용자
            }

            // 사용자 조회 기록 저장 (1시간 TTL)
            stringRedisTemplate.opsForValue().set(userViewKey, "1", USER_VIEW_TTL);

            // 조회수 증가
            Long newCount = stringRedisTemplate.opsForValue().increment(viewCountKey);

            // 조회수 키에 TTL 설정 (처음 생성될 때만)
            if (newCount == 1) {
                stringRedisTemplate.expire(viewCountKey, VIEW_COUNT_TTL);
            }

            // 제목 정보 Hash에 저장
            stringRedisTemplate.opsForHash().put(JOB_TITLES_KEY, cleanJobId, cleanJobTitle);
            stringRedisTemplate.expire(JOB_TITLES_KEY, JOB_TITLES_TTL);

            // 인기 공고 점수 업데이트 (Sorted Set에 jobPostingId만 저장)
            stringRedisTemplate.opsForZSet().incrementScore(HOT_JOBS_KEY, cleanJobId, 1.0);
            stringRedisTemplate.expire(HOT_JOBS_KEY, VIEW_COUNT_TTL);

            log.debug("View count incremented for job {} by user {}. New count: {}",
                    cleanJobId, cleanUserId, newCount);

        } catch (Exception e) {
            log.warn("Failed to increment view count for job {} by user {}: {}",
                    jobPostingId, userId, e.getMessage());
        }
    }

    // 기존 메서드 오버로딩 - 하위 호환성 유지
    public void incrementViewCount(String jobPostingId, String userId) {
        log.warn("incrementViewCount called without job title. Job ID: {}", jobPostingId);
        // 제목 없이 호출된 경우에는 조회수만 증가 (기존 로직 유지)
        incrementViewCountWithoutTitle(jobPostingId, userId);
    }

    // 제목 없이 조회수만 증가하는 private 메서드
    private void incrementViewCountWithoutTitle(String jobPostingId, String userId) {
        try {
            if (jobPostingId == null || jobPostingId.trim().isEmpty()) {
                log.debug("Empty job posting ID provided");
                return;
            }
            if (userId == null || userId.trim().isEmpty()) {
                log.debug("Empty user ID provided");
                return;
            }

            String cleanJobId = jobPostingId.trim();
            String cleanUserId = userId.trim();

            String userViewKey = String.format(USER_VIEW_KEY, cleanUserId, cleanJobId);
            String viewCountKey = String.format(VIEW_COUNT_KEY, cleanJobId);

            Boolean hasViewed = stringRedisTemplate.hasKey(userViewKey);

            if (hasViewed) {
                log.debug("User {} already viewed job {} within 1 hour", cleanUserId, cleanJobId);
                return;
            }

            stringRedisTemplate.opsForValue().set(userViewKey, "1", USER_VIEW_TTL);

            Long newCount = stringRedisTemplate.opsForValue().increment(viewCountKey);

            if (newCount == 1) {
                stringRedisTemplate.expire(viewCountKey, VIEW_COUNT_TTL);
            }

            stringRedisTemplate.opsForZSet().incrementScore(HOT_JOBS_KEY, cleanJobId, 1.0);
            stringRedisTemplate.expire(HOT_JOBS_KEY, VIEW_COUNT_TTL);

        } catch (Exception e) {
            log.warn("Failed to increment view count for job {} by user {}: {}",
                    jobPostingId, userId, e.getMessage());
        }
    }

    // 특정 채용공고의 조회수 조회
    public long getViewCount(String jobPostingId) {
        try {
            String viewCountKey = String.format(VIEW_COUNT_KEY, jobPostingId);
            String countStr = stringRedisTemplate.opsForValue().get(viewCountKey);

            if (countStr == null) {
                return 0L;
            }

            return Long.parseLong(countStr);

        } catch (NumberFormatException e) {
            log.warn("Invalid view count format for job {}", jobPostingId, e);
            return 0L;
        } catch (Exception e) {
            log.error("Failed to get view count for job {}", jobPostingId, e);
            throw new RedisServiceException("Failed to retrieve view count", e);
        }
    }

    // 인기 채용공고 목록 조회 (ID와 제목을 객체로 반환)
    public List<HotJobPostingResponse> getHotJobPostings(int limit) {
        try {
            if (limit <= 0) {
                throw new IllegalArgumentException("Limit must be positive");
            }

            // Sorted Set에서 점수가 높은 순으로 jobPostingId 조회 (순서 보장된 Set 반환)
            Set<String> hotJobIds = stringRedisTemplate.opsForZSet().reverseRange(HOT_JOBS_KEY, 0, limit - 1);

            if (hotJobIds == null || hotJobIds.isEmpty()) {
                return Collections.emptyList();
            }

            // Set을 List로 변환 (LinkedHashSet이므로 순서 보장)
            List<String> jobIdList = new ArrayList<>(hotJobIds);

            // Hash에서 제목 정보 batch 조회
            List<Object> titles = stringRedisTemplate.opsForHash().multiGet(JOB_TITLES_KEY,
                    jobIdList.stream().map(Object.class::cast).collect(Collectors.toList()));

            // HotJobPostingResponse 객체 리스트로 변환
            List<HotJobPostingResponse> result = new ArrayList<>();

            for (int i = 0; i < jobIdList.size(); i++) {
                String jobId = jobIdList.get(i);
                String title = (i < titles.size() && titles.get(i) != null)
                        ? titles.get(i).toString()
                        : "제목 없음";

                result.add(new HotJobPostingResponse(jobId, title));
            }

            return result;

        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            log.error("Failed to get hot job postings with limit {}", limit, e);
            throw new RedisServiceException("Failed to retrieve popular job postings", e);
        }
    }

    // 특정 채용공고의 제목 정보 업데이트
    public void updateJobTitle(String jobPostingId, String newTitle) {
        try {
            if (jobPostingId == null || jobPostingId.trim().isEmpty() ||
                    newTitle == null || newTitle.trim().isEmpty()) {
                log.debug("Invalid parameters for updating job title");
                return;
            }

            String cleanJobId = jobPostingId.trim();
            String cleanTitle = newTitle.trim();

            // Hash에서 제목 정보 업데이트
            stringRedisTemplate.opsForHash().put(JOB_TITLES_KEY, cleanJobId, cleanTitle);

            log.debug("Updated title for job {}: {}", cleanJobId, cleanTitle);

        } catch (Exception e) {
            log.error("Failed to update job title for job {}", jobPostingId, e);
        }
    }

    // 사용자가 특정 공고를 조회했는지 확인
    public boolean hasUserViewedRecently(String jobPostingId, String userId) {
        try {
            String userViewKey = String.format(USER_VIEW_KEY, userId, jobPostingId);
            return stringRedisTemplate.hasKey(userViewKey);

        } catch (Exception e) {
            log.error("Failed to check user view status for job {} by user {}", jobPostingId, userId, e);
            return false;
        }
    }

    // 특정 채용공고의 모든 조회 데이터 삭제 (관리자용)
    public void clearViewData(String jobPostingId) {
        try {
            String viewCountKey = String.format(VIEW_COUNT_KEY, jobPostingId);

            // 조회수 삭제
            stringRedisTemplate.delete(viewCountKey);
            stringRedisTemplate.opsForZSet().remove(HOT_JOBS_KEY, jobPostingId);
            stringRedisTemplate.opsForHash().delete(JOB_TITLES_KEY, jobPostingId);

            log.info("Cleared view data for job {}", jobPostingId);

        } catch (Exception e) {
            log.error("Failed to clear view data for job {}", jobPostingId, e);
            throw new RedisServiceException("Failed to clear view data", e);
        }
    }
}