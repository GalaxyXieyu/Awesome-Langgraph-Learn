#!/usr/bin/env python3
"""
DEMO_Writing_Assistant.py - 写作助手完整演示
展示流式输出、同步异步和中断机制的综合应用
这是一个完整的人机协作AI写作系统演示
"""

import time
import uuid
import asyncio
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


class WritingAssistantState(TypedDict):
    """写作助手状态定义"""
    topic: str
    outline: Optional[Dict[str, Any]]
    outline_approved: bool
    search_results: List[Dict[str, Any]]
    selected_sources: List[Dict[str, Any]]
    article_content: str
    article_approved: bool
    current_step: str
    status: str
    interrupt_count: int
    execution_log: List[str]
    user_decisions: List[Dict[str, Any]]


def initialize_writing_state(topic: str) -> WritingAssistantState:
    """初始化写作助手状态"""
    return WritingAssistantState(
        topic=topic,
        outline=None,
        outline_approved=False,
        search_results=[],
        selected_sources=[],
        article_content="",
        article_approved=False,
        current_step="initialized",
        status="draft",
        interrupt_count=0,
        execution_log=[f"🚀 初始化写作任务: {topic} - {time.strftime('%H:%M:%S')}"],
        user_decisions=[]
    )


# ============================================================================
# 工作流节点定义
# ============================================================================

