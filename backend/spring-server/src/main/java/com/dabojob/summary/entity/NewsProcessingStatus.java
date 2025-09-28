package com.dabojob.summary.entity;

import lombok.Getter;

@Getter
public enum NewsProcessingStatus {
    PROCESSING("처리중", "뉴스 요약 작업이 진행 중입니다"),
    COMPLETED("완료됨", "뉴스 요약 작업이 완료되었습니다"),
    FINISHED("승인됨", "관리자 승인이 완료되어 S3 업로드가 가능합니다");

    private final String displayName;
    private final String description;

    NewsProcessingStatus(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }
}