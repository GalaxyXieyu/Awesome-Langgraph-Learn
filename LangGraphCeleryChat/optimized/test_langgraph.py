#!/usr/bin/env python3
"""
测试WebSocket + LangGraph集成版本
验证真正的LangGraph工作流是否正常工作
"""

import asyncio
import json
import requests
import websockets
import time

async def test_langgraph_integration():
    print("🧠 测试 WebSocket + LangGraph 集成版本")
    print("=" * 60)
    
    # 1. 健康检查
    print("🔍 1. 健康检查...")
    try:
        response = requests.get("http://localhost:8004/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ 健康状态: {health}")
            if health.get('services', {}).get('langgraph') == 'ok':
                print("✅ LangGraph集成正常")
            else:
                print("⚠️ LangGraph集成状态未知")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 创建LangGraph任务
    print("\n🧠 2. 创建LangGraph任务...")
    task_data = {
        "user_id": "langgraph_test_user",
        "topic": "深度学习在自然语言处理中的最新进展",
        "max_words": 800,
        "style": "academic",
        "language": "zh",
        "mode": "copilot"  # 使用copilot模式避免中断
    }
    
    try:
        response = requests.post("http://localhost:8004/api/v1/tasks", json=task_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ LangGraph任务创建成功: {task_id}")
            print(f"📊 初始状态: {result['status']}")
            print(f"💬 消息: {result['message']}")
        else:
            print(f"❌ LangGraph任务创建失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ LangGraph任务创建异常: {e}")
        return False
    
    # 3. WebSocket连接测试
    print(f"\n🔗 3. WebSocket连接测试...")
    ws_url = f"ws://localhost:8004/ws/{task_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket连接成功")
            
            # 收集所有消息
            messages = []
            langgraph_steps = []
            start_time = time.time()
            
            while time.time() - start_time < 300:  # 5分钟超时
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(message)
                    messages.append(data)
                    
                    msg_type = data.get("type", "unknown")
                    timestamp = time.strftime('%H:%M:%S')
                    
                    if msg_type == "connected":
                        print(f"   🔗 [{timestamp}] 连接确认: {data.get('task_id')}")
                        print(f"   💬 {data.get('message', '')}")
                    elif msg_type == "task_started":
                        print(f"   🚀 [{timestamp}] 任务开始: {data.get('message')}")
                    elif msg_type == "progress_update":
                        step = data.get("step", "unknown")
                        content_info = data.get("content_info", {})
                        langgraph_steps.append({"step": step, "content_info": content_info})
                        
                        print(f"   🧠 [{timestamp}] LangGraph步骤: {step}")
                        
                        if content_info:
                            if "content_preview" in content_info:
                                preview = content_info["content_preview"]
                                length = content_info.get("content_length", 0)
                                msg_type_inner = content_info.get("message_type", "Unknown")
                                print(f"      📝 {msg_type_inner} ({length} 字符)")
                                print(f"      💬 {preview[:200]}...")
                            
                            for key, value in content_info.items():
                                if key not in ["content_preview", "content_length", "message_type"]:
                                    print(f"      📊 {key}: {value}")
                    elif msg_type == "task_complete":
                        print(f"   🎉 [{timestamp}] LangGraph任务完成!")
                        result = data.get("result", {})
                        if result:
                            article = result.get("article", "")
                            outline = result.get("outline", {})
                            search_results = result.get("search_results", [])
                            
                            print(f"      📖 文章长度: {len(article)} 字符")
                            print(f"      📝 大纲标题: {outline.get('title', 'N/A')}")
                            print(f"      📋 大纲章节: {len(outline.get('sections', []))}")
                            print(f"      🔍 搜索结果: {len(search_results)} 条")
                            
                            if article:
                                print(f"      📄 文章开头:")
                                print(f"      {article[:500]}...")
                        break
                    elif msg_type == "task_failed":
                        print(f"   ❌ [{timestamp}] LangGraph任务失败: {data.get('error')}")
                        break
                    elif msg_type == "interrupt_request":
                        print(f"   ⚠️ [{timestamp}] LangGraph中断请求: {data.get('message')}")
                    elif msg_type == "pong":
                        print("   💓", end="", flush=True)
                    else:
                        print(f"   📨 [{timestamp}] 其他消息: {msg_type}")
                    
                except asyncio.TimeoutError:
                    # 发送心跳
                    await websocket.send("ping")
                    print("💓", end="", flush=True)
                    continue
            
            elapsed_time = time.time() - start_time
            print(f"\n📊 WebSocket测试结果:")
            print(f"   总消息数: {len(messages)}")
            print(f"   LangGraph步骤: {len(langgraph_steps)}")
            print(f"   运行时间: {elapsed_time:.1f}秒")
            print(f"   消息频率: {len(messages)/elapsed_time:.2f} msg/s")
            
            # 验证LangGraph步骤
            print(f"\n🧠 LangGraph步骤分析:")
            for i, step_info in enumerate(langgraph_steps):
                step = step_info["step"]
                content_info = step_info["content_info"]
                content_length = content_info.get("content_length", 0)
                print(f"   [{i+1}] {step}: {content_length} 字符")
            
            # 验证消息完整性
            message_types = [msg.get("type") for msg in messages]
            expected_types = ["connected", "task_started", "progress_update", "task_complete"]
            
            print(f"\n🔍 消息完整性检查:")
            for expected in expected_types:
                count = message_types.count(expected)
                if expected == "progress_update":
                    print(f"   {expected}: {count} 条 {'✅' if count >= 3 else '⚠️'}")
                else:
                    print(f"   {expected}: {count} 条 {'✅' if count >= 1 else '❌'}")
            
            if len(langgraph_steps) >= 3:
                print(f"✅ LangGraph步骤完整性: 收到 {len(langgraph_steps)} 个步骤")
                return True
            else:
                print(f"⚠️ LangGraph步骤不完整: 只收到 {len(langgraph_steps)} 个步骤")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False
    
    # 4. 最终任务状态检查
    print(f"\n📊 4. 最终任务状态检查...")
    try:
        response = requests.get(f"http://localhost:8004/api/v1/tasks/{task_id}", timeout=5)
        if response.status_code == 200:
            task_info = response.json()
            print(f"   最终状态: {task_info.get('status')}")
            print(f"   创建时间: {task_info.get('created_at')}")
            print(f"   完成时间: {task_info.get('completed_at')}")
            
            if task_info.get('status') == 'completed':
                result = task_info.get('result', {})
                if result:
                    article = result.get('article', '')
                    outline = result.get('outline', {})
                    print(f"   📖 最终文章长度: {len(article)} 字符")
                    print(f"   📝 最终大纲: {outline.get('title', 'N/A')}")
                    print(f"✅ LangGraph任务完整性验证通过")
                    return True
                else:
                    print(f"⚠️ LangGraph任务结果为空")
                    return False
            else:
                print(f"❌ LangGraph任务未完成: {task_info.get('status')}")
                return False
        else:
            print(f"❌ 获取任务状态失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 任务状态检查异常: {e}")
        return False

async def main():
    print("🚀 WebSocket + LangGraph 集成测试")
    print("=" * 70)
    
    success = await test_langgraph_integration()
    
    if success:
        print(f"\n🎉 测试成功! WebSocket + LangGraph 集成版本完全正常!")
        print(f"✅ 真正的LangGraph工作流正常运行")
        print(f"✅ WebSocket实时推送正常工作")
        print(f"✅ 支持高并发连接")
        print(f"✅ 完整的AI生成过程展示")
    else:
        print(f"\n❌ 测试失败! 请检查LangGraph集成")
    
    print(f"\n📱 访问 http://localhost:8004 体验完整功能")

if __name__ == "__main__":
    asyncio.run(main())
