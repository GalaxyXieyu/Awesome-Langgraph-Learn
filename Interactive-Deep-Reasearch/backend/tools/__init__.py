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
from .research.tools import RESEARCH_TOOLS, RESEARCH_TOOLS_ASYNC
from .common.tools import COMMON_TOOLS
from .mcp.tools import MCP_TOOLS


async def get_tools(tool_type: str = "all", mode: str = "copilot") -> List[BaseTool]:
    """
    异步获取包装后的工具
    
    Args:
        tool_type: 工具类型 ("research", "common", "mcp", "all")
        mode: 工具模式 ("copilot", "interactive")
        
    Returns:
        包装后的工具列表
    """
    if tool_type == "research":
        # 默认返回异步工具集以便在异步 Graph 中并发执行
        tools = RESEARCH_TOOLS_ASYNC
    elif tool_type == "common":
        tools = COMMON_TOOLS
    elif tool_type == "mcp":
        tools = MCP_TOOLS
    elif tool_type == "all":
        tools = RESEARCH_TOOLS + COMMON_TOOLS + MCP_TOOLS
    else:
        tools = []
    
    # 使用异步包装器包装工具
    return await wrap_tools(tools, mode)

async def get_research_tools(mode: str = "copilot") -> List[BaseTool]:
    """获取研究工具"""
    return await get_tools("research", mode)


async def get_common_tools(mode: str = "copilot") -> List[BaseTool]:
    """获取通用工具"""
    return await get_tools("common", mode)


async def get_all_tools(mode: str = "copilot") -> List[BaseTool]:
    """获取所有工具"""
    return await get_tools("all", mode)


async def get_mcp_tools(mode: str = "copilot") -> List[BaseTool]:
    """获取 MCP 工具"""
    return await get_tools("mcp", mode)