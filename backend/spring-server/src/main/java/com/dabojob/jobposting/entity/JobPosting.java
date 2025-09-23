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
@Table(name = "job_postings")
public class JobPosting extends BaseTimeEntity {

    @Id
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="company_id", nullable = false)
    private Company company;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "job_sector_id", nullable = false)
    private JobSector jobSector;

    private String title;

    private String url;

    @Column(name="career_info", nullable = false)
    private CareerInfo careerInfo;

    @Column(name="posting_date")
    private LocalDate postingDate;

    @Column(name="deadline_date")
    private LocalDate deadlineDate;


}
