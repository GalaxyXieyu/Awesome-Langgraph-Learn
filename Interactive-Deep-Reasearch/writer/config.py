"""
配置管理模块 - 简单YAML配置系统
"""

import yaml
import os
from typing import Dict, Any, List, Set, Optional
from pathlib import Path

class WriterConfig:
    """Writer配置管理器 - 简单易用的YAML配置"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的writer_config.yaml
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # 缓存配置项以提高性能
        self._cache_config_items()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                # 如果配置文件不存在，返回空配置（使用默认值）
                return {}
        except Exception as e:
            print(f"警告: 加载配置文件失败 {self.config_path}: {e}")
            return {}
    
    def _cache_config_items(self):
        """缓存常用配置项"""
        # 节点控制
        nodes = self.config.get('nodes', {})
        subgraph = nodes.get('subgraph', {})
        main = nodes.get('main', {})
        
        self.subgraph_include: Set[str] = set(subgraph.get('include', []))
        self.subgraph_exclude: Set[str] = set(subgraph.get('exclude', []))
        self.main_include: Set[str] = set(main.get('include', []))
        self.main_exclude: Set[str] = set(main.get('exclude', []))
        
        # 消息类型控制
        messages = self.config.get('messages', {})
        self.message_include: Set[str] = set(messages.get('include', []))
        self.message_exclude: Set[str] = set(messages.get('exclude', []))
        
        # Agent控制
        agents = self.config.get('agents', {})
        self.agent_include: Set[str] = set(agents.get('include', []))
        self.agent_exclude: Set[str] = set(agents.get('exclude', []))
        
        # 流式控制
        streaming = self.config.get('streaming', {})
        self.stream_enabled: bool = streaming.get('enabled', True)
        
        # 节点级别流式控制
        node_streaming = streaming.get('nodes', {})
        self.node_streaming_config: Dict[str, bool] = {
            # 默认配置
            'outline_generation': True,          # 大纲生成：流式
            'outline_confirmation': False,       # 大纲确认：非流式
            'content_creation': False,          # 内容创建：非流式（汇总输出）
            'intelligent_section_processing': False,  # 智能章节处理：非流式
            **node_streaming  # 用户自定义配置覆盖默认值
        }
        

    
    def should_process_subgraph_node(self, node_name: str) -> bool:
        """判断是否应该处理子图节点"""
        # 如果在排除列表中，不处理
        if self.subgraph_exclude and node_name in self.subgraph_exclude:
            return False
        
        # 如果有包含列表且不在其中，不处理
        if self.subgraph_include and node_name not in self.subgraph_include:
            return False
        
        return True
    
    def should_process_main_node(self, node_name: str) -> bool:
        """判断是否应该处理主图节点"""
        if self.main_exclude and node_name in self.main_exclude:
            return False
        
        if self.main_include and node_name not in self.main_include:
            return False
        
        return True
    
    def should_process_message_type(self, message_type: str) -> bool:
        """判断是否应该处理该消息类型"""
        if self.message_exclude and message_type in self.message_exclude:
            return False
        
        if self.message_include and message_type not in self.message_include:
            return False
        
        return True
    
    def should_process_agent(self, agent_name: str) -> bool:
        """判断是否应该处理该Agent"""
        if self.agent_exclude and agent_name in self.agent_exclude:
            return False
        
        if self.agent_include and agent_name not in self.agent_include:
            return False
        
        return True
    

    def should_show_timing(self) -> bool:
        """是否显示时间信息 - 简化为总是显示"""
        return True

    def should_show_agent_hierarchy(self) -> bool:
        """是否显示Agent层级信息 - 简化为总是显示"""
        return True
    
    def is_node_streaming_enabled(self, node_name: str) -> bool:
        """检查指定节点是否启用流式输出"""
        return self.node_streaming_config.get(node_name, True)  # 默认启用流式
    
    def get_node_streaming_config(self) -> Dict[str, bool]:
        """获取所有节点的流式配置"""
        return self.node_streaming_config.copy()
    
    def set_node_streaming(self, node_name: str, enabled: bool):
        """动态设置节点流式配置"""
        self.node_streaming_config[node_name] = enabled
    
    def is_stream_enabled(self) -> bool:
        """是否启用流式模式"""
        return self.stream_enabled
    
    def get_batch_size(self) -> int:
        """获取批量大小 - 简化为固定值"""
        return 10

    def get_max_buffer(self) -> int:
        """获取最大缓冲区大小 - 简化为固定值"""
        return 100
    
    def reload(self):
        """重新加载配置文件"""
        self.config = self._load_config()
        self._cache_config_items()
        print(f"配置已重新加载: {self.config_path}")

# 全局默认配置实例
_default_config = None

def get_writer_config(config_path: Optional[str] = None) -> WriterConfig:
    """获取Writer配置实例"""
    global _default_config
    if _default_config is None or config_path is not None:
        _default_config = WriterConfig(config_path)
    return _default_config