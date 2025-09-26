package com.dabojob.sync.service;

import com.dabojob.company.entity.Company;
import com.dabojob.company.entity.CompanyScale;
import com.dabojob.company.repository.CompanyRepository;
import com.dabojob.global.exception.FileProcessingException;
import com.dabojob.jobposting.entity.CareerInfo;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.entity.JobPostingDocument;
import com.dabojob.jobposting.entity.JobSector;
import com.dabojob.jobposting.repository.JobPostingRepository;
import com.dabojob.jobposting.repository.JobPostingSearchRepository;
import com.dabojob.jobposting.repository.JobSectorRepository;
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

import com.dabojob.sync.dto.CategoryDto;
import com.dabojob.sync.dto.CompanyDto;
import com.dabojob.sync.dto.DartDto;
import com.dabojob.sync.dto.DartSummariesDto;
import com.dabojob.sync.dto.HashtagItemDto;
import com.dabojob.sync.dto.HashtagsDto;
import com.dabojob.sync.dto.JobPostingDto;
import com.dabojob.sync.dto.JobSectorDto;
import com.dabojob.sync.dto.NewsDto;
import com.dabojob.sync.dto.NewsItemDto;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


@Service
@Slf4j
@RequiredArgsConstructor
@Transactional
public class FileProcessingService {

    private final JobSectorRepository jobSectorRepository;
    private final JobPostingRepository jobPostingRepository;
    private final JobPostingSearchRepository jobPostingSearchRepository;
    private final CompanyRepository companyRepository;
    private final CompanyAnalysisSummaryRepository summaryRepository;
    private final HashtagRepository hashtagRepository;
    private final SummaryHashtagRepository summaryHashtagRepository;
    private final NewsRepository newsRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public void processJobSectorFile(JsonNode jsonData, String fileName) {
        try {
            JobSectorDto dto = objectMapper.treeToValue(jsonData, JobSectorDto.class);

            // 중복 체크 - 이미 있으면 넘어감
            if (jobSectorRepository.existsById(dto.getSectorId())) {
                log.info("JobSector already exists with id: {}, skipping", dto.getSectorId());
                return;
            }

            JobSector jobSector = JobSector.builder()
                    .id(dto.getSectorId())
                    .name(dto.getSectorName())
                    .category(dto.getSectorCategory())
                    .build();

            jobSectorRepository.save(jobSector);
            log.info("Saved JobSector: {}", dto.getSectorName());

        } catch (Exception e) {
            log.error("Failed to process JobSector file {}: {}", fileName, e.getMessage(), e);
            throw new FileProcessingException("File processing failed", e);
        }
    }

    public void processJobPostingFile(JsonNode jsonData, String fileName) {
        try {
            JobPostingDto dto = objectMapper.treeToValue(jsonData, JobPostingDto.class);

            // 중복 체크 - 이미 있으면 넘어감
            if (jobPostingRepository.existsById(dto.getJobId())) {
                log.info("JobPosting already exists with id: {}, skipping", dto.getJobId());
                return;
            }

            // 연관 엔티티 조회 또는 생성
            Company company = findOrCreateCompany(dto.getCompanyId());
            JobSector jobSector = findOrCreateJobSector(dto.getSectorId());

            JobPosting jobPosting = JobPosting.builder()
                    .id(dto.getJobId())
                    .company(company)
                    .jobSector(jobSector)
                    .title(dto.getSaraminJobTitle())
                    .url(dto.getSaraminJobUrl())
                    .careerInfo(parseCareerInfo(dto.getCareerInfo()))
                    .postingDate(parseLocalDate(dto.getPostingDate()))
                    .deadlineDate(parseLocalDate(dto.getApplicationDeadline()))
                    .build();

            jobPostingRepository.save(jobPosting);
            log.info("Saved JobPosting: {}", dto.getSaraminJobTitle());


            List<String> hashtagNames = summaryHashtagRepository.findHashtagNamesByMostRecentSummary(company.getId());
            JobPostingDocument jobPostingDocument = JobPostingDocument.of(jobPosting, jobSector, company, hashtagNames);
            jobPostingSearchRepository.save(jobPostingDocument);
            log.info("Saved JobPostingDocument: {}", jobPostingDocument.getJobPostingId());

        } catch (Exception e) {
            log.error("Failed to process JobPosting file {}: {}", fileName, e.getMessage(), e);
            throw new FileProcessingException("File processing failed", e);
        }
    }

