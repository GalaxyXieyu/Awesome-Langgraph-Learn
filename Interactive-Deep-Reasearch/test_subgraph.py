#!/usr/bin/env python3
"""
测试子图调用的简单脚本
"""

import asyncio
from graph import create_deep_research_graph
from state import DeepResearchState

async def test_subgraph_call():
    """测试子图调用是否正常工作"""
    
    # 创建图
    workflow = create_deep_research_graph()
    graph = workflow.compile()
    
    # 准备测试输入
    initial_state = {
        "topic": "人工智能发展趋势",
        "sections": [],
        "research_results": [],
        "approval_status": {
            "outline_confirmation": True  # 跳过大纲确认，直接测试内容创建
        },
        "content_creation_completed": False,
        "performance_metrics": {}
    }
    
    print("🚀 开始测试子图调用...")
    
    try:
        # 直接调用内容创建节点来测试子图
        from graph import call_intelligent_research_subgraph
        
        print("📝 测试子图调用函数...")
        result = await call_intelligent_research_subgraph(initial_state)
        
        print("✅ 子图调用成功!")
        print(f"📊 结果状态: {result.get('content_creation_completed', False)}")
        print(f"📚 章节数量: {len(result.get('sections', []))}")
        
        return result
        
    except Exception as e:
        print(f"❌ 子图调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_subgraph_call())
