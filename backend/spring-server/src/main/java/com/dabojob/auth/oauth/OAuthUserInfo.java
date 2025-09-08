package com.dabojob.auth.oauth;

/**
 * OAuth 제공자별 사용자 정보 추상화 인터페이스
 * 각 OAuth 제공자마다 응답 구조가 다르므로 공통 인터페이스로 통일
 */
public interface OAuthUserInfo {

    /**
     * OAuth 제공자에서의 사용자 고유 ID
     */
    String getProviderId();

    /**
     * OAuth 제공자명 (google, ssafy 등)
     */
    String getProvider();

    /**
     * 사용자 이메일
     */
    String getEmail();

    /**
     * 사용자 이름
     */
    String getName();
}