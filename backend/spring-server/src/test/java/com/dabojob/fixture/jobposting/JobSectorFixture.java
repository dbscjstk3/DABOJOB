package com.dabojob.fixture.jobposting;

import com.dabojob.jobposting.entity.JobSector;
import java.util.Arrays;
import java.util.List;

public class JobSectorFixture {

    public static JobSector defaultJobSector() {
        return JobSector.builder()
                .id(1L)
                .name("백엔드 개발")
                .category("개발")
                .build();
    }

    public static JobSector frontendJobSector() {
        return JobSector.builder()
                .id(2L)
                .name("프론트엔드 개발")
                .category("개발")
                .build();
    }

    public static JobSector dataEngineerJobSector() {
        return JobSector.builder()
                .id(3L)
                .name("데이터 엔지니어")
                .category("개발")
                .build();
    }

    public static JobSector designJobSector() {
        return JobSector.builder()
                .id(4L)
                .name("UI/UX 디자인")
                .category("디자인")
                .build();
    }

    public static JobSector marketingJobSector() {
        return JobSector.builder()
                .id(5L)
                .name("디지털 마케팅")
                .category("마케팅")
                .build();
    }

    public static JobSector qaJobSector() {
        return JobSector.builder()
                .id(6L)
                .name("QA 엔지니어")
                .category("개발")
                .build();
    }

    public static List<JobSector> defaultJobSectorList() {
        return Arrays.asList(
                defaultJobSector(),
                frontendJobSector(),
                dataEngineerJobSector()
        );
    }

    public static List<JobSector> developmentJobSectorList() {
        return Arrays.asList(
                defaultJobSector(),
                frontendJobSector(),
                dataEngineerJobSector(),
                qaJobSector()
        );
    }

    public static List<JobSector> nonDevelopmentJobSectorList() {
        return Arrays.asList(
                designJobSector(),
                marketingJobSector(),
                JobSector.builder()
                        .id(7L)
                        .name("영업")
                        .category("영업")
                        .build()
        );
    }
}