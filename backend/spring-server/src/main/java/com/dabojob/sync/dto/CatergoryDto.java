package com.dabojob.sync.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class CategoryDto {
    private String category;
    private List<HashtagItemDto> hashtags;
}