    public void processCompanyFile(JsonNode jsonData, String fileName) {
        try {
            CompanyDto dto = objectMapper.treeToValue(jsonData, CompanyDto.class);

            // 중복 체크 - 이미 있으면 넘어감
            if (companyRepository.existsById(dto.getCompanyId())) {
                log.info("Company already exists with id: {}, skipping", dto.getCompanyId());
                return;
            }

            Company company = Company.builder()
                    .id(dto.getCompanyId())
                    .name(dto.getCompanyName())
                    .scale(parseCompanyScale(dto.getCompanyScale()))
                    .build();

            companyRepository.save(company);
            log.info("Saved Company: {}", dto.getCompanyName());

        } catch (Exception e) {
            log.error("Failed to process Company file {}: {}", fileName, e.getMessage(), e);
            throw new FileProcessingException("File processing failed", e);
        }
    }

    public void processDartFile(JsonNode jsonData, String fileName) {
        try {
            DartDto dto = objectMapper.treeToValue(jsonData, DartDto.class);

            // Company 조회 또는 생성
            Company company = findOrCreateCompany(dto.getCompanyId());

            // CompanyAnalysisSummary 생성 및 저장
            CompanyAnalysisSummary summary = createCompanyAnalysisSummary(dto, company);
            summary = summaryRepository.save(summary);

            // 해시태그 처리
            processHashtags(dto.getHashtags(), summary);

            // 뉴스 처리
            processNews(dto.getNews(), summary);

            log.info("Saved Dart data for company: {}", company.getName());

        } catch (Exception e) {
            log.error("Failed to process Dart file {}: {}", fileName, e.getMessage(), e);
            throw new FileProcessingException("File processing failed", e);
        }
    }

    private CompanyAnalysisSummary createCompanyAnalysisSummary(DartDto dto, Company company) {
        DartSummariesDto summaries = dto.getDartSummaries();

        return CompanyAnalysisSummary.builder()
                .company(company)
                .businessOverview(summaries.getBusinessOverview())
                .productsService(summaries.getProductsServices())
                .salesContracts(summaries.getRevenueOrders())
                .rndActivities(summaries.getContractsRnd())
                .otherNotes(summaries.getOthers())
                .status(SummaryStatus.CREATED)
                .build();
    }

    private void processHashtags(HashtagsDto hashtagsDto, CompanyAnalysisSummary summary) {
        if (hashtagsDto == null || hashtagsDto.getCategories() == null) {
            return;
        }

        for (CategoryDto category : hashtagsDto.getCategories()) {
            ChapterType chapterType = mapCategoryToChapterType(category.getCategory());

            if (category.getHashtags() != null) {
                for (HashtagItemDto hashtagItem : category.getHashtags()) {
                    // 해시태그 찾기 또는 생성 (중복 허용)
                    Hashtag hashtag = findOrCreateHashtag(hashtagItem.getHashtag());

                    // SummaryHashtag 생성
                    SummaryHashtag summaryHashtag = SummaryHashtag.builder()
                            .summary(summary)
                            .hashtag(hashtag)
                            .chapterType(chapterType)
                            .build();

                    summaryHashtagRepository.save(summaryHashtag);
                }
            }
        }
    }

    private void processNews(NewsDto newsDto, CompanyAnalysisSummary summary) {
        if (newsDto == null || newsDto.getItems() == null) {
            return;
        }

        for (NewsItemDto newsItem : newsDto.getItems()) {
            // 해시태그 찾기 또는 생성
            Hashtag hashtag = findOrCreateHashtag(newsItem.getHashtag());

            // SummaryHashtag 찾기 (chapter 매핑)
            ChapterType chapterType = mapChapterString(newsItem.getChapter());
            SummaryHashtag summaryHashtag = findSummaryHashtag(summary, hashtag, chapterType);

            if (summaryHashtag != null) {
                News news = News.builder()
                        .summaryHashtag(summaryHashtag)
                        .title(newsItem.getTitle())
                        .content(newsItem.getSummary())
                        .url(newsItem.getUrl())
                        .postingDate(parseLocalDate(newsItem.getPublishedDate()))
                        .build();

                newsRepository.save(news);
            }
        }
    }

    private Hashtag findOrCreateHashtag(String hashtagName) {
        if (hashtagName == null || hashtagName.trim().isEmpty()) {
            return null;
        }

        // 중복 허용 - 동일한 이름이면 기존 것 사용, 없으면 새로 생성
        Optional<Hashtag> existing = hashtagRepository.findByName(hashtagName);
        if (existing.isPresent()) {
            return existing.get();
        }

        try {
            // 새로 생성
            Hashtag newHashtag = Hashtag.builder()
                    .name(hashtagName)
                    .build();
            return hashtagRepository.save(newHashtag);
        } catch (DataIntegrityViolationException e) {
            // 다른 스레드가 이미 생성했으니 다시 조회
            return hashtagRepository.findByName(hashtagName)
                    .orElseThrow(() -> new RuntimeException("Hashtag not found after creation: " + hashtagName));
        }
    }

