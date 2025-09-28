package com.dabojob.sync.scheduler;

import com.dabojob.sync.service.S3DataSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class S3DataSyncScheduler {

    private final S3DataSyncService s3DataSyncService;

    @Scheduled(fixedRate = 300000) // 5분마다
    public void syncDataFromS3() {
        log.info("Starting S3 data sync...");

        try {
            s3DataSyncService.syncData();
            log.info("S3 data sync completed successfully");
        } catch (Exception e) {
            log.error("S3 data sync failed: {}", e.getMessage(), e);
        }
    }
}