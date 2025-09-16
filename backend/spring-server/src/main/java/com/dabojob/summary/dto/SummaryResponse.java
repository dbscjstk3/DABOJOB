package com.dabojob.summary.dto;

import com.dabojob.summary.entity.CompanyAnalysisSummary;
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
    private String fullSummary;

    public static SummaryResponse of(CompanyAnalysisSummary summary) {
        return SummaryResponse.builder()
                .summaryId(summary.getSummaryId())
                .companyId(summary.getCompany().getCompanyId())
                .companyName(summary.getCompany().getCompanyName())
                .fullSummary(summary.getOverview())
                .build();
    }
}
