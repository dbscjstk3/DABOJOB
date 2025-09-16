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
    private String overview;
    private String products;
    private String financials;
    private String contracts;
    private String miscInfo;

    private Map<ChapterType, List<String>> chapterHashtags;

    public static SummaryResponse of(CompanyAnalysisSummary summary, Map<ChapterType, List<String>> chapterHashtags) {
        return SummaryResponse.builder()
                .summaryId(summary.getSummaryId())
                .companyId(summary.getCompany().getCompanyId())
                .companyName(summary.getCompany().getCompanyName())
                .overview(summary.getOverview())
                .products(summary.getProducts())
                .financials(summary.getFinancials())
                .contracts(summary.getContracts())
                .miscInfo(summary.getMiscInfo())
                .chapterHashtags(chapterHashtags)
                .build();
    }
}
