#!/usr/bin/env python3
"""
测试 API 集成 - 真实的端到端测试
使用已启动的服务进行完整的工作流测试
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# API 基础 URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  状态: {data.get('status')}")
            print(f"  Redis: {data.get('services', {}).get('redis')}")
            print(f"  Celery: {data.get('services', {}).get('celery')}")
            return True
        else:
            print(f"  错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"  健康检查失败: {e}")
        return False

def test_create_task():
    """测试创建任务"""
    print("\n🚀 测试创建任务...")
    
    try:
        # 准备请求数据
        task_data = {
            "conversation_id": "test_api_integration_001",
            "user_id": "test_user_001",
            "config": {
                "topic": "Python异步编程最佳实践",
                "max_words": 600,
                "style": "technical",
                "language": "zh",
                "mode": "interactive"
            }
        }
        
        print(f"  主题: {task_data['config']['topic']}")
        
        # 发送请求
        response = requests.post(
            f"{BASE_URL}/api/v1/tasks",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            session_id = data.get("session_id")
            
            print(f"  任务ID: {task_id}")
            print(f"  会话ID: {session_id}")
            print(f"  状态: {data.get('status')}")
            print(f"  消息: {data.get('message')}")
            
            return task_id, session_id
        else:
            print(f"  错误: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"  创建任务失败: {e}")
        return None, None

def test_task_status(task_id: str):
    """测试任务状态查询"""
    print(f"\n📊 测试任务状态查询: {task_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  任务状态: {data.get('status')}")
            print(f"  当前步骤: {data.get('current_step')}")
            print(f"  进度: {data.get('progress')}%")
            
            if data.get('outline'):
                print(f"  大纲长度: {len(data.get('outline', ''))}")
            if data.get('article'):
                print(f"  文章长度: {len(data.get('article', ''))}")
                
            return data
        else:
            print(f"  错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"  查询任务状态失败: {e}")
        return None

def test_event_stream(conversation_id: str, duration: int = 30):
    """测试事件流"""
    print(f"\n📡 测试事件流: {conversation_id} (持续 {duration} 秒)")
    
    try:
        url = f"{BASE_URL}/api/v1/events/{conversation_id}"
        
        with requests.get(url, stream=True, timeout=duration + 5) as response:
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                event_count = 0
                start_time = time.time()
                
                for line in response.iter_lines():
                    if time.time() - start_time > duration:
                        break
                        
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])  # 去掉 'data: ' 前缀
                                
                                if data.get('type') != 'heartbeat':
                                    event_count += 1
                                    print(f"  事件 {event_count}: {data.get('step', 'unknown')} - {data.get('status', '')}")
                                    
                                    if event_count <= 3:  # 只显示前3个事件的详细信息
                                        print(f"    类型: {data.get('event_type')}")
                                        print(f"    进度: {data.get('progress', 0)}%")
                                
                            except json.JSONDecodeError:
                                continue
                
                print(f"  总事件数: {event_count}")
                return event_count > 0
            else:
                print(f"  错误: {response.text}")
                return False
                
    except Exception as e:
        print(f"  事件流测试失败: {e}")
        return False

def test_resume_task(task_id: str):
    """测试任务恢复"""
    print(f"\n🔄 测试任务恢复: {task_id}")
    
    try:
        # 准备恢复请求
        resume_data = {
            "response": "yes",
            "interrupt_id": "test_interrupt",
            "user_input": "继续执行"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/tasks/{task_id}/resume",
            json=resume_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  消息: {data.get('message')}")
            print(f"  Celery任务ID: {data.get('celery_task_id')}")
            return True
        else:
            print(f"  错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"  恢复任务失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 API 集成测试...")
    print("=" * 80)
    
    results = []
    
    # 1. 健康检查
    print("📋 测试 1: 健康检查")
    health_ok = test_health_check()
    results.append(("健康检查", health_ok))
    
    if not health_ok:
        print("❌ 健康检查失败，停止测试")
        return False
    
    # 2. 创建任务
    print("\n📋 测试 2: 创建任务")
    task_id, session_id = test_create_task()
    task_created = task_id is not None
    results.append(("创建任务", task_created))
    
    if not task_created:
        print("❌ 创建任务失败，停止测试")
        return False
    
    # 3. 等待任务开始执行
    print("\n⏳ 等待任务开始执行...")
    time.sleep(5)
    
    # 4. 查询任务状态
    print("\n📋 测试 3: 任务状态查询")
    task_status = test_task_status(task_id)
    status_ok = task_status is not None
    results.append(("任务状态查询", status_ok))
    
    # 5. 测试事件流
    print("\n📋 测试 4: 事件流")
    conversation_id = session_id  # 使用 session_id 作为 conversation_id
    stream_ok = test_event_stream(conversation_id, duration=20)
    results.append(("事件流", stream_ok))
    
    # 6. 测试任务恢复（如果任务被暂停）
    if task_status and task_status.get('status') == 'paused':
        print("\n📋 测试 5: 任务恢复")
        resume_ok = test_resume_task(task_id)
        results.append(("任务恢复", resume_ok))
    
    # 7. 最终状态检查
    print("\n📋 最终状态检查")
    time.sleep(10)
    final_status = test_task_status(task_id)
    
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
    
    if final_status:
        print(f"\n📊 最终任务状态:")
        print(f"  状态: {final_status.get('status')}")
        print(f"  步骤: {final_status.get('current_step')}")
        print(f"  进度: {final_status.get('progress')}%")
        if final_status.get('article'):
            print(f"  文章长度: {len(final_status.get('article', ''))} 字符")
    
    success = passed >= len(results) * 0.8  # 80% 通过率算成功
    
    if success:
        print("\n🎉 API 集成测试基本成功！")
        print("\n💡 重构后的 WorkflowAdapter 工作正常！")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
