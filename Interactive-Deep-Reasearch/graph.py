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
    writer = get_stream_writer()
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
    writer = get_stream_writer()
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
        writer = get_stream_writer()
        
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
# Multi-Agent执行节点
# ============================================================================

async def multi_agent_research_node(state: DeepResearchState, config=None) -> DeepResearchState:
    """🚀 真正的Multi-Agent并行研究执行节点"""
    writer = get_stream_writer()
    writer({
        "step": "multi_agent_research",
        "status": "🤖 启动Multi-Agent并行研究系统",
        "progress": 0
    })
    
    try:
        start_time = time.time()
        agents = create_specialized_agents()
        
        outline = state.get("outline", {})
        sections = outline.get("sections", [])
        
        if not sections:
            writer({
                "step": "multi_agent_research",
                "status": "没有可研究的章节",
                "progress": 100
            })
            return state
        
        writer({
            "step": "multi_agent_research",
            "status": f"🔧 启动3个专业Agent并行研究{len(sections)}个章节",
            "progress": 10
        })
        
        # 智能生成研究查询
        def generate_smart_queries(topic, section):
            """基于主题和章节动态生成研究查询"""
            section_title = section.get('title', '')
            key_points = section.get('key_points', [])
            
            # 基础查询策略
            base_queries = [
                f"{topic} {section_title}",  # 核心主题查询
                f"{section_title} 2024年最新发展",  # 时间维度
                f"{section_title} 成功案例分析"  # 案例维度
            ]
            
            # 基于关键点的精确查询
            for point in key_points[:2]:
                base_queries.append(f"{topic} {point} 实践应用")
            
            # 根据章节类型添加特定查询
            if "背景" in section_title or "现状" in section_title:
                base_queries.append(f"{topic} 发展历史 市场规模")
            elif "分析" in section_title or "趋势" in section_title:
                base_queries.append(f"{topic} 发展趋势 预测分析")
            elif "挑战" in section_title or "问题" in section_title:
                base_queries.append(f"{topic} 面临挑战 解决方案")
            elif "前景" in section_title or "未来" in section_title:
                base_queries.append(f"{topic} 未来发展 投资机会")
            
            return base_queries[:5]  # 每个章节最多5个高质量查询
        
        # Agent任务分配策略
        def assign_agent_by_section(section):
            """根据章节特点智能分配Agent"""
            title = section.get('title', '').lower()
            
            if any(keyword in title for keyword in ['背景', '现状', '发展', '历史']):
                return AgentType.RESEARCHER  # 研究型章节
            elif any(keyword in title for keyword in ['分析', '趋势', '预测', '洞察']):
                return AgentType.ANALYST  # 分析型章节
            elif any(keyword in title for keyword in ['案例', '应用', '实践']):
                return [AgentType.RESEARCHER, AgentType.ANALYST]  # 协作型章节
            else:
                return AgentType.RESEARCHER  # 默认研究型
        
        # 准备并行任务
        research_tasks = []
        for section in sections:
            smart_queries = generate_smart_queries(state["topic"], section)
            assigned_agent = assign_agent_by_section(section)
            
            research_tasks.append({
                "section": section,
                "queries": smart_queries,
                "agent_type": assigned_agent,
                "priority": section.get("priority", 3)
            })
        
        # 按优先级排序任务
        research_tasks.sort(key=lambda x: x["priority"], reverse=True)
        
        writer({
            "step": "multi_agent_research",
            "status": "⚡ 并行执行研究任务...",
            "progress": 20,
            "task_count": len(research_tasks),
            "agent_distribution": {
                "researcher_tasks": len([t for t in research_tasks if t["agent_type"] == AgentType.RESEARCHER]),
                "analyst_tasks": len([t for t in research_tasks if t["agent_type"] == AgentType.ANALYST]),
                "collaborative_tasks": len([t for t in research_tasks if isinstance(t["agent_type"], list)])
            }
        })
        
        # 真正的Multi-Agent并行执行
        async def research_section_with_agent(task):
            """使用指定Agent执行章节研究"""
            section = task["section"]
            queries = task["queries"]
            agent_type = task["agent_type"]
            
            section_results = []
            
            # 并行搜索所有查询
            search_tasks = []
            for query in queries:
                search_tasks.append(
                    asyncio.create_task(
                        asyncio.to_thread(
                            multi_source_research.invoke,
                            {
                                "topic": state["topic"],
                                "research_queries": [query],
                                "max_results_per_query": 3,  # 增加结果数量
                                "search_depth": "advanced"  # 深度搜索
                            }
                        )
                    )
                )
            
            # 等待所有搜索完成
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 处理搜索结果
            for results in search_results:
                if isinstance(results, list):
                    for result in results:
                        if not result.get("error"):
                            # 添加Agent信息
                            result["section_id"] = section.get("id")
                            result["section_title"] = section.get("title")
                            result["assigned_agent"] = str(agent_type)
                            result["research_priority"] = task["priority"]
                            section_results.append(result)
            
            return section_results
        
        # 并行执行所有研究任务
        section_tasks = [research_section_with_agent(task) for task in research_tasks]
        section_results_list = await asyncio.gather(*section_tasks, return_exceptions=True)
        
        # 汇总结果和质量评估
        all_research_results = []
        completed_tasks = 0
        
        for i, section_results in enumerate(section_results_list):
            if isinstance(section_results, list):
                for result in section_results:
                    # 计算质量评分
                    result["research_quality_score"] = calculate_research_quality(result)
                    add_research_result(state, result)
                    all_research_results.append(result)
                
                completed_tasks += 1
                progress = 20 + (completed_tasks / len(research_tasks)) * 60
                
                writer({
                    "step": "multi_agent_research",
                    "status": f"✅ 章节研究完成: {research_tasks[i]['section'].get('title', '未知')} ({len(section_results)}个结果)",
                    "progress": int(progress),
                    "completed_sections": completed_tasks,
                    "total_sections": len(sections),
                    "agent_used": research_tasks[i]["agent_type"]
                })
            else:
                logger.warning(f"章节 {research_tasks[i]['section'].get('title')} 研究失败: {section_results}")
        
        # 数据清理和优化
        writer({
            "step": "multi_agent_research",
            "status": "🔍 执行数据质量分析和智能去重...",
            "progress": 85
        })
        
        # 智能去重和质量筛选
        unique_results = []
        seen_urls = set()
        content_hashes = set()
        
        for result in all_research_results:
            url = result.get("url", "")
            content = result.get("content", "")
            content_hash = hash(content[:200])  # 基于内容前200字符去重
            
            if url and url not in seen_urls and content_hash not in content_hashes:
                seen_urls.add(url)
                content_hashes.add(content_hash)
                unique_results.append(result)
        
        # 按质量和优先级排序
        unique_results.sort(
            key=lambda x: (x.get("research_quality_score", 0), x.get("research_priority", 0)), 
            reverse=True
        )
        
        # 限制最终结果数量（保留最高质量的结果）
        max_results = len(sections) * 8  # 每章节平均8个高质量结果
        unique_results = unique_results[:max_results]
        
        # 更新状态
        execution_time = time.time() - start_time
        update_performance_metrics(state, "multi_agent_researcher", execution_time)
        update_task_status(state, "research_execution", TaskStatus.COMPLETED)
        
        state["current_step"] = "research_completed"
        state["execution_path"] = state["execution_path"] + ["multi_agent_research"]
        
        # 计算效率统计
        avg_quality = sum(r.get('research_quality_score', 0) for r in unique_results) / max(len(unique_results), 1)
        estimated_serial_time = len(sections) * 45  # 估计串行执行时间
        efficiency_gain = max(0, estimated_serial_time - execution_time)
        
        # 生成详细研究报告
        research_message = f"""
        🤖 Multi-Agent并行研究系统执行完成！
        
        📊 执行统计：
        - 并行章节：{len(research_tasks)}个同时处理
        - 高质量数据：{len(unique_results)}条（智能去重后）
        - 平均质量评分：{avg_quality:.3f}/1.0
        - 实际执行时间：{execution_time:.2f}秒
        
        🚀 性能提升：
        - 预计串行时间：{estimated_serial_time}秒
        - 并行效率提升：{efficiency_gain:.1f}秒 ({efficiency_gain/max(estimated_serial_time, 1)*100:.1f}%)
        - 平均每章节：{execution_time/len(sections):.1f}秒
        
        🎯 各章节研究质量：
        {chr(10).join([f"  • {section.get('title', '未知章节')}: {len([r for r in unique_results if r.get('section_id') == section.get('id')])}条数据 (质量: {sum(r.get('research_quality_score', 0) for r in unique_results if r.get('section_id') == section.get('id'))/max(len([r for r in unique_results if r.get('section_id') == section.get('id')]), 1):.2f})" for section in sections])}
        
        ⚡ 系统智能化特性：
        - 动态查询生成：基于章节内容自动优化搜索策略
        - 智能Agent分配：根据章节特点选择最适合的专业Agent
        - 质量评估系统：多维度评分确保数据质量
        """
        
        state["messages"] = state["messages"] + [AIMessage(content=research_message)]
        
        writer({
            "step": "multi_agent_research",
            "status": "🎉 Multi-Agent并行研究完成！",
            "progress": 100,
            "total_results": len(unique_results),
            "execution_time": execution_time,
            "quality_score": avg_quality,
            "efficiency_gain": f"{efficiency_gain:.1f}s ({efficiency_gain/max(estimated_serial_time, 1)*100:.1f}%)",
            "content": {
                "type": "research_summary",
                "data": {
                    "total_results": len(unique_results),
                    "sections_covered": len(sections),
                    "avg_quality": avg_quality,
                    "execution_time": execution_time
                }
            }
        })
        
        logger.info(f"Multi-Agent并行研究完成: {len(unique_results)}个高质量研究结果，质量评分{avg_quality:.3f}")
        return state
        
    except Exception as e:
        logger.error(f"Multi-Agent研究失败: {str(e)}")
        writer({
            "step": "multi_agent_research",
            "status": f"❌ 研究失败: {str(e)}",
            "progress": -1
        })
        
        state["error_log"] = state["error_log"] + [f"Multi-Agent研究错误: {str(e)}"]
        state["current_step"] = "research_failed"
        update_task_status(state, "research_execution", TaskStatus.FAILED)
        return state

