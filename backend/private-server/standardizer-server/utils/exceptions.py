"""
커스텀 예외 클래스들
"""


class StandardizerException(Exception):
    """기본 Standardizer 예외"""
    pass


class ConfigurationError(StandardizerException):
    """설정 관련 오류"""
    pass


class DatabaseError(StandardizerException):
    """데이터베이스 관련 오류"""
    pass


class RedisError(StandardizerException):
    """Redis 관련 오류"""
    pass


class DARTError(StandardizerException):
    """DART API 관련 오류"""
    pass


class CrawlingError(StandardizerException):
    """크롤링 관련 오류"""
    pass


class MappingError(StandardizerException):
    """매핑 관련 오류"""
    pass


class LLMError(StandardizerException):
    """LLM 관련 오류"""
    pass


class FileProcessingError(StandardizerException):
    """파일 처리 관련 오류"""
    pass