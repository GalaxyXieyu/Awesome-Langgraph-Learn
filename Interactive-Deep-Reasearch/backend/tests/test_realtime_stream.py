#!/usr/bin/env python3
"""
实时流式输出测试 - 立即显示每个chunk
测试简化后的chunk处理效果
"""

import requests
import json
import sys

def test_realtime_stream():
    """测试实时流式输出 - 验证简化后的chunk处理"""

    print("🚀 实时流式输出测试 (简化版chunk)", flush=True)
    print("=" * 60, flush=True)
    
    # 1. 创建任务
    print("📝 创建研究任务...", flush=True)
    try:
        create_response = requests.post(
            "http://localhost:8000/research/tasks",
            json={
                "topic": "人工智能发展趋势",
                "user_id": "test_user"
            },
            timeout=10
        )
        
        if create_response.status_code != 200:
            print(f"❌ 创建任务失败: {create_response.status_code}", flush=True)
            return
        
        task_data = create_response.json()
        task_id = task_data["task_id"]
        print(f"✅ 任务ID: {task_id}", flush=True)
        
    except Exception as e:
        print(f"❌ 创建任务异常: {e}", flush=True)
        return
    
    # 2. 实时流式输出
    print(f"\n📡 开始实时流式输出...", flush=True)
    print("=" * 60, flush=True)
    
    try:
        with requests.get(
            f"http://localhost:8000/research/tasks/{task_id}/stream",
            stream=True,
            headers={"Accept": "text/event-stream"},
            timeout=120
        ) as response:
            
            if response.status_code != 200:
                print(f"❌ 连接失败: {response.status_code}", flush=True)
                return
            
            chunk_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk_count += 1
                    
                    # 立即打印chunk信息
                    print(f"\n📦 #{chunk_count} | {line[:50]}...", flush=True)
                    
                    if line.startswith("data: "):
                        data_part = line[6:]
                        try:
                            parsed = json.loads(data_part)
                            
                            # 如果是简化的消息数据
                            if 'data' in parsed and isinstance(parsed['data'], dict):
                                msg = parsed['data']
                                msg_type = msg.get('message_type', 'unknown')
                                content = msg.get('content', '')[:100]
                                node = msg.get('node', 'unknown')
                                
                                print(f"   🎯 {msg_type} | {node} | {content}...", flush=True)
                                
                                # 如果是interrupt，特别标注
                                if msg_type == 'interrupt':
                                    print(f"   🚨 中断消息！action: {msg.get('action', 'N/A')}", flush=True)
                                
                            else:
                                # 系统消息
                                msg_type = parsed.get('type', 'system')
                                print(f"   ⚙️ 系统: {msg_type}", flush=True)
                                
                        except json.JSONDecodeError:
                            print(f"   📝 非JSON: {data_part[:50]}...", flush=True)
                    
                    # 限制输出
                    if chunk_count >= 25:
                        print("🛑 达到25个chunk，停止测试", flush=True)
                        break
                        
    except KeyboardInterrupt:
        print("\n🛑 用户中断", flush=True)
    except Exception as e:
        print(f"❌ 流式错误: {e}", flush=True)
    
    print(f"\n🏁 测试完成，共处理 {chunk_count} 个chunk", flush=True)

if __name__ == "__main__":
    # 确保立即输出
    sys.stdout.reconfigure(line_buffering=True)
    test_realtime_stream()
