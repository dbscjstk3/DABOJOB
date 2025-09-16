package com.dabojob.sync.service;

import com.dabojob.company.entity.Company;
import com.dabojob.company.repository.CompanyRepository;
import com.dabojob.jobposting.entity.CompanyJobPosting;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.repository.CompanyJobPostingRepository;
import com.dabojob.jobposting.repository.JobPostingRepository;
import com.dabojob.summary.entity.ChapterType;
import com.dabojob.summary.entity.CompanyAnalysisSummary;
import com.dabojob.summary.entity.Hashtag;
import com.dabojob.summary.entity.News;
import com.dabojob.summary.entity.SummaryHashtag;
import com.dabojob.summary.entity.SummaryStatus;
import com.dabojob.summary.repository.CompanyAnalysisSummaryRepository;
import com.dabojob.summary.repository.HashtagRepository;
import com.dabojob.summary.repository.NewsRepository;
import com.dabojob.summary.repository.SummaryHashtagRepository;
import com.dabojob.sync.dto.JobPostingDataDto;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.LocalDate;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


@Service
@Slf4j
@RequiredArgsConstructor
public class FileProcessingService {

    private final CompanyRepository companyRepository;
    private final JobPostingRepository jobPostingRepository;
    private final CompanyJobPostingRepository companyJobPostingRepository;
    private final HashtagRepository  hashtagRepository;
    private final SummaryHashtagRepository summaryHashtagRepository;
    private final CompanyAnalysisSummaryRepository summaryRepository;
    private final NewsRepository newsRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Transactional
    public void parseAndSaveSummaryData(JsonNode jsonData, String fileName) {
        try {
            log.info("Processing summary report from file: {}", fileName);

            // 1. 기본 정보 추출
            JsonNode metadata = jsonData.get("metadata");
            Integer mappingId = metadata.get("mapping_id").asInt();

            // 2. Company 조회 (임의의 companyId로 가정)
            Long companyId = 1L; // 실제로는 어떤 로직으로 결정
            Company company = companyRepository.findById(companyId)
                    .orElseThrow(() -> new IllegalArgumentException("Company not found: " + companyId));

            // 3. CompanyAnalysisSummary 생성 및 저장
            CompanyAnalysisSummary summary = createSummaryFromJson(jsonData.get("company_analysis"));
            summary.setCompany(company);
            summary = summaryRepository.save(summary);

            // 4. Hashtag 처리 및 SummaryHashtag 생성
            processHashtagsAndCreateMappings(jsonData.get("hashtags"), summary, company);

            // 5. News 데이터 처리
            processNewsData(jsonData.get("news"), summary);

            log.info("Successfully saved all summary data for mappingId: {}", mappingId);

        } catch (Exception e) {
            log.error("Failed to parse and save summary data from file {}: {}", fileName, e.getMessage(), e);
            throw e;
        }
    }

    private CompanyAnalysisSummary createSummaryFromJson(JsonNode companyAnalysis) {
        JsonNode chapters = companyAnalysis.get("chapters");

        String businessOverview = "";
        String productsService = "";
        String salesContracts = "";
        String rndActivities = "";
        String otherNotes = "";

        if (chapters != null) {
            // 챕터 1: 사업의 개요 -> businessOverview
            JsonNode chapter1 = chapters.get("1");
            if (chapter1 != null) {
                businessOverview = chapter1.get("content").asText("");
            }

            // 챕터 2: 주요 제품 및 서비스 -> productsService
            JsonNode chapter2 = chapters.get("2");
            if (chapter2 != null) {
                productsService = chapter2.get("content").asText("");
            }

            // 챕터 3: 매출 및 수주 상황 -> salesContracts
            JsonNode chapter3 = chapters.get("3");
            if (chapter3 != null) {
                salesContracts = chapter3.get("content").asText("");
            }

            // 챕터 4: 주요 계약 및 연구 개발 활동 -> rndActivities
            JsonNode chapter4 = chapters.get("4");
            if (chapter4 != null) {
                rndActivities = chapter4.get("content").asText("");
            }

            // 챕터 5: 기타 참고사항 -> otherNotes
            JsonNode chapter5 = chapters.get("5");
            if (chapter5 != null) {
                otherNotes = chapter5.get("content").asText("");
            }
        }

        return CompanyAnalysisSummary.builder()
                .businessOverview(businessOverview)
                .productsService(productsService)
                .salesContracts(salesContracts)
                .rndActivities(rndActivities)
                .otherNotes(otherNotes)
                .status(SummaryStatus.CREATED)
                .build();
    }

