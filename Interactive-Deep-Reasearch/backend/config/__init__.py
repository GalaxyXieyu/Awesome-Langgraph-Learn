"""配置模块 - Interactive Deep Research 系统配置"""

__version__ = "1.0.0"

# 导出主要组件
from .database import get_database_url, get_connection_kwargs, DATABASE_CONFIG
from .checkpoint import ResearchPostgresSaver

__all__ = [
    "get_database_url",
    "get_connection_kwargs", 
    "DATABASE_CONFIG",
    "ResearchPostgresSaver"
]
