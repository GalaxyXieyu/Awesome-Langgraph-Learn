"""
配置管理
"""

import os
from functools import lru_cache
from ..models.schemas import AppConfig, RedisConfig, CeleryConfig


@lru_cache()
def get_config() -> AppConfig:
    """获取应用配置"""
    
    # Redis 配置 (使用远程 Redis)
    redis_config = RedisConfig(
        host=os.getenv("REDIS_HOST", "dbconn.sealoshzh.site"),
        port=int(os.getenv("REDIS_PORT", "41277")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD", "mfzstl2v"),
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    )
    
    # Celery 配置
    redis_url = f"redis://default:{redis_config.password}@{redis_config.host}:{redis_config.port}/{redis_config.db}"
    celery_config = CeleryConfig(
        broker_url=os.getenv("CELERY_BROKER_URL", redis_url),
        result_backend=os.getenv("CELERY_RESULT_BACKEND", redis_url),
        task_serializer=os.getenv("CELERY_TASK_SERIALIZER", "json"),
        result_serializer=os.getenv("CELERY_RESULT_SERIALIZER", "json"),
        accept_content=os.getenv("CELERY_ACCEPT_CONTENT", "json").split(","),
        timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
        enable_utc=os.getenv("CELERY_ENABLE_UTC", "true").lower() == "true"
    )
    
    # 应用配置
    config = AppConfig(
        app_name=os.getenv("APP_NAME", "LangGraph Celery Chat"),
        version=os.getenv("APP_VERSION", "1.0.0"),
        debug=os.getenv("APP_DEBUG", "false").lower() == "true",
        redis=redis_config,
        celery=celery_config,
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "1440")),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,https://yourdomain.com,file://,null").split(","),
        task_timeout=int(os.getenv("TASK_TIMEOUT", "3600")),
        max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
    )
    
    return config
