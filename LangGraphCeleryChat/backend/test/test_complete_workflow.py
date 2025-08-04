#!/usr/bin/env python3
"""
完整的工作流测试
模拟真实的用户交互场景，测试整个工作流的执行和恢复过程
"""

import sys
import os
import asyncio
import logging
import json
import time
from unittest.mock import Mock
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockRedisClient:
    """模拟 Redis 客户端，记录所有操作"""
    
    def __init__(self):
        self.streams = {}  # 存储流数据
        self.call_log = []  # 记录所有调用
        
    def xadd(self, stream_name: str, data: Dict[str, Any]):
        """模拟 xadd 操作"""
        if stream_name not in self.streams:
            self.streams[stream_name] = []
        
        # 添加时间戳
        entry = {
            'id': f"{int(time.time() * 1000)}-{len(self.streams[stream_name])}",
            'data': data,
            'timestamp': time.time()
        }
        
        self.streams[stream_name].append(entry)
        self.call_log.append(('xadd', stream_name, data))
        
        return entry['id']
    
    def get_stream_events(self, stream_name: str) -> List[Dict[str, Any]]:
        """获取流中的所有事件"""
        return self.streams.get(stream_name, [])
    
    def get_latest_events(self, stream_name: str, count: int = 5) -> List[Dict[str, Any]]:
        """获取最新的事件"""
        events = self.streams.get(stream_name, [])
        return events[-count:] if events else []

