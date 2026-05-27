"""
Multi-Agent Handoff工具模块

定义了各种handoff工具和其他辅助工具
"""

from typing import Annotated, Dict, Any, Optional
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from state import MultiAgentState, add_handoff_record
import json


def create_handoff_tool(agent_name: str, description: Optional[str] = None):
    """
    动态创建handoff工具的工厂函数
    
    Args:
        agent_name: 目标agent的名称
        description: 工具描述
    
    Returns:
        handoff工具函数
    """
    tool_name = f"transfer_to_{agent_name}"
    tool_description = description or f"将任务转交给{agent_name}agent处理"
    
    @tool(name=tool_name, description=tool_description)
    def handoff_tool(
        reason: str,
        context_data: Optional[str] = None,
        state: Annotated[MultiAgentState, InjectedState] = None,
        tool_call_id: Annotated[str, InjectedToolCallId] = None,
    ) -> Command:
        """
        执行handoff操作
        
        Args:
            reason: handoff的原因
            context_data: 要传递的上下文数据(JSON字符串格式)
            state: 注入的状态对象
            tool_call_id: 工具调用ID
        
        Returns:
            Command对象
        """
        # 解析context_data
        parsed_context = {}
        if context_data:
            try:
                parsed_context = json.loads(context_data)
            except json.JSONDecodeError:
                parsed_context = {"raw_data": context_data}
        
        # 创建工具响应消息
        tool_message = {
            "role": "tool",
            "content": f"成功将任务转交给{agent_name}。原因：{reason}",
            "name": tool_name,
            "tool_call_id": tool_call_id
        }
        
        # 更新状态
        current_agent = state.active_agent if state else "unknown"
        updated_state = add_handoff_record(
            state, 
            from_agent=current_agent,
            to_agent=agent_name,
            reason=reason,
            context_data=parsed_context
        )
        
        return Command(
            goto=agent_name,
            update={
                "messages": [tool_message],
                "active_agent": agent_name,
                "handoff_history": updated_state.handoff_history,
                "agents": updated_state.agents,
                "shared_context": {**state.shared_context, **parsed_context}
            },
            graph=Command.PARENT,
        )
    
    return handoff_tool


# 创建具体的handoff工具
transfer_to_researcher = create_handoff_tool(
    "researcher", 
    "需要进行信息搜索、资料收集或研究分析时调用此工具"
)

transfer_to_analyst = create_handoff_tool(
    "analyst",
    "需要进行数据分析、统计分析或深度洞察时调用此工具"
)

transfer_to_writer = create_handoff_tool(
    "writer",
    "需要进行内容创作、文档编写或内容编辑时调用此工具"
)

transfer_to_supervisor = create_handoff_tool(
    "supervisor",
    "需要任务协调、决策或总结汇报时调用此工具"
)


@tool
def get_agent_status(
    agent_name: Optional[str] = None,
    state: Annotated[MultiAgentState, InjectedState] = None,
) -> str:
    """
    获取agent状态信息
    
    Args:
        agent_name: 要查询的agent名称，如果为None则返回所有agents状态
        state: 注入的状态对象
    
    Returns:
        agent状态信息的JSON字符串
    """
    if not state:
        return "无法获取状态信息"
    
    if agent_name:
        if agent_name in state.agents:
            agent_info = state.agents[agent_name]
            return json.dumps({
                "name": agent_info.name,
                "role": agent_info.role,
                "status": agent_info.status,
                "last_action": agent_info.last_action
            }, ensure_ascii=False)
        else:
            return f"未找到名为{agent_name}的agent"
    else:
        # 返回所有agents的状态
        all_agents = {}
        for name, agent_info in state.agents.items():
            all_agents[name] = {
                "role": agent_info.role,
                "status": agent_info.status,
                "last_action": agent_info.last_action
            }
        return json.dumps({
            "active_agent": state.active_agent,
            "system_status": state.system_status,
            "agents": all_agents
        }, ensure_ascii=False)


@tool
def get_handoff_history(
    limit: Optional[int] = 5,
    state: Annotated[MultiAgentState, InjectedState] = None,
) -> str:
    """
    获取handoff历史记录
    
    Args:
        limit: 返回的记录数量限制
        state: 注入的状态对象
    
    Returns:
        handoff历史记录的JSON字符串
    """
    if not state:
        return "无法获取状态信息"
    
    history = state.handoff_history[-limit:] if limit else state.handoff_history
    
    history_data = []
    for record in history:
        history_data.append({
            "from_agent": record.from_agent,
            "to_agent": record.to_agent,
            "reason": record.reason,
            "timestamp": record.timestamp,
            "context_keys": list(record.context_data.keys()) if record.context_data else []
        })
    
    return json.dumps(history_data, ensure_ascii=False)


@tool
def update_shared_context(
    key: str,
    value: str,
    state: Annotated[MultiAgentState, InjectedState] = None,
) -> str:
    """
    更新共享上下文
    
    Args:
        key: 上下文键
        value: 上下文值(JSON字符串)
        state: 注入的状态对象
    
    Returns:
        操作结果
    """
    if not state:
        return "无法获取状态信息"
    
    try:
        parsed_value = json.loads(value)
        state.shared_context[key] = parsed_value
        return f"成功更新共享上下文：{key}"
    except json.JSONDecodeError:
        state.shared_context[key] = value
        return f"成功更新共享上下文：{key} (作为字符串)"


@tool
def get_shared_context(
    key: Optional[str] = None,
    state: Annotated[MultiAgentState, InjectedState] = None,
) -> str:
    """
    获取共享上下文
    
    Args:
        key: 要获取的上下文键，如果为None则返回所有上下文
        state: 注入的状态对象
    
    Returns:
        上下文信息的JSON字符串
    """
    if not state:
        return "无法获取状态信息"
    
    if key:
        if key in state.shared_context:
            return json.dumps(state.shared_context[key], ensure_ascii=False)
        else:
            return f"未找到键为{key}的上下文"
    else:
        return json.dumps(state.shared_context, ensure_ascii=False)


# 研究相关工具
@tool
def search_information(query: str) -> str:
    """
    模拟搜索信息的工具
    
    Args:
        query: 搜索查询
    
    Returns:
        搜索结果
    """
    # 这里是模拟的搜索结果
    return f"关于'{query}'的搜索结果：\n1. 相关资料A\n2. 相关资料B\n3. 相关资料C"


# 分析相关工具
@tool
def analyze_data(data: str, analysis_type: str = "general") -> str:
    """
    模拟数据分析的工具
    
    Args:
        data: 要分析的数据
        analysis_type: 分析类型
    
    Returns:
        分析结果
    """
    return f"{analysis_type}分析结果：\n数据特征：{data[:50]}...\n分析结论：数据显示出明显的模式"


# 写作相关工具
@tool
def generate_content(topic: str, content_type: str = "article") -> str:
    """
    模拟内容生成的工具
    
    Args:
        topic: 内容主题
        content_type: 内容类型
    
    Returns:
        生成的内容
    """
    return f"关于'{topic}'的{content_type}:\n\n# {topic}\n\n这是一个关于{topic}的{content_type}内容..."