#!/usr/bin/env python3
"""
LangGraph Celery Chat API 测试脚本
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any

# API 基础 URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_create_session():
    """测试创建会话"""
    print("\n📝 测试创建会话...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/sessions", params={"user_id": "test_user"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 会话创建成功: {data['session_id']}")
            return data['session_id']
        else:
            print(f"❌ 会话创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 会话创建异常: {e}")
        return None

def test_create_task():
    """测试创建写作任务"""
    print("\n📋 测试创建写作任务...")
    try:
        task_config = {
            "config": {
                "topic": "人工智能在医疗诊断中的应用",
                "mode": "copilot"
            },
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_config)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务创建成功: {data['task_id']}")
            return data['task_id'], data['session_id']
        else:
            print(f"❌ 任务创建失败: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return None, None

def test_get_task_status(task_id: str):
    """测试获取任务状态"""
    print(f"\n📊 测试获取任务状态: {task_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务状态: {data['status']} - {data['current_step']}")
            print(f"   进度: {data['progress']}%")
            return data
        else:
            print(f"❌ 获取任务状态失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 获取任务状态异常: {e}")
        return None

def test_event_stream(session_id: str, duration: int = 10):
    """测试事件流"""
    print(f"\n📡 测试事件流 (监听 {duration} 秒)...")
    try:
        import sseclient
        
        url = f"{BASE_URL}/api/v1/events/{session_id}"
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            client = sseclient.SSEClient(response)
            start_time = time.time()
            event_count = 0
            
            for event in client.events():
                if time.time() - start_time > duration:
                    break
                
                if event.data:
                    try:
                        data = json.loads(event.data)
                        event_count += 1
                        print(f"📨 事件 {event_count}: {data.get('event_type', 'unknown')} - {data.get('data', {}).get('status', '')}")
                    except json.JSONDecodeError:
                        print(f"📨 原始事件: {event.data}")
            
            print(f"✅ 事件流测试完成，收到 {event_count} 个事件")
            return True
        else:
            print(f"❌ 事件流连接失败: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  sseclient 未安装，跳过事件流测试")
        print("   安装命令: pip install sseclient-py")
        return False
    except Exception as e:
        print(f"❌ 事件流测试异常: {e}")
        return False

def monitor_task_completion(task_id: str, max_wait: int = 60):
    """监控任务完成"""
    print(f"\n⏳ 监控任务完成: {task_id} (最多等待 {max_wait} 秒)")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status_data = test_get_task_status(task_id)
        if status_data:
            status = status_data.get('status', 'unknown')
            if status in ['completed', 'failed', 'cancelled']:
                print(f"🎯 任务最终状态: {status}")
                if status == 'completed':
                    print(f"📄 生成文章长度: {status_data.get('word_count', 0)} 字")
                    if status_data.get('article'):
                        preview = status_data['article'][:200] + "..." if len(status_data['article']) > 200 else status_data['article']
                        print(f"📝 文章预览: {preview}")
                return status_data
        
        time.sleep(5)  # 每5秒检查一次
    
    print("⏰ 任务监控超时")
    return None

def main():
    """主测试函数"""
    print("🧪 LangGraph Celery Chat API 测试")
    print("=" * 50)
    
    # 1. 健康检查
    if not test_health_check():
        print("❌ 服务未启动或不可用")
        return
    
    # 2. 创建会话
    session_id = test_create_session()
    if not session_id:
        print("❌ 无法创建会话，停止测试")
        return
    
    # 3. 创建任务
    task_id, task_session_id = test_create_task()
    if not task_id:
        print("❌ 无法创建任务，停止测试")
        return
    
    # 4. 获取初始任务状态 (稍等一下让任务状态写入)
    time.sleep(1)
    initial_status = test_get_task_status(task_id)
    if not initial_status:
        print("❌ 无法获取任务状态")
        return
    
    # 5. 测试事件流（异步）
    print("\n🔄 开始并行测试...")
    
    # 启动事件流监听（在后台）
    import threading
    
    def event_stream_thread():
        test_event_stream(task_session_id or session_id, duration=30)
    
    event_thread = threading.Thread(target=event_stream_thread)
    event_thread.daemon = True
    event_thread.start()
    
    # 6. 监控任务完成
    final_status = monitor_task_completion(task_id, max_wait=120)
    
    # 7. 总结测试结果
    print("\n📊 测试总结")
    print("-" * 30)
    print(f"✅ 健康检查: 通过")
    print(f"✅ 会话创建: 通过 ({session_id})")
    print(f"✅ 任务创建: 通过 ({task_id})")
    print(f"✅ 状态查询: 通过")
    
    if final_status:
        status = final_status.get('status', 'unknown')
        if status == 'completed':
            print(f"✅ 任务执行: 成功完成")
            print(f"   - 生成时间: {final_status.get('generation_time', 0):.2f} 秒")
            print(f"   - 文章字数: {final_status.get('word_count', 0)} 字")
        else:
            print(f"⚠️  任务执行: {status}")
            if final_status.get('error_message'):
                print(f"   - 错误信息: {final_status['error_message']}")
    else:
        print(f"❌ 任务执行: 超时或失败")
    
    print(f"\n🎉 测试完成！")

if __name__ == "__main__":
    main()
