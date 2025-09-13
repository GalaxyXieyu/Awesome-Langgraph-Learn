"""
标准化流式输出系统 - Interactive Deep Research版本
基于Multi-Agent-report的Writer设计，去除emoji表情，添加子图专用功能
提供统一的流式输出格式，便于前端渲染
"""

import time
from typing import Dict, Any, List, Optional
from enum import Enum
from langgraph.config import get_stream_writer
from writer.config import WriterConfig, get_writer_config

# ============================================================================
# 数据扁平化处理器 - 核心组件
# ============================================================================

class FlatDataProcessor:
    """数据扁平化处理器 - 将复杂嵌套数据转换为简单扁平字典"""
    def __init__(self):
        """
        初始化扁平化处理器
        """
        pass

    def flatten_chunk(self, chunk: Any) -> Optional[Dict[str, Any]]:
        """
        扁平化单个chunk数据

        Args:
            chunk: LangGraph的chunk数据

        Returns:
            扁平化的字典 {message_type, tool_name, content, length, duration, node}
        """
        if not chunk:
            return None

        # 处理custom消息格式 ('custom', data)
        if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == 'custom':
            return self._flatten_custom_data(chunk[1])

        # 处理子图嵌套格式 (('subgraph_id',), 'updates'/'messages', data)
        if isinstance(chunk, tuple) and len(chunk) == 3:
            _, chunk_type, _ = chunk
            # 子图数据暂时不扁平化，交给原有逻辑处理
            return None

        # 处理普通格式 ('updates'/'messages', data)
        if isinstance(chunk, tuple) and len(chunk) == 2:
            chunk_type, _ = chunk
            if chunk_type in ['updates', 'messages']:
                # 这些格式需要特殊处理，不做扁平化
                return None

        return None
    
    def _flatten_custom_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """扁平化custom类型的数据"""
        if not isinstance(data, dict):
            return {}
            
        message_type = data.get('message_type', '')
        content = data.get('content', '')
        node_name = data.get('node_name', '')
        metadata = data.get('metadata', {})
        
        # 构建基础扁平结构
        flat_data = {
            'message_type': message_type,
            'content': content,
            'node': node_name,
            'timestamp': data.get('timestamp', time.time())
        }
        
        # 处理不同消息类型的特殊字段
        if message_type == 'tool_call':
            tool_name = metadata.get('tool_name', '')
            tool_args = metadata.get('tool_args', {})
            
            flat_data.update({
                'tool_name': tool_name,
                'content': self._get_tool_call_content(tool_name, tool_args),
                'args': tool_args
            })
            
        elif message_type == 'tool_result':
            tool_name = metadata.get('tool_name', '')
            result_length = metadata.get('result_length', 0)
            step_duration = metadata.get('step_duration', 0)
            full_result = metadata.get('full_result', content)
            
            flat_data.update({
                'tool_name': tool_name,
                'content': self._clean_tool_result(full_result),  # 去除前缀
                'length': result_length,
                'duration': round(step_duration, 2)
            })
            
        elif message_type == 'content':
            chunk_index = metadata.get('chunk_index', 0)
            
            flat_data.update({
                'length': len(content),
                'chunk_index': chunk_index
            })
            
        elif message_type == 'step_complete':
            duration = metadata.get('duration', 0)
            
            flat_data.update({
                'duration': round(duration, 2)
            })
        
        # 添加通用字段
        if 'step_duration' in metadata:
            flat_data['duration'] = round(metadata['step_duration'], 2)
            
        return flat_data
    
    def _get_tool_call_content(self, tool_name: str) -> str:
        """生成简化的工具调用内容描述"""
        return f"调用了 {tool_name} 工具"
    
    def _clean_tool_result(self, content: str) -> str:
        """清理工具结果内容，移除工具名前缀"""
        if not content:
            return ""
            
        # 移除常见的工具结果前缀
        prefixes = [
            ' 执行结果: ',
            ' 执行结果：',
            ' 结果: ',
            ' 结果：'
        ]
        
        for prefix in prefixes:
            if prefix in content:
                # 找到第一个前缀并移除它之前的部分（包括前缀）
                index = content.find(prefix)
                if index >= 0:
                    return content[index + len(prefix):].strip()
        
        return content.strip()

class MessageType(Enum):
    """简化的消息类型枚举 - 核心类型"""
    # 1. 进度相关 - 节点执行状态（支持百分比）
    PROCESSING = "processing"

    # 2. 内容相关 - 实际输出内容
    CONTENT = "content"

    # 3. 思考相关 - AI推理过程（包含planning）
    THINKING = "thinking"

    # 4. 中断相关 - 用户交互
    INTERRUPT = "interrupt"
    INTERRUPT_RESPONSE = "interrupt_response"
    INTERRUPT_RESOLVED = "interrupt_resolved"

    # 保留的特殊类型
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_RESULT = "final_result"
    ERROR = "error"



