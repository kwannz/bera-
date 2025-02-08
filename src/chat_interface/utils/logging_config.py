import logging
from enum import Enum
from typing import Dict, Any


class DebugCategory(Enum):
    API = "api"
    CACHE = "cache"
    CONFIG = "config"
    VALIDATION = "validation"


def get_logger(name: str) -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    extra: Dict[str, Any]
) -> None:
    """带有上下文信息的日志记录"""
    logger.log(level, message, extra=extra)