    private void processHashtagsAndCreateMappings(JsonNode hashtagsData, CompanyAnalysisSummary summary, Company company) {
        JsonNode byChapter = hashtagsData.get("by_chapter");

        if (byChapter != null) {
            byChapter.fields().forEachRemaining(chapterEntry -> {
                String chapterNumber = chapterEntry.getKey(); // "1", "2", "3", "4", "5"
                JsonNode hashtagList = chapterEntry.getValue();

                // 챕터 번호를 ChapterType으로 변환
                ChapterType chapterType = mapChapterNumberToType(chapterNumber);

                if (chapterType != null && hashtagList.isArray()) {
                    for (JsonNode hashtagNode : hashtagList) {
                        String hashtagName = hashtagNode.get("hashtag").asText();

                        Hashtag hashtag = findOrCreateHashtag(hashtagName);
                        createSummaryHashtagIfNotExists(summary, hashtag, company, chapterType);
                    }
                }
            });
        }
    }

    private ChapterType mapChapterNumberToType(String chapterNumber) {
        return switch (chapterNumber) {
            case "1" -> ChapterType.BUSINESS_OVERVIEW;
            case "2" -> ChapterType.PRODUCTS_SERVICE;
            case "3" -> ChapterType.SALES_CONTRACTS;
            case "4" -> ChapterType.RND_ACTIVITIES;
            case "5" -> ChapterType.OTHER_NOTES;
            default -> null;
        };
    }

    private void createSummaryHashtagIfNotExists(CompanyAnalysisSummary summary, Hashtag hashtag, Company company, ChapterType chapterType) {
        boolean exists = summaryHashtagRepository.existsBySummaryAndHashtag(summary, hashtag);

        if (!exists) {
            SummaryHashtag summaryHashtag = SummaryHashtag.builder()
                    .summary(summary)
                    .hashtag(hashtag)
                    .company(company)
                    .chapterType(chapterType)
                    .build();

            summaryHashtagRepository.save(summaryHashtag);
            log.info("Created SummaryHashtag for hashtag: {} in chapter: {}", hashtag.getHashtagName(), chapterType);
        }
    }

    private Hashtag findOrCreateHashtag(String hashtagName) {
        return hashtagRepository.findByHashtagName(hashtagName)
                .orElseGet(() -> {
                    log.info("Creating new hashtag: {}", hashtagName);
                    Hashtag newHashtag = Hashtag.builder()
                            .hashtagName(hashtagName)
                            .build();
                    return hashtagRepository.save(newHashtag);
                });
    }


    private void processNewsData(JsonNode newsData, CompanyAnalysisSummary summary) {
        JsonNode byHashtag = newsData.get("by_hashtag");

        if (byHashtag != null) {
            byHashtag.fields().forEachRemaining(hashtagEntry -> {
                String hashtagName = hashtagEntry.getKey(); // "#플랫폼", "#채용" 등
                JsonNode hashtagData = hashtagEntry.getValue();

                JsonNode articles = hashtagData.get("articles");
                if (articles != null && articles.isArray()) {
                    for (JsonNode articleNode : articles) {
                        createNewsFromJson(articleNode, summary, hashtagName);
                    }
                }
            });
        }
    }

    private void createNewsFromJson(JsonNode articleNode, CompanyAnalysisSummary summary, String hashtagName) {
        Long newsId = articleNode.get("news_id").asLong();
        String title = articleNode.get("title").asText();
        String content = articleNode.get("content").asText();
        String url = articleNode.get("url").asText();
        String pubDateStr = articleNode.get("pub_date").asText();

        // pub_date 파싱 (ISO 8601 형식)
        LocalDate newsCreatedAt = parsePublishDate(pubDateStr);

        // 해당 Summary의 특정 해시태그에 매핑된 SummaryHashtag 찾기
        SummaryHashtag summaryHashtag = findSummaryHashtagByName(summary, hashtagName);

        if (summaryHashtag != null) {
            News news = News.builder()
                    .newsId(newsId)
                    .summaryHashtag(summaryHashtag)
                    .newsTitle(title)
                    .newsContent(content)
                    .newsUrl(url)
                    .newsCreatedAt(newsCreatedAt)
                    .build();

            newsRepository.save(news);
            log.info("Created news: {} for hashtag: {} in chapter: {}",
                    title, hashtagName, summaryHashtag.getChapterType());
        } else {
            log.warn("SummaryHashtag not found for hashtag: {} in summary: {}",
                    hashtagName, summary.getSummaryId());
        }
    }

