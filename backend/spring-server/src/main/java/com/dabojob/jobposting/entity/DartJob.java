package com.dabojob.jobposting.entity;

import com.dabojob.company.entity.DartCompany;
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
@Table(name = "dart_jobs")
public class DartJob extends BaseTimeEntity {

    @Id
    @Column(name="dart_job_id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long dartJobId;

    @OneToOne
    @JoinColumn(name="job_id")
    private JobPosting jobPosting;

    @ManyToOne(fetch =  FetchType.LAZY)
    @JoinColumn(name="company_id")
    private DartCompany  dartCompany;

    @Column(name="company_name_normalized")
    private String companyNameNormalized;

}
