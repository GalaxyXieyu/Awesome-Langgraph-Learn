"""
SubGraph模块
包含各种可复用的子图组件
"""

from .research import (
    SectionResearchSubGraph,
    create_single_section_research_graph,
    create_initial_state
)

__version__ = "1.0.0"
__all__ = [
    "SectionResearchSubGraph",
    "create_single_section_research_graph", 
    "create_initial_state"
]
