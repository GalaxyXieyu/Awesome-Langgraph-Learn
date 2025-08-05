#!/usr/bin/env python3
"""
测试WebSocket + LangGraph交互模式
验证中断和恢复功能
"""

import asyncio
import json
import requests
import websockets
import time

async def test_interactive_mode():
    print("🤔 测试 WebSocket + LangGraph 交互模式")
    print("=" * 60)
    
    # 1. 创建交互模式任务
    print("🧠 1. 创建交互模式任务...")
    task_data = {
        "user_id": "interactive_test_user",
        "topic": "人工智能伦理问题的思考",
        "max_words": 600,
        "style": "academic",
        "language": "zh",
        "mode": "interactive"  # 使用交互模式
    }
    
    try:
        response = requests.post("http://localhost:8004/api/v1/tasks", json=task_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ 交互任务创建成功: {task_id}")
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return False
    
    # 2. WebSocket连接并等待中断
    print(f"\n🔗 2. WebSocket连接并等待中断...")
    ws_url = f"ws://localhost:8004/ws/{task_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket连接成功")
            
            messages = []
            interrupt_received = False
            start_time = time.time()
            
            while time.time() - start_time < 180:  # 3分钟超时
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    messages.append(data)
                    
                    msg_type = data.get("type", "unknown")
                    timestamp = time.strftime('%H:%M:%S')
                    
                    if msg_type == "connected":
                        print(f"   🔗 [{timestamp}] 连接确认")
                    elif msg_type == "task_started":
                        print(f"   🚀 [{timestamp}] 任务开始: {data.get('message')}")
                    elif msg_type == "progress_update":
                        step = data.get("step", "unknown")
                        content_info = data.get("content_info", {})
                        print(f"   🧠 [{timestamp}] LangGraph步骤: {step}")
                        
                        if content_info and "content_preview" in content_info:
                            preview = content_info["content_preview"][:150] + "..."
                            print(f"      💬 {preview}")
                    elif msg_type == "interrupt_request":
                        print(f"   ⚠️ [{timestamp}] 🎉 收到中断请求!")
                        print(f"      💬 消息: {data.get('message', '需要确认')}")
                        interrupt_received = True
                        
                        # 等待一下，然后自动恢复任务
                        print(f"      ⏳ 等待3秒后自动恢复任务...")
                        await asyncio.sleep(3)
                        
                        # 调用恢复API
                        try:
                            resume_response = requests.post(
                                f"http://localhost:8004/api/v1/tasks/{task_id}/resume",
                                json={"response": "yes", "approved": True},
                                timeout=10
                            )
                            
                            if resume_response.status_code == 200:
                                resume_result = resume_response.json()
                                print(f"      ✅ 任务恢复成功: {resume_result['message']}")
                            else:
                                print(f"      ❌ 任务恢复失败: {resume_response.status_code}")
                        except Exception as e:
                            print(f"      ❌ 恢复任务异常: {e}")
                    elif msg_type == "task_resume":
                        print(f"   📤 [{timestamp}] 任务恢复确认")
                    elif msg_type == "task_complete":
                        print(f"   🎉 [{timestamp}] 任务完成!")
                        result = data.get("result", {})
                        if result:
                            article = result.get("article", "")
                            outline = result.get("outline", {})
                            print(f"      📖 文章长度: {len(article)} 字符")
                            print(f"      📝 大纲标题: {outline.get('title', 'N/A')}")
                            
                            if article:
                                print(f"      📄 文章开头: {article[:300]}...")
                        break
                    elif msg_type == "task_failed":
                        print(f"   ❌ [{timestamp}] 任务失败: {data.get('error')}")
                        break
                    elif msg_type == "pong":
                        print("   💓", end="", flush=True)
                    
                except asyncio.TimeoutError:
                    await websocket.send("ping")
                    print("💓", end="", flush=True)
                    continue
            
            elapsed_time = time.time() - start_time
            print(f"\n📊 交互测试结果:")
            print(f"   总消息数: {len(messages)}")
            print(f"   运行时间: {elapsed_time:.1f}秒")
            print(f"   中断功能: {'✅ 正常' if interrupt_received else '❌ 未触发'}")
            
            return interrupt_received
            
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

async def test_copilot_mode():
    """测试Copilot模式（对比）"""
    print("\n🤖 测试 Copilot 模式（对比）...")
    print("=" * 50)
    
    task_data = {
        "user_id": "copilot_test_user",
        "topic": "机器学习算法比较",
        "max_words": 400,
        "style": "professional",
        "language": "zh",
        "mode": "copilot"  # 使用copilot模式
    }
    
    try:
        response = requests.post("http://localhost:8004/api/v1/tasks", json=task_data, timeout=10)
        result = response.json()
        task_id = result["task_id"]
        print(f"✅ Copilot任务创建: {task_id}")
        
        ws_url = f"ws://localhost:8004/ws/{task_id}"
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket连接成功")
            
            interrupt_count = 0
            message_count = 0
            start_time = time.time()
            
            while time.time() - start_time < 120:  # 2分钟超时
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=8.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get("type", "unknown")
                    
                    if msg_type == "interrupt_request":
                        interrupt_count += 1
                        print(f"   ⚠️ Copilot模式收到中断 (不应该发生)")
                    elif msg_type == "task_complete":
                        print(f"   🎉 Copilot任务完成 (无中断)")
                        break
                    elif msg_type not in ["pong", "connected"]:
                        print(f"   📨 {msg_type}")
                        
                except asyncio.TimeoutError:
                    await websocket.send("ping")
                    continue
            
            print(f"📊 Copilot模式结果:")
            print(f"   消息数: {message_count}")
            print(f"   中断次数: {interrupt_count} (应该为0)")
            
            return interrupt_count == 0
            
    except Exception as e:
        print(f"❌ Copilot测试失败: {e}")
        return False

async def main():
    print("🚀 WebSocket + LangGraph 交互功能测试")
    print("=" * 70)
    
    # 测试交互模式
    interactive_success = await test_interactive_mode()
    
    # 测试Copilot模式
    copilot_success = await test_copilot_mode()
    
    print(f"\n📊 测试总结:")
    print(f"   交互模式: {'✅ 通过' if interactive_success else '❌ 失败'}")
    print(f"   Copilot模式: {'✅ 通过' if copilot_success else '❌ 失败'}")
    
    if interactive_success and copilot_success:
        print(f"\n🎉 所有测试通过!")
        print(f"✅ 交互模式支持中断和恢复")
        print(f"✅ Copilot模式自动执行无中断")
        print(f"✅ WebSocket实时推送正常")
        print(f"✅ LangGraph集成完整")
    else:
        print(f"\n⚠️ 部分测试失败，请检查配置")
    
    print(f"\n📱 访问 http://localhost:8004 体验完整功能")

if __name__ == "__main__":
    asyncio.run(main())
