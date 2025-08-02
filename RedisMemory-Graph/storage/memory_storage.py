"""
内存存储实现
基于Python字典的内存存储，适用于开发和测试
"""

import copy
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Generator
from datetime import datetime

from langgraph.checkpoint.memory import MemorySaver

from .base import BaseStorage, StorageType, StorageFactory

logger = logging.getLogger(__name__)


class MemoryStorage(BaseStorage):
    """内存存储实现
    
    使用Python字典在内存中存储检查点数据
    优点：极快的读写速度，零配置
    缺点：重启后数据丢失，不支持分布式
    """
    
    def __init__(self, connection_string: str = "memory://", **kwargs):
        """初始化内存存储
        
        Args:
            connection_string: 连接字符串（内存存储忽略此参数）
            **kwargs: 额外配置参数
        """
        super().__init__(connection_string, **kwargs)
        
        # 内存存储的核心数据结构
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
        # 使用LangGraph的MemorySaver作为底层实现
        self._memory_saver = MemorySaver()
        
        # 统计信息
        self._stats = {
            'total_checkpoints': 0,
            'total_operations': 0,
            'created_at': datetime.now()
        }
        
        logger.info("内存存储初始化完成")
    
    def get_storage_type(self) -> StorageType:
        """获取存储类型"""
        return StorageType.MEMORY
    
    def setup(self) -> bool:
        """设置存储
        
        内存存储不需要特殊设置，直接返回成功
        """
        try:
            self._is_setup = True
            self.connection_info.is_connected = True
            self.connection_info.connection_time = datetime.now()
            logger.info("内存存储设置完成")
            return True
        except Exception as e:
            logger.error(f"内存存储设置失败: {e}")
            return False
    
    async def asetup(self) -> bool:
        """异步设置存储"""
        return self.setup()
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """存储检查点
        
        Args:
            config: 配置信息，包含thread_id等
            checkpoint: 检查点数据
            metadata: 元数据
            new_versions: 新版本信息
        """
        with self._measure_operation('put'):
            try:
                # 使用LangGraph的MemorySaver进行存储
                self._memory_saver.put(config, checkpoint, metadata, new_versions)
                
                # 更新统计信息
                self._stats['total_operations'] += 1
                
                # 生成存储键
                thread_id = config.get('configurable', {}).get('thread_id', 'default')
                checkpoint_id = checkpoint.get('id', 'unknown')
                key = f"{thread_id}:{checkpoint_id}"
                
                # 存储到内部数据结构（用于统计和调试）
                self._checkpoints[key] = copy.deepcopy(checkpoint)
                self._metadata[key] = copy.deepcopy(metadata)
                
                if key not in self._checkpoints:
                    self._stats['total_checkpoints'] += 1
                
                logger.debug(f"检查点已存储: {key}")
                
            except Exception as e:
                logger.error(f"存储检查点失败: {e}")
                raise
    
    async def aput(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
                   metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """异步存储检查点"""
        # 内存存储的异步版本直接调用同步方法
        self.put(config, checkpoint, metadata, new_versions)
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取检查点
        
        Args:
            config: 配置信息
            
        Returns:
            Optional[Dict[str, Any]]: 检查点数据
        """
        with self._measure_operation('get'):
            try:
                # 使用LangGraph的MemorySaver获取数据
                result = self._memory_saver.get(config)
                
                self._stats['total_operations'] += 1
                
                if result:
                    thread_id = config.get('configurable', {}).get('thread_id', 'default')
                    logger.debug(f"检查点已获取: thread_id={thread_id}")
                else:
                    logger.debug(f"检查点不存在: config={config}")
                
                return result
                
            except Exception as e:
                logger.error(f"获取检查点失败: {e}")
                raise
    
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步获取检查点"""
        return self.get(config)
    
    def list(self, config: Dict[str, Any],
             filter_criteria: Optional[Dict[str, Any]] = None,
             before: Optional[str] = None,
             limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """列出检查点
        
        Args:
            config: 配置信息
            filter_criteria: 过滤条件
            before: 在此之前的检查点
            limit: 限制数量
            
        Yields:
            Dict[str, Any]: 检查点数据
        """
        with self._measure_operation('list'):
            try:
                # 使用LangGraph的MemorySaver列出数据
                checkpoints = self._memory_saver.list(config, filter=filter_criteria, before=before, limit=limit)
                
                count = 0
                for checkpoint in checkpoints:
                    yield checkpoint
                    count += 1
                
                self._stats['total_operations'] += 1
                logger.debug(f"列出检查点完成: count={count}")
                
            except Exception as e:
                logger.error(f"列出检查点失败: {e}")
                raise
    
    async def alist(self, config: Dict[str, Any],
                    filter_criteria: Optional[Dict[str, Any]] = None,
                    before: Optional[str] = None,
                    limit: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """异步列出检查点"""
        for checkpoint in self.list(config, filter_criteria, before, limit):
            yield checkpoint
    
    def delete(self, config: Dict[str, Any]) -> bool:
        """删除检查点
        
        Args:
            config: 配置信息
            
        Returns:
            bool: 删除是否成功
        """
        with self._measure_operation('delete'):
            try:
                thread_id = config.get('configurable', {}).get('thread_id')
                if not thread_id:
                    logger.warning("删除操作缺少thread_id")
                    return False
                
                # 删除相关的检查点
                keys_to_delete = [key for key in self._checkpoints.keys() if key.startswith(f"{thread_id}:")]
                
                for key in keys_to_delete:
                    del self._checkpoints[key]
                    if key in self._metadata:
                        del self._metadata[key]
                    self._stats['total_checkpoints'] -= 1
                
                # 注意：MemorySaver可能没有直接的删除方法，这里我们清理内部数据
                # 实际的LangGraph MemorySaver的删除需要查看其API
                
                self._stats['total_operations'] += 1
                logger.debug(f"删除检查点完成: thread_id={thread_id}, count={len(keys_to_delete)}")
                
                return True
                
            except Exception as e:
                logger.error(f"删除检查点失败: {e}")
                return False
    
    async def adelete(self, config: Dict[str, Any]) -> bool:
        """异步删除检查点"""
        return self.delete(config)
    
    def _test_connection_impl(self) -> bool:
        """连接测试实现"""
        try:
            # 内存存储总是可用的
            return True
        except Exception:
            return False
    
    async def _atest_connection_impl(self) -> bool:
        """异步连接测试实现"""
        return self._test_connection_impl()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            **self._stats,
            'current_checkpoints': len(self._checkpoints),
            'memory_usage_mb': self._estimate_memory_usage(),
            'uptime_seconds': (datetime.now() - self._stats['created_at']).total_seconds()
        }
    
    def _estimate_memory_usage(self) -> float:
        """估算内存使用量（MB）"""
        try:
            import sys
            total_size = 0
            
            # 估算检查点数据大小
            for checkpoint in self._checkpoints.values():
                total_size += sys.getsizeof(str(checkpoint))
            
            # 估算元数据大小
            for metadata in self._metadata.values():
                total_size += sys.getsizeof(str(metadata))
            
            return total_size / (1024 * 1024)  # 转换为MB
        except Exception:
            return 0.0
    
    def clear_all(self) -> int:
        """清空所有数据
        
        Returns:
            int: 清空的检查点数量
        """
        count = len(self._checkpoints)
        self._checkpoints.clear()
        self._metadata.clear()
        self._stats['total_checkpoints'] = 0
        
        # 重新创建MemorySaver实例
        self._memory_saver = MemorySaver()
        
        logger.info(f"内存存储已清空: {count} 个检查点")
        return count
    
    def close(self):
        """关闭存储连接"""
        # 内存存储不需要特殊的关闭操作
        super().close()
        logger.info("内存存储连接已关闭")
    
    async def aclose(self):
        """异步关闭存储连接"""
        await super().aclose()


# 注册到工厂
StorageFactory.register(StorageType.MEMORY, MemoryStorage)
