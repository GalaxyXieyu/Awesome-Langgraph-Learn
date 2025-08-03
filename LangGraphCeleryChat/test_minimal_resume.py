#!/usr/bin/env python3
"""
Minimal Resume Functionality Test
Tests the core interrupt and resume mechanism
"""

import requests
import json
import time
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# API 基础 URL
BASE_URL = "http://localhost:8000"

def test_basic_api():
    """测试基本 API 功能"""
    print("🧪 测试基本 API 功能")
    
    # 健康检查
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code != 200:
        print(f"❌ 健康检查失败: {response.status_code}")
        return False
    
    print("✅ 健康检查通过")
    
    # 创建会话
    response = requests.post(f"{BASE_URL}/api/v1/sessions?user_id=test_user")
    if response.status_code != 200:
        print(f"❌ 创建会话失败: {response.status_code}")
        return False
    
    session_data = response.json()
    print(f"✅ 会话创建成功: {session_data['session_id']}")
    
    return True

def test_task_creation():
    """测试任务创建"""
    print("\n🧪 测试任务创建")
    
    task_config = {
        "config": {
            "topic": "简单测试主题",
            "mode": "copilot"  # 使用自动模式避免中断
        },
        "user_id": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_config)
    if response.status_code != 200:
        print(f"❌ 任务创建失败: {response.status_code} - {response.text}")
        return None
    
    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"✅ 任务创建成功: {task_id}")
    
    return task_id

def test_task_status(task_id):
    """测试任务状态查询"""
    print(f"\n🧪 测试任务状态查询: {task_id}")
    
    # 等待任务执行
    for i in range(30):  # 最多等待60秒
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code != 200:
            print(f"❌ 查询任务状态失败: {response.status_code}")
            return False
        
        status_data = response.json()
        status = status_data.get("status")
        error_msg = status_data.get("error_message")
        
        print(f"   状态: {status}")
        
        if status == "completed":
            print("✅ 任务执行成功")
            print(f"   文章字数: {status_data.get('word_count', 0)}")
            return True
        elif status == "failed":
            print(f"❌ 任务执行失败: {error_msg}")
            return False
        
        time.sleep(2)
    
    print("⏰ 任务执行超时")
    return False

def test_interrupt_task():
    """测试中断任务"""
    print("\n🧪 测试中断任务")
    
    task_config = {
        "config": {
            "topic": "需要中断的测试主题",
            "mode": "interactive"  # 交互模式，应该触发中断
        },
        "user_id": "test_interrupt"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_config)
    if response.status_code != 200:
        print(f"❌ 中断任务创建失败: {response.status_code} - {response.text}")
        return None
    
    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"✅ 中断任务创建成功: {task_id}")
    
    # 等待任务执行到中断点
    for i in range(30):
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code != 200:
            print(f"❌ 查询中断任务状态失败: {response.status_code}")
            return None
        
        status_data = response.json()
        status = status_data.get("status")
        error_msg = status_data.get("error_message")
        
        print(f"   状态: {status}")
        
        if status == "paused":
            print("✅ 任务成功中断")
            return task_id
        elif status == "failed":
            print(f"❌ 任务执行失败: {error_msg}")
            return None
        elif status == "completed":
            print("⚠️ 任务直接完成，没有中断")
            return None
        
        time.sleep(2)
    
    print("⏰ 等待中断超时")
    return None

def test_resume_task(task_id):
    """测试恢复任务"""
    print(f"\n🧪 测试恢复任务: {task_id}")
    
    user_response = {
        "response": "确认继续",
        "approved": True,
        "comment": "请继续执行"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tasks/{task_id}/resume", json=user_response)
    if response.status_code != 200:
        print(f"❌ 恢复任务失败: {response.status_code} - {response.text}")
        return False
    
    resume_data = response.json()
    print(f"✅ 任务恢复成功: {resume_data.get('message', 'N/A')}")
    
    # 等待任务完成
    for i in range(30):
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code != 200:
            print(f"❌ 查询恢复任务状态失败: {response.status_code}")
            return False
        
        status_data = response.json()
        status = status_data.get("status")
        error_msg = status_data.get("error_message")
        
        print(f"   状态: {status}")
        
        if status == "completed":
            print("🎉 任务恢复并完成成功")
            print(f"   文章字数: {status_data.get('word_count', 0)}")
            return True
        elif status == "failed":
            print(f"❌ 恢复任务执行失败: {error_msg}")
            return False
        
        time.sleep(2)
    
    print("⏰ 恢复任务执行超时")
    return False

def main():
    """主测试函数"""
    print("🚀 开始最小化 Resume 功能测试")
    print("=" * 50)
    
    # 测试基本 API
    if not test_basic_api():
        print("❌ 基本 API 测试失败")
        return False
    
    # 测试任务创建和执行
    task_id = test_task_creation()
    if not task_id:
        print("❌ 任务创建测试失败")
        return False
    
    if not test_task_status(task_id):
        print("❌ 任务状态测试失败")
        return False
    
    # 测试中断和恢复
    interrupt_task_id = test_interrupt_task()
    if not interrupt_task_id:
        print("❌ 中断任务测试失败")
        return False
    
    if not test_resume_task(interrupt_task_id):
        print("❌ 恢复任务测试失败")
        return False
    
    print("\n🎉 所有测试通过！Resume 功能基本正常")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
