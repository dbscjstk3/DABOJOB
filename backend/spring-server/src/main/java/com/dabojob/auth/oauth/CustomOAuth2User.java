package com.dabojob.auth.oauth;

import com.dabojob.user.entity.User;
import java.util.Collection;
import java.util.Map;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.core.user.OAuth2User;

/**
 * OAuth2User를 구현한 커스텀 사용자 객체
 * Spring Security가 OAuth 인증 후 사용하는 Principal 객체
 */
@Getter
public class CustomOAuth2User implements OAuth2User {

    private final Collection<? extends GrantedAuthority> authorities;
    private final Map<String, Object> attributes;
    private final String nameAttributeKey;
    private final User user;

    public CustomOAuth2User(Collection<? extends GrantedAuthority> authorities,
                            Map<String, Object> attributes,
                            String nameAttributeKey,
                            User user) {
        this.authorities = authorities;
        this.attributes = attributes;
        this.nameAttributeKey = nameAttributeKey;
        this.user = user;
    }

    /**
     * OAuth2User 인터페이스 구현: 사용자 속성 정보
     */
    @Override
    public Map<String, Object> getAttributes() {
        return attributes;
    }

    /**
     * OAuth2User 인터페이스 구현: 사용자 권한 목록
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    /**
     * OAuth2User 인터페이스 구현: 사용자 이름 (주 식별자)
     * OAuth 제공자별로 다를 수 있음 (Google: sub, Kakao: id 등)
     */
    @Override
    public String getName() {
        return String.valueOf(attributes.get(nameAttributeKey));
    }

    /**
     * 우리 시스템의 사용자 ID 반환
     */
    public Long getUserId() {
        return user.getId();
    }

    /**
     * 사용자 이메일 반환
     */
    public String getEmail() {
        return user.getEmail();
    }

    /**
     * 사용자 이름 반환
     */
    public String getUserName() {
        return user.getName();
    }

    /**
     * 사용자 권한 반환
     */
    public String getRole() {
        return user.getRole().getRole();
    }

    /**
     * OAuth 제공자 반환
     */
    public String getProvider() {
        return user.getProvider();
    }

    /**
     * OAuth 제공자에서의 사용자 ID 반환
     */
    public String getProviderId() {
        return user.getProviderId();
    }

    /**
     * 관리자 권한 여부 확인
     */
    public boolean isAdmin() {
        return user.isAdmin();
    }
}