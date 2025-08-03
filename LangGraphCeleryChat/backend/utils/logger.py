"""
日志工具
"""

import logging
import sys
from typing import Optional
from functools import lru_cache


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """设置日志配置"""
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log", encoding="utf-8")
        ]
    )


@lru_cache()
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)
