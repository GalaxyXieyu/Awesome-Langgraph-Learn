"""
应用配置管理
使用Pydantic进行配置验证和类型检查
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class RedisConfig(BaseSettings):
    """Redis配置"""
    url: str = Field(default="redis://localhost:6379", description="Redis连接URL")
    password: Optional[str] = Field(default=None, description="Redis密码")
    db: int = Field(default=0, description="Redis数据库编号")
    
    # TTL配置
    default_ttl: int = Field(default=60, description="默认TTL(分钟)")
    refresh_on_read: bool = Field(default=True, description="读取时刷新TTL")
    
    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    max_connections: int = Field(default=20, description="最大连接数")
    retry_attempts: int = Field(default=3, description="重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")
    
    # 性能配置
    socket_timeout: float = Field(default=5.0, description="Socket超时(秒)")
    socket_connect_timeout: float = Field(default=5.0, description="连接超时(秒)")
    
    class Config:
        env_prefix = "REDIS_"


class PostgreSQLConfig(BaseSettings):
    """PostgreSQL配置"""
    url: str = Field(
        default="postgresql://postgres:password@localhost:5432/langgraph",
        description="PostgreSQL连接URL"
    )
    
    # 连接池配置
    pool_size: int = Field(default=20, description="连接池大小")
    max_overflow: int = Field(default=30, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接池超时(秒)")
    pool_recycle: int = Field(default=3600, description="连接回收时间(秒)")
    
    # 查询配置
    statement_timeout: int = Field(default=30000, description="语句超时(毫秒)")
    
    class Config:
        env_prefix = "POSTGRES_"


class SQLiteConfig(BaseSettings):
    """SQLite配置"""
    database_path: str = Field(default="./data/langgraph.db", description="数据库文件路径")
    
    # 性能配置
    timeout: float = Field(default=20.0, description="数据库锁超时(秒)")
    check_same_thread: bool = Field(default=False, description="检查同一线程")
    
    # WAL模式配置
    journal_mode: str = Field(default="WAL", description="日志模式")
    synchronous: str = Field(default="NORMAL", description="同步模式")
    
    class Config:
        env_prefix = "SQLITE_"


class LLMConfig(BaseSettings):
    """大语言模型配置"""
    provider: str = Field(default="openai", description="LLM提供商")
    model: str = Field(default="gpt-4o-mini", description="模型名称")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    
    # 模型参数
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=1000, description="最大token数")
    
    class Config:
        env_prefix = "LLM_"


class MonitoringConfig(BaseSettings):
    """监控配置"""
    enable_metrics: bool = Field(default=True, description="启用指标收集")
    metrics_port: int = Field(default=8000, description="指标服务端口")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式")
    
    class Config:
        env_prefix = "MONITORING_"


class Settings(BaseSettings):
    """主配置类"""
    
    # 应用基础配置
    app_name: str = Field(default="LangGraph Session Storage Demo", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    
    # 存储配置
    default_storage: str = Field(default="memory", description="默认存储类型")
    
    # 子配置
    redis: RedisConfig = Field(default_factory=RedisConfig)
    postgres: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
    sqlite: SQLiteConfig = Field(default_factory=SQLiteConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    @validator('default_storage')
    def validate_storage_type(cls, v):
        """验证存储类型"""
        valid_types = ['memory', 'redis', 'postgres', 'sqlite']
        if v not in valid_types:
            raise ValueError(f'存储类型必须是: {valid_types}')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """验证运行环境"""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'环境必须是: {valid_envs}')
        return v
    
    def get_storage_config(self, storage_type: Optional[str] = None) -> Dict[str, Any]:
        """获取指定存储类型的配置"""
        storage_type = storage_type or self.default_storage
        
        config_map = {
            'redis': self.redis.dict(),
            'postgres': self.postgres.dict(),
            'sqlite': self.sqlite.dict(),
            'memory': {}
        }
        
        return config_map.get(storage_type, {})
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == 'development'
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局设置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局设置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载设置"""
    global _settings
    _settings = Settings()
    return _settings


# 便捷函数
def get_redis_config() -> RedisConfig:
    """获取Redis配置"""
    return get_settings().redis


def get_postgres_config() -> PostgreSQLConfig:
    """获取PostgreSQL配置"""
    return get_settings().postgres


def get_sqlite_config() -> SQLiteConfig:
    """获取SQLite配置"""
    return get_settings().sqlite


def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return get_settings().llm
