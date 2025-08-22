"""
工具导出模块
提供简单的get_tools函数供其他graph使用
"""

import asyncio
from typing import List, Dict, Any
from langchain_core.tools import BaseTool

# 导入包装器
from .wrapper import wrap_tools

# 导入各类工具
from .research.tools import RESEARCH_TOOLS
from .common.tools import COMMON_TOOLS


async def get_tools_async(tool_type: str = "all", state: Dict[str, Any] = None) -> List[BaseTool]:
    """
    异步获取包装后的工具
    
    Args:
        tool_type: 工具类型 ("research", "common", "all")
        state: 状态字典，用于检测模式
        
    Returns:
        包装后的工具列表
    """
    if tool_type == "research":
        tools = RESEARCH_TOOLS
    elif tool_type == "common":
        tools = COMMON_TOOLS
    elif tool_type == "all":
        tools = RESEARCH_TOOLS + COMMON_TOOLS
    else:
        tools = []
    
    # 使用异步包装器包装工具
    return await wrap_tools(tools, state)


def get_tools(tool_type: str = "all", state: Dict[str, Any] = None) -> List[BaseTool]:
    """
    同步获取包装后的工具（会自动处理async）
    
    Args:
        tool_type: 工具类型 ("research", "common", "all")
        state: 状态字典，用于检测模式
        
    Returns:
        包装后的工具列表
    """
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已有事件循环在运行，创建任务
            return asyncio.create_task(get_tools_async(tool_type, state))
        else:
            # 没有运行的事件循环，直接运行
            return asyncio.run(get_tools_async(tool_type, state))
    except RuntimeError:
        # 没有事件循环，创建一个新的
        return asyncio.run(get_tools_async(tool_type, state))


def get_research_tools(state: Dict[str, Any] = None) -> List[BaseTool]:
    """获取研究工具"""
    return get_tools("research", state)


def get_common_tools(state: Dict[str, Any] = None) -> List[BaseTool]:
    """获取通用工具"""
    return get_tools("common", state)


def get_all_tools(state: Dict[str, Any] = None) -> List[BaseTool]:
    """获取所有工具"""
    return get_tools("all", state)