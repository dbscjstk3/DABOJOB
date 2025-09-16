package com.dabojob.jobposting.entity;

import com.dabojob.company.entity.Company;
import com.dabojob.global.entity.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
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
@Table(name = "company_job_postings")
public class CompanyJobPosting extends BaseTimeEntity {

    @Id
    @Column(name="company_job_posting_id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long companyJobPostingId;

    @OneToOne
    @JoinColumn(name="job_posting_id")
    private JobPosting jobPosting;

    @ManyToOne(fetch =  FetchType.LAZY)
    @JoinColumn(name="company_id")
    private Company company;

    @Column(name="company_name_normalized")
    private String companyNameNormalized;

}
