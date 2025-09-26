package com.dabojob.jobposting.service;

import com.dabojob.fixture.company.CompanyFixture;
import com.dabojob.fixture.jobposting.JobPostingFixture;
import com.dabojob.fixture.user.UserFixture;
import com.dabojob.global.exception.RedisServiceException;
import com.dabojob.jobposting.dto.HotJobPostingResponse;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.repository.JobPostingRepository;
import com.dabojob.user.entity.User;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.data.redis.core.ZSetOperations;

import java.time.Duration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
@DisplayName("ViewCountService 테스트")
public class ViewCountServiceTest {

    @Mock
    @Qualifier("customStringRedisTemplate")
    private RedisTemplate<String, String> stringRedisTemplate;

    @Mock
    private JobPostingRepository jobPostingRepository;

    @Mock
    private ValueOperations<String, String> valueOperations;

    @Mock
    private ZSetOperations<String, String> zSetOperations;

    @InjectMocks
    private ViewCountService viewCountService;

    private JobPosting defaultJobPosting;
    private JobPosting seniorJobPosting;
    private User defaultUser;

    @BeforeEach
    void setUp() {
        defaultJobPosting = JobPostingFixture.defaultJobPosting();
        defaultJobPosting.setCompany(CompanyFixture.defaultCompany());
        seniorJobPosting = JobPostingFixture.seniorJobPosting();
        defaultUser = UserFixture.defaultUser();

        // Redis operations mock 설정
        given(stringRedisTemplate.opsForValue()).willReturn(valueOperations);
        given(stringRedisTemplate.opsForZSet()).willReturn(zSetOperations);
    }

    @Nested
    @DisplayName("조회수 증가 테스트")
    class IncrementViewCountTest {

        @Test
        @DisplayName("정상적으로 조회수를 증가시킨다")
        void incrementViewCount_Success() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            String jobPostingIdStr = jobPostingId.toString();
            String userId = defaultUser.getId().toString();
            String jobTitle = defaultJobPosting.getTitle();
            String companyName = defaultJobPosting.getCompany().getName();

            given(jobPostingRepository.findById(jobPostingId)).willReturn(Optional.of(defaultJobPosting));
            given(stringRedisTemplate.hasKey(anyString())).willReturn(false);
            given(valueOperations.increment(anyString())).willReturn(1L);

            // when
            viewCountService.incrementViewCount(jobPostingIdStr, userId);

            // then
            then(stringRedisTemplate).should().hasKey(contains("user_view"));
            then(valueOperations).should().set(contains("user_view"), eq("1"), any(Duration.class));
            then(valueOperations).should().increment(contains("views"));
            then(stringRedisTemplate).should().expire(contains("views"), any(Duration.class));
            then(valueOperations).should().set(contains("job_titles"), eq(jobTitle), any(Duration.class));
            then(valueOperations).should().set(contains("job_companies"), eq(companyName), any(Duration.class));
            then(zSetOperations).should().incrementScore(eq("hot_jobs"), eq(jobPostingIdStr), eq(1.0));
        }

        @Test
        @DisplayName("동일 사용자가 1시간 내 재조회시 조회수를 증가시키지 않는다")
        void incrementViewCount_AlreadyViewed() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            String jobPostingIdStr = jobPostingId.toString();
            String userId = defaultUser.getId().toString();

            given(jobPostingRepository.findById(jobPostingId)).willReturn(Optional.of(defaultJobPosting));
            given(stringRedisTemplate.hasKey(anyString())).willReturn(true);

            // when
            viewCountService.incrementViewCount(jobPostingIdStr, userId);

