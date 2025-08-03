"""
LangGraph Celery 适配器
将 Interative-Report-Workflow 集成到 Celery 异步任务系统中
"""

import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, Callable
from datetime import datetime

import redis
from celery import current_task
from langgraph.graph import StateGraph
from langgraph.config import get_stream_writer

from ..models.schemas import (
    WritingTaskState, TaskStatus, MessageType, 
    ProgressUpdate, InterruptRequest, StreamEvent
)
from ..utils.redis_client import RedisClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CeleryStreamWriter:
    """
    Celery 流写入器
    将 LangGraph 的流式输出适配到 Redis Streams
    """
    
    def __init__(self, task_id: str, session_id: str, redis_client: RedisClient):
        self.task_id = task_id
        self.session_id = session_id
        self.redis_client = redis_client
        self.stream_name = f"task_events:{session_id}"
        
    def __call__(self, data: Dict[str, Any]) -> None:
        """写入流数据到 Redis Streams"""
        try:
            # 创建流事件
            event = StreamEvent(
                event_id=str(uuid.uuid4()),
                event_type=MessageType.PROGRESS_UPDATE,
                session_id=self.session_id,
                task_id=self.task_id,
                data=data
            )
            
            # 写入 Redis Streams
            self.redis_client.xadd(
                self.stream_name,
                {
                    "event_type": event.event_type.value,
                    "task_id": self.task_id,
                    "data": json.dumps(event.data, ensure_ascii=False)
                }
            )
            
            # 更新任务进度（如果有进度信息）
            if "progress" in data:
                self._update_task_progress(data)
                
        except Exception as e:
            logger.error(f"写入流数据失败: {e}")
    
    def _update_task_progress(self, data: Dict[str, Any]) -> None:
        """更新 Celery 任务进度"""
        try:
            if current_task:
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": data.get("progress", 0),
                        "status": data.get("status", ""),
                        "step": data.get("step", ""),
                        "current_action": data.get("current_action", "")
                    }
                )
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")


