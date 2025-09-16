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
    @Column(name="business_overview",columnDefinition = "TEXT")
    private String businessOverview;

    @Lob
    @Column(name="products_service",columnDefinition = "TEXT")
    private String productsService;

    @Lob
    @Column(name="sales_contracts",columnDefinition = "TEXT")
    private String salesContracts;

    @Lob
    @Column(name="rnd_activities",columnDefinition = "TEXT")
    private String rndActivities;

    @Lob
    @Column(name="other_notes",columnDefinition = "TEXT")
    private String otherNotes;

    @Enumerated(EnumType.STRING)  // DB에 "CREATED", "UPDATED", "FINISHED" 저장
    @Column(name = "status", nullable = false)
    private SummaryStatus status;





}
