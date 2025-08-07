"""
上下文构建模块
负责为智能Supervisor构建分析上下文
"""

from typing import Dict, Any, List


def build_status_summary(state: Dict[str, Any]) -> str:
    """构建项目状态摘要"""
    sections = state.get("sections", [])
    current_index = state.get("current_section_index", 0)
    research_results = state.get("research_results", {})
    writing_results = state.get("writing_results", {})
    topic = state.get("topic", "")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)
    
    # 计算完成进度
    completed_sections = 0
    for i, section in enumerate(sections):
        section_id = section.get("id", "")
        has_research = section_id in research_results and len(research_results[section_id].get("content", "")) >= 500
        has_writing = section_id in writing_results and writing_results[section_id].get("word_count", 0) >= 300
        if has_research and has_writing:
            completed_sections += 1

    return f"""
研究主题: {topic}
总章节数: {len(sections)}
当前处理章节: 第{current_index + 1}章 (索引: {current_index})
完全完成的章节: {completed_sections}/{len(sections)}
已有研究结果的章节: {len(research_results)}
已有写作结果的章节: {len(writing_results)}
当前迭代次数: {iteration_count}/{max_iterations}

项目进度: {completed_sections}/{len(sections)} 章节完成
"""


def build_current_section_info(state: Dict[str, Any]) -> str:
    """构建当前章节信息"""
    sections = state.get("sections", [])
    current_index = state.get("current_section_index", 0)
    research_results = state.get("research_results", {})
    writing_results = state.get("writing_results", {})
    
    if current_index >= len(sections):
        return "所有章节已处理完成"
    
    current_section = sections[current_index]
    section_id = current_section.get("id", "")
    section_title = current_section.get("title", "")
    section_desc = current_section.get("description", "")
    
    # 获取章节尝试次数记录
    section_attempts = state.get("section_attempts", {})
    current_attempts = section_attempts.get(section_id, {"research": 0, "writing": 0})
    research_attempts = current_attempts.get("research", 0)
    writing_attempts = current_attempts.get("writing", 0)

    # 设置最大尝试次数
    MAX_ATTEMPTS = 3

    # 详细分析当前章节状态
    research_analysis = "❌ 未开始研究"
    writing_analysis = "❌ 未开始写作"
    next_step_suggestion = ""

    # 分析研究状态
    if section_id in research_results:
        research_data = research_results[section_id]
        research_content = research_data.get("content", "")
        research_length = len(research_content)

        if research_attempts >= MAX_ATTEMPTS:
            research_analysis = f"✅ 研究已达到最大尝试次数 ({research_attempts}/{MAX_ATTEMPTS})\n   - 内容长度: {research_length}字符\n   - 强制接受当前结果"

            # 研究达到最大次数，检查写作状态
            if section_id not in writing_results:
                next_step_suggestion = "建议: 研究已达最大尝试次数，开始写作 → 选择 'writing'"
            elif writing_attempts >= MAX_ATTEMPTS:
                next_step_suggestion = "建议: 当前章节已达最大尝试次数，移动到下一章节 → 选择 'research'"
            else:
                next_step_suggestion = "建议: 研究完成，开始写作 → 选择 'writing'"
        else:
            research_analysis = f"✅ 研究已完成 (尝试次数: {research_attempts}/{MAX_ATTEMPTS})\n   - 内容长度: {research_length}字符\n   - 内容预览: {research_content[:100]}..."

            # 研究完成，检查写作状态
            if section_id not in writing_results:
                next_step_suggestion = "建议: 研究已完成，应该开始写作 → 选择 'writing'"
            elif writing_attempts >= MAX_ATTEMPTS:
                next_step_suggestion = "建议: 当前章节已完成，移动到下一章节 → 选择 'research'"
            else:
                next_step_suggestion = "建议: 当前章节已完成，移动到下一章节 → 选择 'research'"
    else:
        if research_attempts >= MAX_ATTEMPTS:
            research_analysis = f"⚠️ 研究已达最大尝试次数但无结果 ({research_attempts}/{MAX_ATTEMPTS})"
            next_step_suggestion = "建议: 研究多次失败，跳过到写作或下一章节 → 选择 'writing'"
        else:
            research_analysis = f"❌ 尚未开始研究 (尝试次数: {research_attempts}/{MAX_ATTEMPTS})"
            next_step_suggestion = "建议: 需要开始研究当前章节 → 选择 'research'"

    # 分析写作状态
    if section_id in writing_results:
        writing_data = writing_results[section_id]
        writing_content = writing_data.get("content", "")
        word_count = writing_data.get("word_count", 0)

        if writing_attempts >= MAX_ATTEMPTS:
            writing_analysis = f"✅ 写作已达到最大尝试次数 ({writing_attempts}/{MAX_ATTEMPTS})\n   - 字数: {word_count}字\n   - 强制接受当前结果"
        else:
            writing_analysis = f"✅ 写作已完成 (尝试次数: {writing_attempts}/{MAX_ATTEMPTS})\n   - 字数: {word_count}字\n   - 内容预览: {writing_content[:100]}..."
    else:
        if writing_attempts >= MAX_ATTEMPTS:
            writing_analysis = f"⚠️ 写作已达最大尝试次数但无结果 ({writing_attempts}/{MAX_ATTEMPTS})"
        else:
            writing_analysis = f"❌ 尚未开始写作 (尝试次数: {writing_attempts}/{MAX_ATTEMPTS})"

    return f"""
=== 当前章节详细状态 ===
章节标题: {section_title}
章节ID: {section_id}
章节描述: {section_desc}

研究状态分析:
{research_analysis}

写作状态分析:
{writing_analysis}

=== 决策建议 ===
{next_step_suggestion}
"""


