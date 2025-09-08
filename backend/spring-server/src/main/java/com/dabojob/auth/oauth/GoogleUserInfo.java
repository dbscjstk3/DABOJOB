package com.dabojob.auth.oauth;

import java.util.Map;

/**
 * Google OAuth 사용자 정보 처리 클래스
 * Google OAuth 응답 구조에 맞게 사용자 정보 추출
 */
public class GoogleUserInfo implements OAuthUserInfo {

    private final Map<String, Object> attributes;

    public GoogleUserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String getProviderId() {
        // Google OAuth에서는 'sub' 필드가 사용자 고유 ID
        return (String) attributes.get("sub");
    }

    @Override
    public String getProvider() {
        return "google";
    }

    @Override
    public String getEmail() {
        return (String) attributes.get("email");
    }

    @Override
    public String getName() {
        return (String) attributes.get("name");
    }
}