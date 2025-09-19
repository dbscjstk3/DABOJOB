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

    private Long summaryHashtagId;
    private String url;
    private String title;
    private String content;
    private LocalDate postingDate;

    public static NewsResponse of(News news){
        return NewsResponse.builder()
                .summaryHashtagId(news.getSummaryHashtag().getId())
                .url(news.getUrl())
                .title(news.getTitle())
                .content(news.getContent())
                .postingDate(news.getPostingDate())
                .build();
    }
}
