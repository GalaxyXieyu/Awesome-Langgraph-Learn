"""
状态定义模块
定义研究图的状态结构
"""

from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ResearchState(TypedDict):
    """研究状态定义"""
    # 消息列表，使用add_messages进行累积
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 研究主题
    topic: str
    
    # 当前步骤
    current_step: Optional[str]
    
    # 研究结果
    research_results: List[str]
    
    # 是否完成
    completed: bool


def create_simple_state(topic: str) -> ResearchState:
    """创建简单的初始状态"""
    return ResearchState(
        messages=[],
        topic=topic,
        current_step="start",
        research_results=[],
        completed=False
    )
