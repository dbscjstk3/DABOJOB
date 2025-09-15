package com.dabojob.sync.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class JobPostingDataDto {
    private String saraminJobId;
    private String companyName;
    private String title;
    private String url;
    private Integer experienceLevelCode;
    private Integer jobMidCode;
    private Long postingTimeStamp;
    private Long expirationTimestamp;
    private String companyNameNormalized;
    private String dartId;
}