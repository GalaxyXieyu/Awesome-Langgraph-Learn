"""
核心图模块
高级交互式深度研究报告生成系统的主要工作流图
集成Multi-Agent协作、Human-in-loop交互和流式输出
"""

import json
import time
import asyncio
import uuid
import os
from typing import Dict, Any, List

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.types import interrupt
import logging

# 导入本地模块
from state import (
    DeepResearchState, ReportMode, TaskStatus, InteractionType,
    ReportOutline, ReportSection, ResearchResult,
    update_performance_metrics,
    update_task_status, add_user_interaction, add_node_output
)

# 导入子图模块
from subgraphs.deepresearch.graph import (
    create_intelligent_research_graph
)
# 导入标准化流式输出系统
from writer.core import create_stream_writer, create_workflow_processor

# 导入通用中断节点
from common import create_confirmation_node

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

# 编译子图（全局变量，避免重复编译）- 使用update子图
_intelligent_research_subgraph = None

def get_intelligent_research_subgraph():
    """获取智能研究子图实例"""
    global _intelligent_research_subgraph
    if _intelligent_research_subgraph is None:
        workflow = create_intelligent_research_graph()
        _intelligent_research_subgraph = workflow.compile()
    return _intelligent_research_subgraph

def create_update_subgraph_state(state: DeepResearchState) -> Dict[str, Any]:
    """
    创建update子图的初始状态
    将主图状态转换为update子图所需的状态格式
    """
    outline = state.get("outline", {})
    sections = outline.get("sections", []) if outline else []

    # 转换章节格式，确保每个章节都有id
    formatted_sections = []
    for i, section in enumerate(sections):
        formatted_section = {
            "id": section.get("id", f"section_{i}"),
            "title": section.get("title", f"章节 {i+1}"),
            "description": section.get("description", ""),
            "key_points": section.get("key_points", []),
            "research_queries": section.get("research_queries", [])
        }
        formatted_sections.append(formatted_section)
    # 创建update子图状态
    subgraph_state = {
        "messages": [],
        "user_input": f"请为主题'{state.get('topic', '')}'生成深度研究报告",
        "topic": state.get("topic", ""),
        "mode": "interactive",
        "sections": formatted_sections,
        "current_section_index": 0,
        "research_results": {},
        "writing_results": {},
        "polishing_results": {},
        "final_report": {},
        "execution_path": [],
        "iteration_count": 0,
        "max_iterations": 10,
        "next_action": "research",
        "task_completed": False,
        "error_log": [],
        "section_attempts": {}
    }

    return subgraph_state

