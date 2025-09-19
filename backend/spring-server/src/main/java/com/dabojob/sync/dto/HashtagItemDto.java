package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class HashtagItemDto {
    @JsonProperty("hashtag_id")
    private Long hashtagId;

    private String hashtag;
}
