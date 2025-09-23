package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class JobSectorDto {
    @JsonProperty("job_id")
    private Long jobId;

    @JsonProperty("sector_id")
    private Long sectorId;

    @JsonProperty("sector_name")
    private String sectorName;

    @JsonProperty("sector_category")
    private String sectorCategory;
}
