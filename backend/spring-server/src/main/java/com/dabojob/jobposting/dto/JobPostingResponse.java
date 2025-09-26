package com.dabojob.jobposting.dto;

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
    private String companyName;
    private String title;
    private String url;

    private Long jobSectorId;
    private String jobSectorName;
    private String jobSectorCategory;
    private String careerInfo;

    private LocalDate postingDate;
    private LocalDate deadlineDate;

    public static JobPostingResponse of(JobPosting jobPosting ){
        return JobPostingResponse.builder()
                .jobPostingId(jobPosting.getId())
                .companyId(jobPosting.getCompany().getId())
                .companyName(jobPosting.getCompany().getName())
                .title(jobPosting.getTitle())
                .url(jobPosting.getUrl())
                .jobSectorId(jobPosting.getJobSector().getId())
                .jobSectorName(jobPosting.getJobSector().getName())
                .jobSectorCategory(jobPosting.getJobSector().getCategory())
                .careerInfo(jobPosting.getCareerInfo().getName())
                .postingDate(jobPosting.getPostingDate())
                .deadlineDate(jobPosting.getDeadlineDate())
                .build();
    }



}
