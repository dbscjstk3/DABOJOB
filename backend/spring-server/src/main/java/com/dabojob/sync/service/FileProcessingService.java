package com.dabojob.sync.service;

import com.dabojob.company.entity.Company;
import com.dabojob.company.repository.CompanyRepository;
import com.dabojob.jobposting.entity.CompanyJobPosting;
import com.dabojob.jobposting.entity.JobPosting;
import com.dabojob.jobposting.repository.CompanyJobPostingRepository;
import com.dabojob.jobposting.repository.JobPostingRepository;
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
        StringBuilder fullSummary = new StringBuilder();

        JsonNode chapters = companyAnalysis.get("chapters");
        if (chapters != null) {
            chapters.fields().forEachRemaining(entry -> {
                JsonNode chapter = entry.getValue();
                String name = chapter.get("name").asText();
                String content = chapter.get("content").asText();

                fullSummary.append("[").append(name).append("]\n");
                fullSummary.append(content).append("\n\n");
            });
        }

        return CompanyAnalysisSummary.builder()
                .fullSummary(fullSummary.toString())
                .status(SummaryStatus.CREATED)
                .build();
    }

    private void processHashtagsAndCreateMappings(JsonNode hashtagsData, CompanyAnalysisSummary summary, Company dartCompany) {
        JsonNode byChapter = hashtagsData.get("by_chapter");

        if (byChapter != null) {
            byChapter.fields().forEachRemaining(chapterEntry -> {
                JsonNode hashtagList = chapterEntry.getValue();

                if (hashtagList.isArray()) {
                    for (JsonNode hashtagNode : hashtagList) {
                        String hashtagName = hashtagNode.get("hashtag").asText();

                        // Hashtag 조회 또는 생성
                        Hashtag hashtag = findOrCreateHashtag(hashtagName);

                        // SummaryHashtag 생성 (중복 체크)
                        createSummaryHashtagIfNotExists(summary, hashtag, dartCompany);
                    }
                }
            });
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

    private void createSummaryHashtagIfNotExists(CompanyAnalysisSummary summary, Hashtag hashtag, Company dartCompany) {
        // 중복 체크 (이미 같은 summary-hashtag 매핑이 있는지)
        boolean exists = summaryHashtagRepository.existsBySummaryAndHashtag(summary, hashtag);

        if (!exists) {
            SummaryHashtag summaryHashtag = SummaryHashtag.builder()
                    .summary(summary)
                    .hashtag(hashtag)
                    .company(dartCompany)
                    .build();

            summaryHashtagRepository.save(summaryHashtag);
            log.info("Created SummaryHashtag for hashtag: {}", hashtag.getHashtagName());
        }
    }

    private void processNewsData(JsonNode newsData, CompanyAnalysisSummary summary) {
        JsonNode articles = newsData.get("articles");

        if (articles != null && articles.isArray()) {
            for (JsonNode articleNode : articles) {
                createNewsFromJson(articleNode, summary);
            }
        }
    }

    private void createNewsFromJson(JsonNode articleNode, CompanyAnalysisSummary summary) {
        Long newsId = articleNode.get("news_id").asLong();
        String title = articleNode.get("title").asText();
        String content = articleNode.get("content").asText();
        String url = articleNode.get("url").asText();
        String companyName = articleNode.get("company_name").asText();

        // hashtag_id는 news 구조에서 어떻게 매핑할지 확인 필요
        // 일단 summary와 연결된 SummaryHashtag 중 하나를 사용
        SummaryHashtag summaryHashtag = summaryHashtagRepository.findFirstBySummary(summary);

        if (summaryHashtag != null) {
            News news = News.builder()
                    .newsId(newsId)
                    .summaryHashtag(summaryHashtag)
                    .newsTitle(title)
                    .newsContent(content)
                    .newsUrl(url)
                    .newsCreatedAt(LocalDate.now()) // pub_date 파싱 필요시 수정
                    .build();

            newsRepository.save(news);
            log.info("Created news: {}", title);
        }
    }

    // TODO: JSON 데이터 파싱 및 저장
    @Transactional
    public void parseAndSaveJobPostingData(JsonNode jsonData, String fileName) throws JsonProcessingException {
        try {
            // JSON → DTO 변환
            JobPostingDataDto dto = objectMapper.treeToValue(jsonData, JobPostingDataDto.class);

            // 1. DartCompany 조회 또는 생성
            Company dartCompany = findOrCreateCompany(dto);

            // 2. JobPosting 생성 및 저장
            JobPosting jobPosting = createJobPosting(dto);
            jobPosting = jobPostingRepository.save(jobPosting);

            // 3. DartJob 생성 및 저장 (JobPosting + DartCompany 매핑)
            CompanyJobPosting companyJobPosting = createCompanyJobPosting(jobPosting, dartCompany, dto);
            companyJobPostingRepository.save(companyJobPosting);

            log.info("Successfully saved JobPosting and DartJob for saraminJobId: {}", dto.getSaraminJobId());

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
                    .dartCompanyCode("") //TODO: companyCode를 받아야함 or 필드값삭제
                    .companyName(dto.getCompanyName())  // 회사명도 저장
                    .build();

            return companyRepository.save(newCompany);
        } catch(NumberFormatException e){
            throw new IllegalArgumentException("Invalid Company ID format: " + dto.getCompanyId());
        }

    }

    private JobPosting createJobPosting(JobPostingDataDto dto) {
        return JobPosting.builder()
                .saraminJobPostingId(dto.getSaraminJobId())
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
