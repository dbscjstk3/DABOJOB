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
    private Long jobPostingId;
    private Long companyId;
    private String saraminJobId;
    private String companyName;
    private String title;
    private String url;
    private Integer experienceLevelCode;
    private Integer jobMidCode;
    private LocalDate postingTimeStamp;
    private LocalDate expirationTimestamp;

    public static JobPostingResponse of(JobPosting jobPosting ){
        return JobPostingResponse.builder()
                .jobPostingId(jobPosting.getJobPostingId())
                .companyId(jobPosting.getCompanyJobPosting().getCompany().getCompanyId())
                .saraminJobId(jobPosting.getSaraminJobPostingId())
                .companyName(jobPosting.getCompanyName())
                .title(jobPosting.getTitle())
                .url(jobPosting.getUrl())
                .experienceLevelCode(jobPosting.getExperienceLevelCode())
                .jobMidCode(jobPosting.getJobMidCode())
                .postingTimeStamp(DateTimeUtil.convertToLocalDate(jobPosting.getPostingTimeStamp()))
                .expirationTimestamp(DateTimeUtil.convertToLocalDate(jobPosting.getExpirationTimestamp()))
                .build();
    }



}
