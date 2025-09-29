package com.dabojob.global.exception;

public class RedisServiceException extends RuntimeException {
    public RedisServiceException(String message) {
        super(message);
    }

    public RedisServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
