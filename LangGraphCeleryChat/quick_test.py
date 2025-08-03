#!/usr/bin/env python3
"""
快速测试脚本 - 验证基本组件是否正常工作
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试基础依赖
        import redis
        print("✅ Redis 客户端导入成功")
        
        import celery
        print("✅ Celery 导入成功")
        
        import fastapi
        print("✅ FastAPI 导入成功")
        
        import pydantic
        print("✅ Pydantic 导入成功")
        
        # 测试我们的模块
        from backend.utils.config import get_config
        config = get_config()
        print(f"✅ 配置加载成功: {config.app_name}")
        
        from backend.utils.redis_client import get_redis_client
        redis_client = get_redis_client()
        print("✅ Redis 客户端创建成功")
        
        from backend.utils.session_manager import get_session_manager
        session_manager = get_session_manager()
        print("✅ 会话管理器创建成功")
        
        from backend.models.schemas import WritingTaskConfig, WritingMode
        config = WritingTaskConfig(
            topic="测试主题",
            mode=WritingMode.COPILOT
        )
        print("✅ 数据模型创建成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_redis_connection():
    """测试 Redis 连接"""
    print("\n🔍 测试 Redis 连接...")
    
    try:
        from backend.utils.redis_client import get_redis_client
        redis_client = get_redis_client()
        
        # 测试连接
        if redis_client.ping():
            print("✅ Redis 连接成功")
            
            # 测试基本操作
            test_key = "test:connection"
            test_value = "hello_world"
            
            redis_client.set(test_key, test_value, ex=60)
            retrieved_value = redis_client.get(test_key)
            
            if retrieved_value == test_value:
                print("✅ Redis 读写测试成功")
                redis_client.delete(test_key)
                return True
            else:
                print(f"❌ Redis 读写测试失败: 期望 {test_value}, 得到 {retrieved_value}")
                return False
        else:
            print("❌ Redis 连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis 测试异常: {e}")
        return False

def test_celery_app():
    """测试 Celery 应用"""
    print("\n🔍 测试 Celery 应用...")
    
    try:
        from backend.celery_app import celery_app
        print(f"✅ Celery 应用创建成功: {celery_app.main}")
        
        # 检查任务注册
        registered_tasks = list(celery_app.tasks.keys())
        print(f"📋 已注册任务: {len(registered_tasks)} 个")
        
        for task_name in registered_tasks:
            if not task_name.startswith('celery.'):
                print(f"   - {task_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery 测试异常: {e}")
        return False

def test_fastapi_app():
    """测试 FastAPI 应用"""
    print("\n🔍 测试 FastAPI 应用...")
    
    try:
        from backend.app.main import app
        print(f"✅ FastAPI 应用创建成功: {app.title}")
        
        # 检查路由
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':  # 跳过 HEAD 方法
                        routes.append(f"{method} {route.path}")
        
        print(f"🛣️  已注册路由: {len(routes)} 个")
        for route in routes[:10]:  # 只显示前10个
            print(f"   - {route}")
        
        if len(routes) > 10:
            print(f"   ... 还有 {len(routes) - 10} 个路由")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI 测试异常: {e}")
        return False

async def test_session_manager():
    """测试会话管理器"""
    print("\n🔍 测试会话管理器...")
    
    try:
        from backend.utils.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        # 创建测试会话
        user_id = "test_user_123"
        session_id = await session_manager.create_session(user_id)
        print(f"✅ 会话创建成功: {session_id}")
        
        # 获取会话信息
        session_data = await session_manager.get_session(session_id)
        if session_data and session_data.get('user_id') == user_id:
            print("✅ 会话数据读取成功")
        else:
            print("❌ 会话数据读取失败")
            return False
        
        # 设置任务状态
        task_id = "test_task_123"
        await session_manager.set_task_status(
            task_id=task_id,
            status="running",
            user_id=user_id,
            session_id=session_id
        )
        print("✅ 任务状态设置成功")
        
        # 获取任务状态
        task_data = await session_manager.get_task_status(task_id)
        if task_data and task_data.get('status') == 'running':
            print("✅ 任务状态读取成功")
        else:
            print("❌ 任务状态读取失败")
            return False
        
        # 清理测试数据
        await session_manager.delete_session(session_id)
        print("✅ 测试数据清理完成")
        
        await session_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ 会话管理器测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 LangGraph Celery Chat 组件测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("Redis 连接", test_redis_connection),
        ("Celery 应用", test_celery_app),
        ("FastAPI 应用", test_fastapi_app),
    ]
    
    results = {}
    
    # 运行同步测试
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 运行异步测试
    try:
        import asyncio
        result = asyncio.run(test_session_manager())
        results["会话管理器"] = result
    except Exception as e:
        print(f"❌ 会话管理器测试异常: {e}")
        results["会话管理器"] = False
    
    # 总结结果
    print("\n📊 测试总结")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有组件测试通过！可以启动服务进行完整测试。")
        print("\n📝 下一步:")
        print("1. 启动 Redis: redis-server")
        print("2. 启动服务: ./start_services.sh")
        print("3. 运行 API 测试: python test_api.py")
    else:
        print("⚠️  部分组件测试失败，请检查配置和依赖。")
        
        if not results.get("Redis 连接", False):
            print("\n💡 Redis 连接失败解决方案:")
            print("   - 确保 Redis 服务已启动: redis-server")
            print("   - 检查 Redis 配置: redis-cli ping")
        
        if not results.get("模块导入", False):
            print("\n💡 模块导入失败解决方案:")
            print("   - 安装依赖: pip install -r requirements.txt")
            print("   - 检查 Python 路径配置")

if __name__ == "__main__":
    main()