    private SummaryHashtag findSummaryHashtag(CompanyAnalysisSummary summary, Hashtag hashtag, ChapterType chapterType) {
        if (hashtag == null || chapterType == null) {
            return null;
        }

        // 기존 것이 있는지 확인 (간단한 방법)+-
        SummaryHashtag summaryHashtag = summaryHashtagRepository.findBySummaryAndChapterTypeAndHashtag(summary,chapterType,hashtag);
        if (summaryHashtag != null) {
            return summaryHashtag;
        }
        // 정확한 조회 메서드가 없다면 새로 생성
        summaryHashtag = SummaryHashtag.builder()
                .summary(summary)
                .hashtag(hashtag)
                .chapterType(chapterType)
                .build();

        return summaryHashtagRepository.save(summaryHashtag);
    }

    private ChapterType mapCategoryToChapterType(String category) {
        if (category == null) return ChapterType.OTHER_NOTES;

        return switch (category.toLowerCase()) {
            case "business_overview" -> ChapterType.BUSINESS_OVERVIEW;
            case "products_services" -> ChapterType.PRODUCTS_SERVICE;
            case "revenue_orders" -> ChapterType.SALES_CONTRACTS;
            case "contracts_rnd" -> ChapterType.RND_ACTIVITIES;
            case "other_references" -> ChapterType.OTHER_NOTES;
            default -> ChapterType.OTHER_NOTES;
        };
    }

    private ChapterType mapChapterString(String chapter) {
        if (chapter == null) return ChapterType.OTHER_NOTES;

        return switch (chapter.toLowerCase()) {
            case "business_overview" -> ChapterType.BUSINESS_OVERVIEW;
            case "products_services" -> ChapterType.PRODUCTS_SERVICE;
            case "revenue_orders" -> ChapterType.SALES_CONTRACTS;
            case "contracts_rnd" -> ChapterType.RND_ACTIVITIES;
            case "other_references" -> ChapterType.OTHER_NOTES;
            default -> ChapterType.OTHER_NOTES;
        };
    }

    // Helper methods for finding or creating entities
    private Company findOrCreateCompany(Long companyId) {
        Optional<Company> existing = companyRepository.findById(companyId);
        if (existing.isPresent()) {
            return existing.get();
        }

        // Company가 없으면 기본값으로 생성
        Company newCompany = Company.builder()
                .id(companyId)
                .name("Unknown Company " + companyId)
                .scale(CompanyScale.ETC)
                .build();

        Company saved = companyRepository.save(newCompany);
        log.info("Created new Company with id: {}", companyId);
        return saved;
    }

    private JobSector findOrCreateJobSector(Long sectorId) {
        Optional<JobSector> existing = jobSectorRepository.findById(sectorId);
        if (existing.isPresent()) {
            return existing.get();
        }

        // JobSector가 없으면 기본값으로 생성
        JobSector newJobSector = JobSector.builder()
                .id(sectorId)
                .name("Unknown Sector " + sectorId)
                .category("기타")
                .build();

        JobSector saved = jobSectorRepository.save(newJobSector);
        log.info("Created new JobSector with id: {}", sectorId);
        return saved;
    }
    private CareerInfo parseCareerInfo(String careerInfo) {
        // 임시 처리 - 나중에 쉽게 변경 가능
        if (careerInfo == null || careerInfo.isEmpty()) {
            return CareerInfo.JUNIOR;
        }
        return CareerInfo.JUNIOR;
    }

    private CompanyScale parseCompanyScale(String companyScale) {
        // 임시 처리 - 나중에 쉽게 변경 가능
        if (companyScale == null || companyScale.isEmpty()) {
            return CompanyScale.ETC;
        }
        return CompanyScale.ETC;
    }

    private LocalDate parseLocalDate(String dateStr) {
        if (dateStr == null || dateStr.isEmpty()) {
            return null;
        }
        try {
            // "2025-09-18T14:48:00" 형식 처리
            if (dateStr.contains("T")) {
                return LocalDate.parse(dateStr.substring(0, 10));
            }
            return LocalDate.parse(dateStr);
        } catch (Exception e) {
            log.warn("Failed to parse date: {}", dateStr);
            return null;
        }
    }

}
