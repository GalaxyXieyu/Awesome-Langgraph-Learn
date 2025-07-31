#!/usr/bin/env python3
"""
测试大纲生成的流式输出效果 - 单独测试
"""

import asyncio
from typing import Dict, Any, cast
from graph import create_writing_assistant_graph, initialize_writing_state
from tools import load_knowledge_bases

async def test_outline_streaming():
    """专门测试大纲生成的流式效果"""
    print("🎯 测试大纲生成的流式输出效果")
    print("=" * 50)
    
    # 初始化
    try:
        load_knowledge_bases()
        print("✅ 知识库初始化成功")
    except Exception as e:
        print(f"⚠️ 知识库初始化警告: {e}")
    
    graph = create_writing_assistant_graph()
    print("✅ 图创建成功")
    
    # 初始化状态 - 设置为不需要确认，避开中断问题
    initial_state = initialize_writing_state(
        topic="Python异步编程最佳实践",
        user_id="outline_test",
        max_words=600,
        style="technical",
        language="zh",
        enable_search=False  # 禁用搜索避开后续中断
    )
    
    # 设置不需要确认
    initial_state["require_confirmation"] = False
    
    config: Dict[str, Any] = {"configurable": {"thread_id": "outline_streaming_001"}}
    
    print(f"\n📝 主题: {initial_state['topic']}")
    print("🔧 设置: 跳过确认，专注测试大纲流式生成")
    print("=" * 50)
    
    total_chunks = 0
    outline_updates = 0
    
    try:
        print("🌊 开始监听流式更新...")
        
        # 使用custom模式监听流式更新（包括writer发送的信息）
        async for chunk in graph.astream(initial_state, cast(Any, config), stream_mode="custom"):
            print(f"\n📦 Custom流式更新: {chunk}")
            total_chunks += 1
            
            if total_chunks >= 20:  # 限制输出，避免过多
                break
        
        print(f"\n🔄 再试试values模式...")
        
        # 使用values模式查看状态变化
        step_count = 0
        async for chunk in graph.astream(initial_state, cast(Any, config), stream_mode="values"):
            step_count += 1
            print(f"\n📍 步骤 {step_count} 状态更新:")
            
            current_step = chunk.get("current_step", "unknown")
            print(f"   当前步骤: {current_step}")
            
            # 检查流式生成字段
            if chunk.get("latest_chunk"):
                print(f"   最新chunk: {chunk['latest_chunk'][:50]}...")
                
            if chunk.get("generation_progress"):
                print(f"   生成进度: {chunk['generation_progress']}%")
                
            if chunk.get("chunk_count"):
                print(f"   Chunk计数: {chunk['chunk_count']}")
            
            # 检查大纲状态
            outline = chunk.get("outline")
            if outline:
                outline_updates += 1
                title = outline.get("title", "")
                sections = outline.get("sections", [])
                print(f"   📋 大纲更新 #{outline_updates}: {title} ({len(sections)}个章节)")
                
                if sections:
                    print(f"   最新章节: {sections[-1].get('title', '')}")
            
            if step_count >= 10:  # 安全限制
                break
        
        print(f"\n📊 流式测试结果:")
        print(f"   总chunk数: {total_chunks}")
        print(f"   大纲更新次数: {outline_updates}")
        print(f"   状态更新步骤: {step_count}")
        
        if outline_updates > 0:
            print("✅ 大纲生成具有流式更新效果！")
        else:
            print("⚠️ 没有检测到大纲的流式更新")
            
    except Exception as e:
        print(f"❌ 流式测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_outline_streaming())