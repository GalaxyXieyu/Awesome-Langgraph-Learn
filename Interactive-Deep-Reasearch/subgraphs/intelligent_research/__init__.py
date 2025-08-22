"""
智能研究子图 - 多Agent协作的智能研究系统
包含监督者、研究者、写作者和整合者
"""

from .graph import create_intelligent_research_graph, IntelligentResearchState
from .context_builder import build_supervisor_context, determine_next_action_by_state
from .prompts import get_supervisor_prompt, get_researcher_prompt, get_writer_prompt

__all__ = [
    'create_intelligent_research_graph',
    'IntelligentResearchState',
    'build_supervisor_context',
    'determine_next_action_by_state', 
    'get_supervisor_prompt',
    'get_researcher_prompt',
    'get_writer_prompt'
]