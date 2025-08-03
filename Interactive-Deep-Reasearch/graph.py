"""
核心图模块
高级交互式深度研究报告生成系统的主要工作流图
集成Multi-Agent协作、Human-in-loop交互和流式输出
"""

import json
import time
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
import logging

def safe_get_stream_writer():
    """安全获取流写入器，避免上下文错误"""
    try:
        return get_stream_writer()
    except Exception:
        # 如果没有流上下文，返回一个空的写入器
        return lambda x: None

# 导入本地模块
from state import (
    DeepResearchState, ReportMode, AgentType, InteractionType, TaskStatus,
    ReportOutline, ReportSection, ResearchResult, AnalysisInsight,
    update_performance_metrics, add_research_result,
    add_analysis_insight, update_task_status, add_user_interaction
)
from tools import (
    get_research_tools, get_analysis_tools, get_writing_tools, get_validation_tools,
    advanced_web_search, multi_source_research, content_analyzer, trend_analyzer,
    section_content_generator, report_formatter, quality_validator
)

# 导入子图模块
from subgraph.research.graph import (
    create_intelligent_section_research_graph,
    create_intelligent_initial_state,
    IntelligentSectionState
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# LLM配置
# ============================================================================

def create_llm() -> ChatOpenAI:
    """创建LLM实例"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
    )

# 编译子图（全局变量，避免重复编译）
_intelligent_section_subgraph = None

def get_intelligent_section_subgraph():
    """获取智能章节研究子图实例"""
    global _intelligent_section_subgraph
    if _intelligent_section_subgraph is None:
        workflow = create_intelligent_section_research_graph()
        _intelligent_section_subgraph = workflow.compile()
    return _intelligent_section_subgraph

def call_intelligent_section_research(state: DeepResearchState) -> DeepResearchState:
    """
    调用智能章节研究子图

    这个函数实现了主图和子图之间的状态转换：
    1. 将 DeepResearchState 转换为 IntelligentSectionState
    2. 调用子图进行章节研究
    3. 将结果转换回 DeepResearchState
    """
    try:
        # 获取子图实例
        subgraph = get_intelligent_section_subgraph()

        # 获取当前处理的章节
        current_section_index = state.get("current_section_index", 0)
        sections = state.get("sections", [])

        if current_section_index >= len(sections):
            logger.warning(f"章节索引 {current_section_index} 超出范围，总章节数: {len(sections)}")
            return state

        current_section = sections[current_section_index]

        # 状态转换：DeepResearchState -> IntelligentSectionState
        # 准备前面章节的摘要
        previous_sections_summary = []
        for i in range(current_section_index):
            if i < len(sections) and sections[i].get("content"):
                summary = sections[i].get("content", "")[:200] + "..." if len(sections[i].get("content", "")) > 200 else sections[i].get("content", "")
                previous_sections_summary.append(f"{sections[i].get('title', '')}: {summary}")

        # 准备后续章节大纲
        upcoming_sections_outline = []
        for i in range(current_section_index + 1, len(sections)):
            if i < len(sections):
                upcoming_sections_outline.append(f"{sections[i].get('title', '')}: {sections[i].get('description', '')}")

        subgraph_input = create_intelligent_initial_state(
            topic=state.get("topic", ""),
            section={
                "title": current_section.get("title", ""),
                "description": current_section.get("description", ""),
                "requirements": current_section.get("requirements", [])
            },
            previous_sections_summary=previous_sections_summary,
            upcoming_sections_outline=upcoming_sections_outline,
            report_main_thread=state.get("outline", {}).get("executive_summary", ""),
            writing_style=state.get("writing_style", "professional"),
            quality_threshold=0.8,
            max_iterations=3
        )

        logger.info(f"开始智能章节研究: {current_section.get('title', '未知章节')}")

        # 调用子图
        subgraph_output = subgraph.invoke(subgraph_input)

        # 状态转换：IntelligentSectionState -> DeepResearchState
        if subgraph_output and subgraph_output.get("final_content"):
            # 更新当前章节内容
            updated_sections = sections.copy()
            updated_sections[current_section_index] = {
                **current_section,
                "content": subgraph_output["final_content"],
                "research_data": subgraph_output.get("research_results", []),
                "quality_score": subgraph_output.get("quality_metrics", {}).get("overall_score", 0.0),
                "status": "completed"
            }

            # 合并研究结果到主状态
            new_research_results = []
            research_data = subgraph_output.get("research_data", {})
            initial_research = research_data.get("initial_research", [])
            supplementary_research = research_data.get("supplementary_research", [])

            for research_item in initial_research + supplementary_research:
                new_research_results.append(ResearchResult(
                    id=research_item.get("id", str(uuid.uuid4())),
                    query=research_item.get("query", ""),
                    source_type="web",
                    title=research_item.get("title", ""),
                    content=research_item.get("content", ""),
                    url=research_item.get("url", ""),
                    relevance_score=research_item.get("relevance_score", 0.8),
                    timestamp=research_item.get("timestamp", time.time()),
                    section_id=current_section.get("id", "")
                ))

            # 更新状态
            updated_state = {
                **state,
                "sections": updated_sections,
                "current_section_index": current_section_index + 1,
                "research_results": state.get("research_results", []) + new_research_results,
                "performance_metrics": {
                    **state.get("performance_metrics", {}),
                    "sections_completed": current_section_index + 1,
                    "total_sections": len(sections),
                    "last_section_quality": subgraph_output.get("quality_metrics", {}).get("overall_score", 0.0)
                }
            }

            logger.info(f"章节研究完成: {current_section.get('title', '未知章节')}, 质量分数: {subgraph_output.get('quality_metrics', {}).get('overall_score', 0.0)}")
            return updated_state
        else:
            logger.error("子图返回了空结果")
            return state

    except Exception as e:
        logger.error(f"调用智能章节研究子图时出错: {e}")
        return state

def prepare_subgraph_state(main_state: DeepResearchState, section: Dict[str, Any], section_index: int, completed_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """准备子图输入状态"""

    # 准备前面章节的摘要
    previous_sections_summary = []
    for completed_section in completed_sections:
        if completed_section.get("content"):
            summary = completed_section["content"][:200] + "..." if len(completed_section["content"]) > 200 else completed_section["content"]
            previous_sections_summary.append(f"{completed_section.get('title', '')}: {summary}")

    # 准备后续章节大纲
    all_sections = main_state.get("outline", {}).get("sections", [])
    upcoming_sections_outline = []
    for i in range(section_index + 1, len(all_sections)):
        if i < len(all_sections):
            upcoming_sections_outline.append(f"{all_sections[i].get('title', '')}: {all_sections[i].get('description', '')}")

    # 使用子图的状态创建函数
    return create_intelligent_initial_state(
        topic=main_state.get("topic", ""),
        section=section,
        previous_sections_summary=previous_sections_summary,
        upcoming_sections_outline=upcoming_sections_outline,
        report_main_thread=main_state.get("outline", {}).get("executive_summary", "") if main_state.get("outline") else "",
        writing_style=main_state.get("writing_style", "professional"),
        quality_threshold=0.8,
        max_iterations=3
    )

async def call_intelligent_subgraph(subgraph_state: Dict[str, Any]) -> Dict[str, Any]:
    """调用智能章节研究子图"""
    try:
        # 获取子图实例
        subgraph = get_intelligent_section_subgraph()

        # 调用子图
        result = await subgraph.ainvoke(subgraph_state)

        return result

    except Exception as e:
        logger.error(f"调用智能子图失败: {e}")
        return {}

def convert_research_data_to_results(research_data: List[Dict[str, Any]]) -> List[ResearchResult]:
    """将子图的研究数据转换为主图的 ResearchResult 格式"""
    results = []

    for item in research_data:
        try:
            result = ResearchResult(
                id=item.get("id", str(uuid.uuid4())),
                query=item.get("query", ""),
                source_type="web",
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                relevance_score=item.get("relevance_score", 0.8),
                timestamp=item.get("timestamp", time.time()),
                section_id=item.get("section_id", "")
            )
            results.append(result)
        except Exception as e:
            logger.warning(f"转换研究数据失败: {e}")
            continue

    return results

async def intelligent_section_processing_node(state: DeepResearchState, config=None) -> DeepResearchState:
    """
    智能章节处理节点 - 逐个调用子图处理每个章节

    这个节点的作用：
    1. 获取大纲中的所有章节
    2. 逐个调用智能章节研究子图
    3. 每个章节都经过完整的：研究→分析→生成→质量评估→优化流程
    4. 汇总所有章节形成完整报告
    """
    writer = safe_get_stream_writer()
    writer({
        "step": "intelligent_section_processing",
        "status": "🧠 开始智能章节处理（集成子图）",
        "progress": 0
    })

    try:
        outline = state.get("outline", {})
        sections = outline.get("sections", []) if outline else []

        if not sections:
            writer({
                "step": "intelligent_section_processing",
                "status": "❌ 没有可用的章节信息",
                "progress": -1
            })
            return state

        completed_sections = []
        all_research_data = []

        writer({
            "step": "intelligent_section_processing",
            "status": f"📚 准备处理 {len(sections)} 个章节，每个章节都将经过完整的智能研究流程",
            "progress": 10,
            "total_sections": len(sections)
        })

        # 逐个处理每个章节
        for section_index, section in enumerate(sections):
            writer({
                "step": "intelligent_section_processing",
                "status": f"🔬 处理章节 {section_index + 1}/{len(sections)}: {section.get('title', '未知章节')}",
                "progress": 10 + (section_index / len(sections)) * 80,
                "current_section": section.get('title', '未知章节'),
                "section_index": section_index + 1
            })

            # 准备子图输入状态
            subgraph_state = prepare_subgraph_state(state, section, section_index, completed_sections)

            # 调用智能章节研究子图
            subgraph_result = await call_intelligent_subgraph(subgraph_state)

            if subgraph_result and subgraph_result.get("final_content"):
                # 成功处理章节
                section_result = {
                    **section,
                    "content": subgraph_result["final_content"],
                    "research_data": subgraph_result.get("research_data", {}),
                    "quality_metrics": subgraph_result.get("quality_metrics", {}),
                    "processing_time": subgraph_result.get("processing_time", 0),
                    "iteration_count": subgraph_result.get("iteration_count", 0),
                    "status": "completed"
                }
                completed_sections.append(section_result)

                # 收集研究数据
                research_data = subgraph_result.get("research_data", {})
                if research_data.get("initial_research_results"):
                    all_research_data.extend(research_data["initial_research_results"])
                if research_data.get("supplementary_research_results"):
                    all_research_data.extend(research_data["supplementary_research_results"])

                writer({
                    "step": "intelligent_section_processing",
                    "status": f"✅ 章节完成: {section.get('title', '未知章节')} (质量: {subgraph_result.get('quality_metrics', {}).get('final_quality_score', 0):.2f})",
                    "progress": 10 + ((section_index + 1) / len(sections)) * 80,
                    "completed_sections": len(completed_sections),
                    "quality_score": subgraph_result.get('quality_metrics', {}).get('final_quality_score', 0)
                })
            else:
                # 章节处理失败
                writer({
                    "step": "intelligent_section_processing",
                    "status": f"⚠️ 章节处理失败: {section.get('title', '未知章节')}",
                    "progress": 10 + ((section_index + 1) / len(sections)) * 80
                })
                logger.warning(f"章节处理失败: {section.get('title', '未知章节')}")

        # 更新主图状态
        state["sections"] = completed_sections
        state["research_results"] = convert_research_data_to_results(all_research_data)
        state["content_creation_completed"] = True
        state["completed_sections_count"] = len(completed_sections)

        # 计算整体质量
        avg_quality = sum(s.get("quality_metrics", {}).get("final_quality_score", 0) for s in completed_sections) / max(len(completed_sections), 1)

        writer({
            "step": "intelligent_section_processing",
            "status": f"🎉 智能章节处理完成！成功处理 {len(completed_sections)}/{len(sections)} 个章节",
            "progress": 100,
            "completed_sections": len(completed_sections),
            "total_sections": len(sections),
            "average_quality": avg_quality,
            "total_research_items": len(all_research_data)
        })

        logger.info(f"智能章节处理完成: {len(completed_sections)}/{len(sections)} 个章节, 平均质量: {avg_quality:.3f}")
        return state

    except Exception as e:
        logger.error(f"智能章节处理失败: {str(e)}")
        writer({
            "step": "intelligent_section_processing",
            "status": f"❌ 章节处理失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"智能章节处理错误: {str(e)}"]
        return state

def create_specialized_agents():
    """创建专业化Agent"""
    llm = create_llm()
    
    # 研究专家Agent
    researcher_agent = create_react_agent(
        llm,
        tools=get_research_tools(),
        prompt="""你是一个专业的研究专家。你的职责包括：
        1. 深度搜索和收集相关信息
        2. 评估信息来源的可信度和相关性
        3. 识别关键趋势和发展模式
        4. 提供全面且准确的研究数据
        
        工作原则：
        - 使用多个可信来源验证信息
        - 关注最新发展和趋势
        - 保持客观和批判性思维
        - 提供详细的数据支撑
        
        请确保研究的深度和广度，为后续分析提供充分的数据基础。"""
    )
    
    # 分析专家Agent
    analyst_agent = create_react_agent(
        llm,
        tools=get_analysis_tools(),
        prompt="""你是一个专业的分析专家。你的职责包括：
        1. 深度分析研究数据和信息
        2. 识别关键洞察、模式和趋势
        3. 进行预测性分析和风险评估
        4. 提供数据驱动的结论和建议
        
        分析重点：
        - 趋势识别和模式发现
        - 因果关系分析
        - 影响因素评估
        - 预测性洞察生成
        
        请运用严格的分析方法，确保结论的科学性和可靠性。"""
    )
    
    # 写作专家Agent
    writer_agent = create_react_agent(
        llm,
        tools=get_writing_tools(),
        prompt="""你是一个专业的技术写作专家。你的职责包括：
        1. 将复杂研究和分析转化为清晰的内容
        2. 确保内容结构合理、逻辑清晰
        3. 适应不同读者群体的需求
        4. 保持一致的专业写作风格
        
        写作标准：
        - 结构清晰、层次分明
        - 语言准确、表达流畅
        - 逻辑严密、论证充分
        - 重点突出、易于理解
        
        请确保生成的内容具有专业性、可读性和实用性。"""
    )
    
    # 验证专家Agent
    validator_agent = create_react_agent(
        llm,
        tools=get_validation_tools(),
        prompt="""你是一个专业的质量验证专家。你的职责包括：
        1. 验证报告内容的准确性和完整性
        2. 检查逻辑一致性和论证严密性
        3. 评估内容质量和可读性
        4. 识别问题并提供改进建议
        
        验证标准：
        - 内容准确性和完整性
        - 逻辑一致性和连贯性
        - 结构合理性和可读性
        - 专业性和权威性
        
        请严格按照质量标准进行验证，确保报告的专业水准。"""
    )
    
    return {
        AgentType.RESEARCHER: researcher_agent,
        AgentType.ANALYST: analyst_agent,
        AgentType.WRITER: writer_agent,
        AgentType.VALIDATOR: validator_agent
    }

# ============================================================================
# 智能协调节点
# ============================================================================

async def intelligent_supervisor_node(state: DeepResearchState, config=None) -> DeepResearchState:
    """
    智能监督协调节点
    负责整体任务规划、Agent调度和流程控制
    """
    writer = safe_get_stream_writer()
    writer({
        "step": "supervision",
        "status": "开始智能任务协调",
        "progress": 0,
        "session_id": state["session_id"]
    })
    
    try:
        start_time = time.time()
        llm = create_llm()
        
        # 构建协调分析提示
        supervision_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能的报告生成监督协调器。分析当前状态并决定下一步行动。
            
            可用的Agent类型：
            - researcher: 深度研究和信息收集
            - analyst: 数据分析和洞察生成
            - writer: 内容写作和报告生成
            - validator: 质量验证和改进
            
            可用的行动：
            - outline_generation: 生成报告大纲
            - research_execution: 执行深度研究
            - analysis_generation: 生成分析洞察
            - content_creation: 创建报告内容
            - quality_validation: 质量验证
            - finish: 完成报告生成
            
            请分析当前状态并返回推荐的下一步行动（只返回行动名称）。
            """),
            ("human", """
            当前状态分析：
            - 主题：{topic}
            - 当前步骤：{current_step}
            - 执行路径：{execution_path}
            - 已有大纲：{has_outline}
            - 研究结果数：{research_count}
            - 分析洞察数：{insights_count}
            - 已有最终报告：{has_final_report}
            - 运行模式：{mode}
            
            请根据以上信息推荐下一步行动。
            """)
        ])
        
        # 准备状态分析数据
        analysis_data = {
            "topic": state["topic"],
            "current_step": state["current_step"],
            "execution_path": " → ".join(state["execution_path"]) if state["execution_path"] else "无",
            "has_outline": "是" if state["outline"] else "否",
            "research_count": len(state["research_results"]),
            "insights_count": len(state["analysis_insights"]),
            "has_final_report": "是" if state["final_report"] else "否",
            "mode": state["mode"]
        }
        
        writer({
            "step": "supervision",
            "status": "分析当前状态...",
            "progress": 30,
            "analysis_data": analysis_data
        })
        
        # 流式生成协调决策
        full_response = ""
        chunk_count = 0
        async for chunk in llm.astream(supervision_prompt.format_messages(**analysis_data), config=config):
            if chunk.content:
                full_response += chunk.content
                chunk_count += 1
                
                # 减少进度更新频率，只在特定的chunk数时更新
                if chunk_count % 5 == 0:
                    writer({
                        "step": "supervision",
                        "status": "正在制定协调决策...",
                        "progress": min(80, 60 + (chunk_count // 5) * 4),
                        "reasoning": full_response[:200] + "..." if len(full_response) > 200 else full_response
                    })
        
        # 解析决策
        decision_text = full_response.lower().strip()
        
        # 智能决策逻辑
        if not state["outline"]:
            next_action = "outline_generation"
            reasoning = "需要首先生成报告大纲"
        elif len(state["research_results"]) < 5:  # 需要足够的研究数据
            next_action = "research_execution"
            reasoning = "需要进行深度研究收集数据"
        elif len(state["analysis_insights"]) < 3:  # 需要分析洞察
            next_action = "analysis_generation"
            reasoning = "需要生成分析洞察"
        elif not state["final_report"]:
            next_action = "content_creation"
            reasoning = "需要创建最终报告内容"
        elif state["final_report"] and not state.get("validated", False):
            next_action = "quality_validation"
            reasoning = "需要进行质量验证"
        else:
            next_action = "finish"
            reasoning = "报告生成流程完成"
        
        # 基于响应内容进行微调
        if "outline" in decision_text and not state["outline"]:
            next_action = "outline_generation"
        elif "research" in decision_text:
            next_action = "research_execution"
        elif "analysis" in decision_text or "insight" in decision_text:
            next_action = "analysis_generation"
        elif "content" in decision_text or "write" in decision_text:
            next_action = "content_creation"
        elif "validation" in decision_text or "quality" in decision_text:
            next_action = "quality_validation"
        elif "finish" in decision_text or "complete" in decision_text:
            next_action = "finish"
        
        # 更新状态
        execution_time = time.time() - start_time
        update_performance_metrics(state, "supervisor", execution_time)
        
        state["current_step"] = f"supervised_{next_action}"
        state["execution_path"] = state["execution_path"] + ["supervisor"]
        state["agent_results"]["supervisor"] = {
            "next_action": next_action,
            "reasoning": reasoning,
            "execution_time": execution_time
        }
        
        # 添加监督消息
        supervision_message = f"""
        🧠 智能监督协调完成：
        
        📊 当前状态分析：
        - 大纲状态：{'已生成' if state['outline'] else '待生成'}
        - 研究数据：{len(state['research_results'])}条
        - 分析洞察：{len(state['analysis_insights'])}个
        - 报告状态：{'已生成' if state['final_report'] else '待生成'}
        
        🎯 决策结果：
        - 下一步行动：{next_action}
        - 决策理由：{reasoning}
        - 执行时间：{execution_time:.2f}秒
        """
        
        state["messages"] = state["messages"] + [AIMessage(content=supervision_message)]
        
        writer({
            "step": "supervision",
            "status": "监督协调完成",
            "progress": 100,
            "next_action": next_action,
            "reasoning": reasoning,
            "execution_time": execution_time
        })
        
        logger.info(f"监督协调完成: {next_action} - {reasoning}")
        return state
        
    except Exception as e:
        logger.error(f"监督协调失败: {str(e)}")
        writer({
            "step": "supervision",
            "status": f"监督协调失败: {str(e)}",
            "progress": -1
        })
        
        state["error_log"] = state["error_log"] + [f"监督协调错误: {str(e)}"]
        state["current_step"] = "supervision_failed"
        return state

# ============================================================================
# 大纲生成节点
# ============================================================================

async def outline_generation_node(state: DeepResearchState, config=None) -> DeepResearchState:
    """大纲生成节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "outline_generation",
        "status": "开始生成深度研究大纲",
        "progress": 0
    })
    
    try:
        start_time = time.time()
        llm = create_llm()
        parser = JsonOutputParser(pydantic_object=ReportOutline)
        
        # 构建高级大纲生成提示
        outline_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是专业的报告大纲设计专家。请生成详细的深度研究报告大纲。
            
            要求：
            1. 大纲符合{report_type}报告的标准结构
            2. 针对{target_audience}读者群体设计
            3. 研究深度为{depth_level}级别
            4. 目标字数约{target_length}字
            5. 每个章节包含研究查询关键词
            6. 章节优先级合理分配
            
            {format_instructions}"""),
            ("human", """
            请为以下主题生成专业的深度研究报告大纲：
            
            研究主题：{topic}
            报告类型：{report_type}
            目标读者：{target_audience}
            深度级别：{depth_level}
            
            请确保大纲结构完整、逻辑清晰、便于深度研究。
            """)
        ])
        
        input_data = {
            "topic": state["topic"],
            "report_type": state["report_type"],
            "target_audience": state["target_audience"],
            "depth_level": state["depth_level"],
            "target_length": state["target_length"],
            "format_instructions": parser.get_format_instructions()
        }
        
        writer({
            "step": "outline_generation",
            "status": "正在生成专业大纲...",
            "progress": 30
        })
        
        # 创建LLM链并流式执行
        llm_chain = outline_prompt | llm | parser
        
        outline_data = None
        chunk_count = 0
        current_outline_display = ""
        
        async for chunk in llm_chain.astream(input_data, config=config):
            outline_data = chunk
            chunk_count += 1
            # 实时显示大纲内容（每5个chunk更新一次以减少频率）
            if chunk_count % 5 == 0:
                # 构建当前大纲的显示文本
                if hasattr(chunk, 'title'):
                    current_outline_display = f"🎯 标题：{chunk.title}\n"
                if hasattr(chunk, 'sections') and chunk.sections:
                    current_outline_display += f"📚 章节({len(chunk.sections)}个):\n"
                    for i, section in enumerate(chunk.sections[:3], 1):  # 只显示前3个章节
                        if hasattr(section, 'title'):
                            current_outline_display += f"  {i}. {section.title}\n"
                            if hasattr(section, 'description'):
                                current_outline_display += f"     {section.description}\n"
                    if len(chunk.sections) > 3:
                        current_outline_display += f"  ... 还有{len(chunk.sections)-3}个章节"
                
                writer({
                    "step": "outline_generation",
                    "status": "正在构建大纲结构...",
                    "content": chunk,
                    "progress": min(90, 30 + (chunk_count // 5) * 10),
                    "current_outline": current_outline_display,
                    "chunk_count": chunk_count
                })
                
                # 如果大纲基本完整，提前显示
                if hasattr(chunk, 'title') and hasattr(chunk, 'sections') and len(chunk.sections) >= 3:
                    writer({
                        "step": "outline_generation",
                        "status": "大纲结构已生成，正在完善细节...",
                        "progress": 85,
                        "partial_outline": chunk,
                        "streaming_content": current_outline_display
                    })
        
        # 处理生成结果
        if not outline_data:
            # 创建默认大纲
            outline_data = ReportOutline(
                title=f"{state['topic']} - 深度研究报告",
                executive_summary=f"本报告对{state['topic']}进行全面深入的研究分析，为{state['target_audience']}提供专业洞察。",
                sections=[
                    ReportSection(
                        id="background",
                        title="研究背景与现状",
                        description="分析研究背景、发展历程和当前状态",
                        key_points=["历史发展", "现状分析", "关键特征"],
                        research_queries=[f"{state['topic']} 发展历史", f"{state['topic']} 现状分析", f"{state['topic']} 市场规模"],
                        priority=5
                    ),
                    ReportSection(
                        id="deep_analysis",
                        title="深度分析与洞察",
                        description="进行深入分析，识别关键趋势和模式",
                        key_points=["核心驱动因素", "发展趋势", "影响因素"],
                        research_queries=[f"{state['topic']} 趋势分析", f"{state['topic']} 影响因素", f"{state['topic']} 发展预测"],
                        priority=5
                    ),
                    ReportSection(
                        id="case_studies",
                        title="案例研究与应用",
                        description="分析典型案例和实际应用情况",
                        key_points=["成功案例", "应用场景", "实施经验"],
                        research_queries=[f"{state['topic']} 案例研究", f"{state['topic']} 应用实例", f"{state['topic']} 最佳实践"],
                        priority=4
                    ),
                    ReportSection(
                        id="challenges_opportunities",
                        title="挑战与机遇分析",
                        description="识别面临的挑战和发展机遇",
                        key_points=["主要挑战", "发展机遇", "风险评估"],
                        research_queries=[f"{state['topic']} 挑战分析", f"{state['topic']} 发展机会", f"{state['topic']} 风险评估"],
                        priority=4
                    ),
                    ReportSection(
                        id="future_outlook",
                        title="未来展望与建议",
                        description="预测未来发展并提出专业建议",
                        key_points=["发展预测", "战略建议", "行动计划"],
                        research_queries=[f"{state['topic']} 未来发展", f"{state['topic']} 发展建议", f"{state['topic']} 战略规划"],
                        priority=3
                    )
                ],
                methodology="采用文献研究、案例分析、趋势预测和专家洞察相结合的综合研究方法",
                target_audience=state["target_audience"],
                estimated_length=state["target_length"]
            )
        
        # 转换为字典格式
        if hasattr(outline_data, 'dict'):
            outline_dict = outline_data.dict()
        else:
            outline_dict = dict(outline_data) if outline_data else {}
        
        # 更新状态
        execution_time = time.time() - start_time
        update_performance_metrics(state, "outline_generator", execution_time)
        update_task_status(state, "outline_generation", TaskStatus.COMPLETED)
        
        state["outline"] = outline_dict
        state["current_step"] = "outline_generated"
        state["execution_path"] = state["execution_path"] + ["outline_generation"]
        
        # 创建大纲展示消息
        sections_text = "\n".join([
            f"  {i+1}. {section['title']}\n     {section['description']}\n     关键词: {', '.join(section['research_queries'][:3])}"
            for i, section in enumerate(outline_dict.get("sections", []))
        ])
        
        outline_message = f"""
        📋 深度研究大纲生成完成：
        
        🎯 报告标题：{outline_dict.get('title', '未知')}
        
        📝 执行摘要：
        {outline_dict.get('executive_summary', '无摘要')}
        
        📚 研究章节：
        {sections_text}
        
        🔍 研究方法：{outline_dict.get('methodology', '未指定')}
        📊 预估字数：{outline_dict.get('estimated_length', 0):,}字
        ⏱️ 生成时间：{execution_time:.2f}秒
        """
        
        state["messages"] = state["messages"] + [AIMessage(content=outline_message)]
        
        writer({
            "step": "outline_generation",
            "status": "深度研究大纲生成完成",
            "progress": 100,
            "sections_count": len(outline_dict.get("sections", [])),
            "execution_time": execution_time,
            "content": {
                "type": "outline",
                "data": outline_dict,
                "display_text": outline_message
            }
        })
        
        logger.info(f"大纲生成完成: {len(outline_dict.get('sections', []))}个章节")
        return state
        
    except Exception as e:
        logger.error(f"大纲生成失败: {str(e)}")
        writer({
            "step": "outline_generation",
            "status": f"大纲生成失败: {str(e)}",
            "progress": -1
        })
        
        state["error_log"] = state["error_log"] + [f"大纲生成错误: {str(e)}"]
        state["current_step"] = "outline_generation_failed"
        update_task_status(state, "outline_generation", TaskStatus.FAILED)
        return state

# ============================================================================
# 交互确认节点
# ============================================================================

def create_interaction_node(interaction_type: InteractionType):
    """创建交互确认节点的工厂函数"""
    
    def interaction_node(state: DeepResearchState) -> DeepResearchState:
        """通用交互确认节点"""
        writer = safe_get_stream_writer()
        
        interaction_config = get_interaction_config(interaction_type)
        mode = state["mode"]
        
        writer({
            "step": f"interaction_{interaction_type.value}",
            "status": f"处理{interaction_config['title']}",
            "progress": 0,
            "interaction_type": interaction_type.value,
            "mode": mode.value
        })
        
        # Copilot模式自动通过
        if mode == ReportMode.COPILOT:
            state["approval_status"][interaction_type.value] = True
            state["user_feedback"][interaction_type.value] = {"approved": True, "auto": True}
            
            writer({
                "step": f"interaction_{interaction_type.value}",
                "status": "Copilot模式自动通过",
                "progress": 100,
                "auto_approved": True
            })
            
            state["messages"] = state["messages"] + [
                AIMessage(content=f"🤖 Copilot模式：{interaction_config['copilot_message']}")
            ]
            
            return state
        
        # 交互模式需要用户确认
        message_content = format_interaction_message(state, interaction_type, interaction_config)
        
        writer({
            "step": f"interaction_{interaction_type.value}",
            "status": "等待用户确认",
            "progress": 50,
            "awaiting_user_input": True
        })
        
        # 使用interrupt等待用户输入
        user_response = interrupt({
            "type": interaction_type.value,
            "title": interaction_config["title"],
            "message": message_content,
            "options": interaction_config["options"],
            "default": interaction_config.get("default", "continue")
        })
        
        # 处理用户响应
        approved = user_response.get("approved", True) if isinstance(user_response, dict) else True
        state["approval_status"][interaction_type.value] = approved
        state["user_feedback"][interaction_type.value] = user_response
        
        # 记录交互历史
        add_user_interaction(state, interaction_type.value, user_response)
        
        writer({
            "step": f"interaction_{interaction_type.value}",
            "status": "用户确认完成",
            "progress": 100,
            "user_response": user_response,
            "approved": approved
        })
        
        # 添加确认消息
        status_emoji = "✅" if approved else "❌"
        confirmation_message = f"{status_emoji} {interaction_config['title']}：{'确认通过' if approved else '被拒绝'}"
        
        state["messages"] = state["messages"] + [AIMessage(content=confirmation_message)]
        
        return state
    
    return interaction_node

def get_interaction_config(interaction_type: InteractionType) -> Dict[str, Any]:
    """获取交互配置"""
    configs = {
        InteractionType.OUTLINE_CONFIRMATION: {
            "title": "大纲确认",
            "copilot_message": "自动确认报告大纲，继续执行研究",
            "options": ["确认继续", "修改大纲", "重新生成"],
            "default": "确认继续"
        },
        InteractionType.RESEARCH_PERMISSION: {
            "title": "研究权限确认",
            "copilot_message": "自动允许进行深度研究和数据收集",
            "options": ["允许研究", "跳过研究", "限制范围"],
            "default": "允许研究"
        },
        InteractionType.ANALYSIS_APPROVAL: {
            "title": "分析结果审批",
            "copilot_message": "自动确认分析结果，继续内容生成",
            "options": ["确认分析", "重新分析", "调整方向"],
            "default": "确认分析"
        },
        InteractionType.CONTENT_REVIEW: {
            "title": "内容审查",
            "copilot_message": "自动通过内容审查，准备最终报告",
            "options": ["通过审查", "修改内容", "重写章节"],
            "default": "通过审查"
        },
        InteractionType.FINAL_APPROVAL: {
            "title": "最终审批",
            "copilot_message": "自动完成最终审批，报告生成完成",
            "options": ["最终确认", "再次修改", "生成新版本"],
            "default": "最终确认"
        }
    }
    return configs.get(interaction_type, {})

def format_interaction_message(state: DeepResearchState, interaction_type: InteractionType, config: Dict[str, Any]) -> str:
    """格式化交互消息"""
    if interaction_type == InteractionType.OUTLINE_CONFIRMATION:
        outline = state.get("outline", {})
        sections_text = "\n".join([
            f"  {i+1}. {section.get('title', '未知章节')}\n     {section.get('description', '无描述')}"
            for i, section in enumerate(outline.get("sections", []))
        ])
        return f"""
            请确认以下深度研究报告大纲：

            📋 标题：{outline.get('title', '未知标题')}

            📝 摘要：{outline.get('executive_summary', '无摘要')}

            📚 章节结构：
            {sections_text}

            🔍 研究方法：{outline.get('methodology', '未指定')}
            📊 预估字数：{outline.get('estimated_length', 0):,}字
            👥 目标读者：{outline.get('target_audience', '未知')}
        """
    elif interaction_type == InteractionType.RESEARCH_PERMISSION:
        return f"""
            是否允许对主题「{state['topic']}」进行深度研究？

            研究将包括：
            - 多源网络搜索和信息收集
            - 相关案例和数据分析
            - 趋势识别和模式发现
            - 专业洞察生成

            预计研究时间：5-10分钟
        """
    else:
        return f"请确认{config['title']}相关设置"

# 创建交互节点实例
outline_confirmation_node = create_interaction_node(InteractionType.OUTLINE_CONFIRMATION)
research_permission_node = create_interaction_node(InteractionType.RESEARCH_PERMISSION)
analysis_approval_node = create_interaction_node(InteractionType.ANALYSIS_APPROVAL)
content_review_node = create_interaction_node(InteractionType.CONTENT_REVIEW)
final_approval_node = create_interaction_node(InteractionType.FINAL_APPROVAL)

# ============================================================================
# 图构建和路由逻辑
# ============================================================================




# 注意：原来的 content_creation_node 已被删除
# 现在使用 enhanced_content_creation_node（集成了智能章节研究子图）


async def analysis_generation_node(state: DeepResearchState) -> DeepResearchState:
    """分析洞察生成节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "analysis_generation",
        "status": "开始生成分析洞察",
        "progress": 0
    })
    
    try:
        start_time = time.time()
        
        research_results = state.get("research_results", [])
        if not research_results:
            writer({
                "step": "analysis_generation",
                "status": "没有研究数据可供分析",
                "progress": 100
            })
            return state
        
        writer({
            "step": "analysis_generation", 
            "status": "正在进行趋势分析...",
            "progress": 30
        })
        
        # 使用趋势分析工具
        insights = trend_analyzer.invoke({
            "research_results": research_results,
            "analysis_focus": state.get("report_type", "general")
        })
        
        writer({
            "step": "analysis_generation",
            "status": "正在生成洞察报告...",
            "progress": 70
        })
        
        # 添加洞察到状态
        for insight in insights:
            if not insight.get("error"):
                add_analysis_insight(state, insight)
        
        # 更新状态
        execution_time = time.time() - start_time
        update_performance_metrics(state, "analyst", execution_time)
        update_task_status(state, "analysis_generation", TaskStatus.COMPLETED)
        
        state["current_step"] = "analysis_completed"
        state["execution_path"] = state["execution_path"] + ["analysis_generation"]
        
        # 添加分析完成消息
        analysis_message = f"""
        📈 分析洞察生成完成：
        
        🔍 洞察统计：
        - 生成洞察：{len([i for i in insights if not i.get('error')])}个
        - 数据来源：{len(research_results)}条研究结果
        - 执行时间：{execution_time:.2f}秒
        
        💡 主要洞察类型：
        {chr(10).join([f"  • {insight.get('type', '未知')}: {insight.get('title', '未知标题')}" for insight in insights[:3] if not insight.get('error')])}
        """
        
        state["messages"] = state["messages"] + [AIMessage(content=analysis_message)]
        
        writer({
            "step": "analysis_generation",
            "status": "分析洞察生成完成",
            "progress": 100,
            "insights_count": len([i for i in insights if not i.get('error')]),
            "execution_time": execution_time
        })
        
        logger.info(f"分析生成完成: {len(insights)}个洞察")
        return state
        
    except Exception as e:
        logger.error(f"分析生成失败: {str(e)}")
        writer({
            "step": "analysis_generation",
            "status": f"分析生成失败: {str(e)}",
            "progress": -1
        })
        
        state["error_log"] = state["error_log"] + [f"分析生成错误: {str(e)}"]
        state["current_step"] = "analysis_failed"
        update_task_status(state, "analysis_generation", TaskStatus.FAILED)
        return state

# ============================================================================
# 路由函数 - 简化版本
# ============================================================================

def route_after_outline_confirmation(state: DeepResearchState) -> str:
    """大纲确认后的路由 - 简化版本"""
    if not state["approval_status"].get("outline_confirmation", True):
        return "outline_generation"  # 重新生成大纲
    return "content_creation"  # 直接进入内容创建（集成了子图）



# ============================================================================
# 图构建函数
# ============================================================================

def create_deep_research_graph(checkpointer: Optional[InMemorySaver] = None):
    """创建深度研究报告生成图 - 集成智能章节研究子图"""
    workflow = StateGraph(DeepResearchState)

    # 添加简化的核心节点 - 集成智能章节研究子图
    workflow.add_node("outline_generation", outline_generation_node)
    workflow.add_node("outline_confirmation", outline_confirmation_node)
    # 使用智能章节处理节点（集成了完整的章节研究子图）
    workflow.add_node("content_creation", intelligent_section_processing_node)
    
    # 设置简化的流程：大纲生成 → 大纲确认 → 内容创建
    workflow.add_edge(START, "outline_generation")
    workflow.add_edge("outline_generation", "outline_confirmation")

    # 大纲确认后的条件路由
    workflow.add_conditional_edges(
        "outline_confirmation",
        route_after_outline_confirmation,
        {
            "outline_generation": "outline_generation",
            "content_creation": "content_creation"
        }
    )
    
    workflow.add_edge("content_creation", END)
    
    # 编译图
    if checkpointer is None:
        checkpointer = InMemorySaver()
    
    app = workflow.compile(checkpointer=checkpointer)
    return app
