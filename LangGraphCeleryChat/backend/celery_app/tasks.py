"""
Celery 任务定义
基于 Interative-Report-Workflow 的 LangGraph 工作流
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from . import celery_app
from ..models.schemas import WritingTaskState, TaskStatus, WritingTaskConfig
from ..utils.redis_client import get_redis_client
from ..utils.logger import get_logger
from ..utils.session_manager import get_session_manager
from ..adapters.workflow_adapter import WorkflowAdapter

logger = get_logger(__name__)


@celery_app.task(bind=True)
def execute_writing_task(self, user_id: str, session_id: str, task_id: str, config_data: Dict[str, Any], is_resumed: bool = False, original_conversation_id: Optional[str] = None):
    """
    异步执行写作任务，基于 Interative-Report-Workflow
    
    Args:
        user_id: 用户唯一标识
        session_id: 会话唯一标识  
        task_id: 任务唯一标识
        config_data: 写作任务配置数据
        
    Returns:
        dict: 任务执行结果
    """
    
    async def execute_workflow():
        session_manager = None
        try:
            # 初始化会话管理器
            session_manager = get_session_manager()
            
            # 解析配置
            config = WritingTaskConfig(**config_data)
            
            # 创建任务状态
            task_state = WritingTaskState(
                task_id=task_id,
                session_id=session_id,
                user_id=user_id,
                config=config,
                status=TaskStatus.RUNNING,
                current_step="initializing"
            )
            
            # 更新任务状态到 Redis
            await session_manager.set_task_status(
                task_id=task_id,
                status="running",
                user_id=user_id,
                session_id=session_id,
                metadata=task_state.dict()
            )
            
            # 创建工作流适配器（使用 thread_id 作为统一标识）
            thread_id = original_conversation_id or session_id
            workflow_adapter = WorkflowAdapter(
                thread_id=thread_id,
                redis_client=get_redis_client()
            )

            # 准备初始状态（基于 Interative-Report-Workflow 的 WritingState）
            initial_state = {
                "topic": config.topic,
                "user_id": user_id,
                "max_words": config.max_words,
                "style": config.style.value,
                "language": config.language,
                "mode": config.mode.value,
                "outline": None,
                "article": None,
                "search_results": [],
                "user_confirmation": None,
                "search_permission": None,
                "rag_permission": None,
                "messages": []
            }

            # 执行工作流（使用新的统一接口）
            logger.info(f"开始执行写作任务: {task_id}, 主题: {config.topic}")

            result = await workflow_adapter.execute_workflow(
                initial_state=initial_state
            )
            
            # 处理执行结果
            if result.get("completed", False):
                # 任务完成
                task_dict = task_state.dict()
                task_dict.update({
                    "status": TaskStatus.COMPLETED,
                    "current_step": "completed",
                    "progress": 100,
                    "outline": result.get("outline"),
                    "article": result.get("article"),
                    "search_results": result.get("search_results", []),
                    "word_count": len(result.get("article") or ""),
                    "generation_time": time.time() - task_state.created_at.timestamp(),
                    "completed_at": datetime.now()
                })
                final_state = WritingTaskState(**task_dict)

                # 更新任务状态为完成
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="completed",
                    result=final_state.dict(),
                    user_id=user_id,
                    session_id=session_id
                )

                logger.info(f"写作任务完成: {task_id}")
                return final_state.dict()
            else:
                # 任务被中断，等待用户交互
                task_dict = task_state.dict()
                task_dict.update({
                    "status": TaskStatus.PAUSED,
                    "current_step": result.get("interrupt_type", "waiting"),
                    "progress": result.get("progress", task_state.progress),
                    "updated_at": datetime.now()
                })
                paused_state = WritingTaskState(**task_dict)

                # 更新任务状态为暂停
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="paused",
                    metadata=paused_state.dict(),
                    user_id=user_id,
                    session_id=session_id
                )

                logger.info(f"写作任务暂停，等待用户交互: {task_id}")
                return paused_state.dict()
            
        except Exception as e:
            logger.error(f"执行写作任务失败: {task_id}, 错误: {str(e)}")
            
            # 更新任务状态为失败
            if session_manager:
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="failed",
                    error=str(e),
                    user_id=user_id,
                    session_id=session_id
                )
            
            raise e
        finally:
            # 关闭连接
            if session_manager:
                await session_manager.close()
    
    return asyncio.run(execute_workflow())


@celery_app.task(bind=True)
def resume_writing_task(self, user_id: str, session_id: str, task_id: str, user_response: Dict[str, Any]):
    """
    恢复写作任务，处理用户交互响应
    
    Args:
        user_id: 用户唯一标识
        session_id: 会话唯一标识
        task_id: 任务唯一标识
        user_response: 用户响应数据
        
    Returns:
        dict: 任务执行结果
    """
    
    async def resume_workflow():
        session_manager = None
        try:
            # 初始化会话管理器
            session_manager = get_session_manager()
            
            # 获取任务状态
            task_data = await session_manager.get_task_status(task_id)
            if not task_data:
                raise ValueError(f"任务不存在: {task_id}")
            
            task_state = WritingTaskState(**task_data.get("metadata", {}))
            
            # 更新任务状态为运行中
            task_state.status = TaskStatus.RUNNING
            task_state.updated_at = datetime.now()
            
            await session_manager.set_task_status(
                task_id=task_id,
                status="running",
                user_id=user_id,
                session_id=session_id,
                metadata=task_state.dict()
            )
            
            # 创建工作流适配器（使用相同的 thread_id）
            metadata = task_data.get("metadata", {})
            original_conversation_id = metadata.get("original_conversation_id")
            thread_id = original_conversation_id or session_id

            workflow_adapter = WorkflowAdapter(
                thread_id=thread_id,
                redis_client=get_redis_client()
            )

            # 处理用户响应并恢复工作流（使用新的简化接口）
            logger.info(f"恢复写作任务: {task_id}, 用户响应: {user_response}")

            # 提取用户响应命令 - 采用ReActAgentsTest的简单模式
            resume_command = user_response.get("response", "yes")  # 默认为 yes
            
            # 简化为直接恢复，不重建状态
            logger.info(f"🔄 直接恢复工作流: resume={resume_command}")

            result = await workflow_adapter.execute_workflow(
                resume_command=resume_command
            )
            
            # 更新最终结果
            if result.get("completed", False):
                task_dict = task_state.dict()
                task_dict.update({
                    "status": TaskStatus.COMPLETED,
                    "current_step": "completed",
                    "progress": 100,
                    "outline": result.get("outline"),
                    "article": result.get("article"),
                    "search_results": result.get("search_results", []),
                    "word_count": len(result.get("article") or ""),
                    "generation_time": time.time() - task_state.created_at.timestamp(),
                    "completed_at": datetime.now()
                })
                final_state = WritingTaskState(**task_dict)
                
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="completed",
                    result=final_state.dict(),
                    user_id=user_id,
                    session_id=session_id
                )
                
                return final_state.dict()
            else:
                # 任务仍在进行中，等待下一次用户交互
                task_dict = task_state.dict()
                task_dict.update({
                    "status": TaskStatus.PAUSED,
                    "current_step": result.get("current_step", "waiting"),
                    "progress": result.get("progress", task_state.progress),
                    "updated_at": datetime.now()
                })
                updated_state = WritingTaskState(**task_dict)
                
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="paused",
                    metadata=updated_state.dict(),
                    user_id=user_id,
                    session_id=session_id
                )
                
                return updated_state.dict()
            
        except Exception as e:
            logger.error(f"恢复写作任务失败: {task_id}, 错误: {str(e)}")
            
            # 更新任务状态为失败
            if session_manager:
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="failed",
                    error=str(e),
                    user_id=user_id,
                    session_id=session_id
                )
            
            raise e
        finally:
            # 关闭连接
            if session_manager:
                await session_manager.close()
    
    return asyncio.run(resume_workflow())


@celery_app.task(bind=True)
def cancel_writing_task(self, user_id: str, session_id: str, task_id: str):
    """
    取消写作任务
    
    Args:
        user_id: 用户唯一标识
        session_id: 会话唯一标识
        task_id: 任务唯一标识
        
    Returns:
        dict: 取消结果
    """
    
    async def cancel_workflow():
        session_manager = None
        try:
            # 初始化会话管理器
            session_manager = get_session_manager()
            
            # 更新任务状态为已取消
            await session_manager.set_task_status(
                task_id=task_id,
                status="cancelled",
                user_id=user_id,
                session_id=session_id
            )
            
            logger.info(f"写作任务已取消: {task_id}")
            return {"task_id": task_id, "status": "cancelled", "message": "任务已取消"}
            
        except Exception as e:
            logger.error(f"取消写作任务失败: {task_id}, 错误: {str(e)}")
            raise e
        finally:
            # 关闭连接
            if session_manager:
                await session_manager.close()
    
    return asyncio.run(cancel_workflow())
