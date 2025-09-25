package com.dabojob.fixture.company;

import com.dabojob.company.entity.Company;
import com.dabojob.company.entity.CompanyScale; // 가정
import java.util.Arrays;
import java.util.List;

public class CompanyFixture {

    public static Company defaultCompany() {
        return Company.builder()
                .id(1L)
                .name("테스트 회사")
                .scale(CompanyScale.MEDIUM) // enum 값 가정
                .build();
    }

    public static Company largeCompany() {
        return Company.builder()
                .id(2L)
                .name("대기업 테스트")
                .scale(CompanyScale.BIG)
                .build();
    }

    public static Company startupCompany() {
        return Company.builder()
                .id(3L)
                .name("스타트업 테스트")
                .scale(CompanyScale.SMALL)
                .build();
    }

    public static Company samsungCompany() {
        return Company.builder()
                .id(4L)
                .name("삼성전자")
                .scale(CompanyScale.BIG)
                .build();
    }

    public static Company naverCompany() {
        return Company.builder()
                .id(5L)
                .name("네이버")
                .scale(CompanyScale.BIG)
                .build();
    }

    public static List<Company> defaultCompanyList() {
        return Arrays.asList(
                defaultCompany(),
                largeCompany(),
                startupCompany()
        );
    }

    public static List<Company> largeCompanyList() {
        return Arrays.asList(
                samsungCompany(),
                naverCompany(),
                largeCompany()
        );
    }
}