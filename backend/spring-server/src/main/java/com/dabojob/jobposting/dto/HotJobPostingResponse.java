package com.dabojob.jobposting.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class HotJobPostingResponse {
    private Long jobPostingId;
    private String companyName;
    private String title;
}