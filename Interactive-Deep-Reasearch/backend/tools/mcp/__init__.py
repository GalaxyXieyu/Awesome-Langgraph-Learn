"""
MCP (Model Context Protocol) 工具模块
提供 Bing 搜索和图表生成的 MCP 服务集成
"""

from .tools import (
    bing_search_mcp,
    create_chart_mcp,
    MCP_TOOLS
)
from .client import MCPClientManager

__all__ = [
    "bing_search_mcp", 
    "create_chart_mcp",
    "MCP_TOOLS",
    "MCPClientManager"
]