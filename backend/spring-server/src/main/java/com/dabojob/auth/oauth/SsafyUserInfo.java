package com.dabojob.auth.oauth;

import java.util.Map;

public class SsafyUserInfo implements OAuthUserInfo {

    private final Map<String, Object> attributes;

    public SsafyUserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String getProviderId() {
        return String.valueOf(attributes.get("userId"));
    }

    @Override
    public String getProvider() {
        return "ssafy";
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