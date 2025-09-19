package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DartDto {
    @JsonProperty("job_id")
    private Long jobId;

    @JsonProperty("company_id")
    private Long companyId;

    @JsonProperty("dart_summaries")
    private DartSummariesDto dartSummaries;

    @JsonProperty("news")
    private NewsDto news;

    @JsonProperty("hashtags")
    private HashtagsDto hashtags;

    @JsonProperty("generated_at")
    private String generatedAt;
}