def build_supervisor_context(state: Dict[str, Any]) -> Dict[str, str]:
    """构建完整的Supervisor分析上下文"""
    return {
        "status_summary": build_status_summary(state),
        "current_section_info": build_current_section_info(state),
        "execution_path": str(state.get("execution_path", []))
    }


def assess_content_quality(state: Dict[str, Any]) -> Dict[str, Any]:
    """评估内容质量"""
    sections = state.get("sections", [])
    current_index = state.get("current_section_index", 0)
    research_results = state.get("research_results", {})
    writing_results = state.get("writing_results", {})
    
    quality_assessment = {
        "research_quality": "unknown",
        "writing_quality": "unknown",
        "needs_improvement": False,
        "suggestions": []
    }
    
    if current_index < len(sections):
        current_section = sections[current_index]
        section_id = current_section.get("id", "")
        
        # 评估研究质量
        if section_id in research_results:
            research_content = research_results[section_id].get("content", "")
            if len(research_content) < 500:
                quality_assessment["research_quality"] = "poor"
                quality_assessment["needs_improvement"] = True
                quality_assessment["suggestions"].append("研究内容过短，需要补充更多数据和分析")
            else:
                quality_assessment["research_quality"] = "good"
        
        # 评估写作质量
        if section_id in writing_results:
            writing_content = writing_results[section_id].get("content", "")
            word_count = writing_results[section_id].get("word_count", 0)
            if word_count < 300:
                quality_assessment["writing_quality"] = "poor"
                quality_assessment["needs_improvement"] = True
                quality_assessment["suggestions"].append("写作内容过短，需要扩展和完善")
            else:
                quality_assessment["writing_quality"] = "good"
    
    return quality_assessment


def determine_next_action_by_state(state: Dict[str, Any]) -> tuple[str, str]:
    """基于状态逻辑确定下一步行动（备用方案，考虑尝试次数限制）"""
    sections = state.get("sections", [])
    current_index = state.get("current_section_index", 0)
    research_results = state.get("research_results", {})
    writing_results = state.get("writing_results", {})
    section_attempts = state.get("section_attempts", {})

    MAX_ATTEMPTS = 3

    if current_index >= len(sections):
        return "integration", "所有章节处理完成，开始整合"

    current_section = sections[current_index]
    section_id = current_section.get("id", "")
    current_attempts = section_attempts.get(section_id, {"research": 0, "writing": 0})
    research_attempts = current_attempts.get("research", 0)
    writing_attempts = current_attempts.get("writing", 0)

    # 基于尝试次数的决策逻辑
    if section_id not in research_results:
        if research_attempts >= MAX_ATTEMPTS:
            return "writing", f"研究已达最大尝试次数，跳过到写作: {current_section.get('title', '')}"
        else:
            return "research", f"需要研究章节: {current_section.get('title', '')}"
    elif section_id not in writing_results:
        if writing_attempts >= MAX_ATTEMPTS:
            return "move_to_next_section", f"写作已达最大尝试次数，移动到下一章节"
        else:
            return "writing", f"需要写作章节: {current_section.get('title', '')}"
    else:
        # 当前章节完成，移动到下一章节
        if current_index + 1 < len(sections):
            return "move_to_next_section", "当前章节已完成，移动到下一章节"
        else:
            return "integration", "所有章节完成，开始整合"
