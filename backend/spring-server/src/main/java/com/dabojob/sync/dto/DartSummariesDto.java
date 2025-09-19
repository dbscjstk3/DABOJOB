package com.dabojob.sync.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DartSummariesDto {
    @JsonProperty("business_overview")
    private String businessOverview;

    @JsonProperty("products_services")
    private String productsServices;

    @JsonProperty("revenue_orders")
    private String revenueOrders;

    @JsonProperty("contracts_rnd")
    private String contractsRnd;

    @JsonProperty("others")
    private String others;
}
