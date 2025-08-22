"""
Interactive Deep Research - 工具模块
提供各类专业工具集合
"""

from .research.tools import ALL_RESEARCH_TOOLS
from .common.tools import get_all_tools

# 工具注册表
TOOL_REGISTRY = {
    'research': 'tools.research.tools',
    'common': 'tools.common.tools'
}

__all__ = [
    'ALL_RESEARCH_TOOLS',
    'get_all_tools',
    'TOOL_REGISTRY'
]