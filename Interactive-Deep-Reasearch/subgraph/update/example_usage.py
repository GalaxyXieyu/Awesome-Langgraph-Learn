"""
使用示例：如何获取最终报告
"""

import asyncio
from graph import create_intelligent_research_graph, IntelligentResearchState
from report_extractor import (
    extract_final_report, 
    format_final_report_as_markdown, 
    save_final_report_to_file,
    print_report_info,
    get_report_summary
)


async def run_research_and_get_report():
    """运行研究流程并获取最终报告"""
    print("🚀 开始运行智能研究流程...")
    
    # 创建初始状态
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
        error_log=[],
        section_attempts={}
    )
    
    # 创建工作流
    workflow = create_intelligent_research_graph()
    app = workflow.compile()
    
    config = {"configurable": {"thread_id": "research_session"}}
    
    # 运行工作流
    final_state = None
    async for event in app.astream(initial_state, config=config):
        for node_name, node_state in event.items():
            print(f"📝 节点: {node_name}")
            if node_state.get("task_completed", False):
                print("✅ 任务完成！")
                final_state = node_state
                break
        
        if final_state:
            break
    
    return final_state


def demonstrate_report_extraction():
    """演示如何提取和使用最终报告"""
    print("📊 演示报告提取功能...")
    
    # 模拟一个完成的状态
    completed_state = {
        "final_report": {
            "title": "人工智能发展趋势 - 智能研究报告",
            "topic": "人工智能发展趋势",
            "sections": [
                {
                    "title": "第一章：AI技术现状",
                    "content": """# AI技术现状分析

人工智能技术在2023年取得了重大突破。根据最新数据，全球AI市场规模达到1500亿美元，预计2025年将达到3900亿美元，年复合增长率38.1%。

## 技术发展
- 大语言模型参数规模不断扩大
- GPT系列模型展现出强大的通用能力
- 多模态AI技术快速发展

## 应用领域
- 医疗诊断准确率提升30%
- 金融风控效率提升50%
- 教育个性化学习普及率达到60%

技术优化使得AI模型的性能提升了300%，同时计算成本大幅降低。""",
                    "word_count": 800,
                    "timestamp": 1703123456
                },
                {
                    "title": "第二章：未来发展趋势",
                    "content": """# 未来发展趋势预测

未来AI技术将朝着更加智能化、普及化的方向发展。

## 技术趋势
1. **通用人工智能(AGI)**: 预计2030年前实现重大突破
2. **边缘AI**: 设备端AI处理能力将提升1000倍
3. **量子AI**: 量子计算与AI结合将带来革命性变化

## 应用前景
- 自动驾驶技术将在2025年实现L4级别普及
- 智能制造将推动工业4.0全面升级
- AI助手将成为每个人的数字伙伴

## 挑战与机遇
技术发展的同时，也面临着伦理、安全、就业等挑战，需要全社会共同应对。""",
                    "word_count": 750,
                    "timestamp": 1703123500
                }
            ],
            "total_sections": 2,
            "total_words": 1550,
            "generation_method": "langgraph_intelligent_research",
            "execution_path": ["supervisor", "research", "writing", "research", "writing", "integration"],
            "generation_timestamp": 1703123600.123
        },
        "task_completed": True,
        "topic": "人工智能发展趋势"
    }
    
    print("\n=== 1. 提取最终报告 ===")
    final_report = extract_final_report(completed_state)
    if final_report:
        print("✅ 成功提取最终报告")
    else:
        print("❌ 未找到最终报告")
        return
    
    print("\n=== 2. 打印报告信息 ===")
    print_report_info(completed_state)
    
    print("\n=== 3. 获取报告摘要 ===")
    summary = get_report_summary(final_report)
    print(f"报告摘要:")
    print(f"  标题: {summary['title']}")
    print(f"  总字数: {summary['total_words']}")
    for i, section in enumerate(summary['sections'], 1):
        print(f"  章节{i}: {section['title']} ({section['word_count']}字)")
    
    print("\n=== 4. 保存为Markdown文件 ===")
    filename = save_final_report_to_file(final_report, "demo_report.md")
    print(f"✅ 报告已保存到: {filename}")
    
    print("\n=== 5. 预览Markdown内容 ===")
    markdown_content = format_final_report_as_markdown(final_report)
    print("前200字符预览:")
    print(markdown_content[:200] + "...")


if __name__ == "__main__":
    print("🧪 演示最终报告的提取和使用")
    demonstrate_report_extraction()
    
    print("\n" + "="*50)
    print("💡 实际使用方法:")
    print("1. 运行工作流直到 task_completed = True")
    print("2. 从最终状态中提取 final_report")
    print("3. 使用提供的工具函数处理报告")
    print("="*50)
