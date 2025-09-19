package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class NewsItemDto {
    @JsonProperty("news_id")
    private Long newsId;

    @JsonProperty("hashtag_id")
    private Long hashtagId;

    private String title;
    private String url;

    @JsonProperty("published_date")
    private String publishedDate;

    private String chapter;
    private String hashtag;
    private String summary;

    @JsonProperty("company_name")
    private String companyName;

    private String status;
}
