package com.dabojob.jobposting.entity;

import com.dabojob.company.entity.Company;
import com.dabojob.jobposting.dto.JobPostingResponse;
import com.dabojob.summary.entity.Hashtag;
import com.dabojob.summary.entity.SummaryHashtag;
import java.time.LocalDate;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.CompletionField;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;

import org.springframework.data.elasticsearch.annotations.InnerField;
import org.springframework.data.elasticsearch.annotations.MultiField;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(indexName = "job_posting")
public class JobPostingDocument {

    @Id
    @Field(type = FieldType.Long, index = false, name = "job_posting_id")
    private Long jobPostingId;

    @Field(type = FieldType.Long, index = false, name = "company_id")
    private Long companyId;

    // 메인 검색용
    @MultiField(
            mainField = @Field(type = FieldType.Text, analyzer = "korean", searchAnalyzer = "korean_search", name = "company_name"),
            otherFields = {
                    @InnerField(suffix = "autocomplete", type = FieldType.Search_As_You_Type)
            }
    )
    private String companyName;

    @CompletionField(maxInputLength = 100)
    private String companyNameCompletion;

    @MultiField(
            mainField = @Field(type = FieldType.Text, analyzer = "korean", searchAnalyzer = "korean_search", name = "title"),
            otherFields = {
                    @InnerField(suffix = "autocomplete", type = FieldType.Search_As_You_Type)
            }
    )
    private String title;

    @CompletionField(maxInputLength = 100)
    private String titleCompletion;

    @Field(type = FieldType.Keyword, name="company_scale")
    private String companyScale;

    @Field(type = FieldType.Keyword, index = false)
    private String url;

    @Field(type = FieldType.Keyword, name = "career_info")
    private CareerInfo careerInfo;

    @Field(type = FieldType.Long, name = "job_sector_code", index = false)
    private Long jobSectorCode;

    @Field(type = FieldType.Keyword, name ="job_sector_name" )
    private String jobSectorName;

    @Field(type = FieldType.Text, name ="job_sector_category")
    private String jobSectorCategory;

    @Field(type = FieldType.Text, name ="summary_hashtags")
    private List<String> summaryHashtags;

    @Field(type = FieldType.Date, pattern = "yyyy-MM-dd", name = "posting_date")
    private LocalDate postingDate;

    @Field(type = FieldType.Date, pattern = "yyyy-MM-dd", name = "deadline_date")
    private LocalDate deadlineDate;

    public static JobPostingDocument of (JobPosting jobPosting, JobSector jobSector, Company company, List<SummaryHashtag> hashtags) {
        List<String> hashtagIds = hashtags.stream().map(SummaryHashtag::getHashtag).map(Hashtag::getName).toList();

        return JobPostingDocument.builder()
                .jobPostingId(jobPosting.getId())
                .companyId(company.getId())
                .companyName(company.getName())
                .companyNameCompletion(company.getName())
                .title(jobPosting.getTitle())
                .titleCompletion(jobPosting.getTitle())
                .companyScale(company.getScale().name())
                .url(jobPosting.getUrl())
                .careerInfo(jobPosting.getCareerInfo())
                .jobSectorCode(jobSector.getId())
                .jobSectorName(jobSector.getName())
                .jobSectorCategory(jobSector.getCategory())
                .summaryHashtags(hashtagIds)
                .postingDate(jobPosting.getPostingDate())
                .deadlineDate(jobPosting.getDeadlineDate())
                .build();
    }

    public static JobPostingResponse toResponse(JobPostingDocument document) {
        return JobPostingResponse.builder()
                .jobPostingId(document.getJobPostingId())
                .companyId(document.getCompanyId())
                .companyName(document.getCompanyName())
                .title(document.getTitle())
                .url(document.getUrl())
                .jobSectorId(document.getJobSectorCode())
                .jobSectorName(document.getJobSectorName())
                .jobSectorCategory(document.getJobSectorCategory())
                .careerInfo(document.getCareerInfo().name())
                .postingDate(document.getPostingDate())
                .deadlineDate(document.getDeadlineDate())
                .build();
    }

}