    private LocalDate parsePublishDate(String pubDateStr) {
        try {
            // ISO 8601 형식 파싱: "2024-01-15T08:30:00Z"
            return LocalDate.parse(pubDateStr.substring(0, 10)); // 날짜 부분만 추출
        } catch (Exception e) {
            log.warn("Failed to parse pub_date: {}, using current date", pubDateStr);
            return LocalDate.now();
        }
    }

    private SummaryHashtag findSummaryHashtagByName(CompanyAnalysisSummary summary, String hashtagName) {
        // 먼저 해시태그 조회
        Optional<Hashtag> hashtagOpt = hashtagRepository.findByHashtagName(hashtagName);

        // Summary와 Hashtag로 SummaryHashtag 조회
        return hashtagOpt.map(hashtag -> summaryHashtagRepository.findBySummaryAndHashtag(summary, hashtag))
                .orElse(null);
    }

    // TODO: JSON 데이터 파싱 및 저장
    @Transactional
    public void parseAndSaveJobPostingData(JsonNode jsonData, String fileName) throws JsonProcessingException {
        try {
            // JSON → DTO 변환
            JobPostingDataDto dto = objectMapper.treeToValue(jsonData, JobPostingDataDto.class);

            // 1. Company 조회 또는 생성
            Company company = findOrCreateCompany(dto);

            // 2. JobPosting 생성 및 저장
            JobPosting jobPosting = createJobPosting(dto);
            jobPosting = jobPostingRepository.save(jobPosting);

            // 3. CompanyJobPosting 생성 및 저장 (JobPosting + Company 매핑)
            CompanyJobPosting companyJobPosting = createCompanyJobPosting(jobPosting, company, dto);
            companyJobPostingRepository.save(companyJobPosting);

            log.info("Successfully saved JobPosting and Company for saraminJobPostingId: {}", dto.getSaraminJobPostingId());

        } catch (Exception e) {
            log.error("Failed to parse and save data from file {}: {}", fileName, e.getMessage(), e);
            throw  e;
        }
    }

    private Company findOrCreateCompany(JobPostingDataDto dto) {
        try{

            Long parsedCompanyId = Long.parseLong(dto.getCompanyId());
            // companyId로 기존 Company 조회
            Optional<Company> existingCompany = companyRepository.findByCompanyId(parsedCompanyId);

            if (existingCompany.isPresent()) {
                log.info("Found existing Company for CompanyId: {}", dto.getCompanyId());
                return existingCompany.get();
            }

            // 없으면 새로 생성
            log.info("Creating new Company for CompanyId: {}", dto.getCompanyId());
            Company newCompany = Company.builder()
                    .companyId(parsedCompanyId)
                    .dartCompanyCode("") //TODO: companyCode를 받아야함 or 필드값삭제 or 우리가 받는 값이 companyId가 아닌 dartCompanyCode일수도 -> 확인필요
                    .companyName(dto.getCompanyName())  // 회사명도 저장
                    .build();

            return companyRepository.save(newCompany);
        } catch(NumberFormatException e){
            throw new IllegalArgumentException("Invalid Company ID format: " + dto.getCompanyId());
        }

    }

    private JobPosting createJobPosting(JobPostingDataDto dto) {
        return JobPosting.builder()
                .saraminJobPostingId(dto.getSaraminJobPostingId())
                .companyName(dto.getCompanyName())
                .title(dto.getTitle())
                .url(dto.getUrl())
                .experienceLevelCode(dto.getExperienceLevelCode())
                .jobMidCode(dto.getJobMidCode())
                .postingTimeStamp(dto.getPostingTimeStamp())
                .expirationTimestamp(dto.getExpirationTimestamp())
                .build();
    }

    private CompanyJobPosting createCompanyJobPosting(JobPosting jobPosting, Company company, JobPostingDataDto dto) {
        return CompanyJobPosting.builder()
                .jobPosting(jobPosting)
                .company(company)
                .companyNameNormalized(dto.getCompanyNameNormalized())
                .build();
    }
}
