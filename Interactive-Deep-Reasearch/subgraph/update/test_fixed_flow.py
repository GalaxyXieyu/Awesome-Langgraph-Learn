"""
测试修复后的流程
"""

import asyncio
from graph import create_intelligent_research_graph, IntelligentResearchState


async def test_section_progression():
    """测试章节进度是否正确"""
    print("🧪 测试修复后的章节切换逻辑...")
    
    # 创建测试状态
    initial_state = IntelligentResearchState(
        messages=[],
        user_input="人工智能发展趋势",
        topic="人工智能发展趋势",
        sections=[
            {
                "id": "section_1",
                "title": "AI技术现状",
                "description": "分析当前人工智能技术的发展现状"
            },
            {
                "id": "section_2", 
                "title": "未来发展趋势",
                "description": "预测人工智能未来的发展方向"
            }
        ],
        current_section_index=0,
        research_results={},
        writing_results={},
        polishing_results={},
        final_report={},
        execution_path=[],
        iteration_count=0,
        max_iterations=8,
        next_action="research",
        task_completed=False,
        error_log=[]
    )
    
    # 创建工作流图
    try:
        workflow = create_intelligent_research_graph()
        app = workflow.compile()
        print("✅ 工作流图创建成功")
        
        # 测试执行
        print("🚀 开始执行工作流...")
        
        config = {"configurable": {"thread_id": "test_thread"}}
        
        step_count = 0
        max_steps = 10  # 限制最大步数防止无限循环
        
        async for event in app.astream(initial_state, config=config):
            step_count += 1
            print(f"\n📝 步骤 {step_count}: {list(event.keys())}")
            
            for node_name, node_state in event.items():
                current_index = node_state.get("current_section_index", 0)
                next_action = node_state.get("next_action", "unknown")
                research_count = len(node_state.get("research_results", {}))
                writing_count = len(node_state.get("writing_results", {}))
                
                print(f"  节点: {node_name}")
                print(f"  当前章节索引: {current_index}")
                print(f"  下一步行动: {next_action}")
                print(f"  已完成研究: {research_count}章节")
                print(f"  已完成写作: {writing_count}章节")
                
                if node_state.get("task_completed", False):
                    print("✅ 任务完成！")
                    return
            
            if step_count >= max_steps:
                print("⚠️ 达到最大步数限制，停止测试")
                break
                
        print("✅ 流程测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_section_progression())
