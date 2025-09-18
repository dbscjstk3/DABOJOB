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
    private LocalDateTime lastSyncTime = LocalDateTime.now().minusDays(1);

    public void syncData() {
        try {
            List<S3ObjectSummary> newFiles = getNewJsonFiles();

            if (newFiles.isEmpty()) {
                log.info("No new JSON files found in S3");
                return;
            }

            log.info("Found {} new JSON files", newFiles.size());

            for (S3ObjectSummary file : newFiles) {
                processJsonFile(file);
            }

            lastSyncTime = LocalDateTime.now();

        } catch (Exception e) {
            log.error("Error during S3 data sync: {}", e.getMessage(), e);
            throw e;
        }
    }

    private List<S3ObjectSummary> getNewJsonFiles() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime yesterday = now.minusDays(1);

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

    private void processJsonFile(S3ObjectSummary fileSummary) {
        try {
            log.info("Processing JSON file: {}", fileSummary.getKey());

            S3Object s3Object = amazonS3Client.getObject(bucketName, fileSummary.getKey());
            JsonNode jsonData = objectMapper.readTree(s3Object.getObjectContent());

            String fileName = fileSummary.getKey();

            // 파일명으로 타입 구분
            if (fileName.contains("job_sectors")) {
                fileProcessingService.processJobSectorFile(jsonData, fileName);
            } else if (fileName.contains("job_postings")) {
                fileProcessingService.processJobPostingFile(jsonData, fileName);
            } else if (fileName.contains("companies")) {
                fileProcessingService.processCompanyFile(jsonData, fileName);
            } else if (fileName.contains("Dart")) {
                fileProcessingService.processDartFile(jsonData, fileName);
            } else {
                log.warn("Unknown file type: {}", fileName);
            }

            log.info("Successfully processed JSON file: {}", fileSummary.getKey());

        } catch (Exception e) {
            log.error("Failed to process JSON file {}: {}", fileSummary.getKey(), e.getMessage(), e);
        }
    }
}