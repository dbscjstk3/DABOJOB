package com.dabojob.user.repository.entity;

import com.dabojob.global.enums.UserRole;
import com.dabojob.global.repository.entity.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "users")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class User extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String email;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private UserRole role = UserRole.USER;

    @Column(nullable = false)
    private String provider; // "google", "ssafy"  등

    @Column(name = "provider_id", nullable = false)
    private String providerId; // OAuth 제공자에서의 사용자 고유 ID

    /**
     * 사용자 정보 업데이트 (OAuth 로그인 시 최신 정보로 동기화)
     */
    public void updateProfile(String email, String name) {
        this.email = email;
        this.name = name;
    }

    /**
     * 관리자 권한 부여
     */
    public void grantAdminRole() {
        this.role = UserRole.ADMIN;
    }

    /**
     * 일반 사용자 권한으로 변경
     */
    public void revokeAdminRole() {
        this.role = UserRole.USER;
    }

    /**
     * 관리자인지 확인
     */
    public boolean isAdmin() {
        return role == UserRole.ADMIN;
    }
}