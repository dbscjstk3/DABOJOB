package com.dabojob.company.entity;


import com.dabojob.global.entity.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Table(name = "dart_companies")
public class DartCompany extends BaseTimeEntity {

    @Id
    @Column(name="dart_id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long dartId;

    @Column(name="dart_company_code")
    private String dartCompanyCode;
    @Column(name="dart_company_name")
    private String dartCompanyName;




}
