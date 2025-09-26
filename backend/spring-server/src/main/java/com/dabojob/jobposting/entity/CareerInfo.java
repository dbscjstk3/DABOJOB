package com.dabojob.jobposting.entity;

public enum CareerInfo {
    JUNIOR("신입") ,
    EXPERIENCED("경력") ,
    SENIOR("시니어");

    private final String name;

    CareerInfo(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }
}
