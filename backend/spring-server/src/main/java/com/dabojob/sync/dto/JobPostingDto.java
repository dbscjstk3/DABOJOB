package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class JobPostingDto {
    @JsonProperty("job_id")
    private Long jobId;

    @JsonProperty("company_id")
    private Long companyId;

    @JsonProperty("sector_id")
    private Long sectorId;

    @JsonProperty("saramin_job_title")
    private String saraminJobTitle;

    @JsonProperty("saramin_job_url")
    private String saraminJobUrl;

    @JsonProperty("career_info")
    private String careerInfo;

    @JsonProperty("posting_date")
    private String postingDate;

    @JsonProperty("application_deadline")
    private String applicationDeadline;
}
