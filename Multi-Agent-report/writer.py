"""
LangGraph统一流式输出系统 - 最终版本
解决Agent输出复杂性，提供完美的前端渲染体验
"""

import time
import json
from typing import Dict, Any
from enum import Enum
from langgraph.config import get_stream_writer


class MessageType(Enum):
    """统一消息类型枚举"""
    STEP_START = "step_start"        # 🚀 步骤开始
    STEP_PROGRESS = "step_progress"  # ⏳ 步骤进度
    STEP_COMPLETE = "step_complete"  # ✅ 步骤完成
    AGENT_THINKING = "agent_thinking" # 🧠 Agent思考过程
    TOOL_CALL = "tool_call"          # 🔧 工具调用
    TOOL_RESULT = "tool_result"      # 📊 工具结果
    AI_STREAMING = "ai_streaming"    # 💬 AI流式回复
    AI_COMPLETE = "ai_complete"      # ✅ AI回复完成
    FINAL_RESULT = "final_result"    # 🎯 最终结果
    ERROR = "error"                  # ❌ 错误
    DEBUG = "debug"                  # 🔍 调试


class Writer:
    """统一所有LangGraph节点的输出格式"""
    
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
    
    def step_start(self, description: str):
        """步骤开始"""
        self.step_start_time = time.time()
        self._send_message(MessageType.STEP_START, description)
    
    def step_progress(self, status: str, progress: int, **kwargs):
        """步骤进度 - 支持额外参数"""
        self._send_message(MessageType.STEP_PROGRESS, status, progress=progress, **kwargs)
    
    def step_complete(self, summary: str, **kwargs):
        """步骤完成"""
        duration = time.time() - self.step_start_time
        self._send_message(MessageType.STEP_COMPLETE, summary, duration=duration, **kwargs)
    
    def agent_thinking(self, thought: str):
        """Agent思考过程 - 关键的用户体验功能"""
        self._send_message(MessageType.AGENT_THINKING, thought)
    
    def tool_call(self, tool_name: str, tool_args: Dict[str, Any]):
        """工具调用 - 让用户看到具体调用了什么工具"""
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
        """工具执行结果 - 让用户看到工具返回了什么"""
        # 截断过长的结果用于显示
        display_result = result[:300] + "..." if len(result) > 300 else result
        self._send_message(
            MessageType.TOOL_RESULT,
            f"{tool_name} 执行结果: {display_result}",
            tool_name=tool_name,
            full_result=result,
            result_length=len(result)
        )
    
    def ai_streaming(self, content_chunk: str, chunk_index: int = 0):
        """AI流式输出 - 打字机效果"""
        self._send_message(
            MessageType.AI_STREAMING,
            content_chunk,
            chunk_index=chunk_index,
            is_streaming=True
        )
    
    def ai_complete(self, full_response: str, **kwargs):
        """AI回复完成"""
        self._send_message(
            MessageType.AI_COMPLETE,
            full_response,
            response_length=len(full_response),
            **kwargs
        )
    
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
    
    def debug(self, debug_info: str, **kwargs):
        """调试信息"""
        self._send_message(MessageType.DEBUG, debug_info, **kwargs)


