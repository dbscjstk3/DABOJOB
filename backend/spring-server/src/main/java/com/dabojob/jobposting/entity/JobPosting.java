package com.dabojob.jobposting.entity;

import com.dabojob.global.entity.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Table(name = "job_postings")
public class JobPosting extends BaseTimeEntity {

    @Id
    @Column(name="job_posting_id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long jobPostingId;

    @OneToOne(mappedBy = "jobPosting", fetch = FetchType.LAZY)
    private CompanyJobPosting companyJobPosting;

    @Column(name="saramin_job_posting_id", unique = true)
    private String saraminJobPostingId;

    @Column(name="company_name")
    private String companyName;

    private String title;

    private String url;

    @Column(name = "experience_level_code",columnDefinition = "TINYINT")
    private Integer experienceLevelCode;

    @Column(name="job_mid_code",columnDefinition = "TINYINT")
    private Integer jobMidCode;

    @Column(name="posting_timestamp")
    private Long postingTimeStamp;

    @Column(name="expiration_timestamp")
    private Long expirationTimestamp;


}
