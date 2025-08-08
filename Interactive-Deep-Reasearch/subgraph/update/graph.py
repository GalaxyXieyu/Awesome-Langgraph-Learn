"""
基于LangGraph的智能研究系统
正确使用LangGraph架构：StateGraph + 节点 + 条件路由 + 流式输出
"""

import json
import time
import asyncio
from typing import Dict, Any, List, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
import logging

# 导入模块化组件
from tools import ALL_RESEARCH_TOOLS
from context_builder import build_supervisor_context, determine_next_action_by_state
from prompts import get_supervisor_prompt, get_researcher_prompt, get_writer_prompt

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 状态定义 - LangGraph核心
# ============================================================================

class IntelligentResearchState(TypedDict):
    """智能研究系统状态"""
    messages: Annotated[List, add_messages]  # 消息历史
    user_input: str  # 用户输入
    topic: str  # 研究主题
    sections: List[Dict[str, Any]]  # 章节列表
    current_section_index: int  # 当前处理的章节索引
    research_results: Dict[str, Any]  # 研究结果
    writing_results: Dict[str, Any]  # 写作结果
    polishing_results: Dict[str, Any]  # 润色结果
    final_report: Dict[str, Any]  # 最终报告
    execution_path: List[str]  # 执行路径
    iteration_count: int  # 迭代次数
    max_iterations: int  # 最大迭代次数
    next_action: str  # 下一步行动
    task_completed: bool  # 任务完成标志
    error_log: List[str]  # 错误日志
    section_attempts: Dict[str, Dict[str, int]]  # 每个章节的尝试次数记录 {"section_id": {"research": 2, "writing": 1}}



# ============================================================================
# LLM配置
# ============================================================================

