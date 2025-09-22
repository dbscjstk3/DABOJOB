package com.dabojob.global.exception;

import java.time.LocalDateTime;
import java.util.Map;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ErrorResponse {
    private String message;
    private String code;
    private LocalDateTime timestamp;

    // 추가 필드들
    private String path;
    private Map<String, String> fieldErrors;  // validation 에러용
}
