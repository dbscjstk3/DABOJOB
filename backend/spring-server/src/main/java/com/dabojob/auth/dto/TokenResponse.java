package com.dabojob.auth.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * JWT 토큰 응답 DTO
 * Access Token 갱신 API의 응답으로 사용
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TokenResponse {

    /**
     * JWT Access Token
     */
    private String accessToken;

    /**
     * JWT Refresh Token (필요한 경우에만 포함)
     */
    private String refreshToken;

    /**
     * 토큰 타입 (항상 "Bearer")
     */
    @Builder.Default
    private String tokenType = "Bearer";

    /**
     * Access Token 만료시간 (초 단위)
     */
    private Long expiresIn;

    /**
     * Access Token만 포함하는 응답 생성
     */
    public static TokenResponse ofAccessToken(String accessToken, Long expiresIn) {
        return TokenResponse.builder()
                .accessToken(accessToken)
                .expiresIn(expiresIn)
                .build();
    }

    /**
     * Access Token과 Refresh Token 모두 포함하는 응답 생성
     */
    public static TokenResponse ofBothTokens(String accessToken, String refreshToken, Long expiresIn) {
        return TokenResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .expiresIn(expiresIn)
                .build();
    }
}