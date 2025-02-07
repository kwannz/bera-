import logging
import sys
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

class DebugCategory(Enum):
    TOKEN = "token"
    PRICE = "price"
    SEARCH = "search"
    API = "api"
    ANALYTICS = "analytics"

class CategoryFilter(logging.Filter):
    def __init__(self, debug_categories: Optional[list[DebugCategory]] = None):
        super().__init__()
        self.debug_categories = debug_categories or []
        
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'category'):
            record.category = 'general'
        return not self.debug_categories or record.category in [cat.value for cat in self.debug_categories]

def setup_logging(debug_categories: Optional[list[DebugCategory]] = None, log_file: str = 'berabot.log') -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug_categories else logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(category)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    category_filter = CategoryFilter(debug_categories)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(category_filter)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(category_filter)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