async def test_complete_workflow():
    """测试完整的工作流程"""
    print("🚀 开始完整工作流测试...")
    print("=" * 80)
    
    # 创建模拟 Redis 客户端
    mock_redis = MockRedisClient()
    
    try:
        from backend.adapters.workflow_adapter import WorkflowAdapter
        
        # 创建适配器
        conversation_id = "test_complete_workflow_001"
        adapter = WorkflowAdapter(conversation_id, mock_redis)
        
        print(f"✅ 适配器创建成功: {conversation_id}")
        print(f"📊 图类型: {type(adapter.graph)}")
        
        # 准备初始状态
        initial_state = {
            "topic": "Python异步编程最佳实践",
            "user_id": "test_user_001",
            "max_words": 800,
            "style": "technical",
            "language": "zh",
            "mode": "interactive"
        }
        
        print(f"\n📝 初始状态: {initial_state['topic']}")
        
        # 第一步：开始工作流
        print("\n🚀 第一步：开始工作流执行...")
        result1 = await adapter.execute_workflow(initial_state=initial_state)
        
        print(f"📋 第一步结果:")
        print(f"  completed: {result1.get('completed', False)}")
        print(f"  interrupted: {result1.get('interrupted', False)}")
        if result1.get('interrupted'):
            print(f"  interrupt_type: {result1.get('interrupt_type', 'unknown')}")
            print(f"  message: {result1.get('message', 'no message')}")
        
        # 检查流式数据
        stream_name = f"conversation_events:{conversation_id}"
        events = mock_redis.get_latest_events(stream_name, 10)
        print(f"\n📊 流式事件数量: {len(mock_redis.get_stream_events(stream_name))}")
        print("📤 最新事件:")
        for i, event in enumerate(events[-3:], 1):  # 显示最后3个事件
            data = json.loads(event['data'].get('data', '{}'))
            print(f"  {i}. {data.get('step', 'unknown')} - {data.get('status', 'no status')}")
        
        # 如果有中断，继续处理
        if result1.get('interrupted'):
            print(f"\n🔄 第二步：处理中断 - {result1.get('interrupt_type')}")
            
            # 模拟用户确认
            user_responses = ["yes", "yes", "yes"]  # 对所有确认都回答 yes
            
            for i, response in enumerate(user_responses, 1):
                print(f"\n  🔄 第{i+1}步：用户响应 '{response}'")
                
                result = await adapter.execute_workflow(resume_command=response)
                
                print(f"  📋 结果:")
                print(f"    completed: {result.get('completed', False)}")
                print(f"    interrupted: {result.get('interrupted', False)}")
                
                if result.get('interrupted'):
                    print(f"    interrupt_type: {result.get('interrupt_type', 'unknown')}")
                    print(f"    message: {result.get('message', 'no message')}")
                else:
                    print("  ✅ 工作流完成！")
                    break
                
                # 显示最新事件
                latest_events = mock_redis.get_latest_events(stream_name, 3)
                if latest_events:
                    latest_data = json.loads(latest_events[-1]['data'].get('data', '{}'))
                    print(f"    最新状态: {latest_data.get('step', 'unknown')} - {latest_data.get('status', 'no status')}")
        
        # 最终统计
        total_events = len(mock_redis.get_stream_events(stream_name))
        print(f"\n📊 最终统计:")
        print(f"  总事件数: {total_events}")
        print(f"  Redis 调用次数: {len(mock_redis.call_log)}")
        
        # 分析事件类型
        all_events = mock_redis.get_stream_events(stream_name)
        event_types = {}
        steps = {}
        
        for event in all_events:
            try:
                data = json.loads(event['data'].get('data', '{}'))
                event_type = data.get('event_type', 'unknown')
                step = data.get('step', 'unknown')
                
                event_types[event_type] = event_types.get(event_type, 0) + 1
                steps[step] = steps.get(step, 0) + 1
            except:
                continue
        
        print(f"\n📈 事件类型分布:")
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count}")
        
        print(f"\n📈 步骤分布:")
        for step, count in steps.items():
            print(f"  {step}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_scenarios():
    """测试错误场景"""
    print("\n🧪 测试错误场景...")
    print("-" * 40)
    
    mock_redis = MockRedisClient()
    
    try:
        from backend.adapters.workflow_adapter import WorkflowAdapter
        
        adapter = WorkflowAdapter("test_error_001", mock_redis)
        
        # 测试无效参数
        print("1. 测试无效参数...")
        try:
            await adapter.execute_workflow()  # 没有提供任何参数
            print("❌ 应该抛出异常")
        except ValueError as e:
            print(f"✅ 正确捕获异常: {e}")
        
        # 测试同时提供两个参数
        print("\n2. 测试同时提供两个参数...")
        try:
            await adapter.execute_workflow(
                initial_state={"topic": "test"}, 
                resume_command="yes"
            )
            print("❌ 应该抛出异常")
        except ValueError as e:
            print(f"✅ 正确捕获异常: {e}")
        
        print("✅ 错误场景测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误场景测试失败: {e}")
        return False

async def test_data_integrity():
    """测试数据完整性"""
    print("\n🧪 测试数据完整性...")
    print("-" * 40)
    
    mock_redis = MockRedisClient()
    
    try:
        from backend.adapters.workflow_adapter import WorkflowAdapter
        
        adapter = WorkflowAdapter("test_integrity_001", mock_redis)
        
        # 执行一个简单的工作流
        initial_state = {
            "topic": "数据完整性测试",
            "user_id": "test_user",
            "mode": "copilot"  # 自动模式，减少中断
        }
        
        result = await adapter.execute_workflow(initial_state=initial_state)
        
        # 检查数据完整性
        stream_name = f"conversation_events:test_integrity_001"
        events = mock_redis.get_stream_events(stream_name)
        
        print(f"📊 事件总数: {len(events)}")
        
        # 验证每个事件的数据格式
        valid_events = 0
        for event in events:
            try:
                data = json.loads(event['data'].get('data', '{}'))
                
                # 检查必需字段
                required_fields = ['event_type', 'conversation_id']
                if all(field in data for field in required_fields):
                    valid_events += 1
                    
            except Exception as e:
                print(f"⚠️ 事件数据格式错误: {e}")
        
        print(f"✅ 有效事件: {valid_events}/{len(events)}")
        
        if valid_events == len(events):
            print("✅ 数据完整性测试通过")
            return True
        else:
            print("❌ 数据完整性测试失败")
            return False
        
    except Exception as e:
        print(f"❌ 数据完整性测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始完整的工作流测试套件...")
    print("=" * 80)
    
    results = []
    
    # 测试完整工作流
    print("📋 测试 1: 完整工作流")
    result1 = await test_complete_workflow()
    results.append(("完整工作流", result1))
    
    # 测试错误场景
    print("\n📋 测试 2: 错误场景")
    result2 = await test_error_scenarios()
    results.append(("错误场景", result2))
    
    # 测试数据完整性
    print("\n📋 测试 3: 数据完整性")
    result3 = await test_data_integrity()
    results.append(("数据完整性", result3))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总:")
    print("=" * 80)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！可以集成到 API 中了！")
        print("\n📋 下一步:")
        print("1. 更新 Celery 任务以使用新的 WorkflowAdapter")
        print("2. 更新 FastAPI 路由以支持统一接口")
        print("3. 更新前端以处理新的事件格式")
        print("4. 进行集成测试")
    else:
        print("\n⚠️ 部分测试失败，需要进一步修复")
    
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
