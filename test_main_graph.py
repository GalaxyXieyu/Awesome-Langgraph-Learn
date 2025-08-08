#!/usr/bin/env python3
"""
主图调用示例
演示如何正确调用重构后的主图（使用update子图）
"""

import asyncio
import time
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

# 导入主图和状态
from graph import create_deep_research_graph
from state import create_initial_state, ReportMode

async def test_main_graph():
    """测试主图调用"""
    print("🚀 开始测试主图调用")
    print("=" * 50)
    
    # 1. 创建主图
    print("📊 创建主图...")
    main_graph = create_deep_research_graph()
    print("✅ 主图创建成功")
    
    # 2. 创建初始状态
    print("\n📝 创建初始状态...")
    topic = "人工智能发展全景分析"
    
    initial_state = create_initial_state(
        topic=topic,
        user_id="test_user_001",
        mode=ReportMode.COPILOT,  # 使用自动模式，避免交互
        report_type="research",
        target_audience="技术专家",
        depth_level="deep",
        max_sections=3,  # 限制章节数量，加快测试
        target_length=2000,
        language="zh",
        style="professional"
    )
    
    print(f"✅ 初始状态创建成功")
    print(f"   - 主题: {initial_state['topic']}")
    print(f"   - 模式: {initial_state['mode']}")
    print(f"   - 目标字数: {initial_state['target_length']}")
    
    # 3. 配置执行参数
    config = {
        "configurable": {
            "thread_id": f"main_graph_test_{int(time.time())}"
        }
    }
    
    # 4. 执行主图
    print(f"\n🎯 开始执行主图工作流...")
    print(f"主题: {topic}")
    
    start_time = time.time()
    step_count = 0
    
    try:
        # 使用流式执行，实时显示进度
        async for chunk in main_graph.astream(
            initial_state, 
            config=config,
            stream_mode=["updates", "custom"]
        ):
            step_count += 1
            
            # 解析chunk内容
            if isinstance(chunk, dict):
                for node_name, node_data in chunk.items():
                    if node_name != "__start__" and node_name != "__end__":
                        print(f"\n📍 步骤 {step_count}: {node_name}")
                        
                        # 显示关键信息
                        if isinstance(node_data, dict):
                            if "topic" in node_data:
                                print(f"   🎯 主题: {node_data['topic']}")
                            if "current_step" in node_data:
                                print(f"   📋 当前步骤: {node_data['current_step']}")
                            if "sections" in node_data and node_data["sections"]:
                                sections = node_data["sections"]
                                if isinstance(sections, list) and len(sections) > 0:
                                    print(f"   📚 章节数量: {len(sections)}")
                                    # 显示章节标题
                                    for i, section in enumerate(sections[:3], 1):
                                        if isinstance(section, dict) and "title" in section:
                                            print(f"      {i}. {section['title']}")
                            if "content_creation_completed" in node_data:
                                if node_data["content_creation_completed"]:
                                    print("   ✅ 内容创建完成")
                            if "performance_metrics" in node_data:
                                metrics = node_data["performance_metrics"]
                                if isinstance(metrics, dict):
                                    if "total_words" in metrics:
                                        print(f"   📊 总字数: {metrics['total_words']}")
                                    if "sections_completed" in metrics:
                                        print(f"   📈 完成章节: {metrics['sections_completed']}")
            
            # 限制测试时间，避免长时间运行
            elapsed_time = time.time() - start_time
            if elapsed_time > 300:  # 5分钟超时
                print(f"\n⏰ 测试超时（{elapsed_time:.1f}秒），停止执行")
                break
                
            if step_count > 10:  # 限制步骤数
                print(f"\n⏹️ 达到最大步骤数限制，停止执行")
                break
    
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 显示执行结果
    execution_time = time.time() - start_time
    print(f"\n" + "=" * 50)
    print(f"🎉 主图执行完成!")
    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
    print(f"📊 执行步骤: {step_count}步")
    
    return True

def main():
    """主函数"""
    print("🧪 主图调用测试")
    
    try:
        # 运行异步测试
        result = asyncio.run(test_main_graph())
        
        if result:
            print("\n✅ 测试成功完成！")
            print("\n💡 使用说明:")
            print("1. 主图会自动生成大纲")
            print("2. 然后调用update子图进行研究和写作")
            print("3. update子图使用智能Supervisor进行任务调度")
            print("4. 最终生成完整的研究报告")
        else:
            print("\n❌ 测试失败")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
