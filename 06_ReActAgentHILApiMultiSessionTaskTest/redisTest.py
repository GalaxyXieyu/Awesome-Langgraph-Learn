import asyncio
import json
import logging
import redis.asyncio as redis
from datetime import timedelta
import time
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
from utils.config import Config
from utils.models import AgentResponse



# Author:@南哥AGI研习社 (B站 or YouTube 搜索“南哥AGI研习社”)


logger = logging.getLogger(__name__)


# Redis管理
class RedisSessionManager:
    # 初始化 RedisSessionManager 实例
    # 配置 Redis 连接参数和默认会话超时时间
    def __init__(self, redis_host: str, redis_port: int, redis_db: int, session_timeout: int):
        # 创建 Redis 客户端连接
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        # 设置默认会话过期时间（秒）
        self.session_timeout = session_timeout

    # 关闭 Redis 连接
    async def close(self):
        # 异步关闭 Redis 客户端连接
        await self.redis_client.close()

    # 创建指定用户的新会话
    # 存储结构：session:{user_id}:{session_id}:{task_id} = {
    #   "session_id": session_id,
    #   "task_id": task_id,
    #   "status": "idle|running|completed|error",
    #   "last_response": AgentResponse,
    #   "last_query": str,
    #   "last_updated": timestamp
    # }
    async def create_session(self, user_id: str, task_id: str, session_id: Optional[str] = None, status: str = "active",
                            last_query: Optional[str] = None, last_response: Optional['AgentResponse'] = None,
                            last_updated: Optional[float] = None, ttl: Optional[int] = None) -> str:
        # 如果未提供 session_id，生成新的 UUID
        if session_id is None:
            session_id = str(uuid.uuid4())
        # 如果未提供最后更新时间，设置为 0 秒
        if last_updated is None:
            last_updated = str(timedelta(seconds=0))
        # 使用提供的 TTL 或默认的 session_timeout
        effective_ttl = ttl if ttl is not None else self.session_timeout

        # 构造会话数据结构
        session_data = {
            "session_id": session_id,
            "task_id": task_id,
            "status": status,
            "last_response": last_response.model_dump() if isinstance(last_response, BaseModel) else last_response,
            "last_query": last_query,
            "last_updated": last_updated
        }

        # 将会话数据存储到 Redis，使用 JSON 序列化，并设置过期时间
        session_key = f"session:{user_id}:{session_id}:{task_id}"
        await self.redis_client.set(
            session_key,
            json.dumps(session_data, default=lambda o: o.__dict__ if not hasattr(o, 'model_dump') else o.model_dump()),
            ex=effective_ttl
        )
        # 将 session_id:task_id 添加到用户的会话列表中
        await self.redis_client.sadd(f"user_sessions:{user_id}", f"{session_id}:{task_id}")
        # 将 task_id 添加到会话的任务映射中
        await self.redis_client.sadd(f"task_mapping:{user_id}:{session_id}", task_id)
        # 为任务映射设置过期时间
        await self.redis_client.expire(f"task_mapping:{user_id}:{session_id}", effective_ttl)
        # 记录创建会话的日志
        logger.info(f"Created session {session_id} with task {task_id} for user {user_id}")
        # 返回新创建的 session_id
        return session_id

    # 更新指定用户的特定会话数据
    async def update_session(self, user_id: str, session_id: str, task_id: str, status: Optional[str] = None,
                            last_query: Optional[str] = None, last_response: Optional['AgentResponse'] = None,
                            last_updated: Optional[float] = None, ttl: Optional[int] = None) -> bool:
        # 检查会话是否存在
        session_key = f"session:{user_id}:{session_id}:{task_id}"
        if await self.redis_client.exists(session_key):
            # 获取当前会话数据
            current_data = await self.get_session_by_task(user_id, session_id, task_id)
            if not current_data:
                return False
            # 更新提供的字段
            if status is not None:
                current_data["status"] = status
            if last_response is not None:
                if isinstance(last_response, BaseModel):
                    current_data["last_response"] = last_response.model_dump()
                else:
                    current_data["last_response"] = last_response
            if last_query is not None:
                current_data["last_query"] = last_query
            if last_updated is not None:
                current_data["last_updated"] = last_updated
            # 使用提供的 TTL 或默认的 session_timeout
            effective_ttl = ttl if ttl is not None else self.session_timeout
            # 将更新后的数据重新存储到 Redis，并设置新的过期时间
            await self.redis_client.set(
                session_key,
                json.dumps(current_data,
                           default=lambda o: o.__dict__ if not hasattr(o, 'model_dump') else o.model_dump()),
                ex=effective_ttl
            )
            # 更新任务映射的过期时间
            await self.redis_client.expire(f"task_mapping:{user_id}:{session_id}", effective_ttl)
            # 记录更新会话的日志
            logger.info(f"Updated session {session_id} with task {task_id} for user {user_id}")
            # 更新成功返回 True
            return True
        # 会话不存在返回 False
        return False

    # 检查指定用户ID是否存在
    async def user_id_exists(self, user_id: str) -> bool:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)
        # 检查是否存在 user_sessions:{user_id} 键
        return (await self.redis_client.exists(f"user_sessions:{user_id}")) > 0

    # 检查指定用户ID的指定session_id是否存在
    async def session_id_exists(self, user_id: str, session_id: str) -> bool:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)
        # 检查是否存在 task_mapping:{user_id}:{session_id} 键
        return (await self.redis_client.exists(f"task_mapping:{user_id}:{session_id}")) > 0

    # 检查指定用户ID的指定session_id的指定task_id是否存在
    async def session_task_id_exists(self, user_id: str, session_id: str, task_id: str) -> bool:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)
        # 检查指定用户的特定会话和任务是否存在
        return (await self.redis_client.exists(f"session:{user_id}:{session_id}:{task_id}")) > 0

    # 获取系统内所有用户下的所有session_id
    async def get_all_users_session_ids(self) -> Dict[str, List[str]]:
        # 清理所有用户的无效会话
        await self.cleanup_all_tasks()
        # 初始化结果字典
        result = {}
        # 遍历所有 user_sessions:* 键
        async for key in self.redis_client.scan_iter("user_sessions:*"):
            # 提取用户 ID
            user_id = key.split(":", 1)[1]
            # 获取该用户的所有 session_id:task_id
            session_tasks = await self.redis_client.smembers(f"user_sessions:{user_id}")
            # 提取唯一的 session_id
            session_ids = list({session_task.split(":")[0] for session_task in session_tasks})
            # 如果集合非空，将用户 ID 和 session_id 列表存入结果字典
            if session_ids:
                result[user_id] = session_ids
        # 返回所有用户及其 session_id
        return result

    # 获取系统内所有用户下的所有会话的总数
    async def get_session_count(self) -> int:
        # 清理所有用户的无效会话
        await self.cleanup_all_tasks()
        # 初始化唯一 session_id 集合
        unique_session_ids = set()
        # 遍历所有 user_sessions:* 键
        async for key in self.redis_client.scan_iter("user_sessions:*"):
            # 提取用户 ID
            user_id = key.split(":", 1)[1]
            # 获取该用户的所有 session_id:task_id
            session_tasks = await self.redis_client.smembers(f"user_sessions:{user_id}")
            # 提取唯一的 session_id
            for session_task in session_tasks:
                session_id = session_task.split(":")[0]
                unique_session_ids.add(f"{user_id}:{session_id}")
        # 返回唯一会话总数
        return len(unique_session_ids)

    # 获取指定用户ID的所有session_id
    async def get_all_session_ids(self, user_id: str) -> List[str]:
        # 在查询前清理指定用户的无效会话，确保返回的 session_id 都是有效的
        await self.cleanup_user_tasks(user_id)
        # 从 Redis 获取用户的所有 session_id:task_id
        session_tasks = await self.redis_client.smembers(f"user_sessions:{user_id}")
        # 提取唯一的 session_id
        session_ids = list({session_task.split(":")[0] for session_task in session_tasks})
        # 将集合转换为列表并返回
        return session_ids

    # 获取指定用户ID的最近一次修改的会话ID
    async def get_user_active_session_id(self, user_id: str) -> str | None:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)

        # 获取用户的所有 session_id:task_id
        session_tasks = await self.redis_client.smembers(f"user_sessions:{user_id}")

        # 初始化最新会话信息
        latest_session_id = None
        latest_timestamp = -1  # 使用负值确保任何有效时间戳都更大

        # 遍历每个 session_id:task_id，获取会话数据
        for session_task in session_tasks:
            session_id, task_id = session_task.split(":", 1)
            session = await self.get_session_by_task(user_id, session_id, task_id)
            if session:
                last_updated = session.get('last_updated')
                # 过滤掉 last_updated 为 "0:00:00" 的记录
                if isinstance(last_updated, str) and last_updated == "0:00:00":
                    continue
                # 确保 last_updated 是数字（时间戳）
                if isinstance(last_updated, (int, float)) and last_updated > latest_timestamp:
                    latest_timestamp = last_updated
                    latest_session_id = session_id

        # 返回最新会话ID，如果没有有效会话则返回 None
        return latest_session_id

    # 清理系统内所有无效的任务
    async def cleanup_all_tasks(self) -> None:
        # 遍历所有 user_sessions:* 键
        async for user_key in self.redis_client.scan_iter("user_sessions:*"):
            # 提取用户 ID
            user_id = user_key.split(":", 1)[1]
            # 获取用户会话集合中的所有 session_id:task_id 条目
            session_tasks = await self.redis_client.smembers(f"user_sessions:{user_id}")
            # 遍历每个 session_id:task_id，检查对应的会话数据是否存在
            for session_task in session_tasks:
                session_id, task_id = session_task.split(":", 1)
                if not await self.redis_client.exists(f"session:{user_id}:{session_id}:{task_id}"):
                    # 如果会话数据已过期或不存在，从用户会话集合中移除条目
                    await self.redis_client.srem(f"user_sessions:{user_id}", session_task)
                    # 从任务映射中移除 task_id
                    await self.redis_client.srem(f"task_mapping:{user_id}:{session_id}", task_id)
                    # 删除任务状态数据
                    await self.redis_client.delete(f"task:{task_id}")
                    # 记录移除无效任务的日志
                    logger.info(f"Removed expired task_id {task_id} for user {user_id} and session {session_id}")
            # 如果用户会话集合为空，删除集合
            if not await self.redis_client.scard(f"user_sessions:{user_id}"):
                await self.redis_client.delete(f"user_sessions:{user_id}")
                # 记录删除空用户会话集合的日志
                logger.info(f"Deleted empty user_sessions collection for user {user_id}")
        # 遍历所有 task_mapping:* 键
        async for key in self.redis_client.scan_iter("task_mapping:*"):
            # 提取用户 ID 和会话 ID
            user_id, session_id = key.split(":", 2)[1:]
            # 获取会话的所有 task_id
            task_ids = await self.redis_client.smembers(f"task_mapping:{user_id}:{session_id}")
            # 遍历每个 task_id，检查对应的会话数据是否存在
            for task_id in task_ids:
                if not await self.redis_client.exists(f"session:{user_id}:{session_id}:{task_id}"):
                    # 如果会话数据已过期或不存在，从任务映射中移除 task_id
                    await self.redis_client.srem(f"task_mapping:{user_id}:{session_id}", task_id)
                    # 从用户会话集合中移除对应的 session_id:task_id
                    await self.redis_client.srem(f"user_sessions:{user_id}", f"{session_id}:{task_id}")
                    # 删除任务状态数据
                    await self.redis_client.delete(f"task:{task_id}")
                    # 记录移除无效任务的日志
                    logger.info(f"Removed expired task_id {task_id} for user {user_id} and session {session_id}")
            # 如果任务映射集合为空，删除集合
            if not await self.redis_client.scard(f"task_mapping:{user_id}:{session_id}"):
                await self.redis_client.delete(f"task_mapping:{user_id}:{session_id}")
                # 记录删除空任务映射的日志
                logger.info(f"Deleted empty task_mapping for user {user_id} and session {session_id}")
            # 如果用户会话集合为空，删除集合
            if not await self.redis_client.scard(f"user_sessions:{user_id}"):
                await self.redis_client.delete(f"user_sessions:{user_id}")
                # 记录删除空用户会话集合的日志
                logger.info(f"Deleted empty user_sessions collection for user {user_id}")

    # 清理指定用户ID的所有无效任务
    async def cleanup_user_tasks(self, user_id: str) -> None:
        # 获取用户会话集合中的所有 session_id:task_id 条目
        session_tasks = await self.redis_client.smembers(f"user_sessions:{user_id}")
        # 遍历每个 session_id:task_id，检查对应的会话数据是否存在
        for session_task in session_tasks:
            session_id, task_id = session_task.split(":", 1)
            if not await self.redis_client.exists(f"session:{user_id}:{session_id}:{task_id}"):
                # 如果会话数据已过期或不存在，从用户会话集合中移除条目
                await self.redis_client.srem(f"user_sessions:{user_id}", session_task)
                # 从任务映射中移除 task_id
                await self.redis_client.srem(f"task_mapping:{user_id}:{session_id}", task_id)
                # 删除任务状态数据
                await self.redis_client.delete(f"task:{task_id}")
                # 记录移除无效任务的日志
                logger.info(f"Removed expired task_id {task_id} for user {user_id} and session {session_id}")
        # 遍历指定用户的所有 task_mapping:* 键
        async for key in self.redis_client.scan_iter(f"task_mapping:{user_id}:*"):
            # 提取会话 ID
            session_id = key.split(":", 2)[2]
            # 获取会话的所有 task_id
            task_ids = await self.redis_client.smembers(f"task_mapping:{user_id}:{session_id}")
            # 遍历每个 task_id，检查对应的会话数据是否存在
            for task_id in task_ids:
                if not await self.redis_client.exists(f"session:{user_id}:{session_id}:{task_id}"):
                    # 如果会话数据已过期或不存在，从任务映射中移除 task_id
                    await self.redis_client.srem(f"task_mapping:{user_id}:{session_id}", task_id)
                    # 从用户会话集合中移除对应的 session_id:task_id
                    await self.redis_client.srem(f"user_sessions:{user_id}", f"{session_id}:{task_id}")
                    # 删除任务状态数据
                    await self.redis_client.delete(f"task:{task_id}")
                    # 记录移除无效任务的日志
                    logger.info(f"Removed expired task_id {task_id} for user {user_id} and session {session_id}")
            # 如果任务映射集合为空，删除集合
            if not await self.redis_client.scard(f"task_mapping:{user_id}:{session_id}"):
                await self.redis_client.delete(f"task_mapping:{user_id}:{session_id}")
                # 记录删除空任务映射的日志
                logger.info(f"Deleted empty task_mapping for user {user_id} and session {session_id}")
        # 如果用户会话集合为空，删除集合
        if not await self.redis_client.scard(f"user_sessions:{user_id}"):
            await self.redis_client.delete(f"user_sessions:{user_id}")
            # 记录删除空用户会话集合的日志
            logger.info(f"Deleted empty user_sessions collection for user {user_id}")

    # 获取指定用户当前会话ID的状态数据
    async def get_session(self, user_id: str, session_id: str) -> List[dict]:
        # 在查询前清理指定用户的无效会话，确保返回的 session_id 都是有效的
        await self.cleanup_user_tasks(user_id)
        # 获取会话的所有 task_id
        task_ids = await self.redis_client.smembers(f"task_mapping:{user_id}:{session_id}")
        # 初始化会话数据列表
        sessions = []
        # 遍历每个 task_id，获取对应的会话数据
        for task_id in task_ids:
            session = await self.get_session_by_task(user_id, session_id, task_id)
            if session:
                sessions.append(session)
        # 返回会话数据列表
        return sessions

    # 获取指定用户ID的指定会话ID的所有task_id
    async def get_session_task_ids(self, user_id: str, session_id: str) -> List[str]:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)
        # 从 Redis 获取会话的所有 task_id
        task_ids = await self.redis_client.smembers(f"task_mapping:{user_id}:{session_id}")
        # 将集合转换为列表并返回
        return list(task_ids)

    # 获取指定用户当前会话和任务ID的对应的状态数据
    async def get_session_by_task(self, user_id: str, session_id: str, task_id: str) -> Optional[dict]:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)
        # 从 Redis 获取会话数据
        session_key = f"session:{user_id}:{session_id}:{task_id}"
        session_data = await self.redis_client.get(session_key)
        # 如果会话不存在，返回 None
        if not session_data:
            return None
        # 解析 JSON 数据
        session = json.loads(session_data)
        # 处理 last_response 字段，尝试转换为 AgentResponse 对象
        if session and "last_response" in session:
            if session["last_response"] is not None:
                try:
                    session["last_response"] = AgentResponse(**session["last_response"])
                except Exception as e:
                    # 记录转换失败的错误日志
                    logger.error(f"转换 last_response 失败: {e}")
                    session["last_response"] = None
        # 返回会话数据
        return session

    # 设置任务状态并绑定到用户和会话
    async def set_task_status(self, task_id: str, status: str, result: Optional[Dict] = None,
                            error: Optional[str] = None, user_id: Optional[str] = None,
                            session_id: Optional[str] = None):
        # 构造任务状态数据
        task_data = {
            "task_id": task_id,
            "status": status,
            "result": result,
            "error": error,
            "user_id": user_id,
            "session_id": session_id
        }
        # 将任务状态存储到 Redis，设置过期时间
        await self.redis_client.set(
            f"task:{task_id}",
            json.dumps(task_data),
            ex=Config.TASK_TTL
        )
        # 如果提供了 user_id 和 session_id，将 task_id 绑定到用户和会话
        if user_id and session_id:
            await self.redis_client.sadd(f"task_mapping:{user_id}:{session_id}", task_id)
            await self.redis_client.expire(f"task_mapping:{user_id}:{session_id}", Config.TASK_TTL)
            logger.info(f"任务 {task_id} 已绑定到用户 {user_id} 和会话 {session_id}")

    # 获取单个任务的状态
    async def get_single_task_status(self, task_id: str) -> Optional[Dict]:
        # 从 Redis 获取任务状态数据
        task_data = await self.redis_client.get(f"task:{task_id}")
        # 如果任务数据存在，返回解析后的 JSON 数据
        if task_data:
            return json.loads(task_data)
        # 如果任务不存在，返回 None
        return None

    # 获取指定用户ID和会话ID下所有任务的ID和状态值（拼接为 task_id:status 格式）
    async def get_task_status(self, user_id: str, session_id: str) -> List[str]:
        # 在查询前清理指定用户的无效会话
        await self.cleanup_user_tasks(user_id)
        # 获取会话的所有 task_id
        task_ids = await self.redis_client.smembers(f"task_mapping:{user_id}:{session_id}")
        # 初始化任务状态列表
        task_statuses = []
        # 遍历每个 task_id，获取对应的任务状态
        for task_id in task_ids:
            task_data = await self.get_single_task_status(task_id)
            if task_data and "status" in task_data:
                # 拼接 task_id 和 status 值，添加到列表
                task_statuses.append(f"{task_id}:{task_data['status']}")
        # 返回任务ID和状态值的拼接列表
        return task_statuses

    # 删除指定用户指定会话或指定的任务状态数据
    async def delete_session(self, user_id: str, session_id: str, task_id: Optional[str] = None) -> bool:
        # 如果提供了 task_id，仅删除特定任务的会话
        if task_id:
            session_key = f"session:{user_id}:{session_id}:{task_id}"
            # 从用户会话列表中移除 session_id:task_id
            await self.redis_client.srem(f"user_sessions:{user_id}", f"{session_id}:{task_id}")
            # 从任务映射中移除 task_id
            await self.redis_client.srem(f"task_mapping:{user_id}:{session_id}", task_id)
            # 删除会话数据并记录日志
            deleted = await self.redis_client.delete(session_key) > 0
            logger.info(f"删除会话数据 {user_id}:{session_id}:{task_id}")
            # 如果 task_mapping 集合为空，删除它
            if not await self.redis_client.scard(f"task_mapping:{user_id}:{session_id}"):
                await self.redis_client.delete(f"task_mapping:{user_id}:{session_id}")
                logger.info(f"删除task_mapping 集合为空 {user_id}:{session_id}")
            return deleted
        else:
            # 如果未提供 task_id，删除整个会话的所有任务
            task_ids = await self.redis_client.smembers(f"task_mapping:{user_id}:{session_id}")
            deleted = False
            for task_id in task_ids:
                session_key = f"session:{user_id}:{session_id}:{task_id}"
                # 从用户会话列表中移除 session_id:task_id
                await self.redis_client.srem(f"user_sessions:{user_id}", f"{session_id}:{task_id}")
                # 删除会话数据
                if await self.redis_client.delete(session_key) > 0:
                    deleted = True
                # 记录删除日志
                logger.info(f"用户会话列表中移除 {user_id}:{session_id}:{task_id}")
            # 删除任务映射集合
            await self.redis_client.delete(f"task_mapping:{user_id}:{session_id}")
            return deleted



