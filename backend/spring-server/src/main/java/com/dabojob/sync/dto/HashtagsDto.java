package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class HashtagsDto {
    private List<CategoryDto> categories;

    @JsonProperty("total_categories")
    private Integer totalCategories;
}
