package com.dabojob.fixture.summary;

import com.dabojob.summary.entity.News;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

public class NewsFixture {

    public static News defaultNews() {
        return News.builder()
                .id(1L)
                .summaryHashtag(SummaryHashtagFixture.defaultSummaryHashtag())
                .title("Java 17 새로운 기능 소개")
                .content("Java 17에서 추가된 새로운 기능들에 대해 살펴봅니다.")
                .url("https://example.com/news1")
                .postingDate(LocalDate.of(2024, 1, 15))
                .build();
    }

    public static News springNews() {
        return News.builder()
                .id(2L)
                .summaryHashtag(SummaryHashtagFixture.productsSummaryHashtag())
                .title("Spring Boot 3.0 마이그레이션 가이드")
                .content("Spring Boot 3.0으로 업그레이드하는 방법을 안내합니다.")
                .url("https://example.com/news2")
                .postingDate(LocalDate.of(2024, 1, 20))
                .build();
    }

    public static News reactNews() {
        return News.builder()
                .id(3L)
                .summaryHashtag(SummaryHashtagFixture.salesSummaryHashtag())
                .title("React 18의 새로운 Concurrent 기능")
                .content("React 18에서 도입된 동시성 기능에 대해 알아봅니다.")
                .url("https://example.com/news3")
                .postingDate(LocalDate.of(2024, 1, 25))
                .build();
    }

    public static News pythonNews() {
        return News.builder()
                .id(4L)
                .summaryHashtag(SummaryHashtagFixture.rndSummaryHashtag())
                .title("Python 3.12 성능 개선사항")
                .content("Python 3.12에서 향상된 성능과 새로운 기능들을 소개합니다.")
                .url("https://example.com/news4")
                .postingDate(LocalDate.of(2024, 2, 1))
                .build();
    }

    public static News dockerNews() {
        return News.builder()
                .id(5L)
                .summaryHashtag(SummaryHashtagFixture.otherNotesSummaryHashtag())
                .title("Docker 컨테이너 보안 모범 사례")
                .content("Docker 환경에서 보안을 강화하는 방법들을 정리했습니다.")
                .url("https://example.com/news5")
                .postingDate(LocalDate.of(2024, 2, 5))
                .build();
    }

    public static List<News> defaultNewsList() {
        return Arrays.asList(
                defaultNews(),
                springNews(),
                reactNews()
        );
    }

    public static List<News> recentNewsList() {
        return Arrays.asList(
                pythonNews(),
                dockerNews(),
                News.builder()
                        .id(6L)
                        .summaryHashtag(SummaryHashtagFixture.defaultSummaryHashtag())
                        .title("최신 개발 트렌드 2024")
                        .content("2024년 주목해야 할 개발 기술 트렌드를 분석합니다.")
                        .url("https://example.com/news6")
                        .postingDate(LocalDate.now().minusDays(1))
                        .build()
        );
    }

    public static List<News> oldNewsList() {
        return Arrays.asList(
                defaultNews(),
                springNews(),
                News.builder()
                        .id(7L)
                        .summaryHashtag(SummaryHashtagFixture.salesSummaryHashtag())
                        .title("2023년 기술 회고")
                        .content("2023년 한 해 동안의 기술 발전을 돌아봅니다.")
                        .url("https://example.com/news7")
                        .postingDate(LocalDate.of(2023, 12, 31))
                        .build()
        );
    }
}