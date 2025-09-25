package com.dabojob.fixture.summary;

import com.dabojob.summary.entity.Hashtag;
import java.util.Arrays;
import java.util.List;

public class HashtagFixture {

    public static Hashtag defaultHashtag() {
        return Hashtag.builder()
                .id(1L)
                .name("Java")
                .build();
    }

    public static Hashtag springHashtag() {
        return Hashtag.builder()
                .id(2L)
                .name("Spring")
                .build();
    }

    public static Hashtag reactHashtag() {
        return Hashtag.builder()
                .id(3L)
                .name("React")
                .build();
    }

    public static Hashtag pythonHashtag() {
        return Hashtag.builder()
                .id(4L)
                .name("Python")
                .build();
    }

    public static Hashtag dockerHashtag() {
        return Hashtag.builder()
                .id(5L)
                .name("Docker")
                .build();
    }

    public static List<Hashtag> defaultHashtagList() {
        return Arrays.asList(
                defaultHashtag(),
                springHashtag(),
                reactHashtag()
        );
    }

    public static List<Hashtag> backendHashtagList() {
        return Arrays.asList(
                defaultHashtag(),
                springHashtag(),
                dockerHashtag()
        );
    }

    public static List<Hashtag> frontendHashtagList() {
        return Arrays.asList(
                reactHashtag(),
                Hashtag.builder().id(6L).name("TypeScript").build(),
                Hashtag.builder().id(7L).name("Vue.js").build()
        );
    }
}