def create_llm():
    """创建LLM实例"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
    )

# ============================================================================
# Agent创建 - 专业化Agent
# ============================================================================

def create_research_agents():
    """创建专业化的研究Agent"""
    llm = create_llm()
    
    # 研究员Agent
    researcher_agent = create_react_agent(
        llm,
        tools=ALL_RESEARCH_TOOLS,
        prompt=get_researcher_prompt()
    )
    
    # 写作员Agent - 也可以使用工具获取更多数据
    writer_agent = create_react_agent(
        llm,
        tools=ALL_RESEARCH_TOOLS,  # 写作员也可以调用工具补充数据
        prompt=get_writer_prompt()
    )
    
    return {
        "researcher": researcher_agent,
        "writer": writer_agent
    }

# ============================================================================
# 节点函数 - LangGraph核心组件
# ============================================================================

async def supervisor_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """智能Supervisor节点 - 使用LLM进行智能决策和质量评估"""

    writer = get_stream_writer()

    writer({"step": "supervisor", "status": "开始智能调度分析", "progress": 0})

    llm = create_llm()

    # 使用模块化的上下文构建
    input_data = build_supervisor_context(state)

    # 构建Supervisor的智能决策提示
    supervisor_prompt = get_supervisor_prompt()

    writer({"step": "supervisor", "status": "正在进行智能分析...", "progress": 30})

    formatted_messages = supervisor_prompt.format_messages(**input_data)
    # 流式调用LLM进行智能决策
    full_response = ""
    chunk_count = 0
    async for chunk in llm.astream(formatted_messages, config=config):
        if hasattr(chunk, 'content') and chunk.content:
            content = str(chunk.content)
            full_response += content
            chunk_count += 1
    writer({"step": "supervisor", "status": "解析决策结果...", "content": full_response, "progress": 85})
    import re
    try:
        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', full_response, re.DOTALL)
        decision_json = None
        for json_str in json_matches:
            # 清理JSON字符串
            cleaned_json = json_str.strip()
            # 移除可能的markdown代码块标记
            cleaned_json = re.sub(r'^```json\s*', '', cleaned_json)
            cleaned_json = re.sub(r'\s*```$', '', cleaned_json)

            decision_json = json.loads(cleaned_json)
            break

        if decision_json:
            # 清理JSON键名，处理可能包含换行符和空格的键
            cleaned_json = {}
            for key, value in decision_json.items():
                # 清理键名：移除换行符、制表符和多余空格
                clean_key = key.strip().replace('\n', '').replace('\t', '').replace(' ', '')
                cleaned_json[clean_key] = value

            # 使用清理后的键来获取值
            next_action = cleaned_json.get("action", "integration")
            reasoning = cleaned_json.get("reasoning", "智能分析决策")
            quality_feedback = cleaned_json.get("quality_feedback", "")
            confidence = cleaned_json.get("confidence", 0.7)
            target_section = cleaned_json.get("target_section", "")
        else:
            raise ValueError("无法解析JSON")
    except Exception as parse_error:
        # JSON解析失败，使用备用逻辑
        logger.error(f"JSON解析失败: {str(parse_error)}")
        next_action, reasoning = determine_next_action_by_state(state)
        quality_feedback = "基于状态逻辑的决策"
        confidence = 0.6
        target_section = ""

    # 获取当前进度信息
    sections = state.get("sections", [])
    current_index = state.get("current_section_index", 0)
    research_results = state.get("research_results", {})
    writing_results = state.get("writing_results", {})

    # 全局完成检查 - 检查是否所有章节都有研究和写作结果
    all_sections_completed = True
    for section in sections:
        section_id = section.get("id", "")
        has_research = section_id in research_results and research_results[section_id].get("content", "").strip() != ""
        has_writing = section_id in writing_results and writing_results[section_id].get("content", "").strip() != ""
        if not (has_research and has_writing):
            all_sections_completed = False
            break

    if all_sections_completed and next_action != "integration":
        logger.info("🎉 检测到所有章节都已完成，强制进入integration")
        next_action = "integration"
        reasoning = "所有章节的研究和写作都已完成，开始最终整合"

    # 处理章节索引更新和目标章节设置
    if next_action == "move_to_next_section":
        new_index = current_index + 1
        state["current_section_index"] = new_index
        # 检查是否超出章节范围
        if new_index >= len(sections):
            logger.info("🎉 章节索引超出范围，所有章节已完成，进入integration")
            next_action = "integration"
            reasoning = "所有章节处理完成，开始最终整合"
        else:
            next_action = "research"  # 移动到下一章节后开始研究
            reasoning = f"已从第{current_index + 1}章节移动到第{new_index + 1}章节，开始新章节研究"
        current_index = new_index  # 更新本地变量用于显示
    elif target_section and target_section != "":
        # 如果Supervisor指定了目标章节，找到对应的索引
        target_index = None
        for i, section in enumerate(sections):
            if section.get("id", "") == target_section:
                target_index = i
                break

        if target_index is not None and target_index != current_index:
            logger.info(f"🎯 Supervisor指定目标章节: {target_section}, 更新索引 {current_index} → {target_index}")
            state["current_section_index"] = target_index
            current_index = target_index
            reasoning = f"根据Supervisor指示，切换到目标章节: {sections[target_index].get('title', '')}"

    # 更新状态
    state["next_action"] = next_action
    state["supervisor_reasoning"] = reasoning
    state["quality_feedback"] = quality_feedback
    state["supervisor_confidence"] = confidence
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["execution_path"] = state.get("execution_path", []) + ["intelligent_supervisor"]

    # 添加Supervisor的智能分析消息
    supervisor_message = f"""
    🧠 智能调度分析完成：
    - 决策：{next_action}
    - 理由：{reasoning}
    - 质量反馈：{quality_feedback}
    - 置信度：{confidence:.1%}
    - 当前进度：{current_index}/{len(sections)}章节
    """

    state["messages"] = state.get("messages", []) + [
        AIMessage(content=supervisor_message)
    ]
    return state

async def research_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """研究节点 - 执行章节研究"""
    writer = get_stream_writer()
    try:
        sections = state.get("sections", [])
        current_index = state.get("current_section_index", 0)

        logger.info(f"🔍 Research节点 - 当前章节索引: {current_index}, 总章节数: {len(sections)}")

        if current_index >= len(sections):
            logger.info("📝 所有章节已处理完成，跳过research节点")
            return state

        current_section = sections[current_index]
        section_id = current_section.get("id", "")
        title = current_section.get("title", "")
        description = current_section.get("description", "")

        logger.info(f"📖 开始处理章节: {title} (ID: {section_id})")
        
        # 记录研究尝试次数
        section_attempts = state.get("section_attempts", {})
        if section_id not in section_attempts:
            section_attempts[section_id] = {"research": 0, "writing": 0}
        section_attempts[section_id]["research"] += 1
        state["section_attempts"] = section_attempts

        current_attempt = section_attempts[section_id]["research"]
        writer({"step": "research", "status": f"开始研究: {title} (第{current_attempt}次尝试)", "progress": 0})

        # 创建研究Agent
        agents = create_research_agents()
        researcher = agents["researcher"]
        
        # 构建研究任务
        research_task = f"""
        请深度研究以下章节：
        
        章节标题：{title}
        章节描述：{description}
        
        研究要求：
        1. 使用合适的工具获取相关数据
        2. 如果数据不足，主动使用多个工具补充
        3. 提供详细的分析报告
        """
        
        writer({"step": "research", "status": f"Agent开始研究: {title}", "progress": 30})
        
        # Agent执行研究
        agent_input = {"messages": [HumanMessage(content=research_task)]}
        
        # 流式执行研究 - 使用updates模式获取结构化结果
        full_response = ""
        final_agent_message = None

        try:
            async for chunk in researcher.astream(agent_input, stream_mode="updates"):
                # 处理agent的消息
                if 'agent' in chunk and 'messages' in chunk['agent']:
                    messages = chunk['agent']['messages']
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            content = str(message.content)
                            if content.strip():
                                # 显示流式内容（截断显示）
                                writer({
                                    "step": "research",
                                    "status": f"Agent研究中: {title}",
                                    "progress": 60,
                                    "streaming_content": content[:200] + "..." if len(content) > 200 else content
                                })
                                # 保存最后一条Agent消息作为最终结果
                                final_agent_message = message

                # 处理工具调用结果（可选显示）
                elif 'tools' in chunk:
                    writer({
                        "step": "research",
                        "status": f"工具调用中: {title}",
                        "progress": 50
                    })

            # 使用最终的Agent消息作为研究结果
            if final_agent_message and hasattr(final_agent_message, 'content'):
                full_response = str(final_agent_message.content)
            else:
                full_response = "研究完成，但未获取到最终结果"
        
        except Exception as e:
            logger.error(f"Agent流式执行失败: {e}")
            # 如果流式执行失败，尝试普通执行
            try:
                result = await researcher.ainvoke(agent_input)
                if hasattr(result, 'content'):
                    full_response = str(result.content)
                elif isinstance(result, dict) and 'messages' in result:
                    messages = result['messages']
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            full_response += str(msg.content)
            except Exception as e2:
                logger.error(f"Agent普通执行也失败: {e2}")
                full_response = f"研究执行失败: {str(e2)}"
        
        writer({"step": "research", "status": f"研究完成: {title}", "content": full_response, "progress": 100})
        # 保存研究结果
        research_results = state.get("research_results", {})
        research_results[section_id] = {
            "title": title,
            "content": full_response,
            "timestamp": time.time()
        }
        state["research_results"] = research_results
        state["execution_path"] = state.get("execution_path", []) + ["research"]
        
        writer({
            "step": "research",
            "status": f"研究完成: {title}",
            "progress": 100,
            "result_length": len(full_response)
        })
        
        logger.info(f"研究完成: {title}")
        return state
        
    except Exception as e:
        logger.error(f"研究失败: {e}")
        state["error_log"] = state.get("error_log", []) + [f"研究错误: {e}"]
        return state

async def writing_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """写作节点 - 基于研究结果写作"""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = lambda _: None
    
    try:
        sections = state.get("sections", [])
        current_index = state.get("current_section_index", 0)
        research_results = state.get("research_results", {})

        logger.info(f"✍️ Writing节点 - 当前章节索引: {current_index}, 总章节数: {len(sections)}")

        if current_index >= len(sections):
            logger.info("📝 所有章节已处理完成，跳过writing节点")
            return state

        current_section = sections[current_index]
        section_id = current_section.get("id", "")
        title = current_section.get("title", "")

        logger.info(f"📝 开始写作章节: {title} (ID: {section_id})")
        
        # 记录写作尝试次数
        section_attempts = state.get("section_attempts", {})
        if section_id not in section_attempts:
            section_attempts[section_id] = {"research": 0, "writing": 0}
        section_attempts[section_id]["writing"] += 1
        state["section_attempts"] = section_attempts

        current_attempt = section_attempts[section_id]["writing"]

        # 获取研究数据
        research_data = research_results.get(section_id, {})
        research_content = research_data.get("content", "")

        writer({"step": "writing", "status": f"开始写作: {title} (第{current_attempt}次尝试)", "progress": 0})

        # 创建写作Agent
        agents = create_research_agents()
        writer_agent = agents["writer"]
        
        # 获取其他章节的研究结果作为参考
        all_research_data = ""
        for sec_id, research_data in research_results.items():
            if sec_id != section_id:  # 排除当前章节
                all_research_data += f"\n参考章节 {research_data.get('title', '')}: {research_data.get('content', '')[:200]}...\n"

        # 构建写作任务
        writing_task = f"""
        请基于以下信息，撰写高质量的章节内容：

        当前章节标题：{title}
        当前章节研究数据：
        {research_content}

        其他章节研究数据（供参考）：
        {all_research_data}

        要求：
        1. 专注于当前章节主题
        2. 如果研究数据不足，可以使用工具获取更多信息
        3. 确保内容充实，数据支撑充分
        4. 保持与其他章节的逻辑连贯性
        """
        
        writer({"step": "writing", "status": f"Agent开始写作: {title}", "progress": 30})
        
        # Agent执行写作
        agent_input = {"messages": [HumanMessage(content=writing_task)]}
        
        # 流式执行写作 - 使用updates模式获取结构化结果
        full_response = ""
        final_agent_message = None

        try:
            async for chunk in writer_agent.astream(agent_input, stream_mode="updates"):
                # 处理agent的消息
                if 'agent' in chunk and 'messages' in chunk['agent']:
                    messages = chunk['agent']['messages']
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            content = str(message.content)
                            if content.strip():
                                # 显示流式内容（截断显示）
                                writer({
                                    "step": "writing",
                                    "status": f"Agent写作中: {title}",
                                    "progress": 60,
                                    "streaming_content": content[:200] + "..." if len(content) > 200 else content
                                })
                                # 保存最后一条Agent消息作为最终结果
                                final_agent_message = message

                # 处理工具调用结果（可选显示）
                elif 'tools' in chunk:
                    writer({
                        "step": "writing",
                        "status": f"工具调用中: {title}",
                        "progress": 50
                    })

            # 使用最终的Agent消息作为写作结果
            if final_agent_message and hasattr(final_agent_message, 'content'):
                full_response = str(final_agent_message.content)
            else:
                full_response = "写作完成，但未获取到最终结果"
        
        except Exception as e:
            logger.error(f"写作Agent流式执行失败: {e}")
            # 如果流式执行失败，尝试普通执行
            try:
                result = await writer_agent.ainvoke(agent_input)
                if hasattr(result, 'content'):
                    full_response = str(result.content)
                elif isinstance(result, dict) and 'messages' in result:
                    messages = result['messages']
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            full_response += str(msg.content)
            except Exception as e2:
                logger.error(f"写作Agent普通执行也失败: {e2}")
                full_response = f"写作执行失败: {str(e2)}"
        
        # 保存写作结果
        writing_results = state.get("writing_results", {})
        writing_results[section_id] = {
            "title": title,
            "content": full_response,
            "word_count": len(full_response.split()),
            "timestamp": time.time()
        }
        state["writing_results"] = writing_results
        state["execution_path"] = state.get("execution_path", []) + ["writing"]
        
        writer({
            "step": "writing",
            "status": f"写作完成: {title}",
            "progress": 100,
            "word_count": len(full_response.split())
        })
        
        logger.info(f"写作完成: {title}")
        return state
        
    except Exception as e:
        logger.error(f"写作失败: {e}")
        state["error_log"] = state.get("error_log", []) + [f"写作错误: {e}"]
        return state

async def integration_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """整合节点 - 生成最终报告"""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = lambda _: None

    try:
        writer({"step": "integration", "status": "开始整合最终报告", "progress": 0})

        topic = state.get("topic", "")
        writing_results = state.get("writing_results", {})
        sections = state.get("sections", [])

        # 构建最终报告
        final_sections = []
        total_words = 0

        for section in sections:
            section_id = section.get("id", "")
            if section_id in writing_results:
                section_data = writing_results[section_id]
                final_sections.append(section_data)
                total_words += section_data.get("word_count", 0)

        final_report = {
            "title": f"{topic} - 智能研究报告",
            "topic": topic,
            "sections": final_sections,
            "total_sections": len(final_sections),
            "total_words": total_words,
            "generation_method": "langgraph_intelligent_research",
            "execution_path": state.get("execution_path", []),
            "generation_timestamp": time.time()
        }

        state["final_report"] = final_report
        state["task_completed"] = True
        state["execution_path"] = state.get("execution_path", []) + ["integration"]

        writer({
            "step": "integration",
            "status": "报告整合完成",
            "progress": 100,
            "total_sections": len(final_sections),
            "total_words": total_words
        })

        logger.info(f"报告整合完成: {len(final_sections)}个章节, {total_words}字")
        return state

    except Exception as e:
        logger.error(f"整合失败: {e}")
        state["error_log"] = state.get("error_log", []) + [f"整合错误: {e}"]
        state["task_completed"] = True  # 即使失败也标记完成
        return state

# ============================================================================
# 路由函数 - LangGraph条件路由
# ============================================================================

def route_after_intelligent_supervisor(state: IntelligentResearchState) -> str:
    """智能Supervisor后的路由决策"""
    next_action = state.get("next_action", "integration")

    # 检查是否超过最大迭代次数
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)

    if iteration_count >= max_iterations:
        logger.warning(f"达到最大迭代次数 {max_iterations}，强制进入整合阶段")
        return "integration"

    if next_action == "research":
        return "research"
    elif next_action == "writing":
        return "writing"
    elif next_action == "quality_check":
        return "intelligent_supervisor"  # 回到supervisor进行更详细分析
    else:
        return "integration"

def route_after_research(state: IntelligentResearchState) -> str:
    """研究后的路由决策 - 回到智能supervisor"""
    return "intelligent_supervisor"

def route_after_writing(state: IntelligentResearchState) -> str:
    """写作后的路由决策 - 回到智能supervisor"""
    return "intelligent_supervisor"

def should_end(state: IntelligentResearchState) -> str:
    """判断是否结束"""
    if state.get("task_completed", False):
        return END
    else:
        return "intelligent_supervisor"

# ============================================================================
# 图构建 - LangGraph核心
# ============================================================================

def create_intelligent_research_graph(checkpointer: Optional[InMemorySaver] = None):
    """创建智能研究工作流图 - 使用智能Supervisor"""
    workflow = StateGraph(IntelligentResearchState)

    # 添加节点 - 使用智能supervisor
    workflow.add_node("intelligent_supervisor", supervisor_node)
    workflow.add_node("research", research_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("integration", integration_node)

    # 设置起始节点 - 从智能supervisor开始
    workflow.add_edge(START, "intelligent_supervisor")

    # 添加条件路由 - 智能supervisor的决策路由
    workflow.add_conditional_edges(
        "intelligent_supervisor",
        route_after_intelligent_supervisor,
        {
            "research": "research",
            "writing": "writing",
            "integration": "integration",
            "intelligent_supervisor": "intelligent_supervisor"  # 支持质量检查循环
        }
    )

    # 研究和写作完成后都回到智能supervisor进行质量评估
    workflow.add_conditional_edges(
        "research",
        route_after_research,
        {
            "intelligent_supervisor": "intelligent_supervisor"
        }
    )

    workflow.add_conditional_edges(
        "writing",
        route_after_writing,
        {
            "intelligent_supervisor": "intelligent_supervisor"
        }
    )

    # 整合完成后的结束判断
    workflow.add_conditional_edges(
        "integration",
        should_end,
        {
            "intelligent_supervisor": "intelligent_supervisor",
            END: END
        }
    )
    return workflow
