"""
数据库连接配置和管理
提供统一的数据库连接接口
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import redis
import redis.asyncio as aioredis
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sqlite3
import asyncpg

from .settings import get_settings, RedisConfig, PostgreSQLConfig, SQLiteConfig

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置数据类"""
    storage_type: str
    connection_params: Dict[str, Any]
    is_async: bool = False


class ConnectionManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._async_redis_pool: Optional[aioredis.ConnectionPool] = None
        self._postgres_engine = None
        self._async_postgres_engine = None
        self._sqlite_connection = None
    
    # Redis连接管理
    def get_redis_pool(self) -> redis.ConnectionPool:
        """获取Redis连接池"""
        if self._redis_pool is None:
            config = self.settings.redis
            self._redis_pool = redis.ConnectionPool.from_url(
                config.url,
                password=config.password,
                db=config.db,
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._redis_pool
    
    def get_async_redis_pool(self) -> aioredis.ConnectionPool:
        """获取异步Redis连接池"""
        if self._async_redis_pool is None:
            config = self.settings.redis
            self._async_redis_pool = aioredis.ConnectionPool.from_url(
                config.url,
                password=config.password,
                db=config.db,
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._async_redis_pool
    
    @contextmanager
    def get_redis_connection(self):
        """获取Redis连接（上下文管理器）"""
        pool = self.get_redis_pool()
        connection = redis.Redis(connection_pool=pool)
        try:
            yield connection
        finally:
            connection.close()
    
    @asynccontextmanager
    async def get_async_redis_connection(self):
        """获取异步Redis连接（异步上下文管理器）"""
        pool = self.get_async_redis_pool()
        connection = aioredis.Redis(connection_pool=pool)
        try:
            yield connection
        finally:
            await connection.aclose()
    
    # PostgreSQL连接管理
    def get_postgres_engine(self):
        """获取PostgreSQL引擎"""
        if self._postgres_engine is None:
            config = self.settings.postgres
            self._postgres_engine = create_engine(
                config.url,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_recycle=config.pool_recycle,
                echo=self.settings.debug
            )
        return self._postgres_engine
    
    def get_async_postgres_engine(self):
        """获取异步PostgreSQL引擎"""
        if self._async_postgres_engine is None:
            config = self.settings.postgres
            # 将同步URL转换为异步URL
            async_url = config.url.replace('postgresql://', 'postgresql+asyncpg://')
            self._async_postgres_engine = create_async_engine(
                async_url,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_recycle=config.pool_recycle,
                echo=self.settings.debug
            )
        return self._async_postgres_engine
    
    @contextmanager
    def get_postgres_session(self):
        """获取PostgreSQL会话（上下文管理器）"""
        engine = self.get_postgres_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_postgres_session(self):
        """获取异步PostgreSQL会话（异步上下文管理器）"""
        engine = self.get_async_postgres_engine()
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    # SQLite连接管理
    def get_sqlite_connection(self) -> sqlite3.Connection:
        """获取SQLite连接"""
        if self._sqlite_connection is None:
            config = self.settings.sqlite
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(config.database_path), exist_ok=True)
            
            self._sqlite_connection = sqlite3.connect(
                config.database_path,
                timeout=config.timeout,
                check_same_thread=config.check_same_thread
            )
            
            # 设置WAL模式和其他优化
            cursor = self._sqlite_connection.cursor()
            cursor.execute(f"PRAGMA journal_mode = {config.journal_mode}")
            cursor.execute(f"PRAGMA synchronous = {config.synchronous}")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
            
        return self._sqlite_connection
    
    @contextmanager
    def get_sqlite_session(self):
        """获取SQLite会话（上下文管理器）"""
        connection = self.get_sqlite_connection()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    
    # 连接测试方法
    def test_redis_connection(self) -> bool:
        """测试Redis连接"""
        try:
            with self.get_redis_connection() as conn:
                conn.ping()
            logger.info("Redis连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Redis连接测试失败: {e}")
            return False
    
    async def test_async_redis_connection(self) -> bool:
        """测试异步Redis连接"""
        try:
            async with self.get_async_redis_connection() as conn:
                await conn.ping()
            logger.info("异步Redis连接测试成功")
            return True
        except Exception as e:
            logger.error(f"异步Redis连接测试失败: {e}")
            return False
    
    def test_postgres_connection(self) -> bool:
        """测试PostgreSQL连接"""
        try:
            with self.get_postgres_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("PostgreSQL连接测试成功")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL连接测试失败: {e}")
            return False
    
    async def test_async_postgres_connection(self) -> bool:
        """测试异步PostgreSQL连接"""
        try:
            async with self.get_async_postgres_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("异步PostgreSQL连接测试成功")
            return True
        except Exception as e:
            logger.error(f"异步PostgreSQL连接测试失败: {e}")
            return False
    
    def test_sqlite_connection(self) -> bool:
        """测试SQLite连接"""
        try:
            with self.get_sqlite_session() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            logger.info("SQLite连接测试成功")
            return True
        except Exception as e:
            logger.error(f"SQLite连接测试失败: {e}")
            return False
    
    def test_all_connections(self) -> Dict[str, bool]:
        """测试所有连接"""
        results = {
            'redis': self.test_redis_connection(),
            'postgres': self.test_postgres_connection(),
            'sqlite': self.test_sqlite_connection()
        }
        return results
    
    async def test_all_async_connections(self) -> Dict[str, bool]:
        """测试所有异步连接"""
        results = {
            'redis': await self.test_async_redis_connection(),
            'postgres': await self.test_async_postgres_connection(),
            'sqlite': self.test_sqlite_connection()  # SQLite没有异步版本
        }
        return results
    
    def close_all_connections(self):
        """关闭所有连接"""
        if self._redis_pool:
            self._redis_pool.disconnect()
            self._redis_pool = None
        
        if self._async_redis_pool:
            # 异步连接池需要在事件循环中关闭
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_redis_pool.disconnect())
                else:
                    loop.run_until_complete(self._async_redis_pool.disconnect())
            except Exception as e:
                logger.warning(f"关闭异步Redis连接池时出错: {e}")
            self._async_redis_pool = None
        
        if self._postgres_engine:
            self._postgres_engine.dispose()
            self._postgres_engine = None
        
        if self._async_postgres_engine:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_postgres_engine.dispose())
                else:
                    loop.run_until_complete(self._async_postgres_engine.dispose())
            except Exception as e:
                logger.warning(f"关闭异步PostgreSQL引擎时出错: {e}")
            self._async_postgres_engine = None
        
        if self._sqlite_connection:
            self._sqlite_connection.close()
            self._sqlite_connection = None


# 全局连接管理器实例
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器实例（单例模式）"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_database_config(storage_type: str, is_async: bool = False) -> DatabaseConfig:
    """获取数据库配置"""
    settings = get_settings()
    
    config_map = {
        'redis': DatabaseConfig(
            storage_type='redis',
            connection_params=settings.redis.dict(),
            is_async=is_async
        ),
        'postgres': DatabaseConfig(
            storage_type='postgres',
            connection_params=settings.postgres.dict(),
            is_async=is_async
        ),
        'sqlite': DatabaseConfig(
            storage_type='sqlite',
            connection_params=settings.sqlite.dict(),
            is_async=False  # SQLite不支持异步
        ),
        'memory': DatabaseConfig(
            storage_type='memory',
            connection_params={},
            is_async=is_async
        )
    }
    
    if storage_type not in config_map:
        raise ValueError(f"不支持的存储类型: {storage_type}")
    
    return config_map[storage_type]
