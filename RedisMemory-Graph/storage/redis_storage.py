"""
Redis存储实现
基于Redis的高性能会话存储，支持TTL和集群部署
"""

import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Generator
from datetime import datetime, timedelta

import redis
import redis.asyncio as aioredis
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from .base import BaseStorage, StorageType, StorageFactory
from ..config import get_redis_config

logger = logging.getLogger(__name__)


class RedisStorage(BaseStorage):
    """Redis存储实现
    
    使用Redis作为后端存储，提供高性能的会话持久化
    优点：极高的读写性能，支持TTL，支持集群部署，内置向量搜索
    缺点：需要额外的Redis服务，内存成本较高
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """初始化Redis存储
        
        Args:
            connection_string: Redis连接字符串，格式：redis://[password@]host:port[/db]
            **kwargs: 额外配置参数
                - ttl: TTL配置字典
                - pool_size: 连接池大小
                - retry_attempts: 重试次数
                - socket_timeout: Socket超时时间
        """
        super().__init__(connection_string, **kwargs)
        
        # 获取Redis配置
        self.redis_config = get_redis_config()
        
        # 合并配置
        self.ttl_config = kwargs.get('ttl', {
            'default_ttl': self.redis_config.default_ttl,
            'refresh_on_read': self.redis_config.refresh_on_read
        })
        
        # 连接配置
        self.pool_config = {
            'max_connections': kwargs.get('max_connections', self.redis_config.max_connections),
            'socket_timeout': kwargs.get('socket_timeout', self.redis_config.socket_timeout),
            'socket_connect_timeout': kwargs.get('socket_connect_timeout', self.redis_config.socket_connect_timeout),
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
        
        # 初始化连接池和Saver
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._async_redis_pool: Optional[aioredis.ConnectionPool] = None
        self._redis_saver: Optional[RedisSaver] = None
        self._async_redis_saver: Optional[AsyncRedisSaver] = None
        
        # 统计信息
        self._stats = {
            'total_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'ttl_refreshes': 0,
            'created_at': datetime.now()
        }
        
        logger.info(f"Redis存储初始化: {connection_string}")
    
    def get_storage_type(self) -> StorageType:
        """获取存储类型"""
        return StorageType.REDIS
    
    def _create_redis_pool(self) -> redis.ConnectionPool:
        """创建Redis连接池"""
        if self._redis_pool is None:
            self._redis_pool = redis.ConnectionPool.from_url(
                self.connection_string,
                **self.pool_config
            )
        return self._redis_pool
    
    def _create_async_redis_pool(self) -> aioredis.ConnectionPool:
        """创建异步Redis连接池"""
        if self._async_redis_pool is None:
            self._async_redis_pool = aioredis.ConnectionPool.from_url(
                self.connection_string,
                **self.pool_config
            )
        return self._async_redis_pool
    
    def setup(self) -> bool:
        """设置Redis存储"""
        try:
            # 创建同步RedisSaver
            self._redis_saver = RedisSaver.from_conn_string(
                self.connection_string,
                ttl=self.ttl_config
            )
            self._redis_saver.setup()
            
            self._is_setup = True
            self.connection_info.is_connected = True
            self.connection_info.connection_time = datetime.now()
            
            logger.info("Redis存储设置完成")
            return True
            
        except Exception as e:
            logger.error(f"Redis存储设置失败: {e}")
            self.connection_info.error_message = str(e)
            return False
    
    async def asetup(self) -> bool:
        """异步设置Redis存储"""
        try:
            # 创建异步RedisSaver
            self._async_redis_saver = AsyncRedisSaver.from_conn_string(
                self.connection_string,
                ttl=self.ttl_config
            )
            await self._async_redis_saver.asetup()
            
            self._is_setup = True
            self.connection_info.is_connected = True
            self.connection_info.connection_time = datetime.now()
            
            logger.info("Redis异步存储设置完成")
            return True
            
        except Exception as e:
            logger.error(f"Redis异步存储设置失败: {e}")
            self.connection_info.error_message = str(e)
            return False
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """存储检查点到Redis"""
        with self._measure_operation('put'):
            try:
                if not self._redis_saver:
                    raise RuntimeError("Redis存储未初始化，请先调用setup()")
                
                # 使用RedisSaver存储
                self._redis_saver.put(config, checkpoint, metadata, new_versions)
                
                self._stats['total_operations'] += 1
                
                thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
                checkpoint_id = checkpoint.get('id', 'unknown')
                
                logger.debug(f"检查点已存储到Redis: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
                
            except Exception as e:
                logger.error(f"Redis存储检查点失败: {e}")
                raise
    
    async def aput(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
                   metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """异步存储检查点到Redis"""
        with self._measure_operation('put'):
            try:
                if not self._async_redis_saver:
                    raise RuntimeError("Redis异步存储未初始化，请先调用asetup()")
                
                # 使用AsyncRedisSaver存储
                await self._async_redis_saver.aput(config, checkpoint, metadata, new_versions)
                
                self._stats['total_operations'] += 1
                
                thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
                checkpoint_id = checkpoint.get('id', 'unknown')
                
                logger.debug(f"检查点已异步存储到Redis: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
                
            except Exception as e:
                logger.error(f"Redis异步存储检查点失败: {e}")
                raise
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从Redis获取检查点"""
        with self._measure_operation('get'):
            try:
                if not self._redis_saver:
                    raise RuntimeError("Redis存储未初始化，请先调用setup()")
                
                # 使用RedisSaver获取
                result = self._redis_saver.get(config)
                
                self._stats['total_operations'] += 1
                
                if result:
                    self._stats['cache_hits'] += 1
                    # 如果配置了读取时刷新TTL
                    if self.ttl_config.get('refresh_on_read', False):
                        self._stats['ttl_refreshes'] += 1
                else:
                    self._stats['cache_misses'] += 1
                
                thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
                logger.debug(f"从Redis获取检查点: thread_id={thread_id}, found={result is not None}")
                
                return result
                
            except Exception as e:
                logger.error(f"Redis获取检查点失败: {e}")
                raise
    
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步从Redis获取检查点"""
        with self._measure_operation('get'):
            try:
                if not self._async_redis_saver:
                    raise RuntimeError("Redis异步存储未初始化，请先调用asetup()")
                
                # 使用AsyncRedisSaver获取
                result = await self._async_redis_saver.aget(config)
                
                self._stats['total_operations'] += 1
                
                if result:
                    self._stats['cache_hits'] += 1
                    if self.ttl_config.get('refresh_on_read', False):
                        self._stats['ttl_refreshes'] += 1
                else:
                    self._stats['cache_misses'] += 1
                
                thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
                logger.debug(f"从Redis异步获取检查点: thread_id={thread_id}, found={result is not None}")
                
                return result
                
            except Exception as e:
                logger.error(f"Redis异步获取检查点失败: {e}")
                raise
    
    def list(self, config: Dict[str, Any],
             filter_criteria: Optional[Dict[str, Any]] = None,
             before: Optional[str] = None,
             limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """列出Redis中的检查点"""
        with self._measure_operation('list'):
            try:
                if not self._redis_saver:
                    raise RuntimeError("Redis存储未初始化，请先调用setup()")
                
                # 使用RedisSaver列出
                checkpoints = self._redis_saver.list(config, filter=filter_criteria, before=before, limit=limit)
                
                count = 0
                for checkpoint in checkpoints:
                    yield checkpoint
                    count += 1
                
                self._stats['total_operations'] += 1
                logger.debug(f"从Redis列出检查点: count={count}")
                
            except Exception as e:
                logger.error(f"Redis列出检查点失败: {e}")
                raise
    
    async def alist(self, config: Dict[str, Any],
                    filter_criteria: Optional[Dict[str, Any]] = None,
                    before: Optional[str] = None,
                    limit: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """异步列出Redis中的检查点"""
        with self._measure_operation('list'):
            try:
                if not self._async_redis_saver:
                    raise RuntimeError("Redis异步存储未初始化，请先调用asetup()")
                
                # 使用AsyncRedisSaver列出
                count = 0
                async for checkpoint in self._async_redis_saver.alist(config, filter=filter_criteria, before=before, limit=limit):
                    yield checkpoint
                    count += 1
                
                self._stats['total_operations'] += 1
                logger.debug(f"从Redis异步列出检查点: count={count}")
                
            except Exception as e:
                logger.error(f"Redis异步列出检查点失败: {e}")
                raise
    
    def delete(self, config: Dict[str, Any]) -> bool:
        """删除Redis中的检查点"""
        with self._measure_operation('delete'):
            try:
                if not self._redis_saver:
                    raise RuntimeError("Redis存储未初始化，请先调用setup()")
                
                thread_id = config.get('configurable', {}).get('thread_id')
                if not thread_id:
                    logger.warning("删除操作缺少thread_id")
                    return False
                
                # 注意：需要检查RedisSaver是否有delete_thread方法
                # 这里假设有这个方法，实际使用时需要根据API调整
                try:
                    if hasattr(self._redis_saver, 'delete_thread'):
                        self._redis_saver.delete_thread(thread_id)
                    else:
                        # 如果没有delete_thread方法，需要手动删除相关键
                        logger.warning("RedisSaver没有delete_thread方法，跳过删除操作")
                        return False
                except AttributeError:
                    logger.warning("RedisSaver不支持删除操作")
                    return False
                
                self._stats['total_operations'] += 1
                logger.debug(f"从Redis删除检查点: thread_id={thread_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Redis删除检查点失败: {e}")
                return False
    
    async def adelete(self, config: Dict[str, Any]) -> bool:
        """异步删除Redis中的检查点"""
        with self._measure_operation('delete'):
            try:
                if not self._async_redis_saver:
                    raise RuntimeError("Redis异步存储未初始化，请先调用asetup()")
                
                thread_id = config.get('configurable', {}).get('thread_id')
                if not thread_id:
                    logger.warning("异步删除操作缺少thread_id")
                    return False
                
                # 异步删除
                try:
                    if hasattr(self._async_redis_saver, 'adelete_thread'):
                        await self._async_redis_saver.adelete_thread(thread_id)
                    else:
                        logger.warning("AsyncRedisSaver没有adelete_thread方法，跳过删除操作")
                        return False
                except AttributeError:
                    logger.warning("AsyncRedisSaver不支持异步删除操作")
                    return False
                
                self._stats['total_operations'] += 1
                logger.debug(f"从Redis异步删除检查点: thread_id={thread_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Redis异步删除检查点失败: {e}")
                return False
    
    def _test_connection_impl(self) -> bool:
        """Redis连接测试实现"""
        try:
            pool = self._create_redis_pool()
            with redis.Redis(connection_pool=pool) as conn:
                conn.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接测试失败: {e}")
            return False
    
    async def _atest_connection_impl(self) -> bool:
        """Redis异步连接测试实现"""
        try:
            pool = self._create_async_redis_pool()
            async with aioredis.Redis(connection_pool=pool) as conn:
                await conn.ping()
            return True
        except Exception as e:
            logger.error(f"Redis异步连接测试失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Redis存储统计信息"""
        cache_hit_rate = 0.0
        total_cache_ops = self._stats['cache_hits'] + self._stats['cache_misses']
        if total_cache_ops > 0:
            cache_hit_rate = self._stats['cache_hits'] / total_cache_ops
        
        return {
            **self._stats,
            'cache_hit_rate': cache_hit_rate,
            'uptime_seconds': (datetime.now() - self._stats['created_at']).total_seconds(),
            'ttl_config': self.ttl_config,
            'pool_config': self.pool_config
        }
    
    def get_redis_info(self) -> Dict[str, Any]:
        """获取Redis服务器信息"""
        try:
            if not self._redis_pool:
                self._create_redis_pool()
            
            with redis.Redis(connection_pool=self._redis_pool) as conn:
                info = conn.info()
                return {
                    'redis_version': info.get('redis_version'),
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                    'keyspace_hits': info.get('keyspace_hits'),
                    'keyspace_misses': info.get('keyspace_misses'),
                    'uptime_in_seconds': info.get('uptime_in_seconds')
                }
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}
    
    def close(self):
        """关闭Redis存储连接"""
        try:
            if self._redis_saver:
                # RedisSaver可能有close方法
                if hasattr(self._redis_saver, 'close'):
                    self._redis_saver.close()
                self._redis_saver = None
            
            if self._redis_pool:
                self._redis_pool.disconnect()
                self._redis_pool = None
            
            super().close()
            logger.info("Redis存储连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭Redis存储连接失败: {e}")
    
    async def aclose(self):
        """异步关闭Redis存储连接"""
        try:
            if self._async_redis_saver:
                if hasattr(self._async_redis_saver, 'aclose'):
                    await self._async_redis_saver.aclose()
                self._async_redis_saver = None
            
            if self._async_redis_pool:
                await self._async_redis_pool.disconnect()
                self._async_redis_pool = None
            
            await super().aclose()
            logger.info("Redis异步存储连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭Redis异步存储连接失败: {e}")


# 注册到工厂
StorageFactory.register(StorageType.REDIS, RedisStorage)
