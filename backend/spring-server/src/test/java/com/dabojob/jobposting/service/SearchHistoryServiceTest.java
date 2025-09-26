package com.dabojob.jobposting.service;

import com.dabojob.fixture.user.UserFixture;
import com.dabojob.global.exception.RedisServiceException;
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
import org.springframework.data.redis.core.ZSetOperations;

import java.time.Duration;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
@DisplayName("SearchHistoryService 테스트")
class SearchHistoryServiceTest {



    @Mock
    @Qualifier("customStringRedisTemplate")
    private RedisTemplate<String, String> stringRedisTemplate;

    @Mock
    private ZSetOperations<String, String> zSetOperations;

    @InjectMocks
    private SearchHistoryService searchHistoryService;

    private User defaultUser;
    private User adminUser;
    private User ssafyUser;

    @BeforeEach
    void setUp() {
        defaultUser = UserFixture.defaultUser();
        adminUser = UserFixture.adminUser();
        ssafyUser = UserFixture.ssafyUser();

        given(stringRedisTemplate.opsForZSet()).willReturn(zSetOperations);
    }

    @Nested
    @DisplayName("검색어 기록 저장 테스트")
    class AddSearchHistoryTest {

        @Test
        @DisplayName("검색어를 정상적으로 저장한다")
        void addSearchHistory_Success() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "Spring Boot 개발자";
            given(zSetOperations.count(anyString(), anyDouble(), anyDouble())).willReturn(5L);

            // when
            searchHistoryService.addSearchHistory(userId, keyword);

            // then
            then(zSetOperations).should().add(contains("search_history:" + userId), eq(keyword), anyDouble());
            then(stringRedisTemplate).should().expire(contains("search_history:" + userId), any(Duration.class));
            then(zSetOperations).should().incrementScore(eq("popular_searches"), eq(keyword), eq(1.0));
            then(stringRedisTemplate).should().expire(eq("popular_searches"), any(Duration.class));
        }

        @Test
        @DisplayName("검색어 개수가 제한을 초과하면 오래된 기록을 삭제한다")
        void addSearchHistory_ExceedsLimit() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "React 개발자";
            given(zSetOperations.count(anyString(), anyDouble(), anyDouble())).willReturn(25L); // 제한(20)을 초과

            // when
            searchHistoryService.addSearchHistory(userId, keyword);

