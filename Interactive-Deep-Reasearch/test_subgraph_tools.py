#!/usr/bin/env python3
"""
测试subgraph中的工具调用是否能被正确检测和显示
"""
import asyncio
import time
from graph import create_deep_research_graph
from state import create_simple_state
from langgraph.checkpoint.memory import InMemorySaver

async def test_subgraph_tools():
    """测试subgraph工具调用检测"""
    print("🚀 开始测试subgraph工具调用检测...")
    
    # 创建简单测试状态
    initial_state = create_simple_state("AI在医疗领域的应用前景")
    
    # 创建工作流
    workflow = create_deep_research_graph()
    app = workflow.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": f"test_{int(time.time())}"}}
    
    print("状态:", initial_state)
    print("\n开始执行工作流，检查工具调用...")
    
    chunk_count = 0
    tool_call_count = 0
    
    try:
        async for chunk in app.astream(initial_state, config=config, stream_mode=["custom"]):
            chunk_count += 1
            print(f"\n--- Chunk {chunk_count} ---")
            print(f"类型: {type(chunk)}")
            print(f"内容: {chunk}")
            
            # 检查是否包含工具调用
            if isinstance(chunk, tuple) and len(chunk) == 2:
                chunk_type, chunk_data = chunk
                if isinstance(chunk_data, dict):
                    if "tool_call" in str(chunk_data).lower() or "tool_result" in str(chunk_data).lower():
                        tool_call_count += 1
                        print(f"🔧 发现工具调用! (第{tool_call_count}个)")
                    
                    # 检查message_type
                    if chunk_data.get("message_type") in ["tool_call", "tool_result"]:
                        tool_call_count += 1
                        print(f"🔧 检测到工具消息! 类型: {chunk_data.get('message_type')}")
            
            # 限制输出数量，防止过多输出
            if chunk_count >= 30:
                print("\n⏹️  已输出30个chunk，停止测试...")
                break
                
        print(f"\n📊 测试结果:")
        print(f"- 总共处理了 {chunk_count} 个chunk")
        print(f"- 检测到 {tool_call_count} 个工具调用")
        
        if tool_call_count > 0:
            print("✅ 工具调用检测成功!")
        else:
            print("❌ 未检测到工具调用，可能存在问题")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    asyncio.run(test_subgraph_tools())

if __name__ == "__main__":
    main()