"""
会话管理器
基于 Redis 的会话和任务状态管理
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .redis_client import RedisClient, get_redis_client
from .logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """会话管理器"""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis_client = redis_client or get_redis_client()
        self.session_ttl = 86400  # 24小时
        self.task_ttl = 3600     # 1小时
    
    async def create_session(self, user_id: str) -> str:
        """创建新会话"""
        session_id = f"session_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "active_tasks": json.dumps([]),
            "status": "active"
        }
        
        # 存储会话信息
        session_key = f"session:{session_id}"
        self.redis_client.hmset(session_key, session_data)
        self.redis_client.expire(session_key, self.session_ttl)
        
        # 添加到用户会话列表
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis_client.sadd(user_sessions_key, session_id)
        self.redis_client.expire(user_sessions_key, self.session_ttl)
        
        logger.info(f"创建会话: {session_id} for user: {user_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        session_key = f"session:{session_id}"
        session_data = self.redis_client.hgetall(session_key)
        
        if not session_data:
            return None
        
        # 解析 JSON 字段
        if "active_tasks" in session_data:
            session_data["active_tasks"] = json.loads(session_data["active_tasks"])
        
        return session_data
    
    async def update_session(
        self, 
        user_id: str, 
        session_id: str, 
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        last_response: Optional[Any] = None,
        last_updated: Optional[float] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """更新会话信息"""
        session_key = f"session:{session_id}"
        
        # 获取当前会话数据
        session_data = await self.get_session(session_id)
        if not session_data:
            logger.warning(f"会话不存在: {session_id}")
            return False
        
        # 更新字段
        updates = {
            "last_activity": datetime.now().isoformat()
        }
        
        if task_id:
            active_tasks = session_data.get("active_tasks", [])
            if task_id not in active_tasks:
                active_tasks.append(task_id)
            updates["active_tasks"] = json.dumps(active_tasks)
        
        if status:
            updates["status"] = status
        
        if last_response:
            updates["last_response"] = json.dumps(last_response, default=str)
        
        if last_updated:
            updates["last_updated"] = str(last_updated)
        
        # 更新 Redis
        self.redis_client.hmset(session_key, updates)
        
        # 更新 TTL
        if ttl:
            self.redis_client.expire(session_key, ttl)
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session_key = f"session:{session_id}"
        
        # 获取会话信息
        session_data = await self.get_session(session_id)
        if session_data:
            user_id = session_data.get("user_id")
            
            # 从用户会话列表中移除
            if user_id:
                user_sessions_key = f"user_sessions:{user_id}"
                self.redis_client.srem(user_sessions_key, session_id)
        
        # 删除会话
        result = self.redis_client.delete(session_key)
        
        logger.info(f"删除会话: {session_id}")
        return bool(result)
    
    async def set_task_status(
        self,
        task_id: str,
        status: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """设置任务状态"""
        task_key = f"task:{task_id}"
        logger.info(f"📝 设置任务状态: {task_key} -> {status}")
        
        task_data = {
            "task_id": task_id,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if user_id:
            task_data["user_id"] = user_id
        
        if session_id:
            task_data["session_id"] = session_id
        
        if result:
            task_data["result"] = json.dumps(result, default=str)
        
        if error:
            task_data["error"] = error
        
        if metadata:
            task_data["metadata"] = json.dumps(metadata, default=str)
        
        # 存储任务状态
        self.redis_client.hmset(task_key, task_data)
        self.redis_client.expire(task_key, self.task_ttl)
        
        # 添加到任务索引
        if user_id:
            user_tasks_key = f"user_tasks:{user_id}"
            self.redis_client.sadd(user_tasks_key, task_id)
            self.redis_client.expire(user_tasks_key, self.task_ttl)
        
        if session_id:
            session_tasks_key = f"session_tasks:{session_id}"
            self.redis_client.sadd(session_tasks_key, task_id)
            self.redis_client.expire(session_tasks_key, self.task_ttl)
        
        logger.info(f"设置任务状态: {task_id} -> {status}")
        return True
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task_key = f"task:{task_id}"
        logger.info(f"🔍 从 Redis 查询任务: {task_key}")

        task_data = self.redis_client.hgetall(task_key)
        logger.info(f"📊 Redis 原始数据: {task_data}")

        if not task_data:
            logger.warning(f"❌ Redis 中未找到任务: {task_key}")
            return None
        
        # 解析 JSON 字段
        for field in ["result", "metadata"]:
            if field in task_data and task_data[field]:
                try:
                    task_data[field] = json.loads(task_data[field])
                except json.JSONDecodeError:
                    logger.warning(f"解析任务字段失败: {field}")
        
        return task_data
    
    async def get_user_tasks(self, user_id: str) -> List[str]:
        """获取用户的所有任务"""
        user_tasks_key = f"user_tasks:{user_id}"
        return list(self.redis_client.smembers(user_tasks_key))
    
    async def get_session_tasks(self, session_id: str) -> List[str]:
        """获取会话的所有任务"""
        session_tasks_key = f"session_tasks:{session_id}"
        return list(self.redis_client.smembers(session_tasks_key))
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """获取用户的所有会话"""
        user_sessions_key = f"user_sessions:{user_id}"
        return list(self.redis_client.smembers(user_sessions_key))
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """清理过期数据"""
        # 这里可以实现更复杂的清理逻辑
        # 目前依赖 Redis 的 TTL 自动过期
        return {"message": "依赖 Redis TTL 自动清理"}
    
    async def close(self):
        """关闭连接"""
        if self.redis_client:
            self.redis_client.close()


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    return SessionManager()
