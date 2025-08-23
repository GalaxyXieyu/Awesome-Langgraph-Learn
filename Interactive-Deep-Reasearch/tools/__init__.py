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


async def get_tools(tool_type: str = "all", state: Dict[str, Any] = None) -> List[BaseTool]:
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

async def get_research_tools(state: Dict[str, Any] = None) -> List[BaseTool]:
    """获取研究工具"""
    return await get_tools("research", state)


async def get_common_tools(state: Dict[str, Any] = None) -> List[BaseTool]:
    """获取通用工具"""
    return await get_tools("common", state)


async def get_all_tools(state: Dict[str, Any] = None) -> List[BaseTool]:
    """获取所有工具"""
    return await get_tools("all", state)