class Collector:
    """处理LangGraph混合流模式"""
    
    def __init__(self, writer: Writer):
        self.writer = writer
        self.full_response = ""
        self.tools_used = []
        self.chunk_count = 0
    
    async def process_agent_stream(self, agent_stream, agent_name: str):
        """处理agent的混合流式输出"""
        self.writer.agent_thinking(f"开始分析和处理 {agent_name} 任务...")
        
        try:
            async for chunk in agent_stream:
                await self._process_chunk(chunk)
                
            # 处理完成
            if self.full_response:
                self.writer.ai_complete(
                    self.full_response,
                    tools_used=self.tools_used,
                    total_chunks=self.chunk_count
                )
            
            return self.full_response
            
        except Exception as e:
            self.writer.error(f"{agent_name} 处理失败: {str(e)}", "StreamProcessingError")
            return ""
    
    async def _process_chunk(self, chunk):
        """处理单个chunk - 支持混合模式"""
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
                # 处理嵌套的messages
                if "messages" in node_data:
                    messages = node_data["messages"]
                    if isinstance(messages, list):
                        for message in messages:
                            await self._process_update_message(message, node_name)
                            
                # 处理其他有用的状态信息
                if "reasoning" in node_data:
                    self.writer.agent_thinking(f"[{node_name}] {node_data['reasoning']}")
    
    async def _process_update_message(self, message, source_node: str):
        """处理updates中的单个消息"""
        msg_type = type(message).__name__
        
        if msg_type == "AIMessage":
            # 处理AI消息中的工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', 'unknown_tool')
                    tool_args = tool_call.get('args', {})
                    
                    # 发送工具调用信息
                    self.writer.tool_call(tool_name, tool_args)
                    self.tools_used.append(tool_name)
                    
                    # 特殊处理，提供更好的用户体验
                    if tool_name == "calculator":
                        expr = tool_args.get('expression', '')
                        self.writer.agent_thinking(f"正在计算数学表达式: {expr}")
                    elif tool_name == "web_search":
                        query = tool_args.get('query', '')
                        self.writer.agent_thinking(f"正在搜索相关信息: {query}")
                    elif tool_name == "text_analyzer":
                        self.writer.agent_thinking("正在进行文本分析...")
            
            # 处理AI最终回复内容
            elif hasattr(message, 'content') and message.content:
                content = str(message.content)
                self.full_response += content
                self.writer.agent_thinking(f"Agent回复: {content}")
                
        elif msg_type == "ToolMessage":
            # 处理工具消息
            if hasattr(message, 'content') and message.content:
                tool_name = getattr(message, 'name', 'unknown_tool')
                result = str(message.content)
                
                # 发送工具结果
                self.writer.tool_result(tool_name, result)
                
                # 工具结果也算作响应的一部分
                self.full_response += f"\\n[{tool_name}结果]: {result}"
                
                # 特殊处理，提供更好的用户体验
                if tool_name == "calculator":
                    self.writer.agent_thinking(f"计算完成，结果是: {result}")
                elif tool_name == "web_search":
                    self.writer.agent_thinking("搜索完成，正在分析搜索结果...")
                elif tool_name == "text_analyzer":
                    self.writer.agent_thinking("文本分析完成，正在整理结果...")
    
    async def _handle_ai_message_chunk(self, message):
        """处理AI消息块 - messages模式中的流式内容"""
        # 检查工具调用（messages模式中可能也有）
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get('name', 'unknown_tool')
                tool_args = tool_call.get('args', {})
                self.writer.tool_call(tool_name, tool_args)
                self.tools_used.append(tool_name)
        
        # 检查AI内容
        elif hasattr(message, 'content') and message.content:
            content = str(message.content)
            self.full_response += content
            self.chunk_count += 1
            
            # 发送流式内容
            self.writer.ai_streaming(content, self.chunk_count)
    
    async def _handle_tool_message(self, message):
        """处理工具消息 - messages模式中的工具结果"""
        if hasattr(message, 'content') and message.content:
            tool_name = getattr(message, 'name', 'unknown_tool')
            result = str(message.content)
            
            # 发送工具结果
            self.writer.tool_result(tool_name, result)
            
            # 工具结果也算作响应的一部分
            self.full_response += f"\\n[{tool_name}结果]: {result}"


# ============================================================================
# 便捷函数
# ============================================================================

def create_writer(node_name: str, agent_name: str = "") -> Writer:
    """创建writer"""
    return Writer(node_name, agent_name)

def create_collector(node_name: str, agent_name: str = "") -> Collector:
    """创建流收集器"""
    writer = create_writer(node_name, agent_name)
    return Collector(writer)


# ============================================================================
# 前端渲染示例
# ============================================================================

def format_message_for_frontend(message_dict: Dict[str, Any]) -> str:
    """前端消息格式化示例"""
    msg_type = message_dict["message_type"]
    content = message_dict["content"]
    metadata = message_dict.get("metadata", {})
    
    # 根据消息类型进行不同的格式化
    if msg_type == "step_start":
        return f"🚀 开始: {content}"
    elif msg_type == "step_progress":
        progress = metadata.get("progress", 0)
        return f"⏳ {content} ({progress}%)"
    elif msg_type == "agent_thinking":
        return f"🧠 思考: {content}"
    elif msg_type == "tool_call":
        tool_name = metadata.get("tool_name", "")
        return f"🔧 调用工具: {tool_name}"
    elif msg_type == "tool_result":
        return f"📊 工具结果: {content}"
    elif msg_type == "ai_streaming":
        return content  # 流式内容直接输出，不换行
    elif msg_type == "final_result":
        return f"🎯 最终结果: {content}"
    elif msg_type == "error":
        return f"❌ 错误: {content}"
    else:
        return f"[{msg_type.upper()}] {content}"