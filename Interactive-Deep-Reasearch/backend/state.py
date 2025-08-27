"""
状态管理模块
定义高级交互式深度研究报告生成系统的状态结构
"""

import time
from typing import Dict, Any, List, TypedDict, Annotated, Optional
from enum import Enum
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

# ============================================================================
# 枚举定义
# ============================================================================

class ReportMode(str, Enum):
    """报告生成模式"""
    INTERACTIVE = "interactive"  # 交互模式：需要用户确认每个步骤
    COPILOT = "copilot"         # 副驾驶模式：自动通过所有确认
    GUIDED = "guided"           # 引导模式：提供建议但需要确认

class AgentType(str, Enum):
    """Agent类型"""
    SUPERVISOR = "supervisor"    # 监督器：任务协调和路由
    RESEARCHER = "researcher"    # 研究专家：信息收集和研究
    ANALYST = "analyst"         # 分析专家：数据分析和洞察
    WRITER = "writer"           # 写作专家：内容生成和报告写作
    VALIDATOR = "validator"     # 验证专家：质量控制和验证

class InteractionType(str, Enum):
    """交互类型"""
    OUTLINE_CONFIRMATION = "outline_confirmation"
    RESEARCH_PERMISSION = "research_permission"
    ANALYSIS_APPROVAL = "analysis_approval"
    CONTENT_REVIEW = "content_review"
    FINAL_APPROVAL = "final_approval"

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

# ============================================================================
# 数据模型
# ============================================================================

class ReportSection(BaseModel):
    """报告章节模型"""
    id: str = Field(description="章节唯一标识")
    title: str = Field(description="章节标题")
    description: str = Field(description="章节描述")
    key_points: List[str] = Field(description="关键要点列表")
    research_queries: List[str] = Field(description="相关研究查询")
    priority: int = Field(description="优先级1-5", default=3)
    status: TaskStatus = Field(description="章节状态", default=TaskStatus.PENDING)
    content: Optional[str] = Field(description="章节内容", default=None)
    word_count: int = Field(description="字数统计", default=0)

class ReportOutline(BaseModel):
    """报告大纲模型"""
    title: str = Field(description="报告标题")
    executive_summary: str = Field(description="执行摘要")
    sections: List[ReportSection] = Field(description="报告章节列表")
    methodology: str = Field(description="研究方法论")
    target_audience: str = Field(description="目标读者群体")
    estimated_length: int = Field(description="预估总字数")
    creation_time: float = Field(description="创建时间戳", default_factory=time.time)

class ResearchResult(BaseModel):
    """研究结果模型"""
    id: str = Field(description="结果唯一标识")
    query: str = Field(description="搜索查询")
    source_type: str = Field(description="来源类型：web/knowledge_base/api")
    title: str = Field(description="结果标题")
    content: str = Field(description="内容摘要")
    url: Optional[str] = Field(description="来源URL", default=None)
    credibility_score: float = Field(description="可信度分数0-1", default=0.8)
    relevance_score: float = Field(description="相关性分数0-1", default=0.8)
    timestamp: float = Field(description="获取时间戳", default_factory=time.time)
    section_id: Optional[str] = Field(description="关联章节ID", default=None)

class AnalysisInsight(BaseModel):
    """分析洞察模型"""
    id: str = Field(description="洞察唯一标识")
    type: str = Field(description="洞察类型：trend/pattern/correlation/prediction")
    title: str = Field(description="洞察标题")
    description: str = Field(description="详细描述")
    evidence: List[str] = Field(description="支持证据列表")
    confidence_level: str = Field(description="置信度：high/medium/low")
    implications: List[str] = Field(description="影响和含义")
    timestamp: float = Field(description="生成时间戳", default_factory=time.time)
    section_id: Optional[str] = Field(description="关联章节ID", default=None)

class ExecutionPlan(BaseModel):
    """执行计划模型"""
    recommended_agents: List[str] = Field(description="推荐使用的Agent")
    execution_sequence: List[str] = Field(description="执行步骤序列")
    estimated_duration: str = Field(description="预估执行时间")
    complexity_assessment: str = Field(description="复杂度评估")
    required_interactions: List[str] = Field(description="需要的交互点")
    success_criteria: List[str] = Field(description="成功标准")

class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    start_time: float = Field(description="开始时间戳", default_factory=time.time)
    end_time: Optional[float] = Field(description="结束时间戳", default=None)
    total_duration: Optional[float] = Field(description="总执行时间", default=None)
    agent_execution_times: Dict[str, float] = Field(description="各Agent执行时间", default_factory=dict)
    interaction_count: int = Field(description="交互次数", default=0)
    research_queries_count: int = Field(description="研究查询次数", default=0)
    total_words_generated: int = Field(description="生成总字数", default=0)
    quality_score: Optional[float] = Field(description="质量评分", default=None)

