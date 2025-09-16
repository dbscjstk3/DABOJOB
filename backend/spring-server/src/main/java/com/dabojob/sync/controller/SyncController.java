package com.dabojob.sync.controller;

import com.dabojob.sync.service.S3DataSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/sync")
@RequiredArgsConstructor
public class SyncController {

    private final S3DataSyncService s3DataSyncService;

    @PostMapping("/trigger")
    public ResponseEntity<Map<String, String>> triggerSync() {
        try {
            log.info("Manual S3 data sync triggered via API");

            s3DataSyncService.syncData();

            log.info("Manual S3 data sync completed successfully");
            return ResponseEntity.ok(Map.of(
                    "status", "success",
                    "message", "S3 data sync completed successfully"
            ));

        } catch (Exception e) {
            log.error("Manual S3 data sync failed: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "status", "error",
                    "message", "S3 data sync failed: " + e.getMessage()
            ));
        }
    }
}