            // then
            then(valueOperations).should(never()).increment(anyString());
            then(zSetOperations).should(never()).incrementScore(anyString(), anyString(), anyDouble());
        }

        @Test
        @DisplayName("존재하지 않는 JobPosting ID로 호출시 아무 동작을 하지 않는다")
        void incrementViewCount_JobPostingNotFound() {
            // given
            String jobPostingIdStr = "999";
            String userId = defaultUser.getId().toString();

            given(jobPostingRepository.findById(999L)).willReturn(Optional.empty());

            // when
            viewCountService.incrementViewCount(jobPostingIdStr, userId);

            // then
            then(valueOperations).should(never()).increment(anyString());
            then(zSetOperations).should(never()).incrementScore(anyString(), anyString(), anyDouble());
        }

        @Test
        @DisplayName("null 파라미터로 호출시 아무 동작을 하지 않는다")
        void incrementViewCount_NullParameters() {
            // when & then
            assertThatCode(() -> {
                viewCountService.incrementViewCount(null, "user1");
                viewCountService.incrementViewCount("100", null);
                viewCountService.incrementViewCount("100", "   ");
            }).doesNotThrowAnyException();

            then(valueOperations).should(never()).increment(anyString());
        }

        @Test
        @DisplayName("잘못된 ID 형식으로 호출시 IllegalArgumentException을 던진다")
        void incrementViewCount_InvalidIdFormat() {
            // given
            String invalidJobPostingId = "invalid";
            String userId = defaultUser.getId().toString();

            // when & then
            assertThatThrownBy(() -> viewCountService.incrementViewCount(invalidJobPostingId, userId))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessageContaining("Invalid job posting ID");
        }
    }

    @Nested
    @DisplayName("조회수 조회 테스트")
    class GetViewCountTest {

        @Test
        @DisplayName("조회수를 정상적으로 반환한다")
        void getViewCount_Success() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            given(valueOperations.get(anyString())).willReturn("150");

            // when
            long viewCount = viewCountService.getViewCount(jobPostingId);

            // then
            assertThat(viewCount).isEqualTo(150L);
            then(valueOperations).should().get(contains("views:" + jobPostingId));
        }

        @Test
        @DisplayName("조회수가 없으면 0을 반환한다")
        void getViewCount_NoData() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            given(valueOperations.get(anyString())).willReturn(null);

            // when
            long viewCount = viewCountService.getViewCount(jobPostingId);

            // then
            assertThat(viewCount).isEqualTo(0L);
        }

        @Test
        @DisplayName("잘못된 형식의 조회수는 0을 반환한다")
        void getViewCount_InvalidFormat() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            given(valueOperations.get(anyString())).willReturn("invalid");

            // when
            long viewCount = viewCountService.getViewCount(jobPostingId);

            // then
            assertThat(viewCount).isEqualTo(0L);
        }

        @Test
        @DisplayName("Redis 예외 발생시 RedisServiceException을 던진다")
        void getViewCount_RedisException() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            given(valueOperations.get(anyString())).willThrow(new RuntimeException("Redis error"));

            // when & then
            assertThatThrownBy(() -> viewCountService.getViewCount(jobPostingId))
                    .isInstanceOf(RedisServiceException.class)
                    .hasMessageContaining("Failed to retrieve view count");
        }
    }

    @Nested
    @DisplayName("인기 채용공고 조회 테스트")
    class GetHotJobPostingsTest {

        @Test
        @DisplayName("인기 채용공고 목록을 정상적으로 반환한다")
        void getHotJobPostings_Success() {
            // given
            int limit = 3;
            Set<String> hotJobIds = new LinkedHashSet<>();
            hotJobIds.add("100");
            hotJobIds.add("101");
            hotJobIds.add("102");

            given(zSetOperations.reverseRange(eq("hot_jobs"), eq(0L), eq(2L))).willReturn(hotJobIds);
            given(valueOperations.get("job_titles:100")).willReturn("Spring Boot 개발자");
            given(valueOperations.get("job_companies:100")).willReturn("테크회사A");
            given(valueOperations.get("job_titles:101")).willReturn("React 개발자");
            given(valueOperations.get("job_companies:101")).willReturn("테크회사B");
            given(valueOperations.get("job_titles:102")).willReturn("데이터 엔지니어");
            given(valueOperations.get("job_companies:102")).willReturn("테크회사C");

            // when
            List<HotJobPostingResponse> result = viewCountService.getHotJobPostings(limit);

            // then
            assertThat(result).hasSize(3);
            assertThat(result).extracting("jobPostingId").contains(100L, 101L, 102L);
            assertThat(result).extracting("title").contains("Spring Boot 개발자", "React 개발자", "데이터 엔지니어");
            assertThat(result).extracting("companyName").contains("테크회사A", "테크회사B", "테크회사C");
        }

        @Test
        @DisplayName("데이터가 없으면 빈 리스트를 반환한다")
        void getHotJobPostings_EmptyData() {
            // given
            int limit = 5;
            given(zSetOperations.reverseRange(anyString(), anyLong(), anyLong())).willReturn(null);

            // when
            List<HotJobPostingResponse> result = viewCountService.getHotJobPostings(limit);

            // then
            assertThat(result).isEmpty();
        }

        @Test
        @DisplayName("제목이나 회사명이 없는 경우 기본값을 사용한다")
        void getHotJobPostings_NoTitleOrCompany() {
            // given
            int limit = 2;
            Set<String> hotJobIds = new LinkedHashSet<>();
            hotJobIds.add("100");
            hotJobIds.add("101");

            given(zSetOperations.reverseRange(eq("hot_jobs"), eq(0L), eq(1L))).willReturn(hotJobIds);
            given(valueOperations.get("job_titles:100")).willReturn("Spring Boot 개발자");
            given(valueOperations.get("job_companies:100")).willReturn("테크회사A");
            given(valueOperations.get("job_titles:101")).willReturn(null);
            given(valueOperations.get("job_companies:101")).willReturn(null);

            // when
            List<HotJobPostingResponse> result = viewCountService.getHotJobPostings(limit);

            // then
            assertThat(result).hasSize(2);
            assertThat(result.get(1).getTitle()).isEqualTo("제목 없음");
            assertThat(result.get(1).getCompanyName()).isEqualTo("회사명 없음");
        }

        @Test
        @DisplayName("잘못된 limit 값에 대해 IllegalArgumentException을 던진다")
        void getHotJobPostings_InvalidLimit() {
            // when & then
            assertThatThrownBy(() -> viewCountService.getHotJobPostings(0))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessageContaining("Limit must be positive");

            assertThatThrownBy(() -> viewCountService.getHotJobPostings(-1))
                    .isInstanceOf(IllegalArgumentException.class);
        }
    }

    @Nested
    @DisplayName("기타 기능 테스트")
    class OtherFeaturesTest {

        @Test
        @DisplayName("채용공고 정보를 업데이트한다")
        void updateJobInfo_Success() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            String newTitle = "Updated Title";
            String newCompanyName = "Updated Company";

            // when
            viewCountService.updateJobInfo(jobPostingId, newTitle, newCompanyName);

            // then
            then(valueOperations).should().set(contains("job_titles:" + jobPostingId), eq(newTitle), any(Duration.class));
            then(valueOperations).should().set(contains("job_companies:" + jobPostingId), eq(newCompanyName), any(Duration.class));
        }

        @Test
        @DisplayName("null이나 빈 값으로 업데이트시 해당 필드는 업데이트하지 않는다")
        void updateJobInfo_NullOrEmpty() {
            // given
            Long jobPostingId = defaultJobPosting.getId();

            // when
            viewCountService.updateJobInfo(jobPostingId, null, "");
            viewCountService.updateJobInfo(null, "title", "company");

            // then
            then(valueOperations).should(never()).set(anyString(), anyString(), any(Duration.class));
        }

        @Test
        @DisplayName("사용자의 최근 조회 여부를 확인한다")
        void hasUserViewedRecently_Success() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            String userId = defaultUser.getId().toString();
            given(stringRedisTemplate.hasKey(anyString())).willReturn(true);

            // when
            boolean result = viewCountService.hasUserViewedRecently(jobPostingId, userId);

            // then
            assertThat(result).isTrue();
            then(stringRedisTemplate).should().hasKey(contains("user_view"));
        }

        @Test
        @DisplayName("조회 데이터를 삭제한다")
        void clearViewData_Success() {
            // given
            Long jobPostingId = defaultJobPosting.getId();

            // when
            viewCountService.clearViewData(jobPostingId);

            // then
            then(stringRedisTemplate).should().delete(contains("views:" + jobPostingId));
            then(stringRedisTemplate).should().delete(contains("job_titles:" + jobPostingId));
            then(stringRedisTemplate).should().delete(contains("job_companies:" + jobPostingId));
            then(zSetOperations).should().remove(eq("hot_jobs"), eq(jobPostingId.toString()));
        }

        @Test
        @DisplayName("조회 데이터 삭제 실패시 RedisServiceException을 던진다")
        void clearViewData_Exception() {
            // given
            Long jobPostingId = defaultJobPosting.getId();
            given(stringRedisTemplate.delete(anyString())).willThrow(new RuntimeException("Redis error"));

            // when & then
            assertThatThrownBy(() -> viewCountService.clearViewData(jobPostingId))
                    .isInstanceOf(RedisServiceException.class)
                    .hasMessageContaining("Failed to clear view data");
        }
    }
}