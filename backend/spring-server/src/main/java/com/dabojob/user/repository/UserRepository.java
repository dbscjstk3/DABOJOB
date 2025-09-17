package com.dabojob.user.repository;

import com.dabojob.global.enums.UserRole;
import com.dabojob.user.entity.User;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    /**
     * OAuth 제공자와 제공자 ID로 사용자 조회
     * OAuth 로그인 시 기존 사용자 확인용
     */
    Optional<User> findByProviderAndProviderId(String provider, String providerId);

    /**
     * 이메일로 사용자 조회
     * 동일 이메일로 다른 OAuth 제공자 가입 시 중복 체크용
     */
    Optional<User> findByEmail(String email);



    /**
     * 권한별 사용자 조회
     */
    List<User> findByRole(UserRole role);

    /**
     * 관리자 사용자들만 조회
     */
    @Query("SELECT u FROM User u WHERE u.role = 'ADMIN'")
    List<User> findAllAdmins();

    /**
     * 이메일로 사용자 존재 여부 확인
     */
    boolean existsByEmail(String email);

    /**
     * OAuth 제공자와 제공자 ID로 사용자 존재 여부 확인
     */
    boolean existsByProviderAndProviderId(String provider, String providerId);


    /**
     * OAuth 제공자별 사용자 수 통계
     */
    @Query("SELECT u.provider, COUNT(u) FROM User u GROUP BY u.provider")
    List<Object[]> countByProvider();

    /**
     * 특정 사용자의 OAuth 정보 업데이트
     */
    @Modifying
    @Query("UPDATE User u SET u.email = :email, u.name = :name WHERE u.id = :userId")
    void updateUserProfile(@Param("userId") Long userId,
                           @Param("email") String email,
                           @Param("name") String name);
}