class StreamWriter:
    """标准化流式输出Writer - 简化消息类型版本"""

    def __init__(self, node_name: str = "", agent_name: str = "", custom_templates: Optional[Dict[str, str]] = None, config: Optional[WriterConfig] = None):
        self.node_name = node_name
        self.agent_name = agent_name
        self.step_start_time = time.time()
        self.writer = self._get_safe_writer()
        self.flat_processor = FlatDataProcessor()
        self.config = config or get_writer_config()

        # 消息缓冲区（用于非流式模式）
        self.message_buffer = []

        # 标记未使用的参数以维持向后兼容性
        _ = custom_templates
        
    def _get_safe_writer(self):
        """安全获取writer"""
        try:
            return get_stream_writer()
        except Exception:
            return lambda _: None

    def _calculate_progress_percentage(self, graph_nodes: List[str] = None) -> int:
        """
        根据当前节点计算进度百分比

        Args:
            graph_nodes: 图的节点列表，如果不提供则返回默认进度

        Returns:
            进度百分比 (0-100)
        """
        try:
            if graph_nodes and self.node_name in graph_nodes:
                node_index = graph_nodes.index(self.node_name)
                total_nodes = len(graph_nodes)

                # 基础进度：当前节点在总节点中的位置
                base_progress = (node_index / total_nodes) * 100

                # 节点内进度（假设节点执行到一半）
                node_progress = (100 / total_nodes) * 0.5

                return int(base_progress + node_progress)

            # 子图节点或未知节点，返回默认进度
            return 50

        except Exception:
            return 50
    
    def _send_message(self, msg_type: MessageType, content: str, subtype: str = None, **kwargs):
        """发送简化格式消息 - 支持子类型和进度计算"""
        # 检查消息类型是否应该被处理
        if not self.config.should_process_message_type(msg_type.value):
            return

        # 构建简化消息
        message = {
            "message_type": msg_type.value,
            "content": content,
            "node": self.node_name,
            "timestamp": time.time()
        }

        # 添加子类型
        if subtype:
            message["subtype"] = subtype

        # 为processing类型自动计算进度百分比
        if msg_type == MessageType.PROCESSING and subtype:
            message["progress"] = self._calculate_progress_percentage(subtype)

        # 根据配置决定是否添加元数据
        if self.config.should_show_timing():
            message["duration"] = round(time.time() - self.step_start_time, 2)

        # 添加特定字段
        for key, value in kwargs.items():
            if key not in message:  # 避免覆盖核心字段
                message[key] = value

        # 根据流式配置决定如何发送
        if self.config.is_stream_enabled():
            self.writer(message)
        else:
            self.message_buffer.append(message)
            if len(self.message_buffer) >= self.config.get_batch_size():
                self.flush_buffer()
    
    def flush_buffer(self):
        """刷新消息缓冲区"""
        for message in self.message_buffer:
            self.writer(message)  # 修复：使用正确的tuple格式
        self.message_buffer.clear()
    
    # ============================================================================
    # 新的简化方法 - 4个核心消息类型
    # ============================================================================

    # 核心4个方法 - 对应4个消息类型
    def processing(self, message: str, graph_nodes: List[str] = None, **kwargs):
        """进度处理 - 支持百分比计算"""
        self.step_start_time = time.time()
        if self.config.is_node_streaming_enabled(self.node_name):
            progress = self._calculate_progress_percentage(graph_nodes)
            self._send_message(MessageType.PROCESSING, message, progress=progress, **kwargs)

    def content(self, content: str, **kwargs):
        """内容输出"""
        if self.config.is_node_streaming_enabled(self.node_name):
            self._send_message(MessageType.CONTENT, content, **kwargs)

    def thinking(self, thought: str, **kwargs):
        """思考过程（包含planning）"""
        if self.config.is_node_streaming_enabled(self.node_name):
            self._send_message(MessageType.THINKING, thought, **kwargs)

    def interrupt(self, description: str, **kwargs):
        """中断处理"""
        self._send_message(MessageType.INTERRUPT, description, **kwargs)


    
    def _send_aggregated_result(self, summary: str, **kwargs):
        """发送节点汇总结果 - 用于非流式节点"""
        message = {
            "message_type": "node_complete",  # 新的消息类型
            "content": summary,
            "node": self.node_name,
            "timestamp": time.time(),
            "duration": kwargs.get("duration", 0),
            "aggregated": True,  # 标识这是汇总结果
            **kwargs
        }
        
        if self.config.should_show_timing():
            message["timestamp"] = time.time()
            message["duration"] = kwargs.get("duration", 0)
        
        self.writer(message)
    

    
    # 工具相关方法 - 扁平化版本
    def tool_call(self, tool_name: str, tool_args: Dict[str, Any], custom_content: Optional[str] = None):
        # 使用自定义内容或简化格式
        if custom_content:
            content = custom_content
        else:
            content = f"调用了 {tool_name} 工具"

        self._send_message(
            MessageType.TOOL_CALL,
            content,
            tool_name=tool_name,
            args=tool_args
        )
    
    def tool_result(self, tool_name: str, result: str):
        """工具执行结果 - 扁平化版本"""
        clean_result = self.flat_processor._clean_tool_result(result)
        
        self._send_message(
            MessageType.TOOL_RESULT,
            clean_result,
            tool_name=tool_name,
            length=len(result)
        )
    
    
    # 结果和错误方法  
    def final_result(self, result: str, execution_summary: Dict[str, Any]):
        """最终结果"""
        self._send_message(
            MessageType.FINAL_RESULT,
            result,
            execution_summary=execution_summary,
            is_final=True
        )
    
    def error(self, error_msg: str, error_type: str = "GeneralError"):
        """错误信息"""
        self._send_message(MessageType.ERROR, error_msg, error_type=error_type)



    def interrupt_response(self, response: str, approved: bool, interrupt_id: Optional[str] = None):
        """用户对中断的响应"""
        self._send_message(
            MessageType.INTERRUPT_RESPONSE,
            response,
            approved=approved,
            interrupt_id=interrupt_id
        )

    def interrupt_resolved(self, result: str, interrupt_id: Optional[str] = None):
        """中断已解决"""
        self._send_message(
            MessageType.INTERRUPT_RESOLVED,
            result,
            interrupt_id=interrupt_id,
            status="resolved"
        )
    
