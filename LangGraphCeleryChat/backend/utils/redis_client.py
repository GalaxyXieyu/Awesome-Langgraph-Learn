"""
Redis 客户端工具
"""

import json
import redis
from typing import Dict, Any, Optional, List, Set
from functools import lru_cache

from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis 客户端封装"""
    
    def __init__(self, config=None):
        if config is None:
            config = get_config().redis
        
        self.config = config
        self.client = redis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            password=config.password,
            decode_responses=True,
            max_connections=config.max_connections
        )
    
    def get(self, key: str) -> Optional[str]:
        """获取键值"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 失败: {key}, 错误: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """设置键值"""
        try:
            result = self.client.set(key, value, ex=ex)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET 失败: {key}, 错误: {e}")
            return False
    
    def setex(self, key: str, time: int, value: str) -> bool:
        """设置键值并指定过期时间"""
        try:
            return self.client.setex(key, time, value)
        except Exception as e:
            logger.error(f"Redis SETEX 失败: {key}, 错误: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """删除键"""
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE 失败: {keys}, 错误: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS 失败: {key}, 错误: {e}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段值"""
        try:
            return self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET 失败: {name}.{key}, 错误: {e}")
            return None
    
    def hset(self, name: str, key: str, value: str) -> bool:
        """设置哈希字段值"""
        try:
            return bool(self.client.hset(name, key, value))
        except Exception as e:
            logger.error(f"Redis HSET 失败: {name}.{key}, 错误: {e}")
            return False
    
    def hgetall(self, name: str) -> Dict[str, str]:
        """获取哈希所有字段"""
        try:
            return self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL 失败: {name}, 错误: {e}")
            return {}
    
    def hmset(self, name: str, mapping: Dict[str, str]) -> bool:
        """设置哈希多个字段"""
        try:
            return self.client.hmset(name, mapping)
        except Exception as e:
            logger.error(f"Redis HMSET 失败: {name}, 错误: {e}")
            return False
    
    def expire(self, key: str, time: int) -> bool:
        """设置键过期时间"""
        try:
            return self.client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis EXPIRE 失败: {key}, 错误: {e}")
            return False
    
    def xadd(self, name: str, fields: Dict[str, str], id: str = "*") -> Optional[str]:
        """添加流事件"""
        try:
            return self.client.xadd(name, fields, id=id)
        except Exception as e:
            logger.error(f"Redis XADD 失败: {name}, 错误: {e}")
            return None
    
    def xread(self, streams: Dict[str, str], count: Optional[int] = None, block: Optional[int] = None) -> List:
        """读取流事件"""
        try:
            return self.client.xread(streams, count=count, block=block)
        except Exception as e:
            logger.error(f"Redis XREAD 失败: {streams}, 错误: {e}")
            return []
    
    def xrange(self, name: str, min: str = "-", max: str = "+", count: Optional[int] = None) -> List:
        """获取流范围事件"""
        try:
            return self.client.xrange(name, min=min, max=max, count=count)
        except Exception as e:
            logger.error(f"Redis XRANGE 失败: {name}, 错误: {e}")
            return []
    
    def xgroup_create(self, name: str, groupname: str, id: str = "0", mkstream: bool = False) -> bool:
        """创建消费者组"""
        try:
            return self.client.xgroup_create(name, groupname, id=id, mkstream=mkstream)
        except Exception as e:
            logger.error(f"Redis XGROUP CREATE 失败: {name}.{groupname}, 错误: {e}")
            return False
    
    def xreadgroup(
        self, 
        groupname: str, 
        consumername: str, 
        streams: Dict[str, str], 
        count: Optional[int] = None, 
        block: Optional[int] = None
    ) -> List:
        """消费者组读取流事件"""
        try:
            return self.client.xreadgroup(groupname, consumername, streams, count=count, block=block)
        except Exception as e:
            logger.error(f"Redis XREADGROUP 失败: {groupname}.{consumername}, 错误: {e}")
            return []
    
    def sadd(self, name: str, *values: str) -> int:
        """添加元素到集合"""
        try:
            return self.client.sadd(name, *values)
        except Exception as e:
            logger.error(f"Redis SADD 失败: {name}, 错误: {e}")
            return 0

    def srem(self, name: str, *values: str) -> int:
        """从集合中移除元素"""
        try:
            return self.client.srem(name, *values)
        except Exception as e:
            logger.error(f"Redis SREM 失败: {name}, 错误: {e}")
            return 0

    def smembers(self, name: str) -> Set[str]:
        """获取集合所有成员"""
        try:
            return self.client.smembers(name)
        except Exception as e:
            logger.error(f"Redis SMEMBERS 失败: {name}, 错误: {e}")
            return set()

    def sismember(self, name: str, value: str) -> bool:
        """检查元素是否在集合中"""
        try:
            return self.client.sismember(name, value)
        except Exception as e:
            logger.error(f"Redis SISMEMBER 失败: {name}, 错误: {e}")
            return False

    def ping(self) -> bool:
        """检查连接"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis PING 失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Redis 关闭连接失败: {e}")


@lru_cache()
def get_redis_client() -> RedisClient:
    """获取 Redis 客户端实例"""
    return RedisClient()
