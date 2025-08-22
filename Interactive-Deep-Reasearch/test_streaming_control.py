#!/usr/bin/env python3
"""
测试节点级别流式控制功能
"""

from graph import create_deep_research_graph
from state import create_simple_state
import asyncio
from writer.config import get_writer_config

async def test_streaming_control():
    """测试流式控制功能"""
    print("🧪 测试节点级别流式控制...")
    
    # 检查配置
    config = get_writer_config()
    print(f"大纲生成节点流式配置: {config.is_node_streaming_enabled('outline_generation')}")
    print(f"内容创建节点流式配置: {config.is_node_streaming_enabled('content_creation')}")
    
    # 创建测试状态
    initial_state = create_simple_state("人工智能发展趋势")
    
    # 创建并编译图
    workflow = create_deep_research_graph()
    app = workflow.compile()
    
    print("\n🚀 开始测试...")
    print("=" * 50)
    
    chunk_count = 0
    step_progress_count = 0
    
    # 流式执行
    async for chunk in app.astream(initial_state, stream_mode=["custom"]):
        chunk_count += 1
        print(f"Chunk #{chunk_count}: {chunk}")
        
        # 统计 step_progress 消息数量
        if isinstance(chunk, tuple) and len(chunk) == 2:
            if chunk[0] == 'custom':
                data = chunk[1]
                if data.get('message_type') == 'step_progress':
                    step_progress_count += 1
    
    print("=" * 50)
    print(f"✅ 测试完成!")
    print(f"总chunk数: {chunk_count}")
    print(f"step_progress消息数: {step_progress_count}")
    
    # 预期：如果 outline_generation: false，应该没有或很少 step_progress 消息
    if step_progress_count == 0:
        print("🎉 节点级别流式控制成功！没有流式进度消息。")
    else:
        print(f"⚠️ 仍有 {step_progress_count} 个流式进度消息，可能需要进一步调试。")

if __name__ == "__main__":
    asyncio.run(test_streaming_control())