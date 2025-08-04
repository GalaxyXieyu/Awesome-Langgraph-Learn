"""
工作流适配器
将 Interative-Report-Workflow 集成到 Celery 系统中，使用 Redis 作为 checkpoint 存储
"""

import json
import time
import uuid
import asyncio
import sys
import os
from typing import Dict, Any, Optional, cast
from datetime import datetime

from ..models.schemas import WritingTaskState, TaskStatus, MessageType, StreamEvent
from ..utils.redis_client import RedisClient
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)

# 导入您的真正 Graph
from ..graph.graph import create_writing_assistant_graph
from langgraph.types import Command

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
                    "timestamp": event.timestamp.isoformat(),
                    "data": json.dumps(event.data, ensure_ascii=False, default=str)
                }
            )
            
            logger.debug(f"写入流事件: {data.get('step', 'unknown')} - {data.get('status', '')}")
                
        except Exception as e:
            logger.error(f"写入流数据失败: {e}")


class InterruptManager:
    """
    中断管理器
    处理 LangGraph 的 interrupt 事件
    """

    def __init__(self, task_id: str, session_id: str, redis_client: RedisClient):
        self.task_id = task_id
        self.session_id = session_id
        self.redis_client = redis_client
        self.stream_name = f"task_events:{session_id}"
        self.interrupt_timeout = 300  # 5分钟超时
        
    async def send_interrupt_request(self, interrupt_data: Dict[str, Any]) -> str:
        """
        发送中断请求
        
        Args:
            interrupt_data: 中断数据
            
        Returns:
            interrupt_id: 中断请求ID
        """
        interrupt_id = str(uuid.uuid4())
        
        try:
            # 发送中断请求事件
            event = StreamEvent(
                event_id=interrupt_id,
                event_type=MessageType.INTERRUPT_REQUEST,
                session_id=self.session_id,
                task_id=self.task_id,
                data={
                    "interrupt_id": interrupt_id,
                    "interrupt_type": interrupt_data.get("type", "confirmation"),
                    "title": interrupt_data.get("title", "确认请求"),
                    "message": interrupt_data.get("message", "请确认是否继续"),
                    "options": interrupt_data.get("options", ["确认", "取消"]),
                    "default": interrupt_data.get("default", "确认"),
                    "timeout": interrupt_data.get("timeout", self.interrupt_timeout),
                    "content": interrupt_data.get("content", {})
                }
            )
            
            # 写入事件流
            self.redis_client.xadd(
                self.stream_name,
                {
                    "event_type": event.event_type.value,
                    "task_id": self.task_id,
                    "interrupt_id": interrupt_id,
                    "timestamp": event.timestamp.isoformat(),
                    "data": json.dumps(event.data, ensure_ascii=False, default=str)
                }
            )
            
            # 存储中断状态
            interrupt_key = f"interrupt:{interrupt_id}:state"
            self.redis_client.setex(
                interrupt_key,
                self.interrupt_timeout,
                json.dumps({
                    "status": "waiting",
                    "task_id": self.task_id,
                    "session_id": self.session_id,
                    "created_at": datetime.now().isoformat(),
                    "interrupt_data": interrupt_data
                })
            )
            
            logger.info(f"发送中断请求: {interrupt_id}, 类型: {interrupt_data.get('type')}")
            return interrupt_id
            
        except Exception as e:
            logger.error(f"发送中断请求失败: {e}")
            raise
    
    def get_user_response(self, interrupt_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户响应
        
        Args:
            interrupt_id: 中断请求ID
            
        Returns:
            用户响应数据
        """
        try:
            response_key = f"interrupt:{interrupt_id}:response"
            response_data = self.redis_client.get(response_key)
            
            if response_data:
                return json.loads(response_data)
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户响应失败: {e}")
            return None


class WorkflowAdapter:
    """
    工作流适配器 - 重新设计版本

    核心职责：
    1. 直接调用外部 Interactive-Report-Workflow 图
    2. 处理流式输出适配到 Redis Streams
    3. 管理中断检测和用户交互
    4. 提供统一的执行和恢复接口

    设计原则：
    - 不重新构建图结构
    - 不修改外部图的 checkpoint
    - 只负责调用和数据转换
    """

    def __init__(self, conversation_id: str, redis_client: RedisClient):
        self.conversation_id = conversation_id  # 作为 LangGraph 的 thread_id
        self.redis_client = redis_client
        self.stream_writer = CeleryStreamWriter(conversation_id, conversation_id, redis_client)
        self.interrupt_manager = InterruptManager(conversation_id, conversation_id, redis_client)

        # 直接使用外部图（已配置 Redis checkpoint）
        self.graph = create_writing_assistant_graph()

        logger.info(f"✅ WorkflowAdapter 初始化完成，conversation_id: {conversation_id}")
        logger.info(f"📊 图类型: {type(self.graph)}")

    async def execute_workflow(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        resume_command: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        统一的工作流执行接口

        Args:
            initial_state: 初始状态（用于新任务）
            resume_command: 恢复命令（用于恢复任务，如 "yes", "no"）

        Returns:
            执行结果，包含流式输出、中断信息等
        """
        try:
            # 配置 LangGraph
            config = {
                "configurable": {"thread_id": self.conversation_id}
            }

            # 确定输入参数
            if initial_state is not None and resume_command is not None:
                # 恢复调用，但需要重建状态
                input_data = Command(resume=resume_command)
                logger.info(f"🔄 恢复工作流执行: {self.conversation_id}, command: {resume_command}")
                logger.info(f"📝 重建状态，主题: {initial_state.get('topic', 'unknown')}")

                # 确保 LangGraph 状态中包含所有必需字段
                # 通过先更新状态，然后发送恢复命令
                try:
                    # 先尝试获取当前状态
                    current_state = await self.graph.aget_state(config)
                    if current_state and current_state.values:
                        # 更新现有状态
                        updated_state = {**current_state.values, **initial_state}
                        await self.graph.aupdate_state(config, updated_state)
                        logger.info(f"✅ 状态更新成功，包含字段: {list(updated_state.keys())}")
                    else:
                        # 如果没有现有状态，先初始化状态
                        await self.graph.aupdate_state(config, initial_state)
                        logger.info(f"✅ 状态初始化成功，包含字段: {list(initial_state.keys())}")
                except Exception as e:
                    logger.warning(f"⚠️ 状态更新失败，继续执行: {e}")

            elif initial_state is not None:
                # 初始调用
                input_data = initial_state
                logger.info(f"🚀 开始新的工作流执行: {self.conversation_id}")
                logger.info(f"📝 初始状态: {initial_state.get('topic', 'unknown')}")
            elif resume_command is not None:
                # 纯恢复调用（不重建状态）
                input_data = Command(resume=resume_command)
                logger.info(f"🔄 恢复工作流执行: {self.conversation_id}, command: {resume_command}")
            else:
                raise ValueError("必须提供 initial_state 或 resume_command 之一")

            # 执行图并处理流式输出
            return await self._execute_with_streaming(input_data, config)

        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            raise

    async def _execute_with_streaming(
        self,
        input_data: Any,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行图并处理流式输出

        正确处理 LangGraph 的流式输出格式：
        - ('custom', {...}): 自定义流式数据
        - ('updates', {...}): 状态更新
        - ('updates', {'__interrupt__': ...}): 中断信号
        """
        try:
            final_result = None
            interrupted = False
            interrupt_info = None

            # 使用正确的流式调用方式
            async for chunk in self.graph.astream(
                input_data,
                cast(Any, config),
                stream_mode=["custom", "updates"]
            ):
                logger.info(f"📊 流式输出: {chunk}")

                # 处理不同类型的流式输出
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    stream_type, data = chunk

                    if stream_type == "custom":
                        # 处理自定义流式数据（进度、状态等）
                        await self._handle_custom_stream(data)

                    elif stream_type == "updates":
                        # 处理状态更新
                        if "__interrupt__" in data:
                            # 检测到中断
                            interrupted = True
                            interrupt_info = data["__interrupt__"]
                            logger.info(f"🛑 检测到中断: {interrupt_info}")
                            break
                        else:
                            # 正常状态更新
                            await self._handle_state_update(data)
                            final_result = data

                # 保存最终结果
                if chunk and not interrupted:
                    final_result = chunk

            # 返回执行结果
            if interrupted:
                return await self._handle_interrupt(interrupt_info)
            else:
                return self._format_completion_result(final_result)

        except Exception as e:
            logger.error(f"❌ 流式执行失败: {e}")
            raise

    async def _handle_custom_stream(self, data: Dict[str, Any]):
        """处理自定义流式数据 - 直接使用外部图的格式"""
        try:
            logger.info(f"📥 开始处理流式数据: {data}")

            # 外部图已经提供了正确的格式，直接写入 Redis Streams
            stream_name = f"conversation_events:{self.conversation_id}"
            logger.info(f"📝 写入流名称: {stream_name}")

            # 添加 conversation_id 到数据中
            enhanced_data = {
                **data,
                "conversation_id": self.conversation_id
            }

            # 准备写入 Redis 的数据
            redis_data = {
                "event_type": enhanced_data.get("event_type", "progress_update"),
                "timestamp": str(enhanced_data.get("timestamp", datetime.now().timestamp())),
                "data": json.dumps(enhanced_data, ensure_ascii=False, default=str)
            }
            logger.info(f"📋 Redis 数据: {redis_data}")

            # 直接写入 Redis Streams
            result = self.redis_client.xadd(stream_name, redis_data)
            logger.info(f"📤 流式数据已写入: {result}, step: {data.get('step', 'unknown')}")

        except Exception as e:
            logger.error(f"❌ 处理流式数据失败: {e}")
            import traceback
            logger.error(f"❌ 详细错误: {traceback.format_exc()}")

    async def _handle_state_update(self, data: Dict[str, Any]):
        """处理状态更新 - 直接写入"""
        try:
            stream_name = f"conversation_events:{self.conversation_id}"

            # 添加元数据
            enhanced_data = {
                **data,
                "conversation_id": self.conversation_id,
                "event_type": "state_update"
            }

            # 直接写入 Redis Streams
            self.redis_client.xadd(
                stream_name,
                {
                    "event_type": "state_update",
                    "timestamp": datetime.now().timestamp(),
                    "data": json.dumps(enhanced_data, ensure_ascii=False, default=str)
                }
            )

            logger.debug(f"📤 状态更新已写入: {list(data.keys())}")

        except Exception as e:
            logger.error(f"❌ 处理状态更新失败: {e}")

    async def _handle_interrupt(self, interrupt_info: Any) -> Dict[str, Any]:
        """处理中断信号"""
        try:
            # 解析中断信息
            if hasattr(interrupt_info, '__iter__') and len(interrupt_info) > 0:
                interrupt_data = interrupt_info[0]
                if hasattr(interrupt_data, 'value'):
                    interrupt_value = interrupt_data.value
                else:
                    interrupt_value = interrupt_data
            else:
                interrupt_value = interrupt_info

            # 创建中断事件 - 修复格式以匹配前端期望
            interrupt_id = str(uuid.uuid4())
            interrupt_event = {
                "event_type": "interrupt_request",
                "conversation_id": self.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "interrupt_id": interrupt_id,
                    "interrupt_type": interrupt_value.get("type", "confirmation"),  # 前端期望 interrupt_type
                    "title": interrupt_value.get("message", "需要用户确认"),      # 前端期望 title
                    "message": interrupt_value.get("instructions", "请回复 yes 或 no"),  # 详细消息
                    "timeout": 300
                }
            }

            # 写入 Redis Streams
            stream_name = f"conversation_events:{self.conversation_id}"
            self.redis_client.xadd(
                stream_name,
                {
                    "event_type": interrupt_event["event_type"],
                    "timestamp": interrupt_event["timestamp"],
                    "data": json.dumps(interrupt_event["data"], ensure_ascii=False, default=str)
                }
            )

            logger.info(f"🛑 中断事件已发送: {interrupt_event['data']['interrupt_type']}")

            return {
                "completed": False,
                "interrupted": True,
                "interrupt_id": interrupt_event["data"]["interrupt_id"],
                "interrupt_type": interrupt_event["data"]["interrupt_type"],
                "title": interrupt_event["data"]["title"],
                "message": interrupt_event["data"]["message"]
            }

        except Exception as e:
            logger.error(f"❌ 处理中断失败: {e}")
            return {
                "completed": False,
                "interrupted": True,
                "error": f"处理中断失败: {e}"
            }

    def _format_completion_result(self, final_result: Any) -> Dict[str, Any]:
        """格式化完成结果"""
        try:
            if isinstance(final_result, tuple) and len(final_result) == 2:
                _, data = final_result
            else:
                data = final_result

            # 提取关键信息
            result = {
                "completed": True,
                "interrupted": False,
                "conversation_id": self.conversation_id
            }

            if isinstance(data, dict):
                # 提取常见字段
                if "article_generation" in data:
                    article_data = data["article_generation"]
                    result.update({
                        "outline": article_data.get("outline"),
                        "article": article_data.get("article"),
                        "topic": article_data.get("topic"),
                        "search_results": article_data.get("search_results", [])
                    })
                else:
                    # 直接使用数据
                    result.update({
                        "outline": data.get("outline"),
                        "article": data.get("article"),
                        "topic": data.get("topic"),
                        "search_results": data.get("search_results", [])
                    })

            logger.info(f"✅ 工作流执行完成: {self.conversation_id}")
            return result

        except Exception as e:
            logger.error(f"❌ 格式化完成结果失败: {e}")
            return {
                "completed": True,
                "interrupted": False,
                "conversation_id": self.conversation_id,
                "error": f"格式化结果失败: {e}"
            }

    async def execute_writing_workflow(
        self,
        initial_state: Dict[str, Any],
        task_state: WritingTaskState,
        is_resumed: bool = False
    ) -> Dict[str, Any]:
        """
        执行写作工作流（支持 interrupt 和 streaming）

        Args:
            initial_state: 初始状态
            task_state: 任务状态

        Returns:
            执行结果
        """
        try:
            # 设置配置
            config = {
                "configurable": {"thread_id": self.session_id}
            }

            # 注入流写入器
            self._inject_stream_writer()

            # 执行工作流
            logger.info(f"开始执行工作流: {self.task_id}")

            # 使用 astream 执行图，支持中断和流式输出
            final_result = None
            interrupted = False

            try:
                # 使用您的真正 Graph 的调用方式
                async for chunk in self.graph.astream(initial_state, cast(Any, config), stream_mode=["custom", "updates"]):
                    logger.info(f"工作流步骤: {chunk}")

                    # 处理流式输出
                    await self._handle_streaming_output(chunk)

                    # 更新最终结果
                    if chunk:
                        final_result = chunk

            except Exception as e:
                # 检查是否是中断异常
                if "interrupt" in str(e).lower():
                    logger.info(f"工作流被中断，等待用户响应: {e}")
                    interrupted = True

                    # 获取当前状态
                    current_state = self.graph.get_state(config)

                    # 创建中断数据
                    interrupt_data = self._create_interrupt_data_from_state(current_state)
                    interrupt_id = await self.interrupt_manager.send_interrupt_request(interrupt_data)

                    return {
                        "completed": False,
                        "paused": True,
                        "interrupted": True,
                        "interrupt_id": interrupt_id,
                        "current_step": "awaiting_user_response",
                        "progress": 50,
                        "state": current_state.values if current_state else {}
                    }
                else:
                    raise e

            # 工作流完成
            if not interrupted:
                logger.info(f"工作流执行完成: {self.task_id}")
                return {
                    "completed": True,
                    "outline": final_result.get("outline") if final_result else None,
                    "article": final_result.get("article") if final_result else None,
                    "search_results": final_result.get("search_results", []) if final_result else [],
                    "state": final_result or {}
                }

        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            raise
    
    async def resume_writing_workflow(
        self,
        task_state: WritingTaskState,
        user_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        恢复写作工作流（使用 LangGraph checkpoint）

        Args:
            task_state: 任务状态
            user_response: 用户响应

        Returns:
            执行结果
        """
        try:
            logger.info(f"恢复工作流: {self.task_id}, 用户响应: {user_response}")

            # 设置配置
            config = {
                "configurable": {"thread_id": self.session_id}
            }

            # 处理用户响应
            response_type = user_response.get("response", "")
            approved = user_response.get("approved", False)

            # 根据用户响应决定 resume 参数
            if response_type == "确认继续" or approved or "yes" in response_type.lower():
                resume_value = "yes"
            else:
                resume_value = "no"

            logger.info(f"🔄 使用 Command 恢复工作流: resume={resume_value}")

            # 使用您的 Graph 的 Command 方式恢复
            if REAL_GRAPH_AVAILABLE and Command:
                # 使用 Command(resume="yes") 的方式
                final_result = None
                async for chunk in self.graph.astream(Command(resume=resume_value), cast(Any, config), stream_mode=["custom", "updates"]):
                    logger.info(f"恢复工作流步骤: {chunk}")
                    if chunk:
                        final_result = chunk

                result = final_result
            else:
                # 回退到传统方式
                updated_state = {"user_confirmation": resume_value}
                self.graph.update_state(config, updated_state)
                result = await self.graph.ainvoke(None, config=config)

            # 检查是否完成
            if result and result.get("current_step") == "completed":
                logger.info(f"工作流恢复执行完成: {self.task_id}")
                return {
                    "completed": True,
                    "outline": result.get("outline"),
                    "article": result.get("article"),
                    "search_results": result.get("search_results", []),
                    "state": result
                }
            else:
                # 可能还有其他中断
                logger.info(f"工作流仍在等待: {result.get('current_step') if result else 'unknown'}")
                return {
                    "completed": False,
                    "paused": True,
                    "current_step": result.get("current_step", "waiting") if result else "waiting",
                    "progress": 75,
                    "state": result or {}
                }

        except Exception as e:
            logger.error(f"恢复工作流失败: {e}")
            raise

    def _rebuild_state_from_task(self, task_state: WritingTaskState, user_response: Dict[str, Any]) -> Dict[str, Any]:
        """从任务状态重建工作流状态"""
        state = {
            "topic": task_state.config.topic,
            "user_id": task_state.user_id,
            "max_words": task_state.config.max_words,
            "style": task_state.config.style.value,
            "language": task_state.config.language,
            "mode": task_state.config.mode.value,
            "outline": task_state.outline.model_dump() if task_state.outline else None,
            "article": task_state.article,
            "search_results": [sr.model_dump() for sr in task_state.search_results],
            "messages": []
        }

        # 根据用户响应更新状态
        response_type = user_response.get("response", "")
        approved = user_response.get("approved", False)

        if response_type == "确认继续" or approved:
            state["user_confirmation"] = "yes"
        else:
            state["user_confirmation"] = "no"

        return state
    
    def _inject_stream_writer(self):
        """注入流写入器到全局上下文"""
        # 这里需要模拟 LangGraph 的流上下文
        # 实际实现可能需要根据具体版本调整
        import contextvars
        
        # 创建上下文变量
        if not hasattr(self, '_stream_writer_var'):
            self._stream_writer_var = contextvars.ContextVar('stream_writer')
        
        self._stream_writer_var.set(self.stream_writer)
    
    def _needs_user_interaction(self, node_output: Dict[str, Any]) -> bool:
        """检查是否需要用户交互"""
        current_step = node_output.get("current_step", "")
        return current_step in [
            "awaiting_confirmation",
            "awaiting_search_permission", 
            "awaiting_rag_permission"
        ]
    
    def _create_interrupt_data(self, node_output: Dict[str, Any]) -> Dict[str, Any]:
        """创建中断数据"""
        current_step = node_output.get("current_step", "")
        
        if current_step == "awaiting_confirmation":
            return {
                "type": "outline_confirmation",
                "title": "大纲确认",
                "message": self._format_outline_message(node_output.get("outline", {})),
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
    
    def _format_outline_message(self, outline: Dict[str, Any]) -> str:
        """格式化大纲消息"""
        if not outline:
            return "无大纲数据"
        
        title = outline.get("title", "未知标题")
        sections = outline.get("sections", [])
        
        message = f"请确认以下大纲：\n\n标题：{title}\n\n章节：\n"
        for i, section in enumerate(sections, 1):
            message += f"{i}. {section.get('title', '未知章节')}\n"
            message += f"   描述：{section.get('description', '无描述')}\n\n"
        
        return message
    
    def _calculate_progress(self, node_name: str) -> int:
        """计算进度百分比"""
        progress_map = {
            "generate_outline": 20,
            "outline_confirmation": 30,
            "search_confirmation": 40,
            "search_execution": 60,
            "article_generation": 90
        }
        return progress_map.get(node_name, 0)
    
    def _update_state_with_response(
        self, 
        task_state: WritingTaskState, 
        user_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据用户响应更新状态"""
        # 重建基础状态
        state = {
            "topic": task_state.config.topic,
            "user_id": task_state.user_id,
            "max_words": task_state.config.max_words,
            "style": task_state.config.style.value,
            "language": task_state.config.language,
            "mode": task_state.config.mode.value,
            "outline": task_state.outline.model_dump() if task_state.outline else None,
            "article": task_state.article,
            "search_results": [sr.model_dump() for sr in task_state.search_results],
            "messages": []
        }
        
        # 根据响应类型更新状态
        response_type = user_response.get("type", "")
        approved = user_response.get("approved", False)
        
        if response_type == "outline_confirmation":
            state["user_confirmation"] = "yes" if approved else "no"
        elif response_type == "search_permission":
            state["search_permission"] = "yes" if approved else "no"
        elif response_type == "rag_permission":
            state["rag_permission"] = "yes" if approved else "no"

        return state

    async def _handle_streaming_output(self, chunk: Dict[str, Any]):
        """处理流式输出，存储到 Redis"""
        try:
            # 简化版本：直接存储到 Redis hash
            stream_key = f"stream:{self.task_id}"

            # 序列化数据
            import json
            chunk_data = {
                "data": json.dumps(chunk),
                "timestamp": datetime.now().isoformat(),
                "task_id": self.task_id
            }

            # 存储到 Redis hash（简化版本）
            self.redis_client.hset(
                stream_key,
                datetime.now().isoformat(),
                json.dumps(chunk_data)
            )

            # 设置过期时间（1小时）
            self.redis_client.expire(stream_key, 3600)

            logger.debug(f"流式输出已存储: {stream_key}")

        except Exception as e:
            logger.error(f"处理流式输出失败: {e}")

    def _create_interrupt_data_from_state(self, state) -> Dict[str, Any]:
        """从状态创建中断数据"""
        try:
            state_values = state.values if hasattr(state, 'values') else state

            return {
                "type": "user_confirmation_required",
                "message": "需要用户确认以继续执行",
                "data": state_values,
                "task_id": self.task_id,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"创建中断数据失败: {e}")
            return {
                "type": "error",
                "message": f"创建中断数据失败: {e}",
                "task_id": self.task_id
            }
