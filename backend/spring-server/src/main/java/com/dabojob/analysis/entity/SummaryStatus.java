package com.dabojob.analysis.entity;

import lombok.Getter;

@Getter
public enum SummaryStatus {
    CREATED("작성됨", "보고서가 생성되었습니다"),
    UPDATED("수정됨", "보고서가 수정되었습니다"),
    FINISHED("완료됨", "보고서 작성이 완료되었습니다");

    private final String displayName;
    private final String description;

    SummaryStatus(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

}
