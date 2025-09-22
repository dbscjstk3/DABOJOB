package com.dabojob.summary.service;

import com.dabojob.summary.dto.NewsResponse;
import com.dabojob.summary.entity.Hashtag;
import com.dabojob.summary.entity.News;
import com.dabojob.summary.entity.SummaryHashtag;
import com.dabojob.summary.repository.NewsRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("NewsService 테스트")
class NewsServiceTest {

    @Mock
    private NewsRepository newsRepository;

    @InjectMocks
    private NewsService newsService;

    private News news1;
    private News news2;
    private Hashtag hashtag;
    private SummaryHashtag summaryHashtag;

    @BeforeEach
    void setUp() {
        // 테스트 데이터 준비
        hashtag = Hashtag.builder()
                .id(1L)
                .name("테스트해시태그")
                .build();

        summaryHashtag = SummaryHashtag.builder()
                .id(100L)
                .hashtag(hashtag)
                .build();

        news1 = News.builder()
                .id(1L)
                .summaryHashtag(summaryHashtag)
                .title("뉴스 제목 1")
                .content("뉴스 내용 1")
                .url("https://example.com/news1")
                .postingDate(LocalDate.of(2024, 1, 1))
                .build();

        news2 = News.builder()
                .id(2L)
                .summaryHashtag(summaryHashtag)
                .title("뉴스 제목 2")
                .content("뉴스 내용 2")
                .url("https://example.com/news2")
                .postingDate(LocalDate.of(2024, 1, 2))
                .build();
    }

    @Test
    @DisplayName("정상 케이스: hashtagName이 null일 때 summaryId로만 조회")
    void getNews_WithNullHashtagName_Success() {
        // given
        String summaryId = "100";
        String hashtagName = null;
        List<News> mockNewsList = Arrays.asList(news1, news2);

        when(newsRepository.findBySummaryHashtagId(100L))
                .thenReturn(mockNewsList);

        // when
        List<NewsResponse> result = newsService.getNews(summaryId, hashtagName);

        // then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).getSummaryHashtagId()).isEqualTo(100L);
        assertThat(result.get(0).getTitle()).isEqualTo("뉴스 제목 1");
        assertThat(result.get(0).getUrl()).isEqualTo("https://example.com/news1");
        assertThat(result.get(1).getTitle()).isEqualTo("뉴스 제목 2");

        verify(newsRepository).findBySummaryHashtagId(100L);
        verify(newsRepository, never()).findBySummaryHashtagIdAndHashtagName(anyLong(), anyString());
    }

    @Test
    @DisplayName("정상 케이스: hashtagName이 있을 때 summaryId와 hashtagName으로 조회")
    void getNews_WithHashtagName_Success() {
        // given
        String summaryId = "100";
        String hashtagName = "테스트해시태그";
        List<News> mockNewsList = Arrays.asList(news1);

        when(newsRepository.findBySummaryHashtagIdAndHashtagName(100L, hashtagName))
                .thenReturn(mockNewsList);

        // when
        List<NewsResponse> result = newsService.getNews(summaryId, hashtagName);

        // then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getSummaryHashtagId()).isEqualTo(100L);
        assertThat(result.get(0).getTitle()).isEqualTo("뉴스 제목 1");

        verify(newsRepository).findBySummaryHashtagIdAndHashtagName(100L, hashtagName);
        verify(newsRepository, never()).findBySummaryHashtagId(anyLong());
    }

    @Test
    @DisplayName("정상 케이스: Repository에서 빈 리스트 반환")
    void getNews_EmptyResult_Success() {
        // given
        String summaryId = "100";
        String hashtagName = null;

        when(newsRepository.findBySummaryHashtagId(100L))
                .thenReturn(Collections.emptyList());

        // when
        List<NewsResponse> result = newsService.getNews(summaryId, hashtagName);

        // then
        assertThat(result).isEmpty();
        verify(newsRepository).findBySummaryHashtagId(100L);
    }

    @Test
    @DisplayName("예외 케이스: summaryId가 숫자가 아닌 문자열")
    void getNews_InvalidSummaryIdFormat_ThrowsException() {
        // given
        String invalidSummaryId = "abc123";
        String hashtagName = null;

        // when & then
        assertThatThrownBy(() -> newsService.getNews(invalidSummaryId, hashtagName))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid summary ID format: abc123");

        verify(newsRepository, never()).findBySummaryHashtagId(anyLong());
        verify(newsRepository, never()).findBySummaryHashtagIdAndHashtagName(anyLong(), anyString());
    }

    @Test
    @DisplayName("예외 케이스: summaryId가 실수")
    void getNews_FloatSummaryId_ThrowsException() {
        // given
        String floatSummaryId = "123.45";
        String hashtagName = null;

        // when & then
        assertThatThrownBy(() -> newsService.getNews(floatSummaryId, hashtagName))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid summary ID format: 123.45");
    }

    @Test
    @DisplayName("예외 케이스: summaryId가 null")
    void getNews_NullSummaryId_ThrowsException() {
        // given
        String nullSummaryId = null;
        String hashtagName = null;

        // when & then
        assertThatThrownBy(() -> newsService.getNews(nullSummaryId, hashtagName))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid summary ID format: null");
    }

    @Test
    @DisplayName("예외 케이스: summaryId가 빈 문자열")
    void getNews_EmptySummaryId_ThrowsException() {
        // given
        String emptySummaryId = "";
        String hashtagName = null;

        // when & then
        assertThatThrownBy(() -> newsService.getNews(emptySummaryId, hashtagName))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid summary ID format: ");
    }

    @Test
    @DisplayName("경계 케이스: 매우 큰 summaryId")
    void getNews_LargeSummaryId_Success() {
        // given
        String largeSummaryId = String.valueOf(Long.MAX_VALUE);
        String hashtagName = null;

        when(newsRepository.findBySummaryHashtagId(Long.MAX_VALUE))
                .thenReturn(Collections.emptyList());

        // when
        List<NewsResponse> result = newsService.getNews(largeSummaryId, hashtagName);

        // then
        assertThat(result).isEmpty();
        verify(newsRepository).findBySummaryHashtagId(Long.MAX_VALUE);
    }

    @Test
    @DisplayName("NewsResponse 변환 검증: 모든 필드가 올바르게 매핑되는지 확인")
    void getNews_NewsResponseMapping_Success() {
        // given
        String summaryId = "100";
        String hashtagName = null;
        List<News> mockNewsList = Arrays.asList(news1);

        when(newsRepository.findBySummaryHashtagId(100L))
                .thenReturn(mockNewsList);

        // when
        List<NewsResponse> result = newsService.getNews(summaryId, hashtagName);

        // then
        NewsResponse response = result.get(0);
        assertThat(response.getSummaryHashtagId()).isEqualTo(news1.getSummaryHashtag().getId());
        assertThat(response.getTitle()).isEqualTo(news1.getTitle());
        assertThat(response.getContent()).isEqualTo(news1.getContent());
        assertThat(response.getUrl()).isEqualTo(news1.getUrl());
        assertThat(response.getPostingDate()).isEqualTo(news1.getPostingDate());
    }
}