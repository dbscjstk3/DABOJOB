package com.dabojob.jobposting.repository;

import com.dabojob.jobposting.entity.JobPostingDocument;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.elasticsearch.annotations.Query;
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JobPostingSearchRepository extends ElasticsearchRepository<JobPostingDocument, Long> {

    @Query("""
    {
      "bool": {
        "must": [
          {
            "multi_match": {
              "query": "?0",
              "fields": [
                "title^#{@searchConfig.weights.title}",
                "company_name^#{@searchConfig.weights.companyName}",
                "summary_hashtags^#{@searchConfig.weights.summaryHashtags}",
                "job_sector_name^#{@searchConfig.weights.jobSectorName}",
                "job_sector_category^#{@searchConfig.weights.jobSectorCategory}"
              ],
              "type": "most_fields",
              "tie_breaker": #{@searchConfig.scoring.tieBreaker}
            }
          }
        ],
        "should": [
          {
            "term": {
              "company_scale": {
                "value": "BIG",
                "boost": #{@searchConfig.boost.companyScale.BIG}
              }
            }
          },
          {
            "term": {
              "company_scale": {
                "value": "MEDIUM",
                "boost": #{@searchConfig.boost.companyScale.MEDIUM}
              }
            }
          },
          {
            "term": {
              "company_scale": {
                "value": "SMALL",
                "boost": #{@searchConfig.boost.companyScale.SMALL}
              }
            }
          },
          {
            "range": {
              "posting_date": {
                "gte": "?1",
                "boost": #{@searchConfig.boost.recentPosting.withinWeek}
              }
            }
          },
          {
            "range": {
              "posting_date": {
                "gte": "?2",
                "lt": "?1",
                "boost": #{@searchConfig.boost.recentPosting.withinMonth}
              }
            }
          }
        ],
        "minimum_should_match": 0
      }
    }
    """)
    Page<JobPostingDocument> searchWithWeights(
            String searchString,
            String weekAgo,
            String monthAgo,
            Pageable pageable
    );


    @Query("""
    {
        "multi_match": {
            "query": "?0",
            "fields": ["title^1", "company_name^2"],
            "type": "phrase_prefix",
            "max_expansions": 10
        }
    }
    """)
    Page<JobPostingDocument> findTitleAutocomplete(String prefix, Pageable pageable);


}