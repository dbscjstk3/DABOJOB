package com.dabojob.jobposting.dto;

import com.dabojob.global.utils.DateTimeUtil;
import com.dabojob.jobposting.entity.JobPosting;
import java.time.LocalDate;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class JobPostingResponse {
    private Long jobId;
    private Long dartCompanyId;
    private String saraminJobId;
    private String companyName;
    private String title;
    private String url;
    private Integer experienceLevelCode;
    private LocalDate postingTimeStamp;
    private LocalDate expirationTimestamp;

    public static JobPostingResponse of(JobPosting jobPosting ){
        return JobPostingResponse.builder()
                .jobId(jobPosting.getJobPostingId())
                .dartCompanyId(jobPosting.getDartJob().getDartCompany().getCompanyId())
                .saraminJobId(jobPosting.getSaraminJobId())
                .companyName(jobPosting.getCompanyName())
                .title(jobPosting.getTitle())
                .url(jobPosting.getUrl())
                .experienceLevelCode(jobPosting.getExperienceLevelCode())
                .postingTimeStamp(DateTimeUtil.convertToLocalDate(jobPosting.getPostingTimeStamp()))
                .expirationTimestamp(DateTimeUtil.convertToLocalDate(jobPosting.getExpirationTimestamp()))
                .build();
    }



}