class InterruptHandler:
    """
    中断处理器
    处理 LangGraph 的 interrupt 事件，转换为异步用户交互
    """
    
    def __init__(self, task_id: str, session_id: str, redis_client: RedisClient):
        self.task_id = task_id
        self.session_id = session_id
        self.redis_client = redis_client
        self.interrupt_timeout = 300  # 5分钟超时
        
    async def handle_interrupt(self, interrupt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理中断请求
        
        Args:
            interrupt_data: 中断数据
            
        Returns:
            用户响应数据
        """
        interrupt_id = str(uuid.uuid4())
        
        try:
            # 创建中断请求
            interrupt_request = InterruptRequest(
                interrupt_type=interrupt_data.get("type", "confirmation"),
                title=interrupt_data.get("title", "确认请求"),
                message=interrupt_data.get("message", "请确认是否继续"),
                options=interrupt_data.get("options", ["确认", "取消"]),
                default=interrupt_data.get("default", "确认"),
                timeout=interrupt_data.get("timeout", self.interrupt_timeout),
                content=interrupt_data.get("content", {})
            )
            
            # 发送中断请求事件
            await self._send_interrupt_request(interrupt_id, interrupt_request)
            
            # 等待用户响应
            response = await self._wait_for_user_response(interrupt_id)
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"中断请求超时: {interrupt_id}")
            return {"approved": False, "response": "timeout", "error": "请求超时"}
        except Exception as e:
            logger.error(f"处理中断请求失败: {e}")
            return {"approved": False, "response": "error", "error": str(e)}
    
    async def _send_interrupt_request(self, interrupt_id: str, request: InterruptRequest) -> None:
        """发送中断请求事件"""
        event = StreamEvent(
            event_id=interrupt_id,
            event_type=MessageType.INTERRUPT_REQUEST,
            session_id=self.session_id,
            task_id=self.task_id,
            data={
                "interrupt_id": interrupt_id,
                "request": request.dict()
            }
        )
        
        # 写入事件流
        stream_name = f"task_events:{self.session_id}"
        self.redis_client.xadd(
            stream_name,
            {
                "event_type": event.event_type.value,
                "task_id": self.task_id,
                "interrupt_id": interrupt_id,
                "data": json.dumps(event.data, ensure_ascii=False)
            }
        )
        
        # 存储中断状态
        interrupt_key = f"interrupt:{interrupt_id}:state"
        self.redis_client.setex(
            interrupt_key,
            request.timeout,
            json.dumps({
                "status": "waiting",
                "created_at": datetime.now().isoformat(),
                "request": request.dict()
            })
        )
    
    async def _wait_for_user_response(self, interrupt_id: str) -> Dict[str, Any]:
        """等待用户响应"""
        response_key = f"interrupt:{interrupt_id}:response"
        
        # 轮询等待响应
        start_time = time.time()
        while time.time() - start_time < self.interrupt_timeout:
            response_data = self.redis_client.get(response_key)
            if response_data:
                return json.loads(response_data)
            
            await asyncio.sleep(1)  # 1秒轮询间隔
        
        raise asyncio.TimeoutError("等待用户响应超时")


class LangGraphCeleryAdapter:
    """
    LangGraph Celery 适配器
    将 LangGraph 工作流适配到 Celery 异步任务系统
    """
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        
    async def execute_workflow(
        self,
        graph: StateGraph,
        initial_state: Dict[str, Any],
        task_id: str,
        session_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行 LangGraph 工作流
        
        Args:
            graph: LangGraph 图实例
            initial_state: 初始状态
            task_id: 任务ID
            session_id: 会话ID
            config: 配置参数
            
        Returns:
            执行结果
        """
        try:
            # 创建流写入器和中断处理器
            stream_writer = CeleryStreamWriter(task_id, session_id, self.redis_client)
            interrupt_handler = InterruptHandler(task_id, session_id, self.redis_client)
            
            # 设置配置
            if config is None:
                config = {}
            config["configurable"] = config.get("configurable", {})
            config["configurable"]["thread_id"] = session_id
            
            # 注入流写入器（模拟 LangGraph 的流上下文）
            self._inject_stream_writer(stream_writer)
            
            # 执行工作流
            result = await self._execute_with_interrupts(
                graph, initial_state, config, interrupt_handler
            )
            
            return result
            
        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            raise
    
    def _inject_stream_writer(self, stream_writer: CeleryStreamWriter) -> None:
        """注入流写入器到全局上下文"""
        # 这里需要模拟 LangGraph 的流上下文
        # 实际实现可能需要根据 LangGraph 的具体版本调整
        import contextvars
        
        # 创建上下文变量（如果不存在）
        if not hasattr(self, '_stream_writer_var'):
            self._stream_writer_var = contextvars.ContextVar('stream_writer')
        
        self._stream_writer_var.set(stream_writer)
    
    async def _execute_with_interrupts(
        self,
        graph: StateGraph,
        initial_state: Dict[str, Any],
        config: Dict[str, Any],
        interrupt_handler: InterruptHandler
    ) -> Dict[str, Any]:
        """
        执行带中断处理的工作流
        """
        current_state = initial_state.copy()
        
        try:
            # 使用 astream 执行图
            async for chunk in graph.astream(current_state, config=config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    # 更新当前状态
                    current_state.update(node_output)
                    
                    # 检查是否有中断请求
                    if self._has_interrupt_request(node_output):
                        interrupt_data = self._extract_interrupt_data(node_output)
                        response = await interrupt_handler.handle_interrupt(interrupt_data)
                        
                        # 更新状态中的用户响应
                        current_state.update(self._process_user_response(interrupt_data, response))
                        
                        # 继续执行（LangGraph 会自动处理状态更新）
            
            return current_state
            
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            raise
    
    def _has_interrupt_request(self, node_output: Dict[str, Any]) -> bool:
        """检查节点输出是否包含中断请求"""
        # 根据 Interative-Report-Workflow 的实现
        return (
            node_output.get("current_step") == "awaiting_confirmation" or
            node_output.get("current_step") == "awaiting_search_permission" or
            node_output.get("current_step") == "awaiting_rag_permission"
        )
    
    def _extract_interrupt_data(self, node_output: Dict[str, Any]) -> Dict[str, Any]:
        """从节点输出中提取中断数据"""
        current_step = node_output.get("current_step", "")
        
        if current_step == "awaiting_confirmation":
            return {
                "type": "outline_confirmation",
                "title": "大纲确认",
                "message": f"请确认以下大纲：\n{self._format_outline(node_output.get('outline', {}))}",
                "options": ["确认继续", "重新生成"],
                "default": "确认继续",
                "content": {"outline": node_output.get("outline", {})}
            }
        elif current_step == "awaiting_search_permission":
            return {
                "type": "search_permission",
                "title": "搜索权限确认",
                "message": f"是否允许为主题「{node_output.get('topic', '')}」进行联网搜索？",
                "options": ["允许", "跳过"],
                "default": "允许"
            }
        elif current_step == "awaiting_rag_permission":
            return {
                "type": "rag_permission",
                "title": "RAG增强确认",
                "message": f"是否需要为主题「{node_output.get('topic', '')}」进行RAG知识库增强？",
                "options": ["启用", "跳过"],
                "default": "启用"
            }
        
        return {
            "type": "generic_confirmation",
            "title": "确认请求",
            "message": "请确认是否继续",
            "options": ["确认", "取消"],
            "default": "确认"
        }
    
    def _format_outline(self, outline: Dict[str, Any]) -> str:
        """格式化大纲显示"""
        if not outline:
            return "无大纲数据"
        
        title = outline.get("title", "未知标题")
        sections = outline.get("sections", [])
        
        formatted = f"标题：{title}\n\n章节：\n"
        for i, section in enumerate(sections, 1):
            formatted += f"{i}. {section.get('title', '未知章节')}\n"
            formatted += f"   描述：{section.get('description', '无描述')}\n"
        
        return formatted
    
    def _process_user_response(
        self, 
        interrupt_data: Dict[str, Any], 
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理用户响应，转换为状态更新"""
        interrupt_type = interrupt_data.get("type", "")
        user_response = response.get("response", "")
        approved = response.get("approved", False)
        
        state_updates = {}
        
        if interrupt_type == "outline_confirmation":
            state_updates["user_confirmation"] = "yes" if approved else "no"
        elif interrupt_type == "search_permission":
            state_updates["search_permission"] = "yes" if approved else "no"
        elif interrupt_type == "rag_permission":
            state_updates["rag_permission"] = "yes" if approved else "no"
        
        return state_updates
