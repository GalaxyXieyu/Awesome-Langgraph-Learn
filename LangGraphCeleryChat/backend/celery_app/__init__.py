"""
Celery 应用初始化
"""

from celery import Celery
from ..utils.config import get_config

config = get_config()

# 创建 Celery 应用实例
celery_app = Celery(
    "langgraph_celery_chat",
    broker=config.celery.broker_url,
    backend=config.celery.result_backend,
    include=["backend.celery_app.tasks"]
)

# 配置 Celery
celery_app.conf.update(
    task_serializer=config.celery.task_serializer,
    result_serializer=config.celery.result_serializer,
    accept_content=config.celery.accept_content,
    timezone=config.celery.timezone,
    enable_utc=config.celery.enable_utc,
    task_track_started=True,
    task_time_limit=config.task_timeout,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 导入任务模块
from . import tasks

__all__ = ["celery_app"]
