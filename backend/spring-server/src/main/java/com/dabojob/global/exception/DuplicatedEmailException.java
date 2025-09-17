package com.dabojob.global.exception;

import org.springframework.security.oauth2.core.OAuth2AuthenticationException;

public class DuplicatedEmailException extends OAuth2AuthenticationException {

    public DuplicatedEmailException(String email, String existingProvider) {
        super(String.format("이미 %s로 가입된 이메일입니다: %s", existingProvider, email));
    }
}
