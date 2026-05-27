"""
Multi-Agent Handoff状态定义模块

定义了多智能体系统中使用的状态结构
"""

from typing import Dict, List, Optional, Any
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """Agent信息结构"""
    name: str = Field(description="Agent名称")
    role: str = Field(description="Agent角色描述")
    status: str = Field(default="idle", description="Agent状态: idle, active, busy")
    last_action: Optional[str] = Field(default=None, description="最后执行的操作")


class HandoffContext(BaseModel):
    """Handoff上下文信息"""
    from_agent: str = Field(description="发起handoff的agent")
    to_agent: str = Field(description="目标agent")
    reason: str = Field(description="handoff原因")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="传递的上下文数据")
    timestamp: Optional[str] = Field(default=None, description="handoff时间戳")


class MultiAgentState(MessagesState):
    """多智能体系统的全局状态"""
    
    # 当前活跃的agent
    active_agent: str = Field(default="supervisor", description="当前活跃的agent名称")
    
    # 所有agents的信息
    agents: Dict[str, AgentInfo] = Field(
        default_factory=dict, 
        description="系统中所有agents的信息"
    )
    
    # handoff历史记录
    handoff_history: List[HandoffContext] = Field(
        default_factory=list,
        description="handoff历史记录"
    )
    
    # 共享的上下文数据
    shared_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="所有agents共享的上下文数据"
    )
    
    # 任务状态
    current_task: Optional[str] = Field(
        default=None,
        description="当前正在执行的任务"
    )
    
    # 任务结果
    task_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="各个agents执行任务的结果"
    )
    
    # 系统状态
    system_status: str = Field(
        default="idle",
        description="系统整体状态: idle, processing, completed, error"
    )


class ResearchAgentState(BaseModel):
    """研究Agent的专用状态"""
    research_query: Optional[str] = None
    search_results: List[Dict] = Field(default_factory=list)
    research_progress: float = 0.0
    findings: List[str] = Field(default_factory=list)


class AnalysisAgentState(BaseModel):
    """分析Agent的专用状态"""
    analysis_type: Optional[str] = None
    data_source: Optional[str] = None
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0


class WriterAgentState(BaseModel):
    """写作Agent的专用状态"""
    content_type: Optional[str] = None
    outline: List[str] = Field(default_factory=list)
    draft_content: Optional[str] = None
    revision_count: int = 0


def create_initial_state() -> MultiAgentState:
    """创建初始状态"""
    return MultiAgentState(
        messages=[],
        active_agent="supervisor",
        agents={
            "supervisor": AgentInfo(
                name="supervisor",
                role="任务协调和分配",
                status="active"
            ),
            "researcher": AgentInfo(
                name="researcher", 
                role="信息搜索和研究",
                status="idle"
            ),
            "analyst": AgentInfo(
                name="analyst",
                role="数据分析和洞察",
                status="idle"
            ),
            "writer": AgentInfo(
                name="writer",
                role="内容创作和编辑",
                status="idle"
            )
        },
        system_status="idle"
    )


def update_agent_status(state: MultiAgentState, agent_name: str, status: str) -> MultiAgentState:
    """更新agent状态"""
    if agent_name in state.agents:
        state.agents[agent_name].status = status
    return state


def add_handoff_record(
    state: MultiAgentState, 
    from_agent: str, 
    to_agent: str, 
    reason: str,
    context_data: Dict[str, Any] = None
) -> MultiAgentState:
    """添加handoff记录"""
    from datetime import datetime
    
    handoff = HandoffContext(
        from_agent=from_agent,
        to_agent=to_agent,
        reason=reason,
        context_data=context_data or {},
        timestamp=datetime.now().isoformat()
    )
    
    state.handoff_history.append(handoff)
    state.active_agent = to_agent
    
    # 更新agent状态
    update_agent_status(state, from_agent, "idle")
    update_agent_status(state, to_agent, "active")
    
    return state