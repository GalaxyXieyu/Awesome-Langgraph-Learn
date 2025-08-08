"""
智能章节研究SubGraph模块
基于质量驱动的迭代优化架构：上下文感知 + 智能质量评估 + 自适应补充研究 + 专业润色
"""

# 核心Graph组件
from .graph import (
    create_intelligent_section_research_graph,
    IntelligentSectionState,
    ContextAwareAgent,
    QualityAssessmentAgent,
    AdaptiveResearchAgent
)

# 工具函数
from .tools import (
    advanced_web_search,
    calculate_search_quality,
    deduplicate_search_results,
    calculate_content_quality
)

__version__ = "2.0.0"
__author__ = "AI Assistant"
__description__ = "智能章节研究Graph系统 - 上下文感知 + 质量驱动 + 迭代优化"

__all__ = [
    # 核心Graph组件
    "create_intelligent_section_research_graph",
    "IntelligentSectionState",
    "ContextAwareAgent",
    "QualityAssessmentAgent",
    "AdaptiveResearchAgent",

    # 工具函数
    "advanced_web_search",
    "calculate_search_quality",
    "deduplicate_search_results",
    "calculate_content_quality"
]
