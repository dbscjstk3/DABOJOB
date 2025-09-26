package com.dabojob.fixture.user;

import com.dabojob.global.enums.UserRole;
import com.dabojob.user.entity.User;
import java.util.Arrays;
import java.util.List;

public class UserFixture {

    public static User defaultUser() {
        return User.builder()
                .id(1L)
                .email("user@example.com")
                .name("테스트 사용자")
                .role(UserRole.USER)
                .provider("google")
                .providerId("google_123456789")
                .build();
    }

    public static User adminUser() {
        return User.builder()
                .id(2L)
                .email("admin@example.com")
                .name("관리자")
                .role(UserRole.ADMIN)
                .provider("google")
                .providerId("google_admin_123")
                .build();
    }

    public static User ssafyUser() {
        return User.builder()
                .id(3L)
                .email("ssafy@example.com")
                .name("SSAFY 사용자")
                .role(UserRole.USER)
                .provider("ssafy")
                .providerId("ssafy_987654321")
                .build();
    }

    public static User googleUser() {
        return User.builder()
                .id(4L)
                .email("google.user@gmail.com")
                .name("구글 사용자")
                .role(UserRole.USER)
                .provider("google")
                .providerId("google_111222333")
                .build();
    }

    public static User johnUser() {
        return User.builder()
                .id(5L)
                .email("john.doe@company.com")
                .name("John Doe")
                .role(UserRole.USER)
                .provider("google")
                .providerId("google_john_doe")
                .build();
    }

    public static User superAdminUser() {
        return User.builder()
                .id(6L)
                .email("super.admin@dabojob.com")
                .name("슈퍼 관리자")
                .role(UserRole.ADMIN)
                .provider("ssafy")
                .providerId("ssafy_super_admin")
                .build();
    }

    public static List<User> defaultUserList() {
        return Arrays.asList(
                defaultUser(),
                adminUser(),
                ssafyUser()
        );
    }

    public static List<User> adminUserList() {
        return Arrays.asList(
                adminUser(),
                superAdminUser(),
                User.builder()
                        .id(7L)
                        .email("admin2@example.com")
                        .name("부관리자")
                        .role(UserRole.ADMIN)
                        .provider("google")
                        .providerId("google_admin2")
                        .build()
        );
    }

    public static List<User> regularUserList() {
        return Arrays.asList(
                defaultUser(),
                ssafyUser(),
                googleUser(),
                johnUser()
        );
    }

    public static List<User> googleProviderUserList() {
        return Arrays.asList(
                defaultUser(),
                adminUser(),
                googleUser(),
                johnUser()
        );
    }

    public static List<User> ssafyProviderUserList() {
        return Arrays.asList(
                ssafyUser(),
                superAdminUser(),
                User.builder()
                        .id(8L)
                        .email("ssafy2@ssafy.com")
                        .name("SSAFY 교육생")
                        .role(UserRole.USER)
                        .provider("ssafy")
                        .providerId("ssafy_student_001")
                        .build()
        );
    }
}