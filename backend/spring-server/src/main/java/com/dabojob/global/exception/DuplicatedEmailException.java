package com.dabojob.global.exception;

import org.springframework.security.oauth2.core.OAuth2AuthenticationException;

public class DuplicatedEmailException extends OAuth2AuthenticationException {

    public DuplicatedEmailException(String email, String existingProvider) {
        super(String.format("Already Registered by %s : %s", existingProvider, email));
    }
}
