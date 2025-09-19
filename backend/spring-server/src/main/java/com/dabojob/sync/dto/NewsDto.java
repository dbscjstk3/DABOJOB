package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class NewsDto {
    private List<NewsItemDto> items;

    @JsonProperty("total_count")
    private Integer totalCount;

    @JsonProperty("completed_count")
    private Integer completedCount;

    @JsonProperty("by_hashtag")
    private Map<String, Object> byHashtag;
}