package com.dabojob.summary.dto;

import com.dabojob.summary.entity.ChapterType;
import com.dabojob.summary.entity.CompanyAnalysisSummary;
import java.util.List;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SummaryResponse {

    private Long summaryId;
    private Long companyId;
    private String companyName;
    private String businessOverview;
    private String productsService;
    private String salesContracts;
    private String rndActivities;
    private String otherNotes;

    private Map<ChapterType, List<String>> chapterHashtags;
    private final static String SUMMARY_EMPTY = "Summary file not found";

    public static SummaryResponse of(CompanyAnalysisSummary summary, Map<ChapterType, List<String>> chapterHashtags) {
        return SummaryResponse.builder()
                .summaryId(summary.getId())
                .companyId(summary.getCompany().getId())
                .companyName(summary.getCompany().getName())
                .businessOverview(nullIfEmpty (summary.getBusinessOverview()))
                .productsService(nullIfEmpty (summary.getProductsService()))
                .salesContracts(nullIfEmpty (summary.getSalesContracts()))
                .rndActivities(nullIfEmpty (summary.getRndActivities()))
                .otherNotes(nullIfEmpty (summary.getOtherNotes()))
                .chapterHashtags(chapterHashtags)
                .build();
    }

    private static String nullIfEmpty (String value) {
        return SUMMARY_EMPTY.equals(value) ? null : value;
    }

}
