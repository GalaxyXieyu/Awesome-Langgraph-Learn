"""
数据模型和 Pydantic 模式定义
基于 Interative-Report-Workflow 的状态结构
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """消息类型枚举"""
    TASK_START = "task_start"
    TASK_PAUSE = "task_pause"
    TASK_RESUME = "task_resume"
    TASK_CANCEL = "task_cancel"
    TASK_COMPLETE = "task_complete"
    PROGRESS_UPDATE = "progress_update"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    INTERRUPT_REQUEST = "interrupt_request"
    USER_RESPONSE = "user_response"
    STREAM_CONTENT = "stream_content"
    ERROR = "error"
    WARNING = "warning"


class WritingMode(str, Enum):
    """写作模式枚举"""
    COPILOT = "copilot"      # 自动模式，跳过所有确认
    INTERACTIVE = "interactive"  # 交互模式，需要用户确认


class WritingStyle(str, Enum):
    """写作风格枚举"""
    FORMAL = "formal"
    CASUAL = "casual"
    ACADEMIC = "academic"
    TECHNICAL = "technical"


# ============================================================================
# 基础消息模型
# ============================================================================

class BaseMessage(BaseModel):
    """基础消息模型"""
    type: MessageType
    session_id: str
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)


class ProgressUpdate(BaseModel):
    """进度更新数据"""
    step: str
    progress: int = Field(ge=0, le=100)
    status: str
    current_action: Optional[str] = None
    estimated_remaining: Optional[int] = None  # 秒


class InterruptRequest(BaseModel):
    """交互请求数据"""
    interrupt_type: str
    title: str
    message: str
    options: List[str]
    default: Optional[str] = None
    timeout: Optional[int] = 300  # 5分钟默认超时
    content: Dict[str, Any] = Field(default_factory=dict)


class UserResponse(BaseModel):
    """用户响应数据"""
    interrupt_id: str
    response: str
    approved: bool
    feedback: Optional[str] = None
    modifications: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 写作任务相关模型
# ============================================================================

class OutlineSection(BaseModel):
    """大纲章节模型"""
    title: str = Field(description="章节标题")
    description: str = Field(description="章节描述")
    key_points: List[str] = Field(description="章节要点列表")


class ArticleOutline(BaseModel):
    """文章大纲模型"""
    title: str = Field(description="文章标题")
    sections: List[OutlineSection] = Field(description="章节列表")


class SearchResult(BaseModel):
    """搜索结果模型"""
    title: str
    url: str
    snippet: str
    relevance_score: Optional[float] = None


class WritingTaskConfig(BaseModel):
    """写作任务配置"""
    topic: str = Field(description="文章主题")
    max_words: int = Field(default=1000, description="最大字数")
    style: WritingStyle = Field(default=WritingStyle.FORMAL, description="写作风格")
    language: str = Field(default="zh", description="语言")
    mode: WritingMode = Field(default=WritingMode.INTERACTIVE, description="运行模式")
    enable_search: bool = Field(default=True, description="是否启用联网搜索")


class WritingTaskState(BaseModel):
    """写作任务状态"""
    # 基本信息
    task_id: str
    session_id: str
    user_id: str
    
    # 配置
    config: WritingTaskConfig
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    current_step: str = "initialized"
    progress: int = 0
    
    # 内容
    outline: Optional[ArticleOutline] = None
    article: Optional[str] = None
    search_results: List[SearchResult] = Field(default_factory=list)
    
    # 用户交互
    user_confirmation: Optional[str] = None
    search_permission: Optional[str] = None
    rag_permission: Optional[str] = None
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # 元数据
    word_count: int = 0
    generation_time: Optional[float] = None
    error_message: Optional[str] = None


# ============================================================================
# API 请求/响应模型
# ============================================================================

class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    config: WritingTaskConfig
    user_id: str


class CreateTaskResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    session_id: str
    status: TaskStatus
    message: str = "任务创建成功"


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: TaskStatus
    progress: int
    current_step: str
    outline: Optional[ArticleOutline] = None
    article: Optional[str] = None
    search_results: List[SearchResult] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    word_count: int = 0
    generation_time: Optional[float] = None
    error_message: Optional[str] = None


class InterruptResponseRequest(BaseModel):
    """交互响应请求"""
    response: str
    approved: bool = True
    feedback: Optional[str] = None
    modifications: Dict[str, Any] = Field(default_factory=dict)


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    active_tasks: List[str] = Field(default_factory=list)


# ============================================================================
# 事件流模型
# ============================================================================

class StreamEvent(BaseModel):
    """流事件模型"""
    event_id: str
    event_type: MessageType
    session_id: str
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)


class SSEMessage(BaseModel):
    """Server-Sent Events 消息格式"""
    event: str
    data: str
    id: Optional[str] = None
    retry: Optional[int] = None


# ============================================================================
# 错误模型
# ============================================================================

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error_code: str
    error_message: str
    error_details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    task_id: Optional[str] = None
    session_id: Optional[str] = None


class ValidationError(BaseModel):
    """验证错误模型"""
    field: str
    message: str
    value: Any


# ============================================================================
# 配置模型
# ============================================================================

class RedisConfig(BaseModel):
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10


class CeleryConfig(BaseModel):
    """Celery 配置"""
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True


class AppConfig(BaseModel):
    """应用配置"""
    app_name: str = "LangGraph Celery Chat"
    version: str = "1.0.0"
    debug: bool = False
    redis: RedisConfig = Field(default_factory=RedisConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    
    # JWT 配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24小时
    
    # CORS 配置
    cors_origins: List[str] = ["http://localhost:3000", "https://yourdomain.com"]
    
    # 任务配置
    task_timeout: int = 3600  # 1小时
    max_concurrent_tasks: int = 10
    
    class Config:
        env_prefix = "APP_"