            // then
            then(zSetOperations).should().removeRange(contains("search_history:" + userId), eq(0L), eq(4L)); // 5개 제거
            then(zSetOperations).should().add(anyString(), eq(keyword), anyDouble());
        }

        @Test
        @DisplayName("빈 검색어는 저장하지 않는다")
        void addSearchHistory_EmptyKeyword() {
            // given
            String userId = defaultUser.getId().toString();

            // when
            searchHistoryService.addSearchHistory(userId, "");
            searchHistoryService.addSearchHistory(userId, "   ");
            searchHistoryService.addSearchHistory(userId, null);

            // then
            then(zSetOperations).should(never()).add(anyString(), anyString(), anyDouble());
        }

        @Test
        @DisplayName("검색어 앞뒤 공백을 제거하여 저장한다")
        void addSearchHistory_TrimKeyword() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "  Java 개발자  ";
            String trimmedKeyword = "Java 개발자";

            // when
            searchHistoryService.addSearchHistory(userId, keyword);

            // then
            then(zSetOperations).should().add(anyString(), eq(trimmedKeyword), anyDouble());
            then(zSetOperations).should().incrementScore(eq("popular_searches"), eq(trimmedKeyword), eq(1.0));
        }

        @Test
        @DisplayName("Redis 예외가 발생해도 예외를 던지지 않는다")
        void addSearchHistory_RedisException() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "Python 개발자";
            given(zSetOperations.add(anyString(), anyString(), anyDouble()))
                    .willThrow(new RuntimeException("Redis error"));

            // when & then
            assertThatCode(() -> searchHistoryService.addSearchHistory(userId, keyword))
                    .doesNotThrowAnyException();
        }
    }

    @Nested
    @DisplayName("최근 검색어 조회 테스트")
    class GetUserRecentSearchesTest {

        @Test
        @DisplayName("사용자의 최근 검색어를 조회한다")
        void getUserRecentSearches_Success() {
            // given
            String userId = defaultUser.getId().toString();
            int limit = 5;
            Set<String> searchResults = new LinkedHashSet<>();
            searchResults.add("Spring Boot");
            searchResults.add("React");
            searchResults.add("Vue.js");

            given(zSetOperations.reverseRange(contains("search_history:" + userId), eq(0L), eq(4L)))
                    .willReturn(searchResults);

            // when
            List<String> result = searchHistoryService.getUserRecentSearches(userId, limit);

            // then
            assertThat(result).hasSize(3);
            assertThat(result).containsExactly("Spring Boot", "React", "Vue.js");
        }

        @Test
        @DisplayName("검색 기록이 없으면 빈 리스트를 반환한다")
        void getUserRecentSearches_EmptyHistory() {
            // given
            String userId = defaultUser.getId().toString();
            int limit = 10;
            given(zSetOperations.reverseRange(anyString(), anyLong(), anyLong())).willReturn(null);

            // when
            List<String> result = searchHistoryService.getUserRecentSearches(userId, limit);

            // then
            assertThat(result).isEmpty();
        }

        @Test
        @DisplayName("잘못된 limit 값에 대해 IllegalArgumentException을 던진다")
        void getUserRecentSearches_InvalidLimit() {
            // given
            String userId = defaultUser.getId().toString();

            // when & then
            assertThatThrownBy(() -> searchHistoryService.getUserRecentSearches(userId, 0))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessageContaining("Limit must be positive");

            assertThatThrownBy(() -> searchHistoryService.getUserRecentSearches(userId, -1))
                    .isInstanceOf(IllegalArgumentException.class);
        }

        @Test
        @DisplayName("Redis 예외 발생시 RedisServiceException을 던진다")
        void getUserRecentSearches_RedisException() {
            // given
            String userId = defaultUser.getId().toString();
            int limit = 5;
            given(zSetOperations.reverseRange(anyString(), anyLong(), anyLong()))
                    .willThrow(new RuntimeException("Redis connection failed"));

            // when & then
            assertThatThrownBy(() -> searchHistoryService.getUserRecentSearches(userId, limit))
                    .isInstanceOf(RedisServiceException.class)
                    .hasMessageContaining("Failed to retrieve recent search history");
        }
    }

    @Nested
    @DisplayName("인기 검색어 조회 테스트")
    class GetPopularSearchesTest {

        @Test
        @DisplayName("인기 검색어를 조회한다")
        void getPopularSearches_Success() {
            // given
            int limit = 3;
            Set<String> popularSearches = new LinkedHashSet<>();
            popularSearches.add("Spring Boot");
            popularSearches.add("React");
            popularSearches.add("Python");

            given(zSetOperations.reverseRange(eq("popular_searches"), eq(0L), eq(2L)))
                    .willReturn(popularSearches);

            // when
            List<String> result = searchHistoryService.getPopularSearches(limit);

            // then
            assertThat(result).hasSize(3);
            assertThat(result).containsExactly("Spring Boot", "React", "Python");
        }

        @Test
        @DisplayName("인기 검색어가 없으면 빈 리스트를 반환한다")
        void getPopularSearches_Empty() {
            // given
            int limit = 5;
            given(zSetOperations.reverseRange(eq("popular_searches"), anyLong(), anyLong()))
                    .willReturn(Collections.emptySet());

            // when
            List<String> result = searchHistoryService.getPopularSearches(limit);

            // then
            assertThat(result).isEmpty();
        }

        @Test
        @DisplayName("잘못된 limit 값에 대해 IllegalArgumentException을 던진다")
        void getPopularSearches_InvalidLimit() {
            // when & then
            assertThatThrownBy(() -> searchHistoryService.getPopularSearches(0))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessageContaining("Limit must be positive");

            assertThatThrownBy(() -> searchHistoryService.getPopularSearches(-5))
                    .isInstanceOf(IllegalArgumentException.class);
        }

        @Test
        @DisplayName("Redis 예외 발생시 RedisServiceException을 던진다")
        void getPopularSearches_RedisException() {
            // given
            int limit = 5;
            given(zSetOperations.reverseRange(anyString(), anyLong(), anyLong()))
                    .willThrow(new RuntimeException("Redis error"));

            // when & then
            assertThatThrownBy(() -> searchHistoryService.getPopularSearches(limit))
                    .isInstanceOf(RedisServiceException.class)
                    .hasMessageContaining("Failed to retrieve popular searches");
        }
    }

    @Nested
    @DisplayName("검색어 기록 삭제 테스트")
    class RemoveSearchHistoryTest {

        @Test
        @DisplayName("특정 검색어를 삭제한다")
        void removeUserSearchHistory_Success() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "Spring Boot";
            given(zSetOperations.remove(anyString(), eq(keyword))).willReturn(1L);

            // when
            searchHistoryService.removeUserSearchHistory(userId, keyword);

            // then
            then(zSetOperations).should().remove(contains("search_history:" + userId), eq(keyword));
        }

        @Test
        @DisplayName("존재하지 않는 검색어 삭제시도는 정상 처리된다")
        void removeUserSearchHistory_NotFound() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "Non-existent keyword";
            given(zSetOperations.remove(anyString(), eq(keyword))).willReturn(0L);

            // when & then
            assertThatCode(() -> searchHistoryService.removeUserSearchHistory(userId, keyword))
                    .doesNotThrowAnyException();
        }

        @Test
        @DisplayName("빈 검색어 삭제시 IllegalArgumentException을 던진다")
        void removeUserSearchHistory_EmptyKeyword() {
            // given
            String userId = defaultUser.getId().toString();

            // when & then
            assertThatThrownBy(() -> searchHistoryService.removeUserSearchHistory(userId, ""))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessageContaining("Search keyword cannot be empty");

            assertThatThrownBy(() -> searchHistoryService.removeUserSearchHistory(userId, null))
                    .isInstanceOf(IllegalArgumentException.class);
        }

        @Test
        @DisplayName("Redis 예외 발생시 RedisServiceException을 던진다")
        void removeUserSearchHistory_RedisException() {
            // given
            String userId = defaultUser.getId().toString();
            String keyword = "Java";
            given(zSetOperations.remove(anyString(), anyString()))
                    .willThrow(new RuntimeException("Redis error"));

            // when & then
            assertThatThrownBy(() -> searchHistoryService.removeUserSearchHistory(userId, keyword))
                    .isInstanceOf(RedisServiceException.class)
                    .hasMessageContaining("Failed to remove search history");
        }
    }

    @Nested
    @DisplayName("전체 검색어 기록 삭제 테스트")
    class ClearUserSearchHistoryTest {

        @Test
        @DisplayName("사용자의 모든 검색어 기록을 삭제한다")
        void clearUserSearchHistory_Success() {
            // given
            String userId = defaultUser.getId().toString();
            given(stringRedisTemplate.delete(anyString())).willReturn(true);

            // when
            searchHistoryService.clearUserSearchHistory(userId);

            // then
            then(stringRedisTemplate).should().delete(contains("search_history:" + userId));
        }

        @Test
        @DisplayName("삭제할 기록이 없어도 정상 처리된다")
        void clearUserSearchHistory_NoData() {
            // given
            String userId = defaultUser.getId().toString();
            given(stringRedisTemplate.delete(anyString())).willReturn(false);

            // when & then
            assertThatCode(() -> searchHistoryService.clearUserSearchHistory(userId))
                    .doesNotThrowAnyException();
        }

        @Test
        @DisplayName("Redis 예외 발생시 RedisServiceException을 던진다")
        void clearUserSearchHistory_RedisException() {
            // given
            String userId = defaultUser.getId().toString();
            given(stringRedisTemplate.delete(anyString())).willThrow(new RuntimeException("Redis error"));

            // when & then
            assertThatThrownBy(() -> searchHistoryService.clearUserSearchHistory(userId))
                    .isInstanceOf(RedisServiceException.class)
                    .hasMessageContaining("Failed to clear search history");
        }
    }

    @Nested
    @DisplayName("통합 테스트")
    class IntegrationTest {

        @Test
        @DisplayName("여러 사용자의 검색어 저장 및 인기 검색어 생성 시나리오")
        void multipleUsersSearchScenario() {
            // given
            List<User> users = UserFixture.regularUserList();
            String popularKeyword = "Spring Boot";

            given(zSetOperations.count(anyString(), anyDouble(), anyDouble())).willReturn(1L);

            // when - 여러 사용자가 같은 키워드 검색
            users.forEach(user ->
                    searchHistoryService.addSearchHistory(user.getId().toString(), popularKeyword)
            );

            // then - 인기 검색어에 점수가 누적됨
            then(zSetOperations).should(times(users.size()))
                    .incrementScore(eq("popular_searches"), eq(popularKeyword), eq(1.0));
        }
    }
}