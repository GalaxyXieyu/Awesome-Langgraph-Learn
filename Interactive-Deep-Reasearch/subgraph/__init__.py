"""
SubGraph模块
包含各种可复用的子图组件
"""

from .research import (
    create_intelligent_section_research_graph,
    IntelligentSectionState,
    ContextAwareAgent,
    QualityAssessmentAgent,
    AdaptiveResearchAgent
)

__version__ = "2.0.0"
__all__ = [
    "create_intelligent_section_research_graph",
    "IntelligentSectionState",
    "ContextAwareAgent",
    "QualityAssessmentAgent",
    "AdaptiveResearchAgent"
]
