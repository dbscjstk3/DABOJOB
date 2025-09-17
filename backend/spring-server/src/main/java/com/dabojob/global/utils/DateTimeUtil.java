package com.dabojob.global.utils;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;

public class DateTimeUtil {
    public static LocalDate convertToLocalDate(Long timestamp) {
        return Instant.ofEpochSecond(timestamp)
                .atZone(ZoneId.of("Asia/Seoul"))
                .toLocalDate();
    }
}
