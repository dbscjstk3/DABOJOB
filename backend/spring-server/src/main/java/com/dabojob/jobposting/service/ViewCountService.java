package com.dabojob.jobposting.service;

import com.dabojob.global.exception.RedisServiceException;
import com.dabojob.jobposting.dto.HotJobPostingResponse;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.repository.JobPostingRepository;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
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

    private final JobPostingRepository jobPostingRepository;

    // Redis 키 패턴
    private static final String VIEW_COUNT_KEY = "views:%s"; // views:{jobPostingId}
    private static final String USER_VIEW_KEY = "user_view:%s:%s"; // user_view:{userId}:{jobPostingId}
    private static final String HOT_JOBS_KEY = "hot_jobs"; // Sorted Set for hot jobs
    private static final String JOB_TITLES_KEY = "job_titles:%s"; // job_titles:{jobPostingId}
    private static final String JOB_COMPANIES_KEY = "job_companies:%s"; // job_companies:{jobPostingId}

    private static final Duration VIEW_COUNT_TTL = Duration.ofDays(7); // 7일
    private static final Duration USER_VIEW_TTL = Duration.ofHours(1); // 1시간
    private static final Duration JOB_INFO_TTL = Duration.ofDays(7); // 7일

    public void incrementViewCount(String jobPostingId, String userId) {
        try{

            if (jobPostingId == null) {
                log.debug("Null job posting ID provided");
                return;
            }
            if (userId == null || userId.trim().isEmpty()) {
                log.debug("Empty user ID provided");
                return;
            }

            Long parsedJobPostingId = Long.parseLong(jobPostingId);
            JobPosting jobPosting = jobPostingRepository.findById(parsedJobPostingId).orElse(null);

            if (jobPosting == null) {
                log.debug("Job posting with id {} not found", parsedJobPostingId);
                return;
            }

            String companyName = jobPosting.getCompany().getName();
            String title = jobPosting.getTitle();
            String cleanUserId = userId.trim();

            String userViewKey = String.format(USER_VIEW_KEY, cleanUserId, jobPostingId);
            String viewCountKey = String.format(VIEW_COUNT_KEY, jobPostingId);
            String titleKey = String.format(JOB_TITLES_KEY, jobPostingId);
            String companyKey = String.format(JOB_COMPANIES_KEY, jobPostingId);

            Boolean hasViewed = stringRedisTemplate.hasKey(userViewKey);

            if (hasViewed) {
                log.debug("User {} already viewed job {} within 1 hour", cleanUserId, jobPostingId);
                return;
            }

            stringRedisTemplate.opsForValue().set(userViewKey, "1", USER_VIEW_TTL);

            Long newCount = stringRedisTemplate.opsForValue().increment(viewCountKey);
            if (newCount == 1) {
                stringRedisTemplate.expire(viewCountKey, VIEW_COUNT_TTL);
            }

            // Hot jobs에 추가
            stringRedisTemplate.opsForZSet().incrementScore(HOT_JOBS_KEY, jobPostingId, 1.0);
            stringRedisTemplate.expire(HOT_JOBS_KEY, VIEW_COUNT_TTL);

            // 제목과 회사명 저장
            if (title != null && !title.trim().isEmpty()) {
                stringRedisTemplate.opsForValue().set(titleKey, title.trim(), JOB_INFO_TTL);
            }
            if (companyName != null && !companyName.trim().isEmpty()) {
                stringRedisTemplate.opsForValue().set(companyKey, companyName.trim(), JOB_INFO_TTL);
            }

        } catch (NumberFormatException e) {
            log.warn("Invalid job posting ID. Job ID: {}", jobPostingId);
            throw new IllegalArgumentException("Invalid job posting ID");
        } catch (Exception e) {
            log.warn("Failed to increment view count for job {} by user {}: {}", jobPostingId, userId, e.getMessage());
        }
    }


    // 특정 채용공고의 조회수 조회
    public long getViewCount(Long jobPostingId) {
        try {
            String jobIdStr = String.valueOf(jobPostingId);
            String viewCountKey = String.format(VIEW_COUNT_KEY, jobIdStr);
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

    public List<HotJobPostingResponse> getHotJobPostings(int limit) {
        try {
            if (limit <= 0) {
                throw new IllegalArgumentException("Limit must be positive");
            }

            Set<String> hotJobIds = stringRedisTemplate.opsForZSet().reverseRange(HOT_JOBS_KEY, 0, limit - 1);

            if (hotJobIds == null || hotJobIds.isEmpty()) {
                return Collections.emptyList();
            }

            List<HotJobPostingResponse> result = new ArrayList<>();

            for (String jobIdStr : hotJobIds) {
                try {
                    Long jobId = Long.valueOf(jobIdStr);
                    String titleKey = String.format(JOB_TITLES_KEY, jobIdStr);
                    String companyKey = String.format(JOB_COMPANIES_KEY, jobIdStr);

                    String title = stringRedisTemplate.opsForValue().get(titleKey);
                    String companyName = stringRedisTemplate.opsForValue().get(companyKey);

                    // 기본값 설정
                    if (title == null || title.trim().isEmpty()) {
                        title = "제목 없음";
                    }
                    if (companyName == null || companyName.trim().isEmpty()) {
                        companyName = "회사명 없음";
                    }

                    result.add(new HotJobPostingResponse(jobId, companyName, title));

                } catch (NumberFormatException e) {
                    log.warn("Invalid job posting ID format: {}", jobIdStr, e);
                }
            }

            return result;

        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            log.error("Failed to get hot job postings with limit {}", limit, e);
            throw new RedisServiceException("Failed to retrieve popular job postings", e);
        }
    }

    // 특정 채용공고의 제목과 회사명 정보 업데이트
    public void updateJobInfo(Long jobPostingId, String newTitle, String newCompanyName) {
        try {
            if (jobPostingId == null) {
                log.debug("Invalid job posting ID for updating job info");
                return;
            }

            String jobIdStr = String.valueOf(jobPostingId);
            String titleKey = String.format(JOB_TITLES_KEY, jobIdStr);
            String companyKey = String.format(JOB_COMPANIES_KEY, jobIdStr);

            if (newTitle != null && !newTitle.trim().isEmpty()) {
                stringRedisTemplate.opsForValue().set(titleKey, newTitle.trim(), JOB_INFO_TTL);
            }

            if (newCompanyName != null && !newCompanyName.trim().isEmpty()) {
                stringRedisTemplate.opsForValue().set(companyKey, newCompanyName.trim(), JOB_INFO_TTL);
            }

            log.debug("Updated info for job {}: title={}, company={}", jobIdStr, newTitle, newCompanyName);

        } catch (Exception e) {
            log.error("Failed to update job info for job {}", jobPostingId, e);
        }
    }

    // 사용자가 특정 공고를 조회했는지 확인
    public boolean hasUserViewedRecently(Long jobPostingId, String userId) {
        try {
            String jobIdStr = String.valueOf(jobPostingId);
            String userViewKey = String.format(USER_VIEW_KEY, userId, jobIdStr);
            return stringRedisTemplate.hasKey(userViewKey);

        } catch (Exception e) {
            log.error("Failed to check user view status for job {} by user {}", jobPostingId, userId, e);
            return false;
        }
    }

    // 특정 채용공고의 모든 조회 데이터 삭제 (관리자용)
    public void clearViewData(Long jobPostingId) {
        try {
            String jobIdStr = String.valueOf(jobPostingId);
            String viewCountKey = String.format(VIEW_COUNT_KEY, jobIdStr);
            String titleKey = String.format(JOB_TITLES_KEY, jobIdStr);
            String companyKey = String.format(JOB_COMPANIES_KEY, jobIdStr);

            stringRedisTemplate.delete(viewCountKey);
            stringRedisTemplate.delete(titleKey);
            stringRedisTemplate.delete(companyKey);
            stringRedisTemplate.opsForZSet().remove(HOT_JOBS_KEY, jobIdStr);

            log.info("Cleared view data for job {}", jobIdStr);

        } catch (Exception e) {
            log.error("Failed to clear view data for job {}", jobPostingId, e);
            throw new RedisServiceException("Failed to clear view data", e);
        }
    }
}