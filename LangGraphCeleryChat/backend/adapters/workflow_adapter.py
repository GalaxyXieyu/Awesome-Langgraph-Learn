"""
工作流适配器
将 Interative-Report-Workflow 集成到 Celery 系统中，使用 Redis 作为 checkpoint 存储
"""

import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.schemas import WritingTaskState, TaskStatus, MessageType, StreamEvent
from ..utils.redis_client import RedisClient
from ..utils.logger import get_logger
from ..utils.config import get_config

# 导入 LangGraph Redis checkpoint
try:
    from langgraph.checkpoint.redis import RedisSaver
    REDIS_CHECKPOINT_AVAILABLE = True
except ImportError:
    from langgraph.checkpoint.memory import InMemorySaver
    REDIS_CHECKPOINT_AVAILABLE = False

# 导入 LangGraph 组件
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import TypedDict, List

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
    工作流适配器
    将 Interative-Report-Workflow 适配到 Celery 系统，使用 Redis checkpoint
    """

    def __init__(self, task_id: str, session_id: str, redis_client: RedisClient):
        self.task_id = task_id
        self.session_id = session_id
        self.redis_client = redis_client
        self.stream_writer = CeleryStreamWriter(task_id, session_id, redis_client)
        self.interrupt_manager = InterruptManager(task_id, session_id, redis_client)

        # 创建 Redis checkpoint
        self.checkpointer = self._create_checkpointer()

        # 创建 LangGraph 工作流
        self.graph = self._create_compiled_graph()

    def _create_checkpointer(self):
        """创建 Redis checkpoint"""
        try:
            if REDIS_CHECKPOINT_AVAILABLE:
                config = get_config()
                redis_url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
                if config.redis.password:
                    redis_url = f"redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/{config.redis.db}"

                logger.info(f"使用 Redis checkpoint: {redis_url}")
                return RedisSaver.from_conn_string(redis_url)
            else:
                logger.warning("Redis checkpoint 不可用，使用内存存储")
                return InMemorySaver()
        except Exception as e:
            logger.error(f"创建 checkpoint 失败: {e}")
            return InMemorySaver()

    def _create_compiled_graph(self):
        """创建编译后的图，集成真正的 Interative-Report-Workflow"""
        try:
            # 导入真正的工作流
            import sys
            import os

            # 添加 Interative-Report-Workflow 路径
            workflow_path = os.path.join(os.path.dirname(__file__), "../../../Interative-Report-Workflow")
            if workflow_path not in sys.path:
                sys.path.append(workflow_path)

            try:
                # 暂时禁用原始工作流，因为有图结构错误
                # from graph import create_writing_assistant_graph
                # logger.info("✅ 成功导入 Interative-Report-Workflow")
                #
                # # 使用真正的工作流图
                # graph = create_writing_assistant_graph()
                #
                # # 重新编译图以添加 checkpointer
                # compiled_graph = graph.compile(checkpointer=self.checkpointer)
                # logger.info("✅ 工作流图编译成功")
                # return compiled_graph

                logger.info("🔄 使用修复版简化工作流（支持真正的 interrupt）")
                return self._create_interrupt_capable_graph()

            except ImportError as e:
                logger.warning(f"⚠️ 无法导入 Interative-Report-Workflow: {e}")
                logger.info("🔄 使用简化版工作流")

                # 回退到简化版本
                return self._create_interrupt_capable_graph()

        except Exception as e:
            logger.error(f"创建工作流图失败: {e}")
            raise

    def _create_interrupt_capable_graph(self):
        """创建支持真正 interrupt 的工作流图"""
        from langgraph.graph import StateGraph, START, END
        from langgraph.graph.message import add_messages
        from langchain_core.messages import BaseMessage
        from typing import TypedDict, Annotated, List

        # 定义状态
        class WritingState(TypedDict):
            topic: str
            user_id: str
            max_words: int
            style: str
            language: str
            mode: str
            outline: Optional[Dict[str, Any]]
            article: Optional[str]
            search_results: List[Dict[str, Any]]
            user_confirmation: Optional[str]
            search_permission: Optional[str]
            rag_permission: Optional[str]
            messages: Annotated[List[BaseMessage], add_messages]

        # 创建工作流
        workflow = StateGraph(WritingState)

        # 节点函数
        def generate_outline(state: WritingState) -> WritingState:
            """生成大纲"""
            outline = {
                "title": f"关于{state['topic']}的深度研究报告",
                "sections": [
                    {
                        "title": "概述",
                        "description": f"{state['topic']}的基本概念和重要性",
                        "key_points": [f"{state['topic']}的定义", "发展历程", "重要意义"]
                    },
                    {
                        "title": "现状分析",
                        "description": f"{state['topic']}的当前发展状况",
                        "key_points": ["市场现状", "技术水平", "主要挑战"]
                    },
                    {
                        "title": "技术细节",
                        "description": f"{state['topic']}的核心技术和实现",
                        "key_points": ["核心算法", "技术架构", "实现方案"]
                    },
                    {
                        "title": "应用案例",
                        "description": f"{state['topic']}的实际应用场景",
                        "key_points": ["典型案例", "应用效果", "经验总结"]
                    },
                    {
                        "title": "未来展望",
                        "description": f"{state['topic']}的发展趋势和前景",
                        "key_points": ["发展趋势", "技术突破", "应用前景"]
                    }
                ]
            }

            # 检查模式，如果是交互模式则触发中断
            mode = state.get("mode")
            logger.info(f"生成大纲节点: mode={mode}, topic={state.get('topic')}")

            if mode == "interactive":
                logger.info(f"触发中断: 交互模式需要用户确认大纲")
                from langgraph.errors import NodeInterrupt
                raise NodeInterrupt(f"需要用户确认大纲: {outline['title']}")

            return {
                **state,
                "outline": outline
            }

        def write_article(state: WritingState) -> WritingState:
            """写文章"""
            outline = state.get("outline", {})
            topic = state.get("topic", "未知主题")

            # 简化的文章生成
            article = f"# {outline.get('title', topic) if outline else topic}\n\n"

            if outline:
                sections = outline.get("sections", [])
                for section in sections:
                    article += f"## {section.get('title', '章节')}\n\n"
                    article += f"{section.get('description', '内容描述')}...\n\n"

            article += f"这是关于{topic}的详细分析和研究报告。"

            return {
                **state,
                "article": article
            }

        # 添加节点
        workflow.add_node("generate_outline", generate_outline)
        workflow.add_node("write_article", write_article)

        # 添加边
        workflow.add_edge(START, "generate_outline")
        workflow.add_edge("generate_outline", "write_article")
        workflow.add_edge("write_article", END)

        # 编译图（带 interrupt 支持）
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["write_article"]  # 在写文章前中断
        )

    def _create_simple_graph(self):
        """创建简化版工作流图（带 interrupt 支持）"""
        from langgraph.graph import StateGraph, START, END
        from langgraph.graph.message import add_messages
        from langchain_core.messages import BaseMessage
        from typing import TypedDict, Annotated, List

        # 定义状态
        class WritingState(TypedDict):
            topic: str
            user_id: str
            max_words: int
            style: str
            language: str
            mode: str
            outline: Optional[Dict[str, Any]]
            article: Optional[str]
            search_results: List[Dict[str, Any]]
            user_confirmation: Optional[str]
            search_permission: Optional[str]
            rag_permission: Optional[str]
            messages: Annotated[List[BaseMessage], add_messages]

        # 创建工作流
        workflow = StateGraph(WritingState)

        # 节点函数
        def generate_outline(state: WritingState) -> WritingState:
            """生成大纲"""
            outline = {
                "title": f"关于{state['topic']}的深度研究报告",
                "sections": [
                    {
                        "title": "概述",
                        "description": f"{state['topic']}的基本概念和重要性",
                        "key_points": [f"{state['topic']}的定义", "发展历程", "重要意义"]
                    },
                    {
                        "title": "现状分析",
                        "description": f"{state['topic']}的当前发展状况",
                        "key_points": ["市场现状", "技术水平", "主要挑战"]
                    },
                    {
                        "title": "技术细节",
                        "description": f"{state['topic']}的核心技术和实现",
                        "key_points": ["核心算法", "技术架构", "实现方案"]
                    },
                    {
                        "title": "应用案例",
                        "description": f"{state['topic']}的实际应用场景",
                        "key_points": ["典型案例", "应用效果", "经验总结"]
                    },
                    {
                        "title": "未来展望",
                        "description": f"{state['topic']}的发展趋势和前景",
                        "key_points": ["发展趋势", "技术突破", "应用前景"]
                    }
                ]
            }

            return {
                **state,
                "outline": outline,
                "current_step": "awaiting_confirmation"
            }

        def check_confirmation(state: WritingState) -> str:
            """检查用户确认"""
            mode = state.get("mode", "interactive")
            user_confirmation = state.get("user_confirmation")

            logger.info(f"检查确认状态: mode={mode}, confirmation={user_confirmation}")

            if mode == "copilot":
                logger.info("自动模式，跳过确认")
                return "write_article"  # 自动模式跳过确认

            # 交互模式需要用户确认
            if user_confirmation == "yes":
                logger.info("用户确认，继续写文章")
                return "write_article"
            elif user_confirmation == "no":
                logger.info("用户拒绝，重新生成大纲")
                return "generate_outline"  # 重新生成大纲
            else:
                logger.info("等待用户确认，中断工作流")
                return "wait_confirmation"  # 等待用户确认

        def write_article(state: WritingState) -> WritingState:
            """写文章"""
            outline = state.get("outline", {})
            topic = state.get("topic", "未知主题")

            # 简化的文章生成
            article = f"# {outline.get('title', topic)}\n\n"

            sections = outline.get("sections", [])
            for section in sections:
                article += f"## {section.get('title', '章节')}\n\n"
                article += f"{section.get('description', '内容描述')}...\n\n"

            article += f"这是关于{topic}的详细分析和研究报告。"

            return {
                **state,
                "article": article,
                "current_step": "completed"
            }

        # 添加节点
        workflow.add_node("generate_outline", generate_outline)
        workflow.add_node("write_article", write_article)

        # 添加边
        workflow.add_edge(START, "generate_outline")
        workflow.add_conditional_edges(
            "generate_outline",
            check_confirmation,
            {
                "write_article": "write_article",
                "generate_outline": "generate_outline",
                "wait_confirmation": END  # 中断等待用户确认
            }
        )
        workflow.add_edge("write_article", END)

        # 编译图（带 interrupt）
        # 注意：interrupt_before 只在特定条件下生效
        return workflow.compile(
            checkpointer=self.checkpointer
            # interrupt_before=["write_article"]  # 暂时注释，使用条件中断
        )

    async def execute_writing_workflow(
        self,
        initial_state: Dict[str, Any],
        task_state: WritingTaskState
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
                async for chunk in self.graph.astream(initial_state, config=config):
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

            # 处理用户响应，更新状态
            response_type = user_response.get("response", "")
            approved = user_response.get("approved", False)

            # 构建更新的状态
            updated_state = {}

            if response_type == "确认继续" or approved:
                updated_state["user_confirmation"] = "yes"
            else:
                updated_state["user_confirmation"] = "no"

            # 使用 LangGraph 的 update_state 更新状态
            try:
                # 更新图的状态
                self.graph.update_state(config, updated_state)
                logger.info(f"✅ 状态更新成功: {updated_state}")

                # 继续执行图
                result = await self.graph.ainvoke(None, config=config)

                # 检查是否完成
                if result.get("current_step") == "completed":
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
                    logger.info(f"工作流仍在等待: {result.get('current_step')}")
                    return {
                        "completed": False,
                        "paused": True,
                        "current_step": result.get("current_step", "waiting"),
                        "progress": 75,
                        "state": result
                    }

            except Exception as e:
                logger.error(f"使用 checkpoint 恢复失败: {e}")
                # 回退到重新执行
                logger.info("回退到重新执行工作流")

                # 重建完整状态
                full_state = self._rebuild_state_from_task(task_state, user_response)
                return await self.execute_writing_workflow(full_state, task_state)

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
