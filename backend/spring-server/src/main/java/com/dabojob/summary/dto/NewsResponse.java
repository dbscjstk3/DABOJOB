package com.dabojob.summary.dto;

import com.dabojob.summary.entity.News;
import java.time.LocalDate;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsResponse {

    private Long newsId;
    private Long summaryHashtagId;
    private String newsUrl;
    private String newsTitle;
    private String newsContent;
    private LocalDate newsCreateDate;

    public static NewsResponse of(News news){
        return NewsResponse.builder()
                .newsId(news.getNewsId())
                .summaryHashtagId(news.getSummaryHashtag().getSummaryHashtagId())
                .newsUrl(news.getNewsUrl())
                .newsTitle(news.getNewsTitle())
                .newsContent(news.getNewsContent())
                .newsCreateDate(news.getNewsCreatedAt())
                .build();
    }
}