# ============================================================================
# 主状态类型
# ============================================================================

class DeepResearchState(TypedDict):
    """深度研究报告生成状态"""
    
    # ========== 基础配置 ==========
    topic: str                                    # 研究主题
    mode: ReportMode                             # 运行模式
    user_id: str                                 # 用户标识
    session_id: str                              # 会话标识
    
    # ========== 报告配置 ==========
    report_type: str                             # 报告类型：research/analysis/market/technical
    target_audience: str                         # 目标读者群体
    depth_level: str                             # 深度级别：shallow/medium/deep
    max_sections: int                            # 最大章节数
    target_length: int                           # 目标字数
    language: str                                # 语言设置
    style: str                                   # 写作风格
    
    # ========== 核心内容 ==========
    outline: Optional[Dict[str, Any]]            # 报告大纲（ReportOutline转换的字典）
    research_results: List[Dict[str, Any]]       # 研究结果列表
    analysis_insights: List[Dict[str, Any]]      # 分析洞察列表
    final_report: Optional[str]                  # 最终报告内容
    
    # ========== 节点输出汇总 ==========
    node_outputs: Dict[str, Dict[str, Any]]      # 节点完整输出：{node_name: {content, timestamp, word_count}}
    
    # ========== 执行状态 ==========
    current_step: str                            # 当前执行步骤
    execution_path: List[str]                    # 执行路径记录
    task_status: Dict[str, str]                  # 任务状态映射
    
    # ========== 交互状态 ==========
    user_feedback: Dict[str, Any]                # 用户反馈记录
    approval_status: Dict[str, bool]             # 审批状态记录
    interaction_history: List[Dict[str, Any]]    # 交互历史记录
    confirmations: Dict[str, Dict[str, Any]]     # 通用中断节点确认记录
    
    # ========== 系统状态 ==========
    error_log: List[str]                         # 错误日志
    performance_metrics: Dict[str, Any]          # 性能指标（简化版）
    
    # ========== 消息历史 ==========
    messages: Annotated[List[BaseMessage], add_messages]  # 对话消息历史

# ============================================================================
# 状态初始化函数
# ============================================================================

def create_initial_state(
    topic: str,
    user_id: str,
    mode: ReportMode = ReportMode.INTERACTIVE,
    report_type: str = "research",
    target_audience: str = "专业人士",
    depth_level: str = "deep",
    max_sections: int = 6,
    target_length: int = 3000,
    language: str = "zh",
    style: str = "professional"
) -> DeepResearchState:
    """
    创建初始状态
    
    Args:
        topic: 研究主题
        user_id: 用户ID
        mode: 运行模式
        report_type: 报告类型
        target_audience: 目标读者
        depth_level: 深度级别
        max_sections: 最大章节数
        target_length: 目标字数
        language: 语言
        style: 写作风格
    
    Returns:
        初始化的状态对象
    """
    from langchain_core.messages import HumanMessage
    
    session_id = f"deep_research_{int(time.time())}_{user_id}"
    
    initial_state: DeepResearchState = {
        # 基础配置
        "topic": topic,
        "mode": mode,
        "user_id": user_id,
        "session_id": session_id,
        
        # 报告配置
        "report_type": report_type,
        "target_audience": target_audience,
        "depth_level": depth_level,
        "max_sections": max_sections,
        "target_length": target_length,
        "language": language,
        "style": style,
        
        # 核心内容
        "outline": None,
        "research_results": [],
        "analysis_insights": [],
        "final_report": None,
        
        # 节点输出汇总
        "node_outputs": {},
        
        # 执行状态
        "current_step": "initialized",
        "execution_plan": None,
        "execution_path": [],
        "agent_results": {},
        "task_status": {},
        
        # 交互状态
        "pending_interactions": [],
        "user_feedback": {},
        "approval_status": {},
        "interaction_history": [],
        "confirmations": {},
        
        # 系统状态
        "error_log": [],
        "performance_metrics": {
            "start_time": time.time(),
            "end_time": None,
            "total_duration": None,
            "agent_execution_times": {},
            "interaction_count": 0,
            "research_queries_count": 0,
            "total_words_generated": 0,
            "quality_score": None
        },
        "metadata": {
            "created_at": time.time(),
            "version": "1.0.0",
            "system": "Interactive-Deep-Research"
        },
        
        # 消息历史
        "messages": [
            HumanMessage(content=f"开始生成关于'{topic}'的{report_type}深度研究报告")
        ]
    }
    
    return initial_state

