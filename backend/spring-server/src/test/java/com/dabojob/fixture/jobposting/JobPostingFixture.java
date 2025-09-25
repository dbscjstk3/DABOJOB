package com.dabojob.fixture.jobposting;

import com.dabojob.fixture.company.CompanyFixture;
import com.dabojob.jobposting.entity.CareerInfo;
import com.dabojob.jobposting.entity.JobPosting;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

public class JobPostingFixture {

    public static JobPosting defaultJobPosting() {
        return JobPosting.builder()
                .id(100L)
                .company(CompanyFixture.defaultCompany())
                .jobSector(JobSectorFixture.defaultJobSector())
                .title("Spring Boot 백엔드 개발자")
                .url("https://example.com/job100")
                .careerInfo(CareerInfo.JUNIOR)
                .postingDate(LocalDate.of(2024, 1, 1))
                .deadlineDate(LocalDate.of(2024, 1, 31))
                .build();
    }

    public static JobPosting seniorJobPosting() {
        return JobPosting.builder()
                .id(101L)
                .company(CompanyFixture.largeCompany())
                .jobSector(JobSectorFixture.frontendJobSector())
                .title("React 시니어 개발자")
                .url("https://example.com/job101")
                .careerInfo(CareerInfo.SENIOR)
                .postingDate(LocalDate.of(2024, 1, 5))
                .deadlineDate(LocalDate.of(2024, 2, 5))
                .build();
    }

    public static JobPosting experiencedJobPosting() {
        return JobPosting.builder()
                .id(102L)
                .company(CompanyFixture.startupCompany())
                .jobSector(JobSectorFixture.dataEngineerJobSector())
                .title("데이터 엔지니어")
                .url("https://example.com/job102")
                .careerInfo(CareerInfo.EXPERIENCED)
                .postingDate(LocalDate.of(2024, 1, 10))
                .deadlineDate(LocalDate.of(2024, 2, 10))
                .build();
    }

    public static JobPosting expiredJobPosting() {
        return JobPosting.builder()
                .id(103L)
                .company(CompanyFixture.defaultCompany())
                .jobSector(JobSectorFixture.defaultJobSector())
                .title("만료된 채용공고")
                .url("https://example.com/job103")
                .careerInfo(CareerInfo.JUNIOR)
                .postingDate(LocalDate.of(2023, 12, 1))
                .deadlineDate(LocalDate.of(2023, 12, 31))
                .build();
    }

    public static JobPosting designJobPosting() {
        return JobPosting.builder()
                .id(104L)
                .company(CompanyFixture.samsungCompany())
                .jobSector(JobSectorFixture.designJobSector())
                .title("UI/UX 디자이너")
                .url("https://example.com/job104")
                .careerInfo(CareerInfo.EXPERIENCED)
                .postingDate(LocalDate.now())
                .deadlineDate(LocalDate.now().plusDays(30))
                .build();
    }

    public static JobPosting marketingJobPosting() {
        return JobPosting.builder()
                .id(105L)
                .company(CompanyFixture.naverCompany())
                .jobSector(JobSectorFixture.marketingJobSector())
                .title("디지털 마케팅 매니저")
                .url("https://example.com/job105")
                .careerInfo(CareerInfo.SENIOR)
                .postingDate(LocalDate.now().minusDays(5))
                .deadlineDate(LocalDate.now().plusDays(25))
                .build();
    }

    public static List<JobPosting> defaultJobPostingList() {
        return Arrays.asList(
                defaultJobPosting(),
                seniorJobPosting(),
                experiencedJobPosting()
        );
    }

    public static List<JobPosting> juniorJobPostingList() {
        return Arrays.asList(
                defaultJobPosting(),
                JobPosting.builder()
                        .id(106L)
                        .company(CompanyFixture.naverCompany())
                        .jobSector(JobSectorFixture.frontendJobSector())
                        .title("주니어 프론트엔드 개발자")
                        .url("https://example.com/job106")
                        .careerInfo(CareerInfo.JUNIOR)
                        .postingDate(LocalDate.of(2024, 1, 15))
                        .deadlineDate(LocalDate.of(2024, 2, 15))
                        .build(),
                JobPosting.builder()
                        .id(107L)
                        .company(CompanyFixture.startupCompany())
                        .jobSector(JobSectorFixture.qaJobSector())
                        .title("주니어 QA 엔지니어")
                        .url("https://example.com/job107")
                        .careerInfo(CareerInfo.JUNIOR)
                        .postingDate(LocalDate.of(2024, 1, 20))
                        .deadlineDate(LocalDate.of(2024, 2, 20))
                        .build()
        );
    }

    public static List<JobPosting> expiredJobPostingList() {
        return Arrays.asList(
                expiredJobPosting(),
                JobPosting.builder()
                        .id(108L)
                        .company(CompanyFixture.largeCompany())
                        .jobSector(JobSectorFixture.frontendJobSector())
                        .title("만료된 시니어 개발자")
                        .url("https://example.com/job108")
                        .careerInfo(CareerInfo.SENIOR)
                        .postingDate(LocalDate.of(2023, 11, 1))
                        .deadlineDate(LocalDate.of(2023, 11, 30))
                        .build(),
                JobPosting.builder()
                        .id(109L)
                        .company(CompanyFixture.samsungCompany())
                        .jobSector(JobSectorFixture.designJobSector())
                        .title("만료된 디자이너")
                        .url("https://example.com/job109")
                        .careerInfo(CareerInfo.EXPERIENCED)
                        .postingDate(LocalDate.of(2023, 10, 1))
                        .deadlineDate(LocalDate.of(2023, 10, 31))
                        .build()
        );
    }

    public static List<JobPosting> developmentJobPostingList() {
        return Arrays.asList(
                defaultJobPosting(),
                seniorJobPosting(),
                experiencedJobPosting(),
                JobPosting.builder()
                        .id(110L)
                        .company(CompanyFixture.startupCompany())
                        .jobSector(JobSectorFixture.qaJobSector())
                        .title("QA 엔지니어")
                        .url("https://example.com/job110")
                        .careerInfo(CareerInfo.EXPERIENCED)
                        .postingDate(LocalDate.now().minusDays(3))
                        .deadlineDate(LocalDate.now().plusDays(27))
                        .build()
        );
    }
}