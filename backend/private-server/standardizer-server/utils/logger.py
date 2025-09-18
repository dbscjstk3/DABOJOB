"""
로깅 설정 및 헬퍼
"""
import logging
import sys
from typing import Optional
from config import settings


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    로깅 설정

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

    Returns:
        설정된 logger
    """
    log_level = level or settings.LOG_LEVEL

    # 기본 로깅 설정
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    이름으로 logger 가져오기

    Args:
        name: logger 이름

    Returns:
        logger 인스턴스
    """
    return logging.getLogger(name)


# 기본 logger
logger = get_logger("standardizer")