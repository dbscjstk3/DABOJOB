package com.dabojob.auth.controller;

import com.dabojob.auth.dto.SuccessResponse;
import com.dabojob.auth.dto.TokenResponse;
import com.dabojob.auth.dto.UserInfoResponse;
import com.dabojob.auth.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @GetMapping("/login/{provider}")
    public void loginRedirect(@PathVariable String provider, HttpServletResponse response) throws IOException {
        response.sendRedirect("/oauth2/authorization/" + provider);
    }

    @PostMapping("/refresh")
    public ResponseEntity<TokenResponse> refreshToken(HttpServletRequest request, HttpServletResponse response) {
        TokenResponse tokenResponse = authService.refreshTokenFromCookie(request, response);
        return ResponseEntity.ok(tokenResponse);
    }

    @PostMapping("/logout")
    public ResponseEntity<SuccessResponse> logout(Authentication authentication, HttpServletResponse response) {
        authService.logout(authentication, response);
        return ResponseEntity.ok(new SuccessResponse(true, "로그아웃되었습니다."));
    }


    @GetMapping("/me")
    public ResponseEntity<UserInfoResponse> getCurrentUser(Authentication authentication) {
        UserInfoResponse userInfo = authService.getCurrentUser(authentication);
        return ResponseEntity.ok(userInfo);
    }


//    @PostMapping("/revoke")  // 사용자당 하나의 Refresh Token이 아니라, 여러개를 허용할 것이라면 도입. 단 내부 로직 변경 필요.
//    public ResponseEntity<SuccessResponse> revokeToken(HttpServletRequest request) {
//        authService.revokeTokenFromCookie(request);
//        return ResponseEntity.ok(new SuccessResponse(true, "토큰이 무효화되었습니다."));
//    }
}