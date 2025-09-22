package com.dabojob.sync.service;

import com.amazonaws.services.s3.AmazonS3Client;
import com.amazonaws.services.s3.model.ListObjectsV2Request;
import com.amazonaws.services.s3.model.ListObjectsV2Result;
import com.amazonaws.services.s3.model.S3Object;
import com.amazonaws.services.s3.model.S3ObjectSummary;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Date;
import java.util.List;

@Service
@Slf4j
@RequiredArgsConstructor
public class S3DataSyncService {

    private final AmazonS3Client amazonS3Client;
    private final FileProcessingService fileProcessingService;

    @Value("${cloud.aws.s3.bucket}")
    private String bucketName;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private LocalDateTime lastSyncTime = LocalDateTime.now().minusDays(7);

    public void syncData() {
        try {
            List<S3ObjectSummary> newFiles = getNewJsonFiles();

            if (newFiles.isEmpty()) {
                log.info("No new JSON files found in S3");
                return;
            }

            log.info("Found {} new JSON files", newFiles.size());

            // 파일 타입별 그룹핑 후 순차 처리
            processFilesByTypeInOrder(newFiles);

            lastSyncTime = LocalDateTime.now();

        } catch (Exception e) {
            log.error("Error during S3 data sync: {}", e.getMessage(), e);
            throw e;
        }
    }

    //파일들을 타입별로 그룹핑한 후 의존성 순서에 맞게 처리
    private void processFilesByTypeInOrder(List<S3ObjectSummary> files) {
        Map<String, List<S3ObjectSummary>> filesByType = groupFilesByType(files);

        // 의존성 순서 정의: job_sectors → companies → Dart → job_postings
        String[] processingOrder = {"job_sectors", "companies", "Dart", "job_postings"};

        for (String fileType : processingOrder) {
            List<S3ObjectSummary> typedFiles = filesByType.get(fileType);

            if (typedFiles != null && !typedFiles.isEmpty()) {
                log.info("=== Processing {} files of type: {} ===", typedFiles.size(), fileType);

                for (S3ObjectSummary file : typedFiles) {
                    processFileByType(file, fileType);
                }

                log.info("=== Completed processing {} files ===", fileType);
            } else {
                log.info("No files found for type: {}", fileType);
            }
        }
    }

    //파일들을 타입별로 분류
    private Map<String, List<S3ObjectSummary>> groupFilesByType(List<S3ObjectSummary> files) {
        Map<String, List<S3ObjectSummary>> filesByType = new HashMap<>();

        for (S3ObjectSummary file : files) {
            String fileName = file.getKey();
            String fileType = determineFileType(fileName);

            if (fileType != null) {
                filesByType.computeIfAbsent(fileType, k -> new ArrayList<>()).add(file);
            } else {
                log.warn("Unknown file type for file: {}", fileName);
            }
        }

        // 분류 결과 로깅
        for (Map.Entry<String, List<S3ObjectSummary>> entry : filesByType.entrySet()) {
            log.info("Found {} files of type: {}", entry.getValue().size(), entry.getKey());
        }

        return filesByType;
    }

    //파일명으로 파일 타입 결정
    private String determineFileType(String fileName) {
        if (fileName.contains("job_sectors")) {
            return "job_sectors";
        } else if (fileName.contains("companies")) {
            return "companies";
        } else if (fileName.contains("Dart")) {
            return "Dart";
        } else if (fileName.contains("job_postings")) {
            return "job_postings";
        }
        return null;
    }

    private void processFileByType(S3ObjectSummary fileSummary, String fileType) {
        try {
            log.info("Processing {} file: {}", fileType, fileSummary.getKey());

            S3Object s3Object = amazonS3Client.getObject(bucketName, fileSummary.getKey());
            JsonNode jsonData = objectMapper.readTree(s3Object.getObjectContent());
            String fileName = fileSummary.getKey();

            switch (fileType) {
                case "job_sectors":
                    fileProcessingService.processJobSectorFile(jsonData, fileName);
                    break;
                case "companies":
                    fileProcessingService.processCompanyFile(jsonData, fileName);
                    break;
                case "Dart":
                    fileProcessingService.processDartFile(jsonData, fileName);
                    break;
                case "job_postings":
                    fileProcessingService.processJobPostingFile(jsonData, fileName);
                    break;
                default:
                    log.warn("Unknown file type: {}", fileType);
                    return;
            }

            log.info("Successfully processed {} file: {}", fileType, fileSummary.getKey());

        } catch (Exception e) {
            log.error("Failed to process {} file {}: {}", fileType, fileSummary.getKey(), e.getMessage(), e);
            // 개별 파일 실패가 전체 배치를 중단시키지 않도록 예외를 다시 던지지 않음
        }
    }

    private List<S3ObjectSummary> getNewJsonFiles() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime yesterday = now.minusDays(4);

        String todayPrefix = "reports/" + now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd")) + "/";
        String yesterdayPrefix = "reports/" + yesterday.format(DateTimeFormatter.ofPattern("yyyy-MM-dd")) + "/";

        List<S3ObjectSummary> allFiles = new ArrayList<>();
        allFiles.addAll(getFilesFromPrefix(todayPrefix));
        allFiles.addAll(getFilesFromPrefix(yesterdayPrefix));

        Date lastSyncDate = Date.from(lastSyncTime.toInstant(ZoneOffset.UTC));

        return allFiles.stream()
                .filter(obj -> obj.getKey().endsWith(".json"))
                .filter(obj -> obj.getLastModified().after(lastSyncDate))
                .toList();
    }

    private List<S3ObjectSummary> getFilesFromPrefix(String prefix) {
        try {
            ListObjectsV2Request request = new ListObjectsV2Request()
                    .withBucketName(bucketName)
                    .withPrefix(prefix)
                    .withMaxKeys(100);

            ListObjectsV2Result result = amazonS3Client.listObjectsV2(request);
            return result.getObjectSummaries();
        } catch (Exception e) {
            log.warn("Failed to get files from prefix {}: {}", prefix, e.getMessage());
            return new ArrayList<>();
        }
    }
}