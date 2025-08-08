"""
简化的测试 - 只显示原始的custom数据
"""

import asyncio
import time
from graph import create_multi_agent_graph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
import json


async def test_raw_custom_stream():
    """测试原始custom stream数据"""
    print("🧪 测试原始Custom Stream数据")
    print("="*60)
    
    # 创建图
    checkpointer = InMemorySaver()
    app = create_multi_agent_graph(checkpointer)
    
    # 简单测试用例
    user_input = "计算 25 * 4 的结果"
    
    print(f"📝 用户输入: {user_input}")
    print("-" * 50)
    print("📡 原始Custom Stream数据:")
    print("-" * 50)
    
    # 初始化状态
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_input": user_input,
        "current_agent": "",
        "execution_path": [],
        "agent_results": {},
        "final_result": "",
        "iteration_count": 0,
        "max_iterations": 2,
        "context": {},
        "error_log": [],
        "supervisor_reasoning": "",
        "next_action": "",
        "task_completed": False
    }
    
    config = {"configurable": {"thread_id": f"test_{int(time.time())}"}}
    
    try:
        # 只使用custom模式，打印原始数据
        async for chunk in app.astream(initial_state, config=config, stream_mode=["custom"]):
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk
                
                if mode == "custom":
                    # 直接打印原始JSON数据
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    print("---")  # 分隔符
        
        print("✅ 测试完成")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_raw_custom_stream())