def create_simple_state(topic: str, **kwargs) -> DeepResearchState:
    """
    简化的状态创建函数 - 只需要提供主题，其他都有默认值

    Args:
        topic: 研究主题（必填）
        **kwargs: 可选参数
            - user_id: 用户ID（默认: "user"）
            - mode: 运行模式（默认: COPILOT自动模式）
            - max_sections: 最大章节数（默认: 3）
            - target_length: 目标字数（默认: 2000）
            - language: 语言（默认: "zh"）
            - style: 写作风格（默认: "professional"）

    Returns:
        完整的DeepResearchState

    Example:
        # 最简单的用法
        state = create_simple_state("人工智能发展趋势")

        # 带可选参数
        state = create_simple_state(
            "人工智能发展趋势",
            max_sections=5,
            target_length=3000
        )
    """
    # 设置默认值
    defaults = {
        "user_id": "user",
        "mode": ReportMode.INTERACTIVE,  # 自动模式，无需交互
        "report_type": "research",
        "target_audience": "专业人士",
        "depth_level": "medium",
        "max_sections": 3,
        "target_length": 2000,
        "language": "zh",
        "style": "professional"
    }

    # 合并用户提供的参数
    params = {**defaults, **kwargs}

    return create_initial_state(topic=topic, **params)

# ============================================================================
# 状态更新辅助函数
# ============================================================================

def update_performance_metrics(state: DeepResearchState, agent_type: str, execution_time: float) -> None:
    """更新性能指标"""
    state["performance_metrics"]["agent_execution_times"][agent_type] = execution_time

def add_research_result(state: DeepResearchState, result: ResearchResult) -> None:
    """添加研究结果"""
    result_dict = result.dict() if hasattr(result, 'dict') else result
    state["research_results"].append(result_dict)
    state["performance_metrics"]["research_queries_count"] += 1

def add_analysis_insight(state: DeepResearchState, insight: AnalysisInsight) -> None:
    """添加分析洞察"""
    insight_dict = insight.dict() if hasattr(insight, 'dict') else insight
    state["analysis_insights"].append(insight_dict)

def update_task_status(state: DeepResearchState, task_name: str, status: TaskStatus) -> None:
    """更新任务状态"""
    state["task_status"][task_name] = status.value

def add_user_interaction(state: DeepResearchState, interaction_type: str, user_response: Dict[str, Any]) -> None:
    """记录用户交互"""
    interaction_record = {
        "type": interaction_type,
        "timestamp": time.time(),
        "response": user_response
    }
    state["interaction_history"].append(interaction_record)
    state["performance_metrics"]["interaction_count"] += 1

def add_node_output(state: DeepResearchState, node_name: str, content: str, **metadata) -> None:
    """
    添加节点完整输出到汇总中
    
    Args:
        state: 状态对象
        node_name: 节点名称
        content: 完整内容
        **metadata: 额外元数据(如word_count, status等)
    """
    output_data = {
        "content": content,
        "timestamp": time.time(),
        **metadata
    }
    state["node_outputs"][node_name] = output_data

def get_node_output(state: DeepResearchState, node_name: str) -> Optional[Dict[str, Any]]:
    """获取指定节点的完整输出"""
    return state["node_outputs"].get(node_name)

def get_all_node_outputs(state: DeepResearchState) -> Dict[str, Dict[str, Any]]:
    """获取所有节点的输出汇总"""
    return state["node_outputs"].copy()

def finalize_performance_metrics(state: DeepResearchState) -> None:
    """完成性能指标统计"""
    end_time = time.time()
    state["performance_metrics"]["end_time"] = end_time
    start_time = state["performance_metrics"]["start_time"]
    state["performance_metrics"]["total_duration"] = end_time - start_time

# ============================================================================
# 状态验证函数
# ============================================================================

def validate_state(state: DeepResearchState) -> Dict[str, Any]:
    """
    验证状态完整性
    
    Args:
        state: 状态对象
    
    Returns:
        验证结果字典
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 检查必要字段
    required_fields = ["topic", "user_id", "session_id", "mode"]
    for field in required_fields:
        if not state.get(field):
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"缺少必要字段: {field}")
    
    # 检查配置合理性
    if state.get("target_length", 0) <= 0:
        validation_result["warnings"].append("目标字数应该大于0")
    
    if state.get("max_sections", 0) <= 0:
        validation_result["warnings"].append("最大章节数应该大于0")
    
    # 检查状态一致性
    if state.get("current_step") == "completed" and not state.get("final_report"):
        validation_result["warnings"].append("任务已完成但没有最终报告")
    
    return validation_result

# ============================================================================
# 导出的主要类型和函数
# ============================================================================

__all__ = [
    # 枚举
    "ReportMode", "AgentType", "InteractionType", "TaskStatus",
    
    # 数据模型
    "ReportSection", "ReportOutline", "ResearchResult", "AnalysisInsight", 
    "ExecutionPlan", "PerformanceMetrics",
    
    # 状态类型
    "DeepResearchState",
    
    # 函数
    "create_initial_state", "update_performance_metrics", "add_research_result",
    "add_analysis_insight", "update_task_status", "add_user_interaction",
    "finalize_performance_metrics", "validate_state"
]