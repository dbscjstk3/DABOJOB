package com.dabojob.global.enums;

import lombok.Getter;

@Getter
public enum UserRole {
    USER("ROLE_USER", "일반 사용자"),
    ADMIN("ROLE_ADMIN", "관리자");

    private final String role;
    private final String description;

    UserRole(String role, String description) {
        this.role = role;
        this.description = description;
    }
}