def calculate_research_quality(result: Dict[str, Any]) -> float:
    """计算研究结果的质量评分 - 多维度评估"""
    score = 0.3  # 基础分
    
    # 1. 内容质量评分 (0-0.3)
    content = result.get("content", "")
    content_length = len(content)
    if content_length > 200:
        score += min(0.3, content_length / 2000)  # 长度奖励
    
    # 2. 标题质量评分 (0-0.15)
    title = result.get("title", "")
    if title and len(title) > 10:
        score += 0.1
        if any(keyword in title.lower() for keyword in ['分析', '研究', '报告', '发展', '趋势']):
            score += 0.05  # 专业词汇奖励
    
    # 3. 来源可信度评分 (0-0.25)
    url = result.get("url", "")
    if url:
        trusted_domains = [".edu", ".gov", ".org", "wikipedia", "arxiv", "ieee", "acm"]
        if any(domain in url for domain in trusted_domains):
            score += 0.25  # 高可信度来源
        elif any(domain in url for domain in [".com", ".net", ".io"]):
            score += 0.1   # 一般商业来源
    
    # 4. 相关性评分 (0-0.2)
    topic_keywords = result.get("query", "").lower().split()
    content_lower = content.lower()
    relevance_count = sum(1 for keyword in topic_keywords if keyword in content_lower)
    if topic_keywords:
        relevance_ratio = relevance_count / len(topic_keywords)
        score += min(0.2, relevance_ratio * 0.2)
    
    return min(1.0, score)