class AgentWorkflowProcessor:
    """Agent工作流程处理器 - 使用扁平化数据格式"""

    def __init__(self, writer: StreamWriter, custom_templates: Optional[Dict[str, str]] = None, config: Optional[WriterConfig] = None):
        self.writer = writer
        self.flat_processor = FlatDataProcessor()
        self.chunk_count = 0
        self.current_step = ""
        self.sections_completed = []
        self.research_findings = []
        self.final_output = {}
        # 添加去重缓存 - 基于内容hash去重reasoning消息
        self.processed_reasoning = set()
        # 添加中断去重缓存 - 避免同一个中断被多次处理
        self.processed_interrupts = set()
        self.config = config or get_writer_config()

        # 标记未使用的参数以维持向后兼容性
        _ = custom_templates
    
    def process_chunk(self, chunk: Any) -> Dict[str, Any]:
        """统一智能处理工作流程数据 - 扁平化+原有逻辑兼容+中断处理"""
        self.chunk_count += 1

        # 首先检查是否是中断数据
        interrupt_result = self._handle_interrupt_chunk(chunk)
        if interrupt_result:
            return interrupt_result

        # 首先尝试使用扁平化处理器（仅处理custom消息）
        flat_data = self.flat_processor.flatten_chunk(chunk)
        if flat_data:
            self._handle_flat_data(flat_data)
            return {"chunk_count": self.chunk_count, "current_step": self.current_step, "flat_data": flat_data}

        # 处理子图和其他格式的数据 - 保留原有逻辑
        if isinstance(chunk, tuple):
            if len(chunk) == 3:
                # 嵌套子图格式: (('subgraph_id',), 'messages'/'updates', data)
                subgraph_ids, chunk_type, chunk_data = chunk

                # 检查是否包含中断信息
                if chunk_type == 'updates' and isinstance(chunk_data, dict):
                    interrupt_handled = self._check_for_interrupts_in_updates(chunk_data, subgraph_ids)
                    if interrupt_handled:
                        return {"chunk_count": self.chunk_count, "current_step": self.current_step, "interrupt_handled": True}

                # 提取agent信息
                agent_name = self._extract_agent_name(subgraph_ids)
                agent_hierarchy = self._extract_agent_hierarchy(subgraph_ids)
                return self._process_subgraph_chunk(chunk_type, chunk_data, agent_name, agent_hierarchy)
            elif len(chunk) == 2:
                # 普通格式: ('messages'/'updates', data) 或 ('custom', data)
                chunk_type, chunk_data = chunk
                if chunk_type == 'custom':
                    # custom已经被扁平化处理器处理了
                    return self._process_normal_chunk(chunk_type, chunk_data)
                else:
                    # messages/updates需要特殊处理
                    return self._process_normal_chunk(chunk_type, chunk_data)
        elif isinstance(chunk, dict):
            # 直接的数据格式
            return self._process_custom_data(chunk)

        return {"chunk_count": self.chunk_count, "current_step": self.current_step}
    
    def _extract_agent_name(self, subgraph_ids: tuple) -> str:
        """从subgraph_ids中提取最具体的agent名称"""
        if not isinstance(subgraph_ids, tuple) or not subgraph_ids:
            return "unknown"
        
        agent_names = []
        # 从tuple中提取所有agent名称，建立层级
        # 格式如: ('content_creation:xxx', 'writing:yyy') → ['content_creation', 'writing']
        for subgraph_id in subgraph_ids:
            if isinstance(subgraph_id, str) and ':' in subgraph_id:
                parts = subgraph_id.split(':')
                if len(parts) >= 2:
                    agent_name = parts[0]  # 取冒号前的部分
                    # 验证是否为已知的agent类型
                    if agent_name in ['research', 'writing', 'content_creation', 'tools', 'intelligent_supervisor']:
                        agent_names.append(agent_name)
        
        # 返回最后一个（最具体的）agent，例如writing比content_creation更具体
        return agent_names[-1] if agent_names else "unknown"
    
    def _extract_agent_hierarchy(self, subgraph_ids: tuple) -> List[str]:
        """从subgraph_ids中提取完整的agent层级"""
        if not isinstance(subgraph_ids, tuple) or not subgraph_ids:
            return ["unknown"]
        
        agent_names = []
        # 从tuple中提取所有agent名称，建立层级
        for subgraph_id in subgraph_ids:
            if isinstance(subgraph_id, str) and ':' in subgraph_id:
                parts = subgraph_id.split(':')
                if len(parts) >= 2:
                    agent_name = parts[0]
                    # 验证是否为已知的agent类型
                    if agent_name in ['research', 'writing', 'content_creation', 'tools', 'intelligent_supervisor']:
                        agent_names.append(agent_name)
        
        return agent_names if agent_names else ["unknown"]
    
    # ========================================================================
    # 简化工具处理方法 - 使用统一格式
    # ========================================================================

    def _generate_simple_tool_message(self, tool_name: str) -> str:
        """生成简化的工具调用消息"""
        return f"调用了 {tool_name} 工具"
    
    def _create_agent_message(self, message_type: str, content: str, agent_name: Optional[str] = None,
                             agent_hierarchy: Optional[List[str]] = None, **extras) -> Dict[str, Any]:
        """统一创建带agent信息的消息"""
        message = {
            "message_type": message_type,
            "content": content,
            "node": self.writer.node_name
        }

        # 根据配置决定是否添加时间信息
        if self.config.should_show_timing():
            message["timestamp"] = time.time()
            message["duration"] = round(time.time() - self.writer.step_start_time, 2)

        # 始终添加agent信息（这是核心标识）
        if agent_name:
            message["agent"] = agent_name

        # 根据配置决定是否添加agent层级信息
        if agent_hierarchy and self.config.should_show_agent_hierarchy():
            message["agent_hierarchy"] = agent_hierarchy

        # 添加额外字段
        for key, value in extras.items():
            if key not in message:  # 避免覆盖核心字段
                message[key] = value

        return message

    def _send_agent_message(self, message_type: str, content: str, agent_name: Optional[str] = None,
                           agent_hierarchy: Optional[List[str]] = None, **extras):
        """统一发送带agent信息的消息"""
        message = self._create_agent_message(message_type, content, agent_name, agent_hierarchy, **extras)
        self.writer.writer(message)
    
    def _handle_flat_data(self, flat_data: Dict[str, Any]):
        """处理扁平化数据 - 直接输出扁平格式"""
        message_type = flat_data.get('message_type', '')

        # 直接输出扁平化数据，不再重复处理
        # 这是最简洁的方式 - 扁平数据直接传给前端
        if message_type in ['tool_call', 'tool_result', 'content', 'thinking', 'reasoning']:
            # 数据已经是扁平格式，可以直接使用
            pass

    def _handle_interrupt_chunk(self, chunk: Any) -> Optional[Dict[str, Any]]:
        """处理中断chunk数据"""
        # 检查是否是中断格式: (('subgraph_id',), 'updates', {'__interrupt__': (Interrupt(...),)})
        if isinstance(chunk, tuple) and len(chunk) == 3:
            subgraph_ids, chunk_type, chunk_data = chunk

            if chunk_type == 'updates' and isinstance(chunk_data, dict):
                if '__interrupt__' in chunk_data:
                    interrupt_data = chunk_data['__interrupt__']
                    if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                        interrupt_obj = interrupt_data[0]
                        return self._process_interrupt_object(interrupt_obj, subgraph_ids)

        # 检查是否是主图的中断格式: ('updates', {'__interrupt__': (Interrupt(...),)})
        elif isinstance(chunk, tuple) and len(chunk) == 2:
            chunk_type, chunk_data = chunk

            if chunk_type == 'updates' and isinstance(chunk_data, dict):
                if '__interrupt__' in chunk_data:
                    interrupt_data = chunk_data['__interrupt__']
                    if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                        interrupt_obj = interrupt_data[0]
                        # 主图中断，使用空的subgraph_ids
                        return self._process_interrupt_object(interrupt_obj, ())

        # 检查是否是直接的中断字典格式: {'__interrupt__': (Interrupt(...),)}
        elif isinstance(chunk, dict) and '__interrupt__' in chunk:
            interrupt_data = chunk['__interrupt__']
            if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                interrupt_obj = interrupt_data[0]
                # 主图中断，使用空的subgraph_ids
                return self._process_interrupt_object(interrupt_obj, ())

        return None

    def _process_interrupt_object(self, interrupt_obj: Any, subgraph_ids: tuple) -> Dict[str, Any]:
        """处理中断对象"""
        try:
            # 提取中断信息
            interrupt_value = getattr(interrupt_obj, 'value', {})
            interrupt_id = getattr(interrupt_obj, 'id', 'unknown')

            # 如果已处理过相同的中断，跳过
            if interrupt_id in self.processed_interrupts:
                return {"chunk_count": self.chunk_count, "current_step": self.current_step, "interrupt_skipped": True}

            # 添加到已处理集合
            self.processed_interrupts.add(interrupt_id)

            if isinstance(interrupt_value, dict):
                action_request = interrupt_value.get('action_request', {})
                config = interrupt_value.get('config', {})
                description = interrupt_value.get('description', '')

                if action_request:
                    action = action_request.get('action', '')
                    args = action_request.get('args', {})

                    # 提取agent信息
                    agent_name = self._extract_agent_name(subgraph_ids)

                    # 如果是主图中断，使用特殊的节点名
                    if not subgraph_ids:
                        # 主图中断，从当前节点名获取
                        node_name = getattr(self, 'current_node', 'main_graph')
                    else:
                        node_name = agent_name

                    # 发送中断请求消息
                    self._send_agent_message(
                        "interrupt_request",
                        description,
                        node_name,
                        action=action,
                        args=args,
                        interrupt_id=interrupt_id,
                        config=config
                    )

                    return {
                        "chunk_count": self.chunk_count,
                        "current_step": "interrupt_waiting",
                        "interrupt_processed": True,
                        "interrupt_id": interrupt_id,
                        "action": action,
                        "args": args
                    }

        except Exception as e:
            self.writer.error(f"处理中断时出错: {str(e)}", "InterruptProcessingError")

        return {"chunk_count": self.chunk_count, "current_step": self.current_step}

    def _check_for_interrupts_in_updates(self, updates_data: Dict[str, Any], subgraph_ids: tuple) -> bool:
        """检查updates数据中是否包含中断信息"""
        if '__interrupt__' in updates_data:
            interrupt_data = updates_data['__interrupt__']
            if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                interrupt_obj = interrupt_data[0]
                interrupt_id = getattr(interrupt_obj, 'id', None)

                # 如果已处理过，直接返回True表示已处理，避免后续处理
                if interrupt_id and interrupt_id in self.processed_interrupts:
                    return True

                self._process_interrupt_object(interrupt_obj, subgraph_ids)
                return True
        return False
    
    def _process_subgraph_chunk(self, chunk_type: str, chunk_data: Any, agent_name: str = "unknown", agent_hierarchy: Optional[List[str]] = None) -> Dict[str, Any]:
        """处理子图的嵌套流式输出"""
        # 检查是否应该处理该子图节点
        if not self.config.should_process_subgraph_node(agent_name):
            return {"chunk_count": self.chunk_count, "current_step": self.current_step, "filtered_node": agent_name}

        # 检查是否应该处理该Agent
        if not self.config.should_process_agent(agent_name):
            return {"chunk_count": self.chunk_count, "current_step": self.current_step, "filtered_agent": agent_name}

        if chunk_type == "messages":
            # 处理子图的messages格式
            if isinstance(chunk_data, tuple) and len(chunk_data) == 2:
                # 格式: (AIMessageChunk, metadata)
                message, _ = chunk_data

                # 检查是否是AIMessageChunk并直接输出内容
                if hasattr(message, '__class__') and type(message).__name__ == "AIMessageChunk":
                    if hasattr(message, 'content') and message.content:
                        content = str(message.content)
                        if content and content.strip():
                            # 发送带agent信息的content消息
                            self._send_agent_content(content, agent_name, agent_hierarchy)
                            # 对于AIMessageChunk，不再继续调用_process_message_chunk避免重复
                            return {"chunk_count": self.chunk_count, "current_step": self.current_step}

                # 继续使用原有逻辑处理其他类型
                self._process_message_chunk(message)
            else:
                # 直接的message格式
                self._process_message_chunk(chunk_data)
        elif chunk_type == "updates" and isinstance(chunk_data, dict):
            # 对于updates类型，也传递agent信息
            self._process_content_updates_with_agent(chunk_data, agent_name)

        return {"chunk_count": self.chunk_count, "current_step": self.current_step}

    def _send_agent_content(self, content: str, agent_name: str, agent_hierarchy: Optional[List[str]] = None):
        """发送带agent信息的content消息"""
        # 检查是否应该处理该消息类型
        if not self.config.should_process_message_type("content"):
            return

        message = {
            "message_type": "content",
            "content": content,
            "node": self.writer.node_name,
            "agent": agent_name,  # 最具体的agent
            "length": len(content),
            "chunk_index": 0
        }

        # 根据配置决定是否添加元数据
        if self.config.should_show_timing():
            message["timestamp"] = time.time()
            message["duration"] = round(time.time() - self.writer.step_start_time, 2)

        if self.config.should_show_agent_hierarchy():
            message["agent_hierarchy"] = agent_hierarchy or [agent_name]  # 完整层级

        self.writer.writer(message)
    
    def _process_content_updates_with_agent(self, updates_data: Dict[str, Any], agent_name: str):
        """处理带agent信息的内容更新"""
        for node_name, node_data in updates_data.items():
            if not isinstance(node_data, dict):
                continue
            
            # 检测Agent消息中的工具调用 - 重要：捕获工具使用过程
            if "messages" in node_data:
                messages = node_data["messages"]
                # 处理messages
                if isinstance(messages, list):
                    for message in messages:
                        # 处理单个消息，传递agent信息
                        self._process_agent_message_with_agent(message, node_name, agent_name)
            
            # 其他处理逻辑保持不变...
            # 检测到新章节完成
            if "sections" in node_data:
                sections = node_data["sections"]
                if isinstance(sections, list):
                    for section in sections:
                        if isinstance(section, dict) and section.get("title"):
                            title = section["title"]
                            word_count = section.get("word_count", 0)
                            if title not in [s.get("title") for s in self.sections_completed]:
                                self.sections_completed.append(section)
                                # 在消息中添加agent信息
                                message = {
                                    "message_type": "content_complete",
                                    "content": f"完成章节: {title}",
                                    "node": self.writer.node_name,
                                    "agent": agent_name,
                                    "timestamp": time.time(),
                                    "duration": round(time.time() - self.writer.step_start_time, 2),
                                    "word_count": word_count,
                                    "section_title": title
                                }
                                self.writer.writer(message)
            
            # 检测到新的研究发现
            if "research_results" in node_data:
                research_data = node_data["research_results"]
                if isinstance(research_data, dict):
                    for research in research_data.values():
                        if isinstance(research, dict) and research.get("title"):
                            title = research["title"]
                            if title not in [r.get("title") for r in self.research_findings]:
                                self.research_findings.append(research)
                                # 在消息中添加agent信息
                                message = {
                                    "message_type": "step_progress",
                                    "content": f"发现研究资料: {title}",
                                    "node": self.writer.node_name,
                                    "agent": agent_name,
                                    "timestamp": time.time(),
                                    "duration": round(time.time() - self.writer.step_start_time, 2),
                                    "progress": 0,
                                    "research_title": title
                                }
                                self.writer.writer(message)
            
            # 检测到最终报告
            if "final_report" in node_data:
                self.final_output = node_data["final_report"]
                total_words = self.final_output.get("total_words", 0)
                # 在消息中添加agent信息
                message = {
                    "message_type": "reasoning",
                    "content": f"整合所有内容，生成最终报告 (总字数: {total_words})",
                    "node": self.writer.node_name,
                    "agent": agent_name,
                    "timestamp": time.time(),
                    "duration": round(time.time() - self.writer.step_start_time, 2)
                }
                self.writer.writer(message)
    
    def _process_normal_chunk(self, chunk_type: str, chunk_data: Any) -> Dict[str, Any]:
        """处理普通Agent的流式输出"""
        if chunk_type == "messages":
            self._process_message_chunk(chunk_data)
        elif chunk_type == "updates" and isinstance(chunk_data, dict):
            self._process_content_updates(chunk_data)
        elif chunk_type == "custom" and isinstance(chunk_data, dict):
            self._process_custom_data(chunk_data)
        
        return {"chunk_count": self.chunk_count, "current_step": self.current_step}
    
    def _process_custom_data(self, custom_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理自定义消息数据 - 与FlatDataProcessor配合，处理未被扁平化的数据"""
        # Custom消息优先由FlatDataProcessor处理并扁平化
        # 这里处理那些没有被扁平化处理器捕获的数据
        
        message_type = custom_data.get("message_type", "")
        
        # 针对reasoning消息进行去重处理（保持原有逻辑）
        if message_type == "reasoning":
            content = custom_data.get("content", "")
            metadata = custom_data.get("metadata", {})
            
            # 创建去重key，排除timestamp等时间相关字段
            dedup_key = (
                content,
                metadata.get("node_name", "") if metadata else custom_data.get("node", ""),
                int(metadata.get("step_duration", 0)) if metadata else int(custom_data.get("duration", 0))
            )
            
            # 如果已处理过相同内容，跳过
            if dedup_key in self.processed_reasoning:
                return {"chunk_count": self.chunk_count, "current_step": self.current_step}
            
            self.processed_reasoning.add(dedup_key)
        
        # 只传递用户关心的工作流程消息
        if message_type in ["step_start", "step_progress", "step_complete", 
                           "tool_call", "tool_result", "thinking", "reasoning",
                           "content", "content_complete", "final_result"]:
            
            content = custom_data.get("content", "")
            
            # 处理扁平化格式和原始格式
            if 'metadata' in custom_data:
                # 原始格式，有metadata嵌套
                metadata = custom_data.get("metadata", {})
                
                if message_type == "step_start":
                    self.writer.processing(content)
                elif message_type == "step_progress":
                    self.writer.processing(content, **metadata)
                elif message_type == "step_complete":
                    self.writer.processing(content, **metadata)
                elif message_type == "thinking":
                    self.writer.thinking(content)
                elif message_type == "reasoning":
                    self.writer.thinking(content, **metadata)
                elif message_type == "tool_call":
                    tool_name = metadata.get("tool_name", "")
                    tool_args = metadata.get("tool_args", {})
                    self.writer.tool_call(tool_name, tool_args)
                elif message_type == "tool_result":
                    tool_name = metadata.get("tool_name", "")
                    self.writer.tool_result(tool_name, content)
                elif message_type == "content":
                    self.writer.content(content, chunk_index=metadata.get("chunk_index", 0), **metadata)
                elif message_type == "content_complete":
                    self.writer.content(content, **metadata)
                elif message_type == "final_result":
                    execution_summary = metadata.get("execution_summary", {})
                    self.writer.final_result(content, execution_summary)
            else:
                # 扁平化格式，数据已在顶层 - 这些应该已经被FlatDataProcessor处理了
                # 这里不需要重复处理，直接跳过
                pass
        
        return {"chunk_count": self.chunk_count, "current_step": self.current_step}
    
    def _process_message_chunk(self, message: Any):
        """处理messages类型的chunk - 从AI消息中提取流式信息"""
        if not hasattr(message, '__class__'):
            return

        msg_type = type(message).__name__

        if msg_type in ["AIMessage", "AIMessageChunk"]:
            valid_tool_calls = []

            if hasattr(message, 'tool_calls') and message.tool_calls:
                valid_tool_calls.extend([tc for tc in message.tool_calls if tc.get('name')])

            if valid_tool_calls:
                for tool_call in valid_tool_calls:
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('args', {})

                    if tool_name and isinstance(tool_args, dict):
                        self.writer.tool_call(tool_name, tool_args)
                        tool_message = self._generate_simple_tool_message(tool_name)
                        self.writer.thinking(tool_message)
            
            # 检测AI回复内容
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                
                # 对于AIMessageChunk，内容通常是流式的小片段
                if msg_type == "AIMessageChunk":
                    # 流式内容片段
                    if content and content.strip():
                        self.writer.content(content)
                else:
                    # 完整的AI消息
                    if len(content) > 300:
                        preview = content[:500] + "..." if len(content) > 500 else content
                        self.writer.content(preview)
                    elif len(content) > 50:
                        self.writer.thinking(content)
                    
        elif msg_type == "ToolMessage":
            # 检测工具结果 - 使用统一处理方法
            if hasattr(message, 'content') and message.content:
                tool_name = getattr(message, 'name', 'unknown_tool')
                result = str(message.content)
                
                # 使用统一的工具结果处理方法
                self.writer.tool_result(tool_name, result)

                # 使用简化的工具完成消息
                completion_message = f"{tool_name} 工具执行完成"
                self.writer.thinking(completion_message)
    
    # 删除_process_workflow_step - 该逻辑已被FlatDataProcessor处理
    
    def _process_content_updates(self, updates_data: Dict[str, Any]):
        """处理内容更新 - 恢复完整逻辑处理子图数据"""
        # 首先检查是否包含中断信息
        if '__interrupt__' in updates_data:
            interrupt_data = updates_data['__interrupt__']
            if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                interrupt_obj = interrupt_data[0]
                # 主图中断，使用空的subgraph_ids
                self._process_interrupt_object(interrupt_obj, ())
                return

        for node_name, node_data in updates_data.items():
            if not isinstance(node_data, dict):
                continue
            
            # 处理节点数据 - 恢复原有完整逻辑
            
            # 检测Agent消息中的工具调用 - 重要：捕获工具使用过程
            if "messages" in node_data:
                messages = node_data["messages"]
                # 处理messages
                if isinstance(messages, list):
                    for message in messages:
                        # 处理单个消息
                        self._process_agent_message(message, node_name)
            
            # 检测到新章节完成
            if "sections" in node_data:
                sections = node_data["sections"]
                if isinstance(sections, list):
                    for section in sections:
                        if isinstance(section, dict) and section.get("title"):
                            title = section["title"]
                            word_count = section.get("word_count", 0)
                            if title not in [s.get("title") for s in self.sections_completed]:
                                self.sections_completed.append(section)
                                self.writer.content(
                                    f"完成章节: {title}",
                                    word_count=word_count,
                                    section_title=title
                                )
            
            # 检测到新的研究发现
            if "research_results" in node_data:
                research_data = node_data["research_results"]
                if isinstance(research_data, dict):
                    for research in research_data.values():
                        if isinstance(research, dict) and research.get("title"):
                            title = research["title"]
                            if title not in [r.get("title") for r in self.research_findings]:
                                self.research_findings.append(research)
                                self.writer.processing(
                                    f"发现研究资料: {title}",
                                    research_title=title
                                )
            
            # 检测到最终报告
            if "final_report" in node_data:
                self.final_output = node_data["final_report"]
                _ = self.final_output.get("total_words", 0)
    
    def _process_agent_message(self, message: Any, source_node: str):
        """处理Agent消息，检测工具调用 - 恢复完整逻辑处理子图中的工具调用"""
        _ = source_node
        if not hasattr(message, '__class__'):
            return

        msg_type = type(message).__name__

        if msg_type in ["AIMessage", "AIMessageChunk"]:
            # 初始化工具调用列表
            valid_tool_calls = []

            # 处理有效的 tool_calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                valid_tool_calls.extend([tc for tc in message.tool_calls if tc.get('name')])

            # 处理工具调用
            if valid_tool_calls:
                for tool_call in valid_tool_calls:
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('args', {})

                    # 只有在工具名称和参数都存在时才处理
                    if tool_name and isinstance(tool_args, dict):
                        self.writer.tool_call(tool_name, tool_args)
                        tool_message = self._generate_simple_tool_message(tool_name)
                        self.writer.thinking(tool_message)
            
            # 检测AI回复内容
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                
                # 对于AIMessageChunk，内容通常是流式的小片段
                if msg_type == "AIMessageChunk":
                    # 流式内容片段 - 直接显示
                    if content and content.strip():
                        self.writer.content(content)
                else:
                    # 完整的AI消息
                    if len(content) > 300:
                        self.writer.content(content[:500] + "..." if len(content) > 500 else content)
                    elif len(content) > 50:
                        self.writer.thinking(content)
                    
        elif msg_type == "ToolMessage":
            # 检测工具结果 - 展示工具返回的内容
            if hasattr(message, 'content') and message.content:
                tool_name = getattr(message, 'name', 'unknown_tool')
                result = str(message.content)
                
                # 使用统一的工具结果处理方法
                self.writer.tool_result(tool_name, result)

                # 使用简化的工具完成消息
                completion_message = f"{tool_name} 工具执行完成"
                self.writer.thinking(completion_message)
    
    def _process_agent_message_with_agent(self, message: Any, source_node: str, agent_name: str):
        """处理Agent消息，检测工具调用 - 带agent信息版本"""
        _ = source_node
        if not hasattr(message, '__class__'):
            return

        msg_type = type(message).__name__

        if msg_type in ["AIMessage", "AIMessageChunk"]:
            valid_tool_calls = []

            if hasattr(message, 'tool_calls') and message.tool_calls:
                valid_tool_calls.extend([tc for tc in message.tool_calls if tc.get('name')])

            if valid_tool_calls:
                for tool_call in valid_tool_calls:
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('args', {})

                    if tool_name and isinstance(tool_args, dict):
                        self._send_agent_message(
                            "tool_call", "", agent_name,
                            tool_name=tool_name, args=tool_args
                        )
                        tool_message = self._generate_simple_tool_message(tool_name)
                        self._send_agent_message("thinking", tool_message, agent_name)
            
            # 检测AI回复内容
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                
                # 对于AIMessageChunk，内容通常是流式的小片段
                if msg_type == "AIMessageChunk":
                    # 流式内容片段 - 直接显示
                    if content and content.strip():
                        self._send_agent_message("content", content, agent_name, 
                                               length=len(content), chunk_index=0)
                else:
                    # 完整的AI消息
                    if len(content) > 300:
                        preview_content = content[:500] + "..." if len(content) > 500 else content
                        self._send_agent_message("content", preview_content, agent_name,
                                               length=len(content), chunk_index=0)
                    elif len(content) > 50:
                        self._send_agent_message("reasoning", content, agent_name)
                    
        elif msg_type == "ToolMessage":
            # 检测工具结果 - 展示工具返回的内容
            if hasattr(message, 'content') and message.content:
                tool_name = getattr(message, 'name', 'unknown_tool')
                result = str(message.content)
                
                # 使用统一的工具结果处理方法
                self._send_agent_message("tool_result", result, agent_name,
                                        tool_name=tool_name, length=len(result))

                # 使用简化的工具完成消息
                completion_message = f"{tool_name} 工具执行完成"
                self._send_agent_message("thinking", completion_message, agent_name)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取工作总结"""
        return {
            "total_chunks_processed": self.chunk_count,
            "sections_completed": len(self.sections_completed),
            "research_findings": len(self.research_findings),
            "sections": self.sections_completed,
            "final_output": self.final_output
        }

def create_stream_writer(node_name: str, agent_name: str = "", custom_templates: Optional[Dict[str, str]] = None, config: Optional[WriterConfig] = None) -> StreamWriter:
    """创建扁平化流式writer"""
    return StreamWriter(node_name, agent_name, custom_templates, config)

def create_workflow_processor(node_name: str, agent_name: str = "", custom_templates: Optional[Dict[str, str]] = None, config: Optional[WriterConfig] = None) -> AgentWorkflowProcessor:
    """创建扁平化Agent工作流程处理器"""
    writer = create_stream_writer(node_name, agent_name, custom_templates, config)
    return AgentWorkflowProcessor(writer, custom_templates, config)

def create_flat_processor(custom_templates: Optional[Dict[str, str]] = None) -> FlatDataProcessor:
    """创建纯扁平化数据处理器（无writer输出）"""
    _ = custom_templates  # 保持向后兼容性
    return FlatDataProcessor()

def create_agent_stream_collector(node_name: str, agent_name: str = "", custom_templates: Optional[Dict[str, str]] = None):
    """创建简化的Agent流式输出收集器"""
    writer = create_stream_writer(node_name, agent_name, custom_templates)
    return AgentStreamCollector(writer, custom_templates)

# ============================================================================
# 中断处理器 - 处理LangGraph中断
# ============================================================================

class InterruptHandler:
    """LangGraph中断处理器"""

    def __init__(self, writer: StreamWriter):
        self.writer = writer
        self.pending_interrupts = {}  # interrupt_id -> interrupt_info

    def handle_interrupt_request(self, interrupt_id: str, action: str, args: dict, description: str, config: dict = None):
        """处理中断请求"""
        # 存储中断信息
        self.pending_interrupts[interrupt_id] = {
            'action': action,
            'args': args,
            'description': description,
            'config': config or {},
            'status': 'pending'
        }

        # 发送中断请求消息
        self.writer.interrupt(description, action=action, args=args, interrupt_id=interrupt_id)

    def handle_user_response(self, interrupt_id: str, response: str, approved: bool):
        """处理用户响应"""
        if interrupt_id not in self.pending_interrupts:
            self.writer.error(f"未找到中断ID: {interrupt_id}", "InterruptNotFound")
            return False

        interrupt_info = self.pending_interrupts[interrupt_id]
        interrupt_info['status'] = 'approved' if approved else 'rejected'
        interrupt_info['user_response'] = response

        # 发送响应消息
        self.writer.interrupt_response(response, approved, interrupt_id)

        if approved:
            # 执行被中断的操作
            result = self._execute_approved_action(interrupt_info)
            self.writer.interrupt_resolved(f"操作已执行: {result}", interrupt_id)
        else:
            self.writer.interrupt_resolved("操作已取消", interrupt_id)

        # 清理已处理的中断
        del self.pending_interrupts[interrupt_id]
        return True

    def _execute_approved_action(self, interrupt_info: dict) -> str:
        """执行被批准的操作"""
        action = interrupt_info.get('action', '')
        args = interrupt_info.get('args', {})

        # 这里可以根据action类型执行相应的操作
        # 对于web_search，返回搜索参数信息
        if action == 'web_search':
            query = args.get('query', '')
            return f"web_search(query='{query}')"

        return f"{action}({args})"

    def get_pending_interrupts(self) -> Dict[str, Any]:
        """获取待处理的中断"""
        return self.pending_interrupts.copy()

    def clear_interrupt(self, interrupt_id: str):
        """清理指定中断"""
        if interrupt_id in self.pending_interrupts:
            del self.pending_interrupts[interrupt_id]

def create_interrupt_handler(node_name: str, agent_name: str = "", config: Optional[WriterConfig] = None) -> InterruptHandler:
    """创建中断处理器"""
    writer = create_stream_writer(node_name, agent_name, None, config)
    return InterruptHandler(writer)

# ============================================================================
# Agent流式输出处理器 - 参考Multi-Agent-report设计
# ============================================================================

class AgentStreamCollector:
    """Agent流式输出收集器 - 简化版本，使用FlatDataProcessor"""
    
    def __init__(self, writer: StreamWriter, custom_templates: Optional[Dict[str, str]] = None):
        self.writer = writer
        self.flat_processor = FlatDataProcessor()
        self.full_response = ""
        self.tools_used = []
        self.chunk_count = 0

        # 标记未使用的参数以维持向后兼容性
        _ = custom_templates
    
    async def process_agent_stream(self, agent_stream, agent_name: str):
        """处理agent的混合流式输出 - 简化版本"""
        self.writer.thinking(f"开始分析和处理 {agent_name} 任务...")
        
        try:
            async for chunk in agent_stream:
                self.chunk_count += 1
                
                # 优先使用FlatDataProcessor处理
                flat_data = self.flat_processor.flatten_chunk(chunk)
                if flat_data:
                    # 如果是工具调用，记录工具名
                    if flat_data.get('message_type') == 'tool_call':
                        tool_name = flat_data.get('tool_name', '')
                        if tool_name and tool_name not in self.tools_used:
                            self.tools_used.append(tool_name)
                    
                    # 如果是内容流，累积响应
                    elif flat_data.get('message_type') == 'content':
                        content = flat_data.get('content', '')
                        if content:
                            self.full_response += content
                
            # 处理完成
            if self.full_response:
                self.writer.processing(
                    f"{agent_name}任务完成",
                    word_count=len(self.full_response.split()),
                    tools_used=self.tools_used,
                    total_chunks=self.chunk_count
                )
            
            return self.full_response
            
        except Exception as e:
            self.writer.error(f"{agent_name} 处理失败: {str(e)}", "StreamProcessingError")
            return ""