async def report_generation(state: DeepResearchState) -> DeepResearchState:
    """
    调用智能研究子图 - 统一流式输出

    这个函数实现了主图和子图之间的状态转换，智能识别Agent工作流程
    """
    # 创建工作流程处理器 - 不使用模板，保持简洁
    processor = create_workflow_processor("intelligent_research", "深度研究报告生成")
    processor.writer.processing("开始深度研究报告生成")

    # 获取子图实例
    subgraph = get_intelligent_research_subgraph()
    subgraph_input = create_update_subgraph_state(state)

    processor.writer.processing(
        "准备研究计划",
        sections_count=len(subgraph_input.get("sections", []))
    )
    
    # 用于收集最终结果的变量
    subgraph_output = {}
    updated_sections = []
    new_research_results = []
    
    # 流式调用子图，使用增强的processor统一处理嵌套流式输出
    async for chunk in subgraph.astream(subgraph_input, stream_mode=["updates", "messages"], subgraphs=True):
        # 使用增强的processor统一处理所有类型的chunk
        processor.process_chunk(chunk)
        # 同时收集实际数据用于状态更新，处理嵌套结构
        if isinstance(chunk, tuple):
            if len(chunk) >= 3:
                # 嵌套子图格式: (('subgraph_id',), 'updates', data)
                _, chunk_type, chunk_data = chunk[0], chunk[1], chunk[2]
            elif len(chunk) >= 2:
                # 普通格式: ('updates', data)
                chunk_type, chunk_data = chunk[0], chunk[1]
            else:
                continue
            
            if chunk_type == "updates" and isinstance(chunk_data, dict):
                for node_output in chunk_data.values():
                    if node_output and isinstance(node_output, dict):
                        subgraph_output.update(node_output)
                        
                        # 收集章节更新
                        if "sections" in node_output:
                            sections_data = node_output["sections"]
                            if isinstance(sections_data, list):
                                for section_data in sections_data:
                                    updated_section = {
                                        "title": section_data.get("title", ""),
                                        "content": section_data.get("content", ""),
                                        "word_count": section_data.get("word_count", 0),
                                        "status": "completed"
                                    }
                                    if not any(s.get("title") == updated_section["title"] for s in updated_sections):
                                        updated_sections.append(updated_section)
                        
                        # 收集研究结果
                        if "research_results" in node_output:
                            research_results = node_output["research_results"]
                            if isinstance(research_results, dict):
                                for research_data in research_results.values():
                                    research_result = ResearchResult(
                                        id=str(uuid.uuid4()),
                                        query=f"研究章节: {research_data.get('title', '')}",
                                        source_type="subgraph",
                                        title=research_data.get("title", ""),
                                        content=research_data.get("content", ""),
                                        url="",
                                        relevance_score=0.9,
                                        timestamp=research_data.get("timestamp", time.time()),
                                        section_id=research_data.get("id", "")
                                    )
                                    if not any(r.title == research_result.title for r in new_research_results):
                                        new_research_results.append(research_result)
    # 处理最终结果
    if subgraph_output.get("final_report"):

        final_report = subgraph_output["final_report"]
        final_sections_data = final_report.get("sections", [])

        # 确保所有章节都被处理
        for section_data in final_sections_data:
            updated_section = {
                "title": section_data.get("title", ""),
                "content": section_data.get("content", ""),
                "word_count": section_data.get("word_count", 0),
                "status": "completed"
            }
            if not any(s.get("title") == updated_section["title"] for s in updated_sections):
                updated_sections.append(updated_section)

        # 更新状态
        updated_state = {
            **state,
            "sections": updated_sections,
            "research_results": state.get("research_results", []) + new_research_results,
            "content_creation_completed": True,
            "completed_sections_count": len(updated_sections),
            "performance_metrics": {
                **state.get("performance_metrics", {}),
                "sections_completed": len(updated_sections),
                "total_sections": len(updated_sections),
                "total_words": final_report.get("total_words", 0)
            }
        }

        processor.writer.final_result(
            f"深度研究报告生成完成",
            {
                "sections_count": len(updated_sections),
                "total_words": final_report.get("total_words", 0),
                "research_findings": len(new_research_results)
            }
        )
        return updated_state
    else:
        # 返回部分结果
        updated_state = {
            **state,
            "sections": updated_sections,
            "research_results": state.get("research_results", []) + new_research_results,
            "content_creation_completed": len(updated_sections) > 0,
            "completed_sections_count": len(updated_sections),
            "performance_metrics": {
                **state.get("performance_metrics", {}),
                "sections_completed": len(updated_sections),
                "total_sections": len(updated_sections),
                "total_words": sum(section.get("word_count", 0) for section in updated_sections)
            }
        }
        
        processor.writer.processing(
            "部分内容生成完成",
            sections_count=len(updated_sections),
            is_partial=True
        )
        return updated_state

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
    智能章节处理节点 - 使用update子图进行整体研究和写作

    这个节点的作用：
    1. 获取大纲中的所有章节
    2. 调用update子图进行智能研究和写作
    3. 子图内部处理：智能Supervisor → 研究 → 写作 → 整合
    4. 返回完整的研究报告
    """
    # 使用扁平化Writer - 不使用模板，保持简洁
    writer = create_stream_writer("intelligent_section_processing", "智能章节处理")
    writer.processing("开始智能研究处理（使用update子图）")

    try:
        outline = state.get("outline", {})
        sections = outline.get("sections", []) if outline else []

        if not sections:
            writer.error("没有可用的章节信息", "NoSectionsError")
            return state

        writer.processing(
            f"准备使用智能Supervisor处理 {len(sections)} 个章节",
            total_sections=len(sections)
        )

        # 调用update子图进行整体处理
        writer.processing("启动智能研究子图")

        # 直接调用子图（按照官方文档的方式）
        updated_state = await call_intelligent_research_subgraph(state)

        # 检查处理结果
        if updated_state.get("content_creation_completed"):
            completed_sections = updated_state.get("sections", [])
            total_words = updated_state.get("performance_metrics", {}).get("total_words", 0)

            writer.processing(
                "智能研究完成",
                completed_sections=len(completed_sections),
                total_sections=len(sections),
                total_words=total_words
            )

            logger.info(f"智能研究完成: {len(completed_sections)} 个章节, 总字数: {total_words}")
            return updated_state
        else:
            writer.processing("子图处理未完成，返回原状态")
            logger.warning("子图处理未完成")
            return state

    except Exception as e:
        logger.error(f"智能章节处理失败: {str(e)}")
        writer.error(f"章节处理失败: {str(e)}", "IntelligentSectionProcessingError")

        state["error_log"] = state.get("error_log", []) + [f"智能章节处理错误: {str(e)}"]
        return state

# ============================================================================
# 大纲生成节点
# ============================================================================

async def outline_generation(state: DeepResearchState, config=None) -> DeepResearchState:
    """大纲生成节点 - 支持流式输出汇总"""
    # 使用扁平化处理器 - 不使用模板，保持简洁
    processor = create_workflow_processor("outline_generation", "大纲生成器")
    processor.writer.processing("开始生成深度研究大纲")

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
        
        processor.writer.processing("正在生成专业大纲...")

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
                
                processor.writer.content(
                    str(chunk),
                    current_outline=current_outline_display,
                    chunk_count=chunk_count
                )

                # 如果大纲基本完整，提前显示
                if hasattr(chunk, 'title') and hasattr(chunk, 'sections') and len(chunk.sections) >= 3:
                    processor.writer.processing(
                        "大纲结构已生成，正在完善细节...",
                        partial_outline=chunk,
                        streaming_content=current_outline_display
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
        
        add_node_output(
            state, 
            "outline_generation", 
            outline_data,  # 只存储原始累计的content
            execution_time=execution_time,
            word_count=len(outline_data),
            status="completed"
        )
        
        processor.writer.processing(
            "深度研究大纲生成完成",
            sections_count=len(outline_dict.get("sections", [])),
            execution_time=execution_time,
            outline_data=outline_dict,
            display_text=outline_data
        )
        
        from writer.config import get_writer_config
        config = get_writer_config()
        if not config.is_node_streaming_enabled("outline_generation"):
            from langgraph.config import get_stream_writer
            writer = get_stream_writer()
            if writer:
                aggregated_message = {
                    "message_type": "node_output_complete",
                    "content": outline_data,  # 🔥 只发送最原始的累计content
                    "node": "outline_generation",
                    "timestamp": time.time(),
                    "duration": execution_time,
                    "word_count": len(outline_data)
                }
                writer(aggregated_message)
        return state
        
    except Exception as e:
        logger.error(f"大纲生成失败: {str(e)}")
        processor.writer.error(f"大纲生成失败: {str(e)}", "OutlineGenerationError")
        
        # 错误情况也记录到 node_outputs
        add_node_output(
            state, 
            "outline_generation", 
            f"错误：{str(e)}",
            status="failed",
            error=str(e)
        )
        
        state["error_log"] = state["error_log"] + [f"大纲生成错误: {str(e)}"]
        state["current_step"] = "outline_generation_failed"
        update_task_status(state, "outline_generation", TaskStatus.FAILED)
        return state

# ============================================================================
# 交互确认节点 - 使用通用中断节点
# ============================================================================

def create_interaction_node_legacy(interaction_type: InteractionType):
    """创建交互确认节点的工厂函数 - 使用统一的中断机制"""

    async def interaction_node(state: DeepResearchState, config=None) -> DeepResearchState:
        """通用交互确认节点 - 统一中断处理格式"""
        # 使用扁平化处理器
        processor = create_workflow_processor(f"interaction_{interaction_type.value}", f"{interaction_type.value}_交互")
        processor.writer.processing(f"开始{interaction_type.value}确认")

        interaction_config = get_interaction_config(interaction_type)
        mode = state["mode"]

        # Copilot模式自动通过
        if mode == ReportMode.COPILOT:
            processor.writer.processing("Copilot模式自动通过")

            state["approval_status"][interaction_type.value] = True
            state["user_feedback"][interaction_type.value] = {"approved": True, "auto": True}

            processor.writer.processing(f"Copilot模式自动通过", auto_approved=True)

            state["messages"] = state["messages"] + [
                AIMessage(content=f"🤖 Copilot模式：{interaction_config['copilot_message']}")
            ]

            return state

        # Interactive模式：使用统一的中断机制
        processor.writer.processing("准备用户确认...")

        # 构建中断请求，格式与工具包装器一致
        message_content = format_interaction_message(state, interaction_type, interaction_config)

        # 创建标准化的中断请求
        request: HumanInterrupt = {
            "action_request": {
                "action": f"confirm_{interaction_type.value}",
                "args": {
                    "interaction_type": interaction_type.value,
                    "title": interaction_config["title"],
                    "message": message_content,
                    "options": interaction_config["options"]
                }
            },
            "config": {
                "allow_accept": True,
                "allow_edit": False,  # 确认节点通常不允许编辑
                "allow_respond": True
            },
            "description": f"请确认{interaction_config['title']}：\n\n{message_content}\n\n可选操作：\n- 输入 'yes' 确认通过\n- 输入 'no' 拒绝\n- 输入 'response' 提供自定义反馈",
        }

        processor.writer.processing("等待用户确认...")

        # 调用统一的中断函数
        response = types.interrupt(request)

        processor.writer.processing("处理用户响应...")

        # 标准化响应处理
        if response["type"] == "accept":
            # 用户确认通过
            approved = True
            user_feedback = {"approved": True, "type": "accept"}
            result_message = f"✅ {interaction_config['title']}：确认通过"

        elif response["type"] == "reject":
            # 用户拒绝
            approved = False
            user_feedback = {"approved": False, "type": "reject"}
            result_message = f"❌ {interaction_config['title']}：被拒绝"

        elif response["type"] == "response":
            # 用户提供自定义反馈
            user_feedback_content = response.get("args", "")
            approved = True  # 默认认为提供反馈就是通过
            user_feedback = {"approved": True, "type": "response", "content": user_feedback_content}
            result_message = f"💬 {interaction_config['title']}：用户反馈 - {user_feedback_content}"

        else:
            # 未知响应类型，默认拒绝
            approved = False
            user_feedback = {"approved": False, "type": "unknown", "raw_response": response}
            result_message = f"❓ {interaction_config['title']}：未知响应，默认拒绝"

        # 更新状态
        state["approval_status"][interaction_type.value] = approved
        state["user_feedback"][interaction_type.value] = user_feedback

        # 记录交互历史
        add_user_interaction(state, interaction_type.value, user_feedback)

        # 添加确认消息
        state["messages"] = state["messages"] + [AIMessage(content=result_message)]

        processor.writer.processing(
            result_message,
            approved=approved,
            user_feedback=user_feedback,
            interaction_type=interaction_type.value
        )

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

# ============================================================================
# 使用通用中断节点创建具体的交互节点
# ============================================================================

def get_outline_data(state: DeepResearchState) -> Dict[str, Any]:
    """获取大纲确认所需的数据"""
    outline = state.get("outline", {})
    sections_text = "\n".join([
        f"  {i+1}. {section.get('title', '未知章节')}\n     {section.get('description', '无描述')}"
        for i, section in enumerate(outline.get("sections", []))
    ])

    return {
        "title": outline.get('title', '未知标题'),
        "executive_summary": outline.get('executive_summary', '无摘要'),
        "sections_text": sections_text,
        "methodology": outline.get('methodology', '未指定'),
        "estimated_length": outline.get('estimated_length', 0),
        "target_audience": outline.get('target_audience', '未知')
    }

def process_outline_confirmation(state: DeepResearchState, response_data: Dict[str, Any]) -> DeepResearchState:
    """处理大纲确认响应"""
    # 更新确认状态
    state["approval_status"]["outline_confirmation"] = response_data.get("approved", False)
    state["user_feedback"]["outline_confirmation"] = response_data

    # 记录交互历史
    add_user_interaction(state, "outline_confirmation", response_data)

    return state

# 创建大纲确认节点
_outline_confirmation_base_node = create_confirmation_node(
    node_name="outline_confirmation",
    title="大纲确认",
    message_template="""请确认以下深度研究报告大纲：

    标题：{title}

    摘要：{executive_summary}

    章节结构：
    {sections_text}

    研究方法：{methodology}
    预估字数：{estimated_length:,}字
    目标读者：{target_audience}""",
    get_data_func=get_outline_data
)

async def outline_confirmation(state: DeepResearchState, config=None) -> DeepResearchState:
    """带有自定义处理的大纲确认节点"""
    # 调用基础的确认节点
    result_state = await _outline_confirmation_base_node(state, config)

    # 应用自定义处理
    if "confirmations" in result_state and "outline_confirmation" in result_state["confirmations"]:
        confirmation_data = result_state["confirmations"]["outline_confirmation"]
        result_state = process_outline_confirmation(result_state, confirmation_data)

    return result_state

# ============================================================================
# 路由函数
# ============================================================================

def route_after_outline_confirmation(state: DeepResearchState) -> str:
    """大纲确认后的路由 - 适配通用中断节点"""
    # 检查通用中断节点的确认状态
    confirmations = state.get("confirmations", {})
    outline_confirmation = confirmations.get("outline_confirmation", {})

    # 如果用户拒绝或没有确认，重新生成大纲
    if not outline_confirmation.get("approved", True):
        return "outline_generation"

    # 确认通过，进入内容创建
    return "report_generation"

# ============================================================================
# 图构建函数
# ============================================================================

def create_deep_research_graph():
    """创建深度研究报告生成图 - 集成智能章节研究子图"""
    workflow = StateGraph(DeepResearchState)

    # 添加简化的核心节点 - 集成智能章节研究子图
    workflow.add_node("outline_generation", outline_generation)
    workflow.add_node("outline_confirmation", outline_confirmation)
    workflow.add_node("report_generation", report_generation)
    # 设置简化的流程：大纲生成 → 大纲确认 → 内容创建
    workflow.add_edge(START, "outline_generation")
    workflow.add_edge("outline_generation", "outline_confirmation")

    # 大纲确认后的条件路由
    workflow.add_conditional_edges(
        "outline_confirmation",
        route_after_outline_confirmation,
        {
            "outline_generation": "outline_generation",
            "report_generation": "report_generation"
        }
    )
    
    workflow.add_edge("report_generation", END)
    
    return workflow
