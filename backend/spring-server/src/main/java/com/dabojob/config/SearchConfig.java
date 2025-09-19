package com.dabojob.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@ConfigurationProperties(prefix = "search")
@Data
@Component
public class SearchConfig {

    private Weights weights = new Weights();
    private Boost boost = new Boost();
    private Fuzziness fuzziness = new Fuzziness();
    private Pagination pagination = new Pagination();
    private Scoring scoring = new Scoring();

    @Data
    public static class Weights {
        private float title = 5.0f;
        private float companyName = 4.0f;
        private float summaryHashtags = 3.0f;
        private float jobSectorName = 2.0f;
        private float jobSectorCategory = 1.0f;
    }

    @Data
    public static class Boost {
        private CompanyScale companyScale = new CompanyScale();
        private RecentPosting recentPosting = new RecentPosting();
    }

    @Data
    public static class CompanyScale {
        private float BIG = 1.5f;
        private float MEDIUM = 1.3f;
        private float SMALL = 1.1f;
        private float ETC = 1.0f;
    }

    @Data
    public static class RecentPosting {
        private float withinWeek = 1.3f;
        private float withinMonth = 1.1f;
        private float older = 1.0f;
    }

    @Data
    public static class Fuzziness {
        private String autoThreshold = "AUTO";
        private int maxDistance = 2;
    }

    @Data
    public static class Pagination {
        private int defaultSize = 20;
        private int maxSize = 100;
    }

    @Data
    public static class Scoring {
        private double minScore = 0.1;
        private double tieBreaker = 0.3;
    }
}