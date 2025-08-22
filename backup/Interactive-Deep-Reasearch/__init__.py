"""
Interactive Deep Research - 智能交互式深度研究系统

一个基于LangGraph的多Agent协作研究报告生成系统，
支持配置驱动的流式输出和Human-in-the-loop交互。

主要特性:
- 模块化架构设计
- 配置驱动的Writer系统
- 多Agent协作子图
- 标准化工具集合

快速开始:
    from graph import create_deep_research_graph
    from state import create_simple_state
    from writer.core import create_workflow_processor
    
    # 创建主图
    graph = create_deep_research_graph()
    
    # 创建初始状态
    state = create_simple_state("研究人工智能的发展趋势")
    
    # 创建输出处理器
    processor = create_workflow_processor("main")
    
    # 运行图
    for chunk in graph.stream(state):
        result = processor.process_chunk(chunk)
        print(result)
"""

__version__ = "1.0.0"

# 核心模块导出 - 主文件在根目录
from graph import create_deep_research_graph
from state import DeepResearchState, create_simple_state
from writer.core import create_workflow_processor, create_stream_writer
from writer.config import WriterConfig
from subgraphs import create_intelligent_research_graph, IntelligentResearchState

__all__ = [
    'create_deep_research_graph',
    'DeepResearchState', 
    'create_simple_state',
    'create_workflow_processor',
    'create_stream_writer',
    'WriterConfig',
    'create_intelligent_research_graph',
    'IntelligentResearchState'
]