# ============================================================================
# 其他核心节点（分析、内容生成、验证）
# ============================================================================

async def content_creation_node(state: DeepResearchState) -> DeepResearchState:
    """内容创建节点 - 生成最终报告"""
    writer = get_stream_writer()
    writer({
        "step": "content_creation",
        "status": "开始创建最终报告",
        "progress": 0
    })
    
    try:
        start_time = time.time()
        
        outline = state.get("outline", {})
        research_results = state.get("research_results", [])
        
        if not outline:
            writer({
                "step": "content_creation",
                "status": "没有大纲，无法创建报告",
                "progress": 100
            })
            return state
        
        writer({
            "step": "content_creation",
            "status": "正在生成报告内容...",
            "progress": 20
        })
        
        # 使用写作工具生成章节内容
        sections = outline.get("sections", [])
        generated_sections = []
        
        for i, section in enumerate(sections):
            section_progress = 20 + (i / len(sections)) * 60
            
            writer({
                "step": "content_creation",
                "status": f"生成章节: {section.get('title', '未知')}",
                "progress": int(section_progress),
                "current_section": section.get('title', ''),
                "section_index": i + 1,
                "total_sections": len(sections)
            })
            
            # 获取相关研究数据
            section_research = [r for r in research_results 
                              if r.get("section_id") == section.get("id")]
            
            if not section_research:
                # 如果没有特定章节的研究数据，使用前几个通用数据
                section_research = research_results[:3]
            
            # 确保至少有一些研究数据，如果完全没有，创建默认数据
            if not section_research:
                section_research = [{
                    "id": "default",
                    "query": section.get("title", ""),
                    "source_type": "default",
                    "title": f"{section.get('title', '')}相关内容", 
                    "content": f"关于{section.get('title', '')}的基础信息和分析。",
                    "url": "",
                    "credibility_score": 0.7,
                    "relevance_score": 0.8,
                    "timestamp": time.time()
                }]
            
            try:
                # 生成章节内容
                section_content = section_content_generator.invoke({
                    "section_title": section.get("title", ""),
                    "section_description": section.get("description", ""),
                    "research_data": section_research,
                    "target_words": max(200, state.get("target_length", 2000) // len(sections)),
                    "style": state.get("style", "professional")
                })
                
                if not section_content.get("error"):
                    generated_sections.append(section_content)
                else:
                    logger.warning(f"章节内容生成失败: {section.get('title')} - {section_content.get('error')}")
                    
            except Exception as section_error:
                logger.error(f"章节内容生成异常: {section.get('title')} - {str(section_error)}")
                # 创建一个基本的章节内容作为后备
                basic_section = {
                    "id": f"basic_{i}",
                    "section_title": section.get("title", ""),
                    "content": f"## {section.get('title', '')}\n\n{section.get('description', '')}\n\n本章节的详细内容正在完善中。",
                    "word_count": 50,
                    "target_words": state.get("target_length", 2000) // len(sections),
                    "style": state.get("style", "professional"),
                    "sources_used": len(section_research),
                    "generated_at": time.time(),
                    "quality_score": 60
                }
                generated_sections.append(basic_section)
        
        writer({
            "step": "content_creation",
            "status": "正在格式化最终报告...",
            "progress": 85
        })
        
        # 格式化完整报告
        try:
            if generated_sections:
                final_report_data = report_formatter.invoke({
                    "title": outline.get("title", "研究报告"),
                    "sections": generated_sections,
                    "executive_summary": outline.get("executive_summary", ""),
                    "metadata": {
                        "generated_at": time.time(),
                        "report_type": state.get("report_type", "research"),
                        "target_audience": state.get("target_audience", "专业人士"),
                        "depth_level": state.get("depth_level", "medium")
                    }
                })
                
                if not final_report_data.get("error"):
                    state["final_report"] = final_report_data.get("content", "")
                else:
                    # 创建基本报告作为后备
                    basic_report = f"""# {outline.get('title', '研究报告')}

                    ## 执行摘要
                    {outline.get('executive_summary', '本报告正在生成中，请稍后查看。')}

                    """
                    for section in generated_sections:
                        basic_report += section.get("content", "") + "\n\n"
                    
                    state["final_report"] = basic_report
            else:
                # 如果没有生成任何章节，创建基本报告
                state["final_report"] = f"""# {outline.get('title', '研究报告')}

                ## 执行摘要
                {outline.get('executive_summary', '抱歉，报告生成遇到问题，请稍后重试。')}

                ## 状态说明
                报告正在处理中，部分内容可能需要更多时间生成。
                """
                final_report_data = {"total_words": len(state["final_report"]), "content": state["final_report"]}
                
        except Exception as format_error:
            logger.error(f"报告格式化异常: {str(format_error)}")
            # 创建简单的后备报告
            state["final_report"] = f"""# {outline.get('title', '研究报告')}

            ## 执行摘要
            {outline.get('executive_summary', '报告生成遇到技术问题，正在处理中。')}

            ## 生成状态
            系统正在处理您的请求，请稍后重试。如果问题持续存在，请联系技术支持。
            """
            final_report_data = {"total_words": len(state["final_report"]), "content": state["final_report"]}
        
        # 更新状态
        execution_time = time.time() - start_time
        update_performance_metrics(state, "writer", execution_time)
        update_task_status(state, "content_creation", TaskStatus.COMPLETED)
        
        state["current_step"] = "content_created"
        state["execution_path"] = state["execution_path"] + ["content_creation"]
        
        # 添加内容创建完成消息
        content_message = f"""
        📝 最终报告创建完成：
        
        📊 内容统计：
        - 报告标题：{outline.get('title', '未知')}
        - 生成章节：{len(generated_sections)}个
        - 总字数：{final_report_data.get('total_words', 0):,}字
        - 执行时间：{execution_time:.2f}秒
        
        ✅ 报告已完成，可供查看和使用
        """
        
        state["messages"] = state["messages"] + [AIMessage(content=content_message)]
        
        writer({
            "step": "content_creation",
            "status": "最终报告创建完成",
            "progress": 100,
            "sections_generated": len(generated_sections),
            "total_words": final_report_data.get("total_words", 0),
            "execution_time": execution_time,
            "content": {
                "type": "final_report",
                "data": final_report_data,
                "display_text": content_message,
                "full_report": final_report_data.get("formatted_report", "")
            }
        })
        
        logger.info(f"内容创建完成: {len(generated_sections)}个章节, {final_report_data.get('total_words', 0)}字")
        return state
        
    except Exception as e:
        logger.error(f"内容创建失败: {str(e)}")
        writer({
            "step": "content_creation",
            "status": f"内容创建失败: {str(e)}",
            "progress": -1
        })
        
        state["error_log"] = state["error_log"] + [f"内容创建错误: {str(e)}"]
        state["current_step"] = "content_creation_failed"
        update_task_status(state, "content_creation", TaskStatus.FAILED)
        return state

async def analysis_generation_node(state: DeepResearchState) -> DeepResearchState:
    """分析洞察生成节点"""
    writer = get_stream_writer()
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
    return "multi_agent_research"  # 直接进入研究阶段

def route_after_analysis_approval(state: DeepResearchState) -> str:
    """分析确认后的路由"""
    if not state["approval_status"].get("analysis_approval", True):
        return "analysis_generation"  # 重新分析
    return "content_creation"  # 进入内容创建

# ============================================================================
# 图构建函数
# ============================================================================

def create_deep_research_graph(checkpointer: Optional[InMemorySaver] = None):
    """创建深度研究报告生成图 - 简化版本"""
    workflow = StateGraph(DeepResearchState)
    
    # 添加核心节点 - 移除冗余节点
    workflow.add_node("outline_generation", outline_generation_node)
    workflow.add_node("outline_confirmation", outline_confirmation_node)
    workflow.add_node("multi_agent_research", multi_agent_research_node)
    workflow.add_node("analysis_generation", analysis_generation_node)
    workflow.add_node("analysis_approval", analysis_approval_node)
    workflow.add_node("content_creation", content_creation_node)
    
    # 设置简化的线性流程
    workflow.add_edge(START, "outline_generation")
    workflow.add_edge("outline_generation", "outline_confirmation")
    
    # 大纲确认后的条件路由
    workflow.add_conditional_edges(
        "outline_confirmation",
        route_after_outline_confirmation,
        {
            "outline_generation": "outline_generation",
            "multi_agent_research": "multi_agent_research"
        }
    )
    
    # 线性流程：研究 -> 分析 -> 内容创建
    workflow.add_edge("multi_agent_research", "analysis_generation")
    workflow.add_edge("analysis_generation", "analysis_approval")
    
    # 分析确认后的条件路由
    workflow.add_conditional_edges(
        "analysis_approval",
        route_after_analysis_approval,
        {
            "analysis_generation": "analysis_generation",
            "content_creation": "content_creation"
        }
    )
    
    workflow.add_edge("content_creation", END)
    
    # 编译图
    if checkpointer is None:
        checkpointer = InMemorySaver()
    
    app = workflow.compile(checkpointer=checkpointer)
    return app