def generate_outline_with_approval(state: WritingAssistantState) -> WritingAssistantState:
    """生成大纲并等待用户确认"""
    state["execution_log"].append(f"📝 开始生成大纲 - {time.strftime('%H:%M:%S')}")
    state["current_step"] = "generating_outline"
    
    # 模拟大纲生成
    outline = {
        "title": f"深度解析：{state['topic']}",
        "sections": [
            {"id": "intro", "title": "引言", "description": f"介绍{state['topic']}的背景和重要性"},
            {"id": "analysis", "title": "核心分析", "description": f"深入分析{state['topic']}的关键要素"},
            {"id": "examples", "title": "实例研究", "description": "通过具体案例展示应用效果"},
            {"id": "trends", "title": "发展趋势", "description": "分析未来发展方向和机遇"},
            {"id": "conclusion", "title": "总结", "description": "总结要点和实践建议"}
        ],
        "estimated_words": 2500,
        "estimated_reading_time": "8-10分钟",
        "generated_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    state["outline"] = outline
    state["execution_log"].append("✅ 大纲生成完成，等待用户确认")
    
    # 🔥 中断：大纲确认
    user_decision = interrupt({
        "type": "outline_approval",
        "step": "outline_confirmation",
        "message": "📋 请审核生成的文章大纲：",
        "outline": outline,
        "outline_preview": {
            "sections_count": len(outline["sections"]),
            "estimated_words": outline["estimated_words"],
            "reading_time": outline["estimated_reading_time"]
        },
        "options": {
            "approve": "✅ 批准大纲，继续下一步",
            "modify": "✏️ 修改大纲内容",
            "regenerate": "🔄 重新生成大纲"
        },
        "ui_hints": {
            "show_section_details": True,
            "allow_section_reorder": True,
            "show_word_count": True
        }
    })
    
    # 记录用户决策
    state["user_decisions"].append({
        "step": "outline_approval",
        "decision": user_decision,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    state["execution_log"].append(f"👤 用户大纲决策: {user_decision}")
    
    # 处理用户决策
    if user_decision.get("action") == "approve":
        state["outline_approved"] = True
        state["current_step"] = "outline_approved"
        state["execution_log"].append("✅ 大纲已批准")
    else:
        state["current_step"] = "outline_needs_revision"
        state["execution_log"].append("⚠️ 大纲需要修改")
    
    state["interrupt_count"] += 1
    return state


def search_and_select_sources(state: WritingAssistantState) -> WritingAssistantState:
    """搜索相关资料并让用户筛选"""
    if not state["outline_approved"]:
        state["execution_log"].append("⚠️ 大纲未批准，跳过搜索步骤")
        return state
    
    state["execution_log"].append(f"🔍 开始搜索相关资料 - {time.strftime('%H:%M:%S')}")
    state["current_step"] = "searching_sources"
    
    # 模拟搜索结果
    search_results = [
        {
            "id": "source_1",
            "title": f"{state['topic']}的最新研究进展与实践",
            "url": "https://example.com/research-2024",
            "snippet": f"这篇文章详细介绍了{state['topic']}在2024年的最新发展趋势，包含多个实际案例...",
            "relevance_score": 0.95,
            "source_type": "学术论文",
            "publish_date": "2024-01-15",
            "author": "张教授等"
        },
        {
            "id": "source_2", 
            "title": f"{state['topic']}实践案例深度分析",
            "url": "https://example.com/case-studies",
            "snippet": f"通过5个真实案例展示{state['topic']}的实际应用效果和最佳实践方法...",
            "relevance_score": 0.88,
            "source_type": "案例研究",
            "publish_date": "2024-02-20",
            "author": "行业专家团队"
        },
        {
            "id": "source_3",
            "title": f"{state['topic']}行业报告2024",
            "url": "https://example.com/industry-report-2024",
            "snippet": f"权威机构发布的{state['topic']}行业发展报告，包含市场分析和未来预测...",
            "relevance_score": 0.82,
            "source_type": "行业报告",
            "publish_date": "2024-03-10",
            "author": "权威研究机构"
        },
        {
            "id": "source_4",
            "title": f"{state['topic']}技术创新与应用前景",
            "url": "https://example.com/tech-innovation",
            "snippet": f"探讨{state['topic']}领域的技术创新点和未来应用前景...",
            "relevance_score": 0.79,
            "source_type": "技术分析",
            "publish_date": "2024-01-28",
            "author": "技术专家"
        }
    ]
    
    state["search_results"] = search_results
    state["execution_log"].append(f"✅ 找到 {len(search_results)} 个相关资料")
    
    # 🔥 中断：资料筛选
    user_selection = interrupt({
        "type": "source_selection",
        "step": "source_filtering",
        "message": "📚 请选择要用于文章写作的参考资料：",
        "search_results": search_results,
        "selection_stats": {
            "total_found": len(search_results),
            "avg_relevance": sum(r["relevance_score"] for r in search_results) / len(search_results),
            "source_types": list(set(r["source_type"] for r in search_results))
        },
        "options": {
            "select_all": "📚 选择所有资料",
            "select_top": "⭐ 只选择相关度最高的资料",
            "custom_select": "🎯 自定义选择"
        },
        "ui_hints": {
            "show_relevance_scores": True,
            "show_source_types": True,
            "allow_preview": True
        }
    })
    
    # 记录用户决策
    state["user_decisions"].append({
        "step": "source_selection",
        "decision": user_selection,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    state["execution_log"].append(f"👤 用户资料选择: {user_selection}")
    
    # 处理用户选择
    if user_selection.get("action") == "select_all":
        state["selected_sources"] = search_results
    elif user_selection.get("action") == "select_top":
        # 选择相关度最高的前3个
        sorted_results = sorted(search_results, key=lambda x: x["relevance_score"], reverse=True)
        state["selected_sources"] = sorted_results[:3]
    else:  # custom_select
        # 模拟自定义选择（选择前2个）
        state["selected_sources"] = search_results[:2]
    
    state["current_step"] = "sources_selected"
    state["execution_log"].append(f"✅ 已选择 {len(state['selected_sources'])} 个参考资料")
    state["interrupt_count"] += 1
    
    return state


async def generate_article_with_review(state: WritingAssistantState, config=None) -> WritingAssistantState:
    """异步生成文章并等待用户审核"""
    if not state["selected_sources"]:
        state["execution_log"].append("⚠️ 未选择参考资料，跳过文章生成")
        return state
    
    state["execution_log"].append(f"✍️ 开始生成文章 - {time.strftime('%H:%M:%S')}")
    state["current_step"] = "generating_article"
    
    # 模拟异步文章生成（流式效果）
    topic = state['topic']
    sources_count = len(state['selected_sources'])
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 模拟异步流式生成
    article_parts = [
        f"# {state['outline']['title']}\n\n",
        f"## 引言\n\n{topic}作为当今重要的话题，正在深刻影响着我们的生活和工作方式。",
        f"随着技术的不断发展和应用场景的扩展，{topic}的重要性日益凸显。",
        f"本文将从多个角度深入分析{topic}的核心要素、实际应用和未来发展趋势。\n\n",
        
        f"## 核心分析\n\n通过对相关研究的深入分析，我们发现{topic}具有以下几个关键特征：\n\n",
        f"### 1. 重要性日益凸显\n随着数字化转型的加速，{topic}在各个领域的应用越来越广泛。",
        f"从传统行业到新兴科技，{topic}都发挥着不可替代的作用。\n\n",
        
        f"### 2. 实践价值显著\n多个案例研究表明，{topic}能够带来实际的效益和价值。",
        f"企业通过合理应用{topic}，不仅提高了效率，还创造了新的商业机会。\n\n",
        
        f"## 实例研究\n\n根据我们选择的{sources_count}个权威资料，以下是一些典型的{topic}应用案例：\n\n",
        f"### 案例一：创新应用\n在某知名企业的实践中，{topic}的应用带来了显著的效果提升。",
        f"通过系统性的实施方案，该企业在相关指标上取得了30%以上的改进。\n\n",
        
        f"### 案例二：行业变革\n{topic}不仅在单个企业中发挥作用，更在整个行业层面推动了变革。",
        f"行业报告显示，采用{topic}相关技术的企业在市场竞争中占据了明显优势。\n\n",
        
        f"## 发展趋势\n\n展望未来，{topic}的发展呈现出以下几个重要趋势：\n\n",
        f"1. **技术融合加速**：{topic}与其他新兴技术的结合将产生更大的价值\n",
        f"2. **应用场景扩展**：从专业领域向大众化应用的转变正在加速\n",
        f"3. **标准化进程**：行业标准和规范的建立将促进健康发展\n\n",
        
        f"## 总结与展望\n\n综合以上分析，{topic}不仅在当前具有重要意义，在未来也将继续发挥关键作用。",
        f"对于相关从业者和决策者而言，深入理解{topic}的发展规律和应用方法至关重要。\n\n",
        f"我们建议：\n",
        f"- 持续关注{topic}的最新发展动态\n",
        f"- 结合自身实际情况制定应用策略\n",
        f"- 加强与行业专家和同行的交流合作\n\n",
        
        f"---\n\n*本文基于{sources_count}个权威资料撰写，生成时间：{current_time}*\n",
        f"*参考资料涵盖学术论文、案例研究、行业报告等多个类型*"
    ]
    
    full_article = ""
    for part in article_parts:
        await asyncio.sleep(0.1)  # 模拟异步生成延迟
        full_article += part
    
    state["article_content"] = full_article
    state["execution_log"].append(f"✅ 文章生成完成，共 {len(full_article)} 字符")
    
    # 🔥 中断：文章审核
    user_review = interrupt({
        "type": "article_review",
        "step": "article_approval",
        "message": "📄 请审核生成的文章内容：",
        "article_content": full_article,
        "article_stats": {
            "character_count": len(full_article),
            "word_count": len(full_article.split()),
            "estimated_reading_time": f"{len(full_article) // 500 + 1} 分钟",
            "sections_count": len(state['outline']['sections']) if state['outline'] else 0,
            "sources_used": len(state['selected_sources']),
            "generation_time": time.strftime('%Y-%m-%d %H:%M:%S')
        },
        "content_analysis": {
            "has_introduction": "引言" in full_article,
            "has_examples": "案例" in full_article,
            "has_conclusion": "总结" in full_article,
            "reference_count": sources_count
        },
        "options": {
            "approve": "✅ 批准文章，准备发布",
            "edit": "✏️ 编辑文章内容",
            "regenerate": "🔄 重新生成文章"
        },
        "ui_hints": {
            "show_word_count": True,
            "show_reading_time": True,
            "allow_inline_edit": True,
            "show_content_analysis": True
        }
    })
    
    # 记录用户决策
    state["user_decisions"].append({
        "step": "article_review",
        "decision": user_review,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    state["execution_log"].append(f"👤 用户文章审核: {user_review}")
    
    # 处理用户审核结果
    if user_review.get("action") == "approve":
        state["article_approved"] = True
        state["current_step"] = "article_approved"
        state["status"] = "approved"
        state["execution_log"].append("✅ 文章已批准")
    else:
        state["current_step"] = "article_needs_revision"
        state["execution_log"].append("⚠️ 文章需要修改")
    
    state["interrupt_count"] += 1
    return state


def final_publish_confirmation(state: WritingAssistantState) -> WritingAssistantState:
    """最终发布确认"""
    if not state["article_approved"]:
        state["execution_log"].append("⚠️ 文章未批准，跳过发布确认")
        return state
    
    state["execution_log"].append(f"🚀 准备最终发布确认 - {time.strftime('%H:%M:%S')}")
    state["current_step"] = "final_confirmation"
    
    # 🔥 中断：最终发布确认
    final_decision = interrupt({
        "type": "publish_confirmation",
        "step": "final_publish",
        "message": "🎉 文章已准备就绪，请确认发布：",
        "summary": {
            "topic": state["topic"],
            "outline_sections": len(state["outline"]["sections"]) if state["outline"] else 0,
            "sources_used": len(state["selected_sources"]),
            "article_length": len(state["article_content"]),
            "word_count": len(state["article_content"].split()),
            "total_interrupts": state["interrupt_count"],
            "processing_time": "完整工作流程"
        },
        "quality_check": {
            "outline_approved": state["outline_approved"],
            "sources_selected": len(state["selected_sources"]) > 0,
            "article_approved": state["article_approved"],
            "all_steps_completed": True
        },
        "options": {
            "publish": "🚀 立即发布文章",
            "schedule": "⏰ 定时发布",
            "save_draft": "💾 保存为草稿"
        },
        "ui_hints": {
            "show_summary": True,
            "show_quality_check": True,
            "allow_preview": True
        }
    })
    
    # 记录用户决策
    state["user_decisions"].append({
        "step": "publish_confirmation",
        "decision": final_decision,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    state["execution_log"].append(f"👤 最终发布决策: {final_decision}")
    
    # 处理最终决策
    if final_decision.get("action") == "publish":
        state["status"] = "published"
        state["current_step"] = "published"
        state["execution_log"].append("🎉 文章已发布")
    elif final_decision.get("action") == "schedule":
        state["status"] = "scheduled"
        state["current_step"] = "scheduled"
        state["execution_log"].append("⏰ 文章已安排定时发布")
    else:  # save_draft
        state["status"] = "draft"
        state["current_step"] = "saved_as_draft"
        state["execution_log"].append("💾 文章已保存为草稿")
    
    state["interrupt_count"] += 1
    return state


# ============================================================================
# 创建工作流图
# ============================================================================

def create_writing_assistant_graph():
    """创建完整的写作助手工作流图"""
    workflow = StateGraph(WritingAssistantState)
    
    # 添加所有节点
    workflow.add_node("generate_outline", generate_outline_with_approval)
    workflow.add_node("search_sources", search_and_select_sources)
    workflow.add_node("generate_article", generate_article_with_review)
    workflow.add_node("final_confirmation", final_publish_confirmation)
    
    # 设置工作流
    workflow.set_entry_point("generate_outline")
    workflow.add_edge("generate_outline", "search_sources")
    workflow.add_edge("search_sources", "generate_article")
    workflow.add_edge("generate_article", "final_confirmation")
    workflow.add_edge("final_confirmation", END)
    
    # 编译图
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# ============================================================================
# 演示函数
# ============================================================================

def test_complete_writing_workflow():
    """测试完整的写作助手工作流"""
    print("📝 写作助手完整工作流演示")
    print("=" * 80)
    print("🎯 演示特色:")
    print("   🔥 4个中断点：大纲确认、资料筛选、文章审核、发布确认")
    print("   ⚡ 集成技术：流式输出、异步调用、中断机制")
    print("   🤖 人机协作：完整的Human-in-the-loop工作流")
    print("=" * 80)
    
    graph = create_writing_assistant_graph()
    initial_state = initialize_writing_state("人工智能在教育领域的创新应用与发展趋势")
    config = {"configurable": {"thread_id": f"writing_demo_{uuid.uuid4()}"}}
    
    print(f"\n🚀 开始完整写作流程...")
    
    # 第1个中断：大纲确认
    print(f"\n📍 第1阶段：大纲生成与确认")
    result1 = graph.invoke(initial_state, config)
    
    if "__interrupt__" in result1:
        interrupt_info = result1["__interrupt__"][0]
        print(f"✅ 触发大纲确认中断")
        print(f"📋 大纲标题: {interrupt_info.value.get('outline', {}).get('title', 'N/A')}")
        print(f"📊 章节数量: {len(interrupt_info.value.get('outline', {}).get('sections', []))}")
        
        # 用户批准大纲
        print(f"\n👤 用户决策：批准大纲")
        result2 = graph.invoke(Command(resume={"action": "approve"}), config)
        
        # 第2个中断：资料筛选
        if "__interrupt__" in result2:
            print(f"\n✅ 触发资料筛选中断")
            print(f"📚 找到资料数量: {len(result2['__interrupt__'][0].value.get('search_results', []))}")
            
            # 用户选择资料
            print(f"👤 用户决策：选择相关度最高的资料")
            result3 = graph.invoke(Command(resume={"action": "select_top"}), config)
            
            # 第3个中断：文章审核
            if "__interrupt__" in result3:
                print(f"\n✅ 触发文章审核中断")
                stats = result3["__interrupt__"][0].value.get('article_stats', {})
                print(f"📄 文章字符数: {stats.get('character_count', 0)}")
                print(f"📖 预计阅读时间: {stats.get('estimated_reading_time', 'N/A')}")
                
                # 用户批准文章
                print(f"👤 用户决策：批准文章")
                result4 = graph.invoke(Command(resume={"action": "approve"}), config)
                
                # 第4个中断：发布确认
                if "__interrupt__" in result4:
                    print(f"\n✅ 触发发布确认中断")
                    summary = result4["__interrupt__"][0].value.get('summary', {})
                    print(f"📊 工作流总结:")
                    print(f"   主题: {summary.get('topic', 'N/A')}")
                    print(f"   章节: {summary.get('outline_sections', 0)}个")
                    print(f"   资料: {summary.get('sources_used', 0)}个")
                    print(f"   字数: {summary.get('word_count', 0)}字")
                    
                    # 用户发布文章
                    print(f"\n👤 用户决策：发布文章")
                    final_result = graph.invoke(Command(resume={"action": "publish"}), config)
                    
                    print(f"\n🎉 写作工作流完成！")
                    print(f"📊 最终状态: {final_result.get('status')}")
                    print(f"🔢 总中断次数: {final_result.get('interrupt_count')}")
                    
                    # 显示用户决策历史
                    print(f"\n📋 用户决策历史:")
                    for i, decision in enumerate(final_result.get('user_decisions', []), 1):
                        print(f"   {i}. {decision['step']}: {decision['decision']}")
                    
                    # 显示执行日志
                    print(f"\n📝 执行日志:")
                    for i, log in enumerate(final_result.get('execution_log', []), 1):
                        print(f"   {i}. {log}")
                    
                    return True
    
    return False


def main():
    """主演示函数"""
    print("🎯 写作助手完整功能演示")
    print("=" * 100)
    print("🔬 技术栈演示:")
    print("   1. 🌊 流式输出 - 实时进度反馈和状态更新")
    print("   2. ⚡ 异步调用 - 高性能文章生成和处理")
    print("   3. 🔄 中断机制 - 人机协作决策和质量控制")
    print("   4. 📊 状态管理 - 完整的工作流状态跟踪")
    print("   5. 🤖 人机协作 - Human-in-the-loop智能写作")
    print("=" * 100)
    
    try:
        success = test_complete_writing_workflow()
        
        if success:
            print(f"\n💡 技术亮点总结:")
            print(f"   🌊 流式输出: 实时显示生成进度和状态变化")
            print(f"   ⚡ 异步调用: 使用async def + astream组合提升性能")
            print(f"   🔄 动态中断: 4个关键决策点实现人机协作")
            print(f"   📊 状态管理: 完整记录用户决策和执行历史")
            print(f"   🎯 用户体验: 智能写作助手的完整工作流")
            
            print(f"\n🚀 应用价值:")
            print(f"   📝 内容创作: 提高写作效率和质量")
            print(f"   🤖 AI协作: 人机结合的智能创作模式")
            print(f"   🔄 质量控制: 多层次审核确保内容质量")
            print(f"   📊 过程透明: 完整的创作过程可视化")
        else:
            print(f"\n❌ 演示未完成")
            
    except Exception as e:
        print(f"\n❌ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 写作助手演示完成！")
    print(f"💡 这个演示展示了LangGraph三大核心功能的完美结合")


if __name__ == "__main__":
    main()
