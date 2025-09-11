package com.dabojob.analysis.entity;


import com.dabojob.company.entity.DartCompany;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
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
@Table(name = "summary_hashtags")
public class SummaryHashtag {

    @Id
    @Column(name="summary_hashtag_id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long summaryHashtagId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="summary_id")
    private CompanyAnalysisSummary summary;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="hashtag_id")
    private Hashtag hashtag;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="dart_id")
    private DartCompany dartCompany;
}
