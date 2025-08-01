"""
智能章节研究系统简单测试
"""

import asyncio
import time
from langgraph.checkpoint.memory import InMemorySaver
from graph import (
    create_intelligent_section_research_graph,
    create_intelligent_initial_state
)

async def simple_test():
    """简单测试智能章节研究功能"""
    print("🧠 智能章节研究系统测试")
    print("=" * 50)
    
    # 创建图和应用
    workflow = create_intelligent_section_research_graph()
    checkpointer = InMemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    # 测试章节
    section = {
        "id": "ai_current_status",
        "title": "人工智能发展现状",
        "key_points": ["技术突破", "市场规模", "应用领域", "发展趋势"],
        "priority": 5
    }
    
    print(f"📋 测试主题: 人工智能技术发展报告")
    print(f"📄 测试章节: {section['title']}")
    print(f"🔑 关键点: {', '.join(section['key_points'])}")
    print()
    
    # 创建智能初始状态
    initial_state = create_intelligent_initial_state(
        topic="人工智能技术发展报告",
        section=section,
        previous_sections_summary=[
            "前言部分介绍了AI的基本概念和重要性",
            "历史回顾章节梳理了AI发展的重要里程碑"
        ],
        upcoming_sections_outline=[
            "技术挑战与解决方案分析",
            "未来发展趋势预测",
            "政策建议与展望"
        ],
        report_main_thread="全面分析AI技术发展现状，为政策制定提供参考",
        writing_style="professional",
        quality_threshold=0.75,  # 中等质量要求
        max_iterations=2  # 限制迭代次数
    )
    
    # 配置
    config = {
        "configurable": {
            "thread_id": f"simple_test_{int(time.time())}"
        }
    }
    
    try:
        start_time = time.time()
        
        print("🚀 开始执行智能研究...")
        print("-" * 50)
        
        # 流式执行
        step_count = 0
        async for event in app.astream(initial_state, config=config, stream_mode="custom"):
            if isinstance(event, dict):
                step = event.get("step", "")
                status = event.get("status", "")
                progress = event.get("progress", 0)
                
                if step and status:
                    step_count += 1
                    print(f"[{step_count:2d}] {step}: {status} ({progress}%)")
                    
                    # 显示关键信息
                    content = event.get("content")
                    if content and content.get("type") == "quality_assessment":
                        data = content.get("data", {})
                        quality = data.get("overall_quality", 0)
                        gaps = len(data.get("content_gaps", []))
                        print(f"     📊 质量评分: {quality:.3f}, 内容缺口: {gaps}个")
                    
                    elif content and content.get("type") == "final_result":
                        data = content.get("data", {})
                        quality_metrics = data.get("quality_metrics", {})
                        final_quality = quality_metrics.get("final_quality_score", 0)
                        iterations = quality_metrics.get("iteration_count", 0)
                        print(f"     🎉 最终质量: {final_quality:.3f}, 迭代次数: {iterations}")
        
        # 获取最终结果
        final_state = await app.aget_state(config)
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 50)
        print("🎉 测试完成！")
        print("=" * 50)
        
        if final_state and final_state.values:
            state_data = final_state.values
            final_result = state_data.get("final_result", {})
            execution_summary = state_data.get("execution_summary", {})
            
            # 基本统计
            print(f"⏱️  执行时间: {execution_time:.1f}秒")
            print(f"🔄 迭代次数: {execution_summary.get('iterations_performed', 0)}")
            print(f"📊 最终质量: {execution_summary.get('final_quality_score', 0):.3f}")
            
            # 内容统计
            quality_metrics = final_result.get("quality_metrics", {})
            content_evolution = quality_metrics.get("content_evolution", {})
            print(f"📝 内容长度: {content_evolution.get('final_length', 0)}字符")
            
            # 智能特性验证
            intelligence_features = execution_summary.get("intelligence_features", {})
            print(f"\n🧠 智能特性:")
            print(f"   ✅ 上下文感知: {intelligence_features.get('context_aware', False)}")
            print(f"   ✅ 质量驱动: {intelligence_features.get('quality_driven', False)}")
            print(f"   ✅ 迭代改进: {intelligence_features.get('iterative_improvement', False)}")
            print(f"   ✅ 自适应研究: {intelligence_features.get('adaptive_research', False)}")
            
            # 内容预览
            final_content = final_result.get("final_content", "")
            if final_content:
                print(f"\n📝 内容预览 (前200字符):")
                print("-" * 50)
                print(final_content[:200] + "..." if len(final_content) > 200 else final_content)
                print("-" * 50)
            
            # 错误日志
            error_log = state_data.get("error_log", [])
            if error_log:
                print(f"\n⚠️  错误日志: {len(error_log)}个错误")
                for error in error_log[:3]:  # 只显示前3个错误
                    print(f"   - {error}")
            else:
                print(f"\n✅ 无错误发生")
                
            return True
        else:
            print("❌ 无法获取最终结果")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False

async def quick_test():
    """快速测试基本功能"""
    print("⚡ 快速功能测试")
    print("=" * 30)
    
    try:
        # 测试工具导入
        from tools import advanced_web_search, calculate_content_quality
        print("✅ 工具模块导入成功")
        
        # 测试图创建
        from graph import create_intelligent_section_research_graph
        workflow = create_intelligent_section_research_graph()
        print("✅ 智能图创建成功")
        
        # 测试状态创建
        from graph import create_intelligent_initial_state
        test_section = {
            "id": "test",
            "title": "测试章节",
            "key_points": ["测试点1", "测试点2"],
            "priority": 3
        }
        
        initial_state = create_intelligent_initial_state(
            topic="测试主题",
            section=test_section
        )
        print("✅ 初始状态创建成功")
        
        print("\n🎉 所有基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 快速测试失败: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("🧪 智能章节研究系统测试套件")
    print("=" * 60)
    
    # 快速测试
    quick_success = await quick_test()
    
    if quick_success:
        print("\n" + "=" * 60)
        # 完整测试
        full_success = await simple_test()
        
        if full_success:
            print(f"\n🎉 所有测试通过！系统运行正常。")
        else:
            print(f"\n⚠️  完整测试失败，但基本功能正常。")
    else:
        print(f"\n❌ 基本功能测试失败，请检查环境配置。")

if __name__ == "__main__":
    asyncio.run(main())
