#!/usr/bin/env python3
"""
测试 Resume 功能
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

def test_interrupt_workflow():
    """测试中断工作流"""
    print("🧪 测试 LangGraph Interrupt 和 Resume 功能")
    print("=" * 60)
    
    # 1. 创建一个需要用户交互的任务
    print("\n📋 步骤 1: 创建交互式任务...")
    
    task_config = {
        "config": {
            "topic": "人工智能在自动驾驶中的应用",
            "mode": "interactive"  # 交互模式，会触发中断
        },
        "user_id": "test_user_interrupt"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_config)
    if response.status_code != 200:
        print(f"❌ 任务创建失败: {response.status_code} - {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data["task_id"]
    session_id = task_data["session_id"]
    
    print(f"✅ 任务创建成功: {task_id}")
    print(f"   会话 ID: {session_id}")
    
    # 2. 等待任务执行到中断点
    print(f"\n⏳ 步骤 2: 等待任务执行到中断点...")
    
    max_wait = 30  # 最多等待30秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            task_status = response.json()
            status = task_status.get("status")
            current_step = task_status.get("current_step", "")
            
            print(f"   状态: {status}, 步骤: {current_step}")
            
            if status == "paused" or "awaiting" in current_step:
                print(f"✅ 任务已暂停，等待用户交互")
                print(f"   当前步骤: {current_step}")
                
                # 显示大纲
                outline = task_status.get("outline")
                if outline:
                    print(f"   生成的大纲:")
                    print(f"     标题: {outline.get('title', 'N/A')}")
                    sections = outline.get("sections", [])
                    for i, section in enumerate(sections[:3], 1):
                        print(f"     {i}. {section.get('title', 'N/A')}")
                
                break
            elif status == "completed":
                print(f"⚠️ 任务已完成，没有触发中断")
                return
            elif status == "failed":
                print(f"❌ 任务执行失败")
                return
        
        time.sleep(2)
    else:
        print(f"⏰ 等待超时，任务可能没有触发中断")
        return
    
    # 3. 发送用户响应，恢复任务
    print(f"\n🔄 步骤 3: 发送用户响应，恢复任务...")
    
    # 模拟用户确认继续
    user_response = {
        "response": "确认继续",
        "approved": True,
        "comment": "大纲看起来不错，请继续写文章"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/tasks/{task_id}/resume",
        json=user_response
    )
    
    if response.status_code != 200:
        print(f"❌ 恢复任务失败: {response.status_code} - {response.text}")
        return
    
    resume_data = response.json()
    print(f"✅ 任务恢复成功")
    print(f"   消息: {resume_data.get('message', 'N/A')}")
    
    # 4. 监控任务完成
    print(f"\n📊 步骤 4: 监控任务完成...")
    
    max_wait = 60  # 最多等待60秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            task_status = response.json()
            status = task_status.get("status")
            current_step = task_status.get("current_step", "")
            progress = task_status.get("progress", 0)
            
            print(f"   状态: {status}, 步骤: {current_step}, 进度: {progress}%")
            
            if status == "completed":
                print(f"🎉 任务完成！")
                
                # 显示结果
                article = task_status.get("article", "")
                word_count = task_status.get("word_count", 0)
                generation_time = task_status.get("generation_time", 0)
                
                print(f"   文章字数: {word_count}")
                print(f"   生成时间: {generation_time:.2f} 秒")
                print(f"   文章预览: {article[:100]}...")
                
                break
            elif status == "failed":
                error_msg = task_status.get("error_message", "未知错误")
                print(f"❌ 任务执行失败: {error_msg}")
                return
            elif status == "paused":
                print(f"⚠️ 任务再次暂停，可能需要更多用户交互")
                break
        
        time.sleep(3)
    else:
        print(f"⏰ 等待超时")
    
    print(f"\n🎯 Resume 功能测试完成")

def test_reject_and_regenerate():
    """测试拒绝大纲并重新生成"""
    print("\n" + "=" * 60)
    print("🧪 测试拒绝大纲并重新生成功能")
    print("=" * 60)
    
    # 创建任务
    task_config = {
        "config": {
            "topic": "区块链技术在供应链管理中的应用",
            "mode": "interactive"
        },
        "user_id": "test_user_reject"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_config)
    if response.status_code != 200:
        print(f"❌ 任务创建失败: {response.status_code} - {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data["task_id"]
    
    print(f"✅ 任务创建成功: {task_id}")
    
    # 等待中断
    time.sleep(5)
    
    # 拒绝大纲
    user_response = {
        "response": "拒绝",
        "approved": False,
        "comment": "大纲不够详细，请重新生成"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/tasks/{task_id}/resume",
        json=user_response
    )
    
    if response.status_code == 200:
        print(f"✅ 拒绝响应发送成功")
    else:
        print(f"❌ 拒绝响应失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API 服务未运行，请先启动服务")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 API 服务，请确保服务已启动")
        sys.exit(1)
    
    # 运行测试
    test_interrupt_workflow()
    test_reject_and_regenerate()
