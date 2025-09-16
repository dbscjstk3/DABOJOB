package com.dabojob.summary.entity;

import com.dabojob.company.entity.Company;
import com.dabojob.global.entity.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.Lob;
import jakarta.persistence.ManyToOne;
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
@Table(name = "company_analysis_summaries")
public class CompanyAnalysisSummary extends BaseTimeEntity {

    @Id
    @Column(name="summary_id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long summaryId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "company_id")
    private Company company;

    @Column(name="company_name_normalized")
    private String companyNameNormalized;

    @Lob
    @Column(name="full_summary",columnDefinition = "TEXT")
    private String fullSummary;

    @Enumerated(EnumType.STRING)  // DB에 "CREATED", "UPDATED", "FINISHED" 저장
    @Column(name = "status", nullable = false)
    private SummaryStatus status;





}
