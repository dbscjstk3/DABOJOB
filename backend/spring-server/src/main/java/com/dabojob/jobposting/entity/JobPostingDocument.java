package com.dabojob.jobposting.entity;

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
            mainField = @Field(type = FieldType.Text, analyzer = "korean", searchAnalyzer = "korean_search"),
            otherFields = {
                    @InnerField(suffix = "autocomplete", type = FieldType.Search_As_You_Type)
            }
    )
    @Field(name = "company_name")
    private String companyName;

    @CompletionField(maxInputLength = 100)
    private String companyNameCompletion;

    @MultiField(
            mainField = @Field(type = FieldType.Text, analyzer = "korean", searchAnalyzer = "korean_search"),
            otherFields = {
                    @InnerField(suffix = "autocomplete", type = FieldType.Search_As_You_Type)
            }
    )
    @Field(name = "title")
    private String title;

    @CompletionField(maxInputLength = 100)
    private String titleCompletion;

    @Field(type = FieldType.Integer, name="company_scale")
    private Integer companyScale;

    @Field(type = FieldType.Keyword, index = false)
    private String url;

    @Field(type = FieldType.Keyword, name = "career_info")
    private CareerInfo careerInfo;

    @Field(type = FieldType.Integer, name = "job_sector_code", index = false)
    private Integer jobSectorCode;

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

}