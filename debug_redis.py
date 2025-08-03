#!/usr/bin/env python3
"""
调试 Redis 连接问题
"""

import sys
import os
import asyncio

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.config import get_config
from backend.utils.redis_client import get_redis_client
from backend.utils.session_manager import get_session_manager

async def debug_redis():
    """调试 Redis 连接"""
    print("🔍 调试 Redis 连接问题")
    print("=" * 50)
    
    # 1. 检查配置
    config = get_config()
    print(f"📋 Redis 配置:")
    print(f"   Host: {config.redis.host}")
    print(f"   Port: {config.redis.port}")
    print(f"   DB: {config.redis.db}")
    print(f"   Password: {'***' if config.redis.password else 'None'}")
    
    # 2. 测试 Redis 客户端
    redis_client = get_redis_client()
    print(f"\n🔗 测试 Redis 连接:")
    
    if redis_client.ping():
        print("✅ Redis 连接成功")
    else:
        print("❌ Redis 连接失败")
        return
    
    # 3. 测试写入和读取
    test_key = "debug:test_key"
    test_value = "test_value_123"
    
    print(f"\n📝 测试 Redis 读写:")
    
    # 写入
    success = redis_client.set(test_key, test_value, ex=60)
    print(f"写入结果: {success}")
    
    # 读取
    retrieved = redis_client.get(test_key)
    print(f"读取结果: {retrieved}")
    
    if retrieved == test_value:
        print("✅ Redis 读写测试成功")
    else:
        print(f"❌ Redis 读写测试失败: 期望 {test_value}, 得到 {retrieved}")
    
    # 4. 测试 hash 操作
    print(f"\n📊 测试 Redis Hash 操作:")
    
    hash_key = "debug:test_hash"
    hash_data = {
        "field1": "value1",
        "field2": "value2",
        "status": "test"
    }
    
    # 写入 hash
    success = redis_client.hmset(hash_key, hash_data)
    print(f"Hash 写入结果: {success}")
    
    # 读取 hash
    retrieved_hash = redis_client.hgetall(hash_key)
    print(f"Hash 读取结果: {retrieved_hash}")
    
    if retrieved_hash == hash_data:
        print("✅ Redis Hash 测试成功")
    else:
        print(f"❌ Redis Hash 测试失败")
        print(f"   期望: {hash_data}")
        print(f"   得到: {retrieved_hash}")
    
    # 5. 测试会话管理器
    print(f"\n👤 测试会话管理器:")
    
    session_manager = get_session_manager()
    
    # 创建测试任务
    test_task_id = "debug_task_123"
    test_user_id = "debug_user"
    test_session_id = "debug_session"
    
    print(f"创建测试任务: {test_task_id}")
    
    success = await session_manager.set_task_status(
        task_id=test_task_id,
        status="pending",
        user_id=test_user_id,
        session_id=test_session_id,
        metadata={
            "test": "data",
            "created_at": "2025-08-03T22:00:00Z"
        }
    )
    
    print(f"任务创建结果: {success}")
    
    # 查询任务
    task_data = await session_manager.get_task_status(test_task_id)
    print(f"任务查询结果: {task_data}")
    
    if task_data:
        print("✅ 会话管理器测试成功")
    else:
        print("❌ 会话管理器测试失败")
    
    # 6. 直接检查 Redis 中的任务键
    print(f"\n🔍 直接检查 Redis 键:")
    
    task_key = f"task:{test_task_id}"
    direct_data = redis_client.hgetall(task_key)
    print(f"直接查询 {task_key}: {direct_data}")
    
    # 7. 列出所有相关的键
    print(f"\n📋 列出所有任务相关的键:")
    
    # 注意：这里使用 Redis 的 KEYS 命令，生产环境中应该避免
    try:
        all_task_keys = redis_client.client.keys("task:*")
        print(f"所有任务键: {all_task_keys}")
        
        for key in all_task_keys[:5]:  # 只显示前5个
            data = redis_client.hgetall(key)
            print(f"  {key}: {data}")
            
    except Exception as e:
        print(f"列出键失败: {e}")
    
    # 清理测试数据
    redis_client.delete(test_key, hash_key, task_key)
    await session_manager.close()
    
    print(f"\n🎯 调试完成")

if __name__ == "__main__":
    asyncio.run(debug_redis())
