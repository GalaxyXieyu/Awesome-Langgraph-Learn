"""
标准化流式输出系统 - Interactive Deep Research版本
基于Multi-Agent-report的Writer设计，去除emoji表情，添加子图专用功能
提供统一的流式输出格式，便于前端渲染
"""

import time
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from langgraph.config import get_stream_writer


class MessageType(Enum):
    """Agent工作流程消息类型枚举"""
    # 步骤状态 - 当前在做什么
    STEP_START = "step_start"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETE = "step_complete"
    
    # 工具使用 - Agent使用工具的过程
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    
    # 思考过程 - Agent的推理
    THINKING = "thinking"
    REASONING = "reasoning"
    
    # 内容输出 - 实际产出
    CONTENT_STREAMING = "content_streaming"
    CONTENT_COMPLETE = "content_complete"
    
    # 结果状态
    FINAL_RESULT = "final_result"
    ERROR = "error"


class StreamWriter:
    """标准化流式输出Writer - 去除emoji版本"""
    
    def __init__(self, node_name: str = "", agent_name: str = ""):
        self.node_name = node_name
        self.agent_name = agent_name
        self.step_start_time = time.time()
        self.writer = self._get_safe_writer()
        
    def _get_safe_writer(self):
        """安全获取writer"""
        try:
            return get_stream_writer()
        except Exception:
            return lambda _: None
    
    def _send_message(self, msg_type: MessageType, content: str, **kwargs):
        """发送统一格式消息"""
        message = {
            "message_type": msg_type.value,
            "timestamp": time.time(),
            "node_name": self.node_name,
            "agent_name": self.agent_name,
            "content": content,
            "metadata": {
                "step_duration": time.time() - self.step_start_time,
                **kwargs
            }
        }
        self.writer(message)
    
    # 基础步骤方法
    def step_start(self, description: str):
        """步骤开始"""
        self.step_start_time = time.time()
        self._send_message(MessageType.STEP_START, description)
    
    def step_progress(self, status: str, progress: int, **kwargs):
        """步骤进度"""
        self._send_message(MessageType.STEP_PROGRESS, status, progress=progress, **kwargs)
    
    def step_complete(self, summary: str, **kwargs):
        """步骤完成"""
        calculated_duration = time.time() - self.step_start_time
        # 如果用户没有提供duration，使用计算的duration
        if "duration" not in kwargs:
            kwargs["duration"] = calculated_duration
        self._send_message(MessageType.STEP_COMPLETE, summary, **kwargs)
    
    # 思考过程方法
    def thinking(self, thought: str):
        """Agent思考过程"""
        self._send_message(MessageType.THINKING, thought)
    
    def reasoning(self, reasoning: str, **kwargs):
        """Agent推理分析"""
        self._send_message(MessageType.REASONING, reasoning, **kwargs)
    
    # 内容输出方法
    def content_streaming(self, content_chunk: str, chunk_index: int = 0):
        """流式内容输出"""
        self._send_message(
            MessageType.CONTENT_STREAMING,
            content_chunk,
            chunk_index=chunk_index,
            is_streaming=True
        )
    
    def content_complete(self, content_summary: str, **kwargs):
        """内容输出完成"""
        self._send_message(
            MessageType.CONTENT_COMPLETE,
            content_summary,
            **kwargs
        )
    
    # 工具相关方法
    def tool_call(self, tool_name: str, tool_args: Dict[str, Any]):
        """工具调用"""
        args_str = json.dumps(tool_args, ensure_ascii=False)
        content = f"调用 {tool_name} 工具"
        self._send_message(
            MessageType.TOOL_CALL,
            content,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_args_display=args_str
        )
    
    def tool_result(self, tool_name: str, result: str):
        """工具执行结果"""
        display_result = result[:300] + "..." if len(result) > 300 else result
        self._send_message(
            MessageType.TOOL_RESULT,
            f"{tool_name} 执行结果: {display_result}",
            tool_name=tool_name,
            full_result=result,
            result_length=len(result)
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
    


class AgentWorkflowProcessor:
    """Agent工作流程处理器 - 智能识别工作阶段"""
    
    def __init__(self, writer: StreamWriter):
        self.writer = writer
        self.chunk_count = 0
        self.current_step = ""
        self.sections_completed = []
        self.research_findings = []
        self.final_output = {}
        # 添加去重缓存 - 基于内容hash去重reasoning消息
        self.processed_reasoning = set()
    
    def process_chunk(self, chunk: Any) -> Dict[str, Any]:
        """统一智能处理工作流程数据 - 支持普通Agent和嵌套子图的流式输出"""
        self.chunk_count += 1
        
        # 处理不同格式的chunk数据
        if isinstance(chunk, tuple):
            if len(chunk) == 3:
                # 嵌套子图格式: (('subgraph_id',), 'messages'/'updates', data)
                _, chunk_type, chunk_data = chunk
                return self._process_subgraph_chunk(chunk_type, chunk_data)
            elif len(chunk) == 2:
                # 普通格式: ('messages'/'updates', data) 或 ('custom', data)
                chunk_type, chunk_data = chunk
                return self._process_normal_chunk(chunk_type, chunk_data)
        elif isinstance(chunk, dict):
            # 直接的数据格式 (custom消息等)
            return self._process_custom_data(chunk)
        
        return {"chunk_count": self.chunk_count, "current_step": self.current_step}
    
    def _process_subgraph_chunk(self, chunk_type: str, chunk_data: Any) -> Dict[str, Any]:
        """处理子图的嵌套流式输出"""
        if chunk_type == "messages":
            self._process_message_chunk(chunk_data)
        elif chunk_type == "updates" and isinstance(chunk_data, dict):
            self._process_content_updates(chunk_data)
        
        return {"chunk_count": self.chunk_count, "current_step": self.current_step}
    
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
        """处理自定义消息数据 - 包括step状态、reasoning等"""
        message_type = custom_data.get("message_type", "")
        
        # 针对reasoning消息进行去重处理
        if message_type == "reasoning":
            content = custom_data.get("content", "")
            metadata = custom_data.get("metadata", {})
            
            # 创建去重key，排除timestamp等时间相关字段
            dedup_key = (
                content,
                metadata.get("node_name", ""),
                metadata.get("agent_name", ""), 
                int(metadata.get("step_duration", 0))  # 取整数避免小数差异
            )
            
            # 如果已处理过相同内容，跳过
            if dedup_key in self.processed_reasoning:
                return {"chunk_count": self.chunk_count, "current_step": self.current_step}
            
            self.processed_reasoning.add(dedup_key)
        
        # 只传递用户关心的工作流程消息
        if message_type in ["step_start", "step_progress", "step_complete", 
                           "tool_call", "tool_result", "thinking", "reasoning",
                           "content_streaming", "content_complete", "final_result"]:
            # 直接传递给writer处理
            content = custom_data.get("content", "")
            metadata = custom_data.get("metadata", {})
            
            # 根据消息类型调用对应的writer方法
            if message_type == "step_start":
                self.writer.step_start(content)
            elif message_type == "step_progress":
                progress = metadata.get("progress", 0)
                self.writer.step_progress(content, progress, **metadata)
            elif message_type == "step_complete":
                self.writer.step_complete(content, **metadata)
            elif message_type == "thinking":
                self.writer.thinking(content)
            elif message_type == "reasoning":
                self.writer.reasoning(content, **metadata)
            elif message_type == "tool_call":
                tool_name = metadata.get("tool_name", "")
                tool_args = metadata.get("tool_args", {})
                self.writer.tool_call(tool_name, tool_args)
            elif message_type == "tool_result":
                tool_name = metadata.get("tool_name", "")
                self.writer.tool_result(tool_name, content)
            elif message_type == "content_streaming":
                self.writer.content_streaming(content, metadata.get("chunk_index", 0))
            elif message_type == "content_complete":
                self.writer.content_complete(content, **metadata)
            elif message_type == "final_result":
                execution_summary = metadata.get("execution_summary", {})
                self.writer.final_result(content, execution_summary)
        
        return {"chunk_count": self.chunk_count, "current_step": self.current_step}
    
    def _process_message_chunk(self, message: Any):
        """处理messages类型的chunk - 从AI消息中提取流式信息"""
        if not hasattr(message, '__class__'):
            return
            
        msg_type = type(message).__name__
        
        if msg_type == "AIMessage":
            # 检测工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', 'unknown_tool')
                    tool_args = tool_call.get('args', {})
                    
                    # 发送工具调用信息
                    self.writer.tool_call(tool_name, tool_args)
                    
                    # 根据工具类型提供用户友好的思考过程
                    if tool_name in ["advanced_web_search", "web_search_tool"]:
                        query = tool_args.get('query', '')
                        self.writer.thinking(f"搜索相关信息: {query}")
                    elif tool_name in ["multi_source_research", "trend_analysis_tool"]:
                        topic = tool_args.get('topic', '')
                        self.writer.thinking(f"进行深度研究: {topic}")
                    elif tool_name == "content_analyzer":
                        self.writer.thinking("分析内容质量")
                    elif tool_name in ["content_writer_tool", "enhanced_writer"]:
                        title = tool_args.get('title', '')
                        self.writer.thinking(f"开始生成内容: {title}")
                    else:
                        self.writer.thinking(f"调用{tool_name}工具")
            
            # 检测AI回复内容
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                # 如果内容较长，可能是生成的文章内容
                if len(content) > 300:
                    preview = content[:500] + "..." if len(content) > 500 else content
                    self.writer.content_streaming(preview)
                elif len(content) > 50:
                    self.writer.reasoning(content)
                    
        elif msg_type == "ToolMessage":
            # 检测工具结果
            if hasattr(message, 'content') and message.content:
                tool_name = getattr(message, 'name', 'unknown_tool')
                result = str(message.content)
                
                # 发送工具结果
                self.writer.tool_result(tool_name, result)
                
                # 根据工具类型提供反馈
                if tool_name in ["advanced_web_search", "web_search_tool"]:
                    self.writer.thinking("搜索完成，分析搜索结果的相关性")
                elif tool_name in ["multi_source_research", "trend_analysis_tool"]:
                    self.writer.thinking("研究分析完成，开始整理研究结果")
                elif tool_name in ["content_writer_tool", "enhanced_writer"]:
                    word_count = len(result.split()) if result else 0
                    self.writer.thinking(f"内容生成完成 ({word_count}词)，检查质量")
                else:
                    self.writer.thinking(f"{tool_name}工具执行完成")
    
    def _process_workflow_step(self, custom_data: Dict[str, Any]):
        """处理工作流程步骤"""
        step = custom_data.get("step", "")
        status = custom_data.get("status", "")
        progress = custom_data.get("progress", 0)
        
        # 智能映射工作步骤
        if step == "research":
            if progress == 0:
                self.writer.step_start("开始研究分析")
                self.current_step = "researching"
            elif progress == 100:
                self.writer.step_complete("研究分析完成")
            else:
                self.writer.step_progress("正在收集研究资料", progress)
                
        elif step == "writing":
            if progress == 0:
                self.writer.step_start("开始内容写作")
                self.current_step = "writing"
            elif progress == 100:
                self.writer.step_complete("内容写作完成")
            else:
                self.writer.step_progress("正在撰写内容", progress)
        
        elif step == "supervisor":
            self.writer.thinking("分析当前进度，决定下一步操作")
            self.current_step = "planning"
        
        # 处理流式写作内容
        if "streaming_content" in custom_data:
            content = custom_data["streaming_content"]
            self.writer.content_streaming(content)
    
    def _process_content_updates(self, updates_data: Dict[str, Any]):
        """处理内容更新 - 关注用户关心的产出"""
        for node_name, node_data in updates_data.items():
            if not isinstance(node_data, dict):
                continue
            
            # 处理节点数据
            
            # 检测Agent消息中的工具调用 - 重要：捕获工具使用过程
            if "messages" in node_data:
                messages = node_data["messages"]
                # 处理messages
                if isinstance(messages, list):
                    for i, message in enumerate(messages):
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
                                self.writer.content_complete(
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
                                self.writer.step_progress(
                                    f"发现研究资料: {title}",
                                    progress=None,
                                    research_title=title
                                )
            
            # 检测到最终报告
            if "final_report" in node_data:
                self.final_output = node_data["final_report"]
                total_words = self.final_output.get("total_words", 0)
                self.writer.reasoning(f"整合所有内容，生成最终报告 (总字数: {total_words})")
    
    def _process_agent_message(self, message: Any, source_node: str):
        """处理Agent消息，检测工具调用 - 核心功能：展示工具使用过程"""
        if not hasattr(message, '__class__'):
            return
            
        msg_type = type(message).__name__
        # 静默处理Agent消息
        
        if msg_type == "AIMessage":
            # 检测工具调用 - 这是用户最关心的部分
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # 检测到工具调用，处理每个工具
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', 'unknown_tool')
                    tool_args = tool_call.get('args', {})
                    
                    # 发送工具调用信息
                    self.writer.tool_call(tool_name, tool_args)
                    
                    # 根据工具类型提供用户友好的思考过程
                    if tool_name == "trend_analysis_tool":
                        topic = tool_args.get('topic', '')
                        self.writer.thinking(f"使用趋势分析工具研究: {topic}")
                    elif tool_name == "web_search_tool":
                        query = tool_args.get('query', '')
                        self.writer.thinking(f"搜索相关信息: {query}")
                    elif tool_name == "industry_data_tool":
                        industry = tool_args.get('industry', '')
                        self.writer.thinking(f"获取行业数据: {industry}")
                    elif tool_name == "get_research_context_tool":
                        query = tool_args.get('query', '')
                        self.writer.thinking(f"查询研究上下文: {query}")
                    elif tool_name == "advanced_web_search":
                        query = tool_args.get('query', '')
                        self.writer.thinking(f"高级搜索: {query}")
                    elif tool_name == "multi_source_research":
                        topic = tool_args.get('topic', '')
                        self.writer.thinking(f"多源研究: {topic}")
                    elif tool_name == "content_analyzer":
                        self.writer.thinking("分析内容质量")
                    elif tool_name == "content_writer_tool":
                        title = tool_args.get('title', '')
                        self.writer.thinking(f"开始生成内容: {title}")
                    elif tool_name == "enhanced_writer":
                        self.writer.thinking("使用高级写作工具生成内容")
                    else:
                        self.writer.thinking(f"调用{tool_name}工具")
            else:
                # AIMessage没有工具调用
                pass
            
            # 检测AI回复内容
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                # 如果内容较长，可能是生成的文章内容
                if len(content) > 300:
                    self.writer.content_streaming(content[:500] + "..." if len(content) > 500 else content)
                elif len(content) > 50:
                    self.writer.reasoning(content)
                    
        elif msg_type == "ToolMessage":
            # 检测工具结果 - 展示工具返回的内容
            if hasattr(message, 'content') and message.content:
                tool_name = getattr(message, 'name', 'unknown_tool')
                result = str(message.content)
                
                # 发送工具结果
                self.writer.tool_result(tool_name, result)
                
                # 根据工具类型提供反馈
                if tool_name == "trends_analysis_tool":
                    self.writer.thinking("趋势分析完成，开始整理研究结果")
                elif tool_name == "web_search_tool":
                    self.writer.thinking("搜索完成，分析搜索结果的相关性")
                elif tool_name in ["content_writer_tool", "enhanced_writer"]:
                    word_count = len(result.split()) if result else 0
                    self.writer.thinking(f"内容生成完成 ({word_count}词)，检查质量")
                else:
                    self.writer.thinking(f"{tool_name}工具执行完成")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取工作总结"""
        return {
            "total_chunks_processed": self.chunk_count,
            "sections_completed": len(self.sections_completed),
            "research_findings": len(self.research_findings),
            "sections": self.sections_completed,
            "final_output": self.final_output
        }


# ============================================================================
# 便捷函数
# ============================================================================

def create_stream_writer(node_name: str, agent_name: str = "") -> StreamWriter:
    """创建标准化流式writer"""
    return StreamWriter(node_name, agent_name)

def create_workflow_processor(node_name: str, agent_name: str = "") -> AgentWorkflowProcessor:
    """创建Agent工作流程处理器"""
    writer = create_stream_writer(node_name, agent_name)
    return AgentWorkflowProcessor(writer)

def create_agent_stream_collector(node_name: str, agent_name: str = ""):
    """创建Agent流式输出收集器"""
    writer = create_stream_writer(node_name, agent_name)
    return AgentStreamCollector(writer)


# ============================================================================
# 前端渲染辅助函数
# ============================================================================

def format_message_for_frontend(message_dict: Dict[str, Any]) -> Dict[str, Any]:
    """前端消息格式化 - 去除emoji版本"""
    msg_type = message_dict["message_type"] 
    content = message_dict["content"]
    metadata = message_dict.get("metadata", {})
    timestamp = message_dict.get("timestamp", time.time())
    
    # 基础格式化信息
    formatted = {
        "type": msg_type,
        "content": content,
        "timestamp": timestamp,
        "metadata": metadata
    }
    
    # 根据消息类型添加特定格式
    if msg_type == "step_start":
        formatted["display"] = f"开始: {content}"
        formatted["icon"] = "play"
        
    elif msg_type == "step_progress":
        progress = metadata.get("progress", 0)
        formatted["display"] = f"{content} ({progress}%)"
        formatted["progress"] = progress
        formatted["icon"] = "progress"
        
    elif msg_type == "step_complete":
        duration = metadata.get("duration", 0)
        formatted["display"] = f"完成: {content} ({duration:.1f}s)"
        formatted["icon"] = "check"
        
    elif msg_type == "thinking":
        formatted["display"] = f"思考: {content}"
        formatted["icon"] = "brain"
        
    elif msg_type == "reasoning":
        formatted["display"] = f"分析: {content}"
        formatted["icon"] = "lightbulb"
        
    elif msg_type == "tool_call":
        tool_name = metadata.get("tool_name", "")
        formatted["display"] = f"调用工具: {tool_name}"
        formatted["tool_name"] = tool_name
        formatted["icon"] = "tool"
        
    elif msg_type == "tool_result":
        tool_name = metadata.get("tool_name", "")
        result_length = metadata.get("result_length", 0)
        formatted["display"] = f"工具结果: {tool_name}"
        if result_length > 0:
            formatted["display"] += f" ({result_length}字符)"
        formatted["tool_name"] = tool_name
        formatted["result_length"] = result_length
        formatted["icon"] = "result"
        
    elif msg_type == "content_streaming":
        formatted["display"] = content
        formatted["icon"] = "edit"
        formatted["is_streaming"] = True
        
    elif msg_type == "content_complete":
        word_count = metadata.get("word_count", 0)
        formatted["display"] = f"完成: {content}"
        if word_count > 0:
            formatted["display"] += f" ({word_count}字)"
        formatted["word_count"] = word_count
        formatted["icon"] = "document"
        
    elif msg_type == "error":
        formatted["display"] = f"错误: {content}"
        formatted["icon"] = "error"
        formatted["level"] = "error"
        
    else:
        formatted["display"] = f"[{msg_type.upper()}] {content}"
        formatted["icon"] = "info"
    
    return formatted


def get_message_types_for_frontend() -> Dict[str, Dict[str, str]]:
    """获取所有消息类型的前端配置"""
    return {
        msg_type.value: {
            "name": msg_type.value,
            "description": f"消息类型: {msg_type.value}",
            "category": _get_message_category(msg_type)
        }
        for msg_type in MessageType
    }

def _get_message_category(msg_type: MessageType) -> str:
    """获取消息类型的分类"""
    if msg_type.value.startswith("step_"):
        return "step"
    elif msg_type.value.startswith("ai_"):
        return "ai"
    elif msg_type.value.startswith("tool_"):
        return "tool"
    elif msg_type.value.startswith("subgraph_"):
        return "subgraph"
    else:
        return "general"


# ============================================================================
# Agent流式输出处理器 - 参考Multi-Agent-report设计
# ============================================================================

class AgentStreamCollector:
    """
    Agent流式输出收集器
    参考Multi-Agent-report的Collector设计，专门处理Agent的复杂流式输出
    自动检测工具调用、AI消息、错误等
    """
    
    def __init__(self, writer: StreamWriter):
        self.writer = writer
        self.full_response = ""
        self.tools_used = []
        self.chunk_count = 0
    
    async def process_agent_stream(self, agent_stream, agent_name: str):
        """处理agent的混合流式输出"""
        self.writer.thinking(f"开始分析和处理 {agent_name} 任务...")
        
        try:
            async for chunk in agent_stream:
                await self._process_chunk(chunk)
                
            # 处理完成
            if self.full_response:
                self.writer.content_complete(
                    f"{agent_name}任务完成",
                    word_count=len(self.full_response.split()),
                    tools_used=self.tools_used,
                    total_chunks=self.chunk_count
                )
            
            return self.full_response
            
        except Exception as e:
            self.writer.error(f"{agent_name} 处理失败: {str(e)}", "StreamProcessingError")
            return ""
    
    async def _process_chunk(self, chunk):
        """处理单个chunk - 支持混合模式"""
        self.chunk_count += 1
        
        if isinstance(chunk, tuple) and len(chunk) == 2:
            # 混合模式: (mode, data)
            mode, data = chunk
            
            if mode == "messages":
                await self._process_message_chunk(data)
            elif mode == "updates":
                await self._process_update_chunk(data)
        else:
            # 纯messages模式: (message, metadata)
            await self._process_message_chunk(chunk)
    
    async def _process_message_chunk(self, data):
        """处理messages模式的数据"""
        if isinstance(data, tuple) and len(data) == 2:
            message, metadata = data
        else:
            message, metadata = data, {}
            
        msg_type = type(message).__name__
        
        if msg_type == "AIMessageChunk":
            await self._handle_ai_message_chunk(message)
        elif msg_type == "ToolMessage":
            await self._handle_tool_message(message)
    
    async def _process_update_chunk(self, data):
        """处理updates模式的数据 - 正确解析嵌套结构"""
        for node_name, node_data in data.items():
            if isinstance(node_data, dict):
                # 处理嵌套的messages - 关键：检测工具调用
                if "messages" in node_data:
                    messages = node_data["messages"]
                    if isinstance(messages, list):
                        for message in messages:
                            await self._process_update_message(message, node_name)
    
    async def _process_update_message(self, message, source_node: str):
        """处理updates中的单个消息"""
        msg_type = type(message).__name__
        
        if msg_type == "AIMessage":
            # 处理AI消息中的工具调用 - 这是关键功能！
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', 'unknown_tool')
                    tool_args = tool_call.get('args', {})
                    
                    # 发送工具调用信息
                    self.writer.tool_call(tool_name, tool_args)
                    self.tools_used.append(tool_name)
                    
                    # 特殊处理，提供更好的用户体验
                    if tool_name == "advanced_web_search":
                        query = tool_args.get('query', '')
                        self.writer.thinking(f"正在搜索相关信息: {query}")
                    elif tool_name == "multi_source_research":
                        topic = tool_args.get('topic', '')
                        self.writer.thinking(f"正在进行多源研究: {topic}")
                    elif tool_name == "content_analyzer":
                        self.writer.thinking(f"正在分析内容质量")
                    elif tool_name == "trend_analyzer":
                        self.writer.thinking(f"正在进行趋势分析")
                    else:
                        self.writer.thinking(f"正在调用 {tool_name} 工具")
            
            # 处理AI消息内容
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                if content.strip():
                    # 积累完整响应
                    self.full_response = content
                    
                    # 流式展示内容（截断显示）
                    preview = content[:200] + "..." if len(content) > 200 else content
                    self.writer.content_streaming(preview)
        
        elif msg_type == "ToolMessage":
            # 处理工具执行结果
            if hasattr(message, 'content') and message.content:
                result = str(message.content)
                tool_name = getattr(message, 'name', 'unknown_tool')
                
                # 发送工具结果
                self.writer.tool_result(tool_name, result)
                
                # 根据工具类型提供反馈
                if tool_name == "advanced_web_search":
                    self.writer.reasoning(f"搜索结果分析完成，获得有价值信息")
                elif tool_name == "multi_source_research": 
                    self.writer.reasoning(f"多源研究完成，数据收集充分")
                elif tool_name in ["content_analyzer", "trend_analyzer"]:
                    self.writer.reasoning(f"{tool_name}分析完成，开始整理结果")
                else:
                    self.writer.reasoning(f"{tool_name}工具执行完成")
    
    async def _handle_ai_message_chunk(self, message):
        """处理AI消息块 - 流式内容"""
        if hasattr(message, 'content') and message.content:
            content = str(message.content)
            if content.strip():
                self.full_response += content
                # 流式展示
                self.writer.content_streaming(content)
    
    async def _handle_tool_message(self, message):
        """处理工具消息"""
        if hasattr(message, 'content') and message.content:
            result = str(message.content)
            tool_name = getattr(message, 'name', 'unknown_tool')
            self.writer.tool_result(tool_name, result)