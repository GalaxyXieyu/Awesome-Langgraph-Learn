"""
存储基类定义
定义所有存储实现的统一接口
"""

import time
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Generator
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    REDIS = "redis"
    POSTGRES = "postgres"
    SQLITE = "sqlite"


@dataclass
class StorageMetrics:
    """存储性能指标"""
    operation_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    error_count: int = 0
    last_operation_time: Optional[datetime] = None
    
    def update(self, operation_time: float, success: bool = True):
        """更新指标"""
        self.operation_count += 1
        self.total_time += operation_time
        self.avg_time = self.total_time / self.operation_count
        self.min_time = min(self.min_time, operation_time)
        self.max_time = max(self.max_time, operation_time)
        self.last_operation_time = datetime.now()
        
        if not success:
            self.error_count += 1
    
    def reset(self):
        """重置指标"""
        self.operation_count = 0
        self.total_time = 0.0
        self.avg_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0
        self.error_count = 0
        self.last_operation_time = None


@dataclass
class ConnectionInfo:
    """连接信息"""
    storage_type: StorageType
    connection_string: str
    is_connected: bool = False
    connection_time: Optional[datetime] = None
    last_ping_time: Optional[datetime] = None
    error_message: Optional[str] = None


class BaseStorage(ABC):
    """存储基类
    
    定义所有存储实现必须遵循的接口规范
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """初始化存储
        
        Args:
            connection_string: 连接字符串
            **kwargs: 额外的配置参数
        """
        self.connection_string = connection_string
        self.config = kwargs
        self.metrics = {
            'put': StorageMetrics(),
            'get': StorageMetrics(),
            'list': StorageMetrics(),
            'delete': StorageMetrics()
        }
        self.connection_info = ConnectionInfo(
            storage_type=self.get_storage_type(),
            connection_string=connection_string
        )
        self._is_setup = False
    
    @abstractmethod
    def get_storage_type(self) -> StorageType:
        """获取存储类型"""
        pass
    
    @abstractmethod
    def setup(self) -> bool:
        """设置存储（创建必要的表、索引等）
        
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    async def asetup(self) -> bool:
        """异步设置存储
        
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], 
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """存储检查点
        
        Args:
            config: 配置信息
            checkpoint: 检查点数据
            metadata: 元数据
            new_versions: 新版本信息
        """
        pass
    
    @abstractmethod
    async def aput(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
                   metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """异步存储检查点"""
        pass
    
    @abstractmethod
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取检查点
        
        Args:
            config: 配置信息
            
        Returns:
            Optional[Dict[str, Any]]: 检查点数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步获取检查点"""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def alist(self, config: Dict[str, Any],
                    filter_criteria: Optional[Dict[str, Any]] = None,
                    before: Optional[str] = None,
                    limit: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """异步列出检查点"""
        pass
    
    @abstractmethod
    def delete(self, config: Dict[str, Any]) -> bool:
        """删除检查点
        
        Args:
            config: 配置信息
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def adelete(self, config: Dict[str, Any]) -> bool:
        """异步删除检查点"""
        pass
    
    def test_connection(self) -> bool:
        """测试连接
        
        Returns:
            bool: 连接是否正常
        """
        try:
            start_time = time.time()
            result = self._test_connection_impl()
            operation_time = time.time() - start_time
            
            self.connection_info.is_connected = result
            self.connection_info.last_ping_time = datetime.now()
            self.connection_info.error_message = None
            
            if result:
                logger.info(f"{self.get_storage_type().value} 连接测试成功 ({operation_time:.3f}s)")
            else:
                logger.warning(f"{self.get_storage_type().value} 连接测试失败")
            
            return result
        except Exception as e:
            self.connection_info.is_connected = False
            self.connection_info.error_message = str(e)
            logger.error(f"{self.get_storage_type().value} 连接测试异常: {e}")
            return False
    
    async def atest_connection(self) -> bool:
        """异步测试连接"""
        try:
            start_time = time.time()
            result = await self._atest_connection_impl()
            operation_time = time.time() - start_time
            
            self.connection_info.is_connected = result
            self.connection_info.last_ping_time = datetime.now()
            self.connection_info.error_message = None
            
            if result:
                logger.info(f"{self.get_storage_type().value} 异步连接测试成功 ({operation_time:.3f}s)")
            else:
                logger.warning(f"{self.get_storage_type().value} 异步连接测试失败")
            
            return result
        except Exception as e:
            self.connection_info.is_connected = False
            self.connection_info.error_message = str(e)
            logger.error(f"{self.get_storage_type().value} 异步连接测试异常: {e}")
            return False
    
    @abstractmethod
    def _test_connection_impl(self) -> bool:
        """连接测试的具体实现"""
        pass
    
    @abstractmethod
    async def _atest_connection_impl(self) -> bool:
        """异步连接测试的具体实现"""
        pass
    
    def get_metrics(self) -> Dict[str, StorageMetrics]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """重置性能指标"""
        for metric in self.metrics.values():
            metric.reset()
    
    def get_connection_info(self) -> ConnectionInfo:
        """获取连接信息"""
        return self.connection_info
    
    def _measure_operation(self, operation_name: str):
        """操作性能测量装饰器上下文管理器"""
        class OperationMeasurer:
            def __init__(self, storage: 'BaseStorage', op_name: str):
                self.storage = storage
                self.op_name = op_name
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                operation_time = time.time() - self.start_time
                success = exc_type is None
                
                if self.op_name in self.storage.metrics:
                    self.storage.metrics[self.op_name].update(operation_time, success)
                
                if not success:
                    logger.error(f"{self.storage.get_storage_type().value} {self.op_name} 操作失败: {exc_val}")
        
        return OperationMeasurer(self, operation_name)
    
    def close(self):
        """关闭存储连接"""
        self.connection_info.is_connected = False
        logger.info(f"{self.get_storage_type().value} 存储连接已关闭")
    
    async def aclose(self):
        """异步关闭存储连接"""
        self.connection_info.is_connected = False
        logger.info(f"{self.get_storage_type().value} 异步存储连接已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self._is_setup:
            self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self._is_setup:
            await self.asetup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.aclose()
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"{self.__class__.__name__}("
                f"type={self.get_storage_type().value}, "
                f"connected={self.connection_info.is_connected})")


class StorageFactory:
    """存储工厂类"""
    
    _storage_classes = {}
    
    @classmethod
    def register(cls, storage_type: StorageType, storage_class: type):
        """注册存储类"""
        cls._storage_classes[storage_type] = storage_class
    
    @classmethod
    def create(cls, storage_type: Union[str, StorageType], 
               connection_string: str, **kwargs) -> BaseStorage:
        """创建存储实例
        
        Args:
            storage_type: 存储类型
            connection_string: 连接字符串
            **kwargs: 额外配置
            
        Returns:
            BaseStorage: 存储实例
        """
        if isinstance(storage_type, str):
            storage_type = StorageType(storage_type)
        
        if storage_type not in cls._storage_classes:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        
        storage_class = cls._storage_classes[storage_type]
        return storage_class(connection_string, **kwargs)
    
    @classmethod
    def get_supported_types(cls) -> List[StorageType]:
        """获取支持的存储类型"""
        return list(cls._storage_classes.keys())
