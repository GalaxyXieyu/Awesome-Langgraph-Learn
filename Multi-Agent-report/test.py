"""
测试流式多智能体系统
"""

import asyncio
import time
from graph import create_multi_agent_graph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage

async def test_streaming_multiagent():
    """测试流式多智能体系统"""
    print("🚀 测试流式多智能体系统")
    print("=" * 60)
    
    # 创建图
    checkpointer = InMemorySaver()
    app = create_multi_agent_graph(checkpointer)
    
    # 测试用例
    test_cases = [
        "计算 25 * 4 的结果",
        "搜索Python的优势",
        "分析这句话的情感：今天天气很好，我很开心！"
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n🧪 测试案例 {i}: {user_input}")
        print("-" * 50)
        
        # 初始化状态
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "current_agent": "",
            "execution_path": [],
            "agent_results": {},
            "final_result": "",
            "quality_score": 0.0,
            "iteration_count": 0,
            "max_iterations": 3,
            "context": {},
            "error_log": [],
            "supervisor_reasoning": "",
            "next_action": "",
            "task_completed": False
        }
        
        config = {"configurable": {"thread_id": f"test_{i}_{int(time.time())}"}} 
        start_time = time.time()
        step_count = 0

        try:
            # 流式执行 - 使用messages模式获得token级流式输出
            async for chunk in app.astream(initial_state, config=config, stream_mode=["updates", "messages", "custom"]):
                step_count += 1
                current_time = time.time() - start_time
                # 处理不同的流式模式
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    # 多模式流式输出：(mode, data)
                    mode, data = chunk

                    if mode == "updates":
                        # 只显示重要的节点更新
                        for node_name, node_data in data.items():
                            if isinstance(node_data, dict):
                                current_agent = node_data.get('current_agent', '')
                                next_action = node_data.get('next_action', '')
                                final_result = node_data.get('final_result', '')

                                if current_agent:
                                    print(f"  🤖 当前Agent: {current_agent}")
                                if next_action:
                                    print(f"  ➡️ 下一步: {next_action}")
                                if final_result:
                                    print(f"  🎯 最终结果: {final_result[:100]}{'...' if len(final_result) > 100 else ''}")

                    elif mode == "messages":
                        # 处理LLM token流式输出 - 打字机效果
                        token, metadata = data
                        if hasattr(token, 'content') and token.content:
                            # 显示所有 Agent 相关节点的打字机效果
                            node_name = metadata.get('langgraph_node', '') if metadata else ''
                            if node_name in ['agent_execution', 'result_integration', 'supervisor']:
                                # 直接输出token内容，不换行，实现打字机效果
                                print(token.content, end='', flush=True)

                    elif mode == "custom":
                        # 处理自定义流式输出（进度更新等）
                        if isinstance(data, dict) and data.get("step"):
                            status = data.get("status", "")
                            progress = data.get("progress", 0)
                            if status:
                                print(f"  📊 {status} (进度: {progress}%)")

                # 只在非 messages 模式时换行
                if not (isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "messages"):
                    print()

                # 如果超过20步，停止（防止无限循环）
                if step_count > 2000:
                    print("⚠️ 达到最大步数限制，停止执行")
                    break

            total_time = time.time() - start_time
            print(f"✅ 测试完成，总耗时: {total_time:.2f}秒，共{step_count}步")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
        
        if i < len(test_cases):
            print("\n" + "=" * 60)
            await asyncio.sleep(1)  # 短暂暂停
    
    print("\n🎉 所有测试完成！")

if __name__ == "__main__":
    asyncio.run(test_streaming_multiagent())
