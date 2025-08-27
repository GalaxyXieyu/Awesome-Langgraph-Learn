"""
Interactive Deep Research - Writer系统
标准化流式输出系统，支持配置驱动的节点和消息筛选
"""

from writer.core import (
    StreamWriter, 
    AgentWorkflowProcessor,
    FlatDataProcessor,
    MessageType,
    create_stream_writer,
    create_workflow_processor,
    create_flat_processor
)
from writer.config import WriterConfig, get_writer_config

__all__ = [
    'StreamWriter',
    'AgentWorkflowProcessor', 
    'FlatDataProcessor',
    'MessageType',
    'create_stream_writer',
    'create_workflow_processor',
    'create_flat_processor',
    'WriterConfig',
    'get_writer_config'
]