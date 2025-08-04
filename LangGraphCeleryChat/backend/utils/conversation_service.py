"""
会话服务层
处理会话管理和 resume 逻辑的核心业务逻辑
"""

import json
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .redis_client import RedisClient, get_redis_client
from .session_manager import SessionManager, get_session_manager
from .logger import get_logger

logger = get_logger(__name__)


class ConversationService:
    """
    会话服务类
    封装会话管理和 resume 判断逻辑
    """
    
    def __init__(self, redis_client: Optional[RedisClient] = None, session_manager: Optional[SessionManager] = None):
        self.redis_client = redis_client or get_redis_client()
        self.session_manager = session_manager or get_session_manager()
    
    async def check_conversation_exists(self, conversation_id: str) -> bool:
        """
        检查会话是否存在
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            bool: 会话是否存在
        """
        try:
            logger.info(f"🔍 检查会话是否存在: {conversation_id}")
            
            # 检查会话数据是否存在
            session_data = await self.session_manager.get_session(conversation_id)
            
            if session_data:
                logger.info(f"✅ 会话存在: {conversation_id}")
                return True
            else:
                logger.info(f"❌ 会话不存在: {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"检查会话存在性失败: {conversation_id}, 错误: {e}")
            return False
    
    async def should_resume_or_create(self, conversation_id: Optional[str], user_id: str) -> Tuple[str, bool]:
        """
        判断是恢复现有会话还是创建新会话
        
        Args:
            conversation_id: 可选的会话ID
            user_id: 用户ID
            
        Returns:
            Tuple[str, bool]: (实际使用的会话ID, 是否为恢复模式)
        """
        try:
            # 如果没有提供 conversation_id，直接创建新会话
            if not conversation_id:
                logger.info(f"📝 未提供会话ID，创建新会话 for user: {user_id}")
                new_session_id = await self.create_new_conversation(user_id)
                return new_session_id, False
            
            # 检查提供的会话是否存在
            exists = await self.check_conversation_exists(conversation_id)
            
            if exists:
                logger.info(f"🔄 会话存在，进入恢复模式: {conversation_id}")
                return conversation_id, True
            else:
                logger.info(f"📝 会话不存在，创建新会话: {conversation_id} -> new session")
                new_session_id = await self.create_new_conversation(user_id)
                return new_session_id, False
                
        except Exception as e:
            logger.error(f"判断恢复或创建失败: {e}")
            # 出错时默认创建新会话
            new_session_id = await self.create_new_conversation(user_id)
            return new_session_id, False
    
    async def create_new_conversation(self, user_id: str) -> str:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 新创建的会话ID
        """
        try:
            logger.info(f"📝 创建新会话 for user: {user_id}")
            session_id = await self.session_manager.create_session(user_id)
            logger.info(f"✅ 新会话创建成功: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建新会话失败: {e}")
            raise
    
    async def prepare_resume_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        准备恢复上下文
        获取会话的历史任务和状态信息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复上下文数据
        """
        try:
            logger.info(f"📋 准备恢复上下文: {conversation_id}")
            
            # 获取会话信息
            session_data = await self.session_manager.get_session(conversation_id)
            if not session_data:
                logger.warning(f"会话不存在，无法准备恢复上下文: {conversation_id}")
                return None
            
            # 获取会话的所有任务
            task_ids = await self.session_manager.get_session_tasks(conversation_id)
            
            # 获取最近的任务状态
            recent_tasks = []
            for task_id in task_ids[-5:]:  # 最近5个任务
                task_data = await self.session_manager.get_task_status(task_id)
                if task_data:
                    recent_tasks.append(task_data)
            
            context = {
                "session_id": conversation_id,
                "user_id": session_data.get("user_id"),
                "created_at": session_data.get("created_at"),
                "last_activity": session_data.get("last_activity"),
                "total_tasks": len(task_ids),
                "recent_tasks": recent_tasks,
                "active_tasks": session_data.get("active_tasks", [])
            }
            
            logger.info(f"✅ 恢复上下文准备完成: {conversation_id}, 任务数: {len(task_ids)}")
            return context
            
        except Exception as e:
            logger.error(f"准备恢复上下文失败: {conversation_id}, 错误: {e}")
            return None
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话摘要信息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话摘要
        """
        try:
            context = await self.prepare_resume_context(conversation_id)
            if not context:
                return None
            
            # 统计信息
            recent_tasks = context.get("recent_tasks", [])
            completed_tasks = [t for t in recent_tasks if t.get("status") == "completed"]
            failed_tasks = [t for t in recent_tasks if t.get("status") == "failed"]
            paused_tasks = [t for t in recent_tasks if t.get("status") == "paused"]
            
            summary = {
                "conversation_id": conversation_id,
                "user_id": context.get("user_id"),
                "created_at": context.get("created_at"),
                "last_activity": context.get("last_activity"),
                "statistics": {
                    "total_tasks": context.get("total_tasks", 0),
                    "completed_tasks": len(completed_tasks),
                    "failed_tasks": len(failed_tasks),
                    "paused_tasks": len(paused_tasks)
                },
                "can_resume": len(paused_tasks) > 0,
                "last_task": recent_tasks[0] if recent_tasks else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取会话摘要失败: {conversation_id}, 错误: {e}")
            return None
    
    async def validate_resume_request(self, conversation_id: str, task_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证恢复请求的有效性
        
        Args:
            conversation_id: 会话ID
            task_id: 可选的任务ID
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 检查会话是否存在
            if not await self.check_conversation_exists(conversation_id):
                return False, f"会话不存在: {conversation_id}"
            
            # 如果指定了任务ID，检查任务是否存在且属于该会话
            if task_id:
                task_data = await self.session_manager.get_task_status(task_id)
                if not task_data:
                    return False, f"任务不存在: {task_id}"
                
                task_session_id = task_data.get("session_id")
                if task_session_id != conversation_id:
                    return False, f"任务不属于指定会话: {task_id} -> {task_session_id} != {conversation_id}"
                
                # 检查任务状态是否可以恢复
                task_status = task_data.get("status")
                if task_status not in ["paused", "failed"]:
                    return False, f"任务状态不支持恢复: {task_status}"
            
            return True, "验证通过"
            
        except Exception as e:
            logger.error(f"验证恢复请求失败: {e}")
            return False, f"验证失败: {str(e)}"
    
    async def close(self):
        """关闭连接"""
        if self.session_manager:
            await self.session_manager.close()


def get_conversation_service() -> ConversationService:
    """获取会话服务实例"""
    return ConversationService()
