package com.dabojob.analysis.entity;

import com.dabojob.company.entity.DartCompany;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDate;
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
@Table(name = "news")
public class News {

    @Id
    @Column(name="news_id")
    private String newsId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "dart_id")
    private DartCompany  dartCompany;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "summary_id")
    private CompanyAnalysisSummary summary;

    @Column(name="news_content")
    private String newsContent;

    @Column(name="news_url")
    private String newsUrl;

    @Column(name="news_created_at")
    private LocalDate newsCreatedAt;


}
