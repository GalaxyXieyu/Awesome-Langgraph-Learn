"""
测试不同存储方案的性能和功能
"""

import time
import asyncio
from typing import Dict, Any
from graph import create_chat_bot, chat_with_memory
from langchain_core.messages import HumanMessage


def test_memory_storage():
    """测试内存存储"""
    print("\n🧠 测试内存存储")
    print("-" * 30)
    
    app = create_chat_bot("memory")
    thread_id = "memory_test"
    
    # 测试对话连续性
    response1 = chat_with_memory(app, "我叫张三", thread_id)
    print(f"👤 我叫张三")
    print(f"🤖 {response1}")
    
    response2 = chat_with_memory(app, "我叫什么名字？", thread_id)
    print(f"👤 我叫什么名字？")
    print(f"🤖 {response2}")
    
    return "张三" in response2 or "你叫张三" in response2


def test_redis_storage():
    """测试Redis存储"""
    print("\n🔴 测试Redis存储")
    print("-" * 30)
    
    try:
        app = create_chat_bot("redis")
        thread_id = "redis_test"
        
        # 测试对话连续性
        response1 = chat_with_memory(app, "我是李四", thread_id)
        print(f"👤 我是李四")
        print(f"🤖 {response1}")
        
        response2 = chat_with_memory(app, "你记得我是谁吗？", thread_id)
        print(f"👤 你记得我是谁吗？")
        print(f"🤖 {response2}")
        
        return "李四" in response2 or "你是李四" in response2
        
    except Exception as e:
        print(f"❌ Redis测试失败: {e}")
        return False


def test_cross_session():
    """测试跨会话记忆"""
    print("\n🔄 测试跨会话记忆")
    print("-" * 30)
    
    app = create_chat_bot("redis")
    
    # 会话1
    thread_id_1 = "session_1"
    chat_with_memory(app, "我喜欢Python编程", thread_id_1)
    print("👤 会话1: 我喜欢Python编程")
    
    # 会话2 - 不同的线程ID
    thread_id_2 = "session_2"
    response = chat_with_memory(app, "我喜欢什么？", thread_id_2)
    print(f"👤 会话2: 我喜欢什么？")
    print(f"🤖 会话2: {response}")
    
    # 回到会话1
    response = chat_with_memory(app, "我喜欢什么？", thread_id_1)
    print(f"👤 会话1: 我喜欢什么？")
    print(f"🤖 会话1: {response}")
    
    return "Python" in response


def performance_test():
    """性能测试"""
    print("\n⚡ 性能测试")
    print("-" * 30)
    
    results = {}
    
    # 测试内存存储性能
    print("测试内存存储性能...")
    app_memory = create_chat_bot("memory")
    start_time = time.time()
    
    for i in range(10):
        chat_with_memory(app_memory, f"测试消息 {i}", f"perf_memory_{i}")
    
    memory_time = time.time() - start_time
    results["memory"] = memory_time
    print(f"内存存储 10次操作耗时: {memory_time:.3f}秒")
    
    # 测试Redis存储性能
    print("测试Redis存储性能...")
    try:
        app_redis = create_chat_bot("redis")
        start_time = time.time()
        
        for i in range(10):
            chat_with_memory(app_redis, f"测试消息 {i}", f"perf_redis_{i}")
        
        redis_time = time.time() - start_time
        results["redis"] = redis_time
        print(f"Redis存储 10次操作耗时: {redis_time:.3f}秒")
        
    except Exception as e:
        print(f"Redis性能测试失败: {e}")
        results["redis"] = None
    
    return results


def storage_comparison():
    """存储方案对比"""
    print("\n📊 存储方案对比")
    print("=" * 50)
    
    comparison = {
        "内存存储 (MemorySaver)": {
            "优点": ["极快的读写速度", "零配置", "适合开发测试"],
            "缺点": ["重启后数据丢失", "不支持分布式", "内存限制"],
            "适用场景": "开发、测试、演示"
        },
        "Redis存储 (RedisSaver)": {
            "优点": ["高性能", "持久化", "支持TTL", "支持集群"],
            "缺点": ["需要Redis服务", "内存成本", "网络延迟"],
            "适用场景": "生产环境、高并发、分布式系统"
        }
    }
    
    for storage_name, info in comparison.items():
        print(f"\n🔹 {storage_name}")
        print(f"   ✅ 优点: {', '.join(info['优点'])}")
        print(f"   ❌ 缺点: {', '.join(info['缺点'])}")
        print(f"   🎯 适用: {info['适用场景']}")


def main():
    """主测试函数"""
    print("🚀 LangGraph 会话存储测试套件")
    print("=" * 50)
    
    # 功能测试
    print("\n📋 功能测试")
    memory_ok = test_memory_storage()
    redis_ok = test_redis_storage()
    cross_session_ok = test_cross_session()
    
    print(f"\n📊 测试结果:")
    print(f"   内存存储: {'✅ 通过' if memory_ok else '❌ 失败'}")
    print(f"   Redis存储: {'✅ 通过' if redis_ok else '❌ 失败'}")
    print(f"   跨会话记忆: {'✅ 通过' if cross_session_ok else '❌ 失败'}")
    
    # 性能测试
    perf_results = performance_test()
    
    if perf_results.get("memory") and perf_results.get("redis"):
        speedup = perf_results["memory"] / perf_results["redis"]
        print(f"\n⚡ 性能对比:")
        print(f"   内存存储相对Redis快 {speedup:.1f}x")
    
    # 存储方案对比
    storage_comparison()
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()
