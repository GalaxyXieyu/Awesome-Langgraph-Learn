"""
测试脚本
运行带有human-in-loop功能的深度研究图
"""

import asyncio
import time
from langgraph.checkpoint.memory import InMemorySaver

from graph import create_deep_research_graph_with_tools
from state import create_simple_state


async def main():
    """主函数，用于运行研究图"""
    
    # 创建一个内存检查点，用于保存状态
    checkpointer = InMemorySaver()
    
    # 创建初始状态
    initial_state = create_simple_state("人工智能发展全景分析")
    
    # 创建工作流
    workflow = await create_deep_research_graph_with_tools()
    
    # 编译应用
    app = workflow.compile(checkpointer=checkpointer)
    
    # 创建唯一的线程ID
    config = {"configurable": {"thread_id": f"research_{int(time.time())}"}}
    
    print(f"开始研究任务，主题：'{initial_state['topic']}'")
    print(f"线程ID: {config['configurable']['thread_id']}")
    
    try:
        # 使用 astream 异步运行图
        async for chunk in app.astream(initial_state, config=config, stream_mode="values"):
            # 打印每个节点的输出
            for key, value in chunk.items():
                print(f"\n--- 输出自节点: {key} ---")
                print(value)
                print("---------------------")
                
    except Exception as e:
        print(f"\n出现错误: {e}")


if __name__ == "__main__":
    # 运行主异步函数
    asyncio.run(main())

