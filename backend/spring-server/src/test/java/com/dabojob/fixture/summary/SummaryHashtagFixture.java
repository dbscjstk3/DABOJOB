package com.dabojob.fixture.summary;

import com.dabojob.summary.entity.ChapterType;
import com.dabojob.summary.entity.SummaryHashtag;
import java.util.Arrays;
import java.util.List;

public class SummaryHashtagFixture {

    public static SummaryHashtag defaultSummaryHashtag() {
        return SummaryHashtag.builder()
                .id(1L)
                .summary(CompanyAnalysisSummaryFixture.defaultSummary())
                .chapterType(ChapterType.BUSINESS_OVERVIEW)
                .hashtag(HashtagFixture.defaultHashtag())
                .build();
    }

    public static SummaryHashtag productsSummaryHashtag() {
        return SummaryHashtag.builder()
                .id(2L)
                .summary(CompanyAnalysisSummaryFixture.defaultSummary())
                .chapterType(ChapterType.PRODUCTS_SERVICE)
                .hashtag(HashtagFixture.springHashtag())
                .build();
    }

    public static SummaryHashtag salesSummaryHashtag() {
        return SummaryHashtag.builder()
                .id(3L)
                .summary(CompanyAnalysisSummaryFixture.createdSummary())
                .chapterType(ChapterType.SALES_CONTRACTS)
                .hashtag(HashtagFixture.reactHashtag())
                .build();
    }

    public static SummaryHashtag rndSummaryHashtag() {
        return SummaryHashtag.builder()
                .id(4L)
                .summary(CompanyAnalysisSummaryFixture.updatedSummary())
                .chapterType(ChapterType.RND_ACTIVITIES)
                .hashtag(HashtagFixture.pythonHashtag())
                .build();
    }

    public static SummaryHashtag otherNotesSummaryHashtag() {
        return SummaryHashtag.builder()
                .id(5L)
                .summary(CompanyAnalysisSummaryFixture.samsungSummary())
                .chapterType(ChapterType.OTHER_NOTES)
                .hashtag(HashtagFixture.dockerHashtag())
                .build();
    }

    public static List<SummaryHashtag> defaultSummaryHashtagList() {
        return Arrays.asList(
                defaultSummaryHashtag(),
                productsSummaryHashtag(),
                salesSummaryHashtag()
        );
    }

    public static List<SummaryHashtag> businessOverviewHashtagList() {
        return Arrays.asList(
                defaultSummaryHashtag(),
                SummaryHashtag.builder()
                        .id(6L)
                        .summary(CompanyAnalysisSummaryFixture.createdSummary())
                        .chapterType(ChapterType.BUSINESS_OVERVIEW)
                        .hashtag(HashtagFixture.springHashtag())
                        .build(),
                SummaryHashtag.builder()
                        .id(7L)
                        .summary(CompanyAnalysisSummaryFixture.updatedSummary())
                        .chapterType(ChapterType.BUSINESS_OVERVIEW)
                        .hashtag(HashtagFixture.reactHashtag())
                        .build()
        );
    }

    public static List<SummaryHashtag> rndHashtagList() {
        return Arrays.asList(
                rndSummaryHashtag(),
                SummaryHashtag.builder()
                        .id(8L)
                        .summary(CompanyAnalysisSummaryFixture.defaultSummary())
                        .chapterType(ChapterType.RND_ACTIVITIES)
                        .hashtag(HashtagFixture.defaultHashtag())
                        .build(),
                SummaryHashtag.builder()
                        .id(9L)
                        .summary(CompanyAnalysisSummaryFixture.naverSummary())
                        .chapterType(ChapterType.RND_ACTIVITIES)
                        .hashtag(HashtagFixture.dockerHashtag())
                        .build()
        );
    }
}