# 测试代码
async def test_redis_session_manager():
    # 初始化 RedisSessionManager
    session_manager = RedisSessionManager(
        redis_host="localhost",
        redis_port=6379,
        redis_db=0,
        session_timeout=60 # 设置默认会话超时为10秒
    )

    try:
        # 测试1: 创建新用户、会话及任务
        user_id = "user_id_001"
        session_id = "session_id_001"
        task_id = str(uuid.uuid4())
        query = "测试查询"
        # 初始时未提供 session_id，将自动生成，使用自定义 TTL
        session_id = await session_manager.create_session(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            last_query=query,
            status="idle",
            ttl=180
        )
        print(f"创建的用户ID、会话ID和任务ID: {user_id}:{session_id}:{task_id}\n\n")
        print(f"创建后，检查用户是否存在:: {await session_manager.user_id_exists(user_id)}")
        print(f"创建后，检查会话是否存在: {await session_manager.session_id_exists(user_id, session_id)}")
        print(f"创建后，检查任务是否存在: {await session_manager.session_task_id_exists(user_id, session_id, task_id)}")

        # # 测试2: 更新会话并延长 TTL
        # user_id = "user_id_002"
        # session_id ="session_id_001"
        # task_id = "e3a7b7c3-fb5c-4349-90c0-e65cf06450b7"
        # await session_manager.update_session(
        #     user_id=user_id,
        #     session_id=session_id,
        #     task_id=task_id,
        #     status="running",
        #     last_query="更新后的查询",
        #     last_updated=time.time(),
        #     ttl=600
        # )
        # print(f"更新的用户ID、会话ID和任务ID: {user_id}:{session_id}:{task_id}\n\n")
        # print(f"更新后，检查用户是否存在:: {await session_manager.user_id_exists(user_id)}")
        # print(f"更新后，检查会话是否存在: {await session_manager.session_id_exists(user_id, session_id)}")
        # print(f"更新后，检查任务是否存在: {await session_manager.session_task_id_exists(user_id, session_id, task_id)}")

        # # 测试3: 获取系统内所有用户下的所有 session_id
        # session_ids = await session_manager.get_all_users_session_ids()
        # print(f"系统内所有的会话列表: {session_ids}")

        # # 测试4: 获取系统内所有用户下的所有会话的总数
        # count = await session_manager.get_session_count()
        # print(f"当前系统内所有的会话数量: {count}")

        # # 测试5: 获取指定用户的所有session_id
        # user_id = "user_id_001"
        # session_ids = await session_manager.get_all_session_ids(user_id)
        # print(f"指定用户 {user_id} 的会话列表: {session_ids}")

        # # 测试6: 获取指定用户ID的最近一次修改的会话ID
        # user_id = "user_id_001"
        # result = await session_manager.get_user_active_session_id(user_id)
        # print(f"指定用户 {user_id}当前激活的会话是: {result}")

        # # 测试7: 清理系统内所有无效的任务
        # result = await session_manager.cleanup_all_tasks()
        # print(f"清理所有用户的无效会话: {result}")

        # # 测试8: 清理指定用户ID的所有无效任务
        # user_id = "user_id_001"
        # result = await session_manager.cleanup_user_tasks(user_id)
        # print(f"清理指定用户{user_id}的无效会话: {result}")

        # # 测试9: 获取指定用户当前会话ID的状态数据
        # user_id = "user_id_001"
        # session_id ="session_id_001"
        # session = await session_manager.get_session(user_id, session_id)
        # print(f"指定用户下会话 {user_id}:{session_id} 的状态数据是: {session}")

        # # 测试10: 获取指定用户指定会话的所有task_id
        # user_id = "user_id_001"
        # session_id ="session_id_001"
        # task_ids = await session_manager.get_session_task_ids(user_id, session_id)
        # print(f"指定用户会话 {user_id}:{session_id} 的任务列表: {task_ids}")

        # # 测试11: 获取指定用户指定会话指定任务ID的状态数据
        # user_id = "user_id_002"
        # session_id ="session_id_001"
        # task_id ="e3a7b7c3-fb5c-4349-90c0-e65cf06450b7"
        # session = await session_manager.get_session_by_task(user_id, session_id, task_id)
        # print(f"指定用户下会话 {user_id}:{session_id}:{task_id} 的状态数据是: {session}")

        # # 测试12: 删除指定用户的特定会话
        # user_id = "test_user_1"
        # session_id = "e9933ef9-0b92-45d1-9e4c-1209800e17e7"
        # result = await session_manager.delete_session(user_id, session_id)
        # print(f"删除指定用户的特定会话{user_id}:{session_id}: {result}")


    finally:
        pass
        # # 关闭 Redis 连接
        # await session_manager.close()
        # print("\n=== 测试完成，Redis 连接已关闭 ===")


# 运行测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_redis_session_manager())