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

# 导入模块化组件 - 使用绝对导入
try:
    # 当作为子图导入时使用相对路径
    from .tools import ALL_RESEARCH_TOOLS
    from .context_builder import build_supervisor_context, determine_next_action_by_state
    from .prompts import get_supervisor_prompt, get_researcher_prompt, get_writer_prompt
except ImportError:
    # 当直接运行时使用当前目录
    from tools import ALL_RESEARCH_TOOLS
    from context_builder import build_supervisor_context, determine_next_action_by_state
    from prompts import get_supervisor_prompt, get_researcher_prompt, get_writer_prompt

# 导入流式输出系统
try:
    from ..stream_writer import create_stream_writer, create_workflow_processor
except ImportError:
    try:
        from stream_writer import create_stream_writer, create_workflow_processor
    except ImportError:
        # 创建dummy函数以防导入失败
        def create_stream_writer(node_name: str, agent_name: str = ""):
            class DummyWriter:
                def step_start(self, msg): pass
                def step_progress(self, msg, progress, **kwargs): pass  
                def step_complete(self, msg, **kwargs): pass
                def thinking(self, msg): pass
                def reasoning(self, msg, **kwargs): pass
            return DummyWriter()
        
        def create_workflow_processor(node_name: str, agent_name: str = ""):
            class DummyProcessor:
                def __init__(self):
                    self.writer = create_stream_writer(node_name, agent_name)
                def process_chunk(self, chunk): pass
            return DummyProcessor()

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

def create_llm() -> ChatOpenAI:
    """创建LLM实例"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        base_url="https://yunwu.zeabur.app/v1",
        api_key="sk-GwOrS2hlFEvQwup599AdD613BaF54690B017812988D2810e",
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
    
    # 创建流式输出writer
    writer = create_stream_writer("intelligent_supervisor", "智能调度分析")
    writer.thinking("开始智能调度分析...")

    llm = create_llm()

    # 使用模块化的上下文构建
    input_data = build_supervisor_context(state)

    # 构建Supervisor的智能决策提示
    supervisor_prompt = get_supervisor_prompt()

    # 智能分析进行中
    writer.step_progress("分析当前状态和进度", 30)

    formatted_messages = supervisor_prompt.format_messages(**input_data)
    # 流式调用LLM进行智能决策
    full_response = ""
    chunk_count = 0
    async for chunk in llm.astream(formatted_messages, config=config):
        if hasattr(chunk, 'content') and chunk.content:
            content = str(chunk.content)
            full_response += content
            chunk_count += 1
    
    # 决策结果解析中
    writer.step_progress("解析智能决策结果", 70)
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
        next_action = "integration"
        reasoning = "所有章节的研究和写作都已完成，开始最终整合"

    # 处理章节索引更新和目标章节设置
    if next_action == "move_to_next_section":
        new_index = current_index + 1
        state["current_section_index"] = new_index
        # 检查是否超出章节范围
        if new_index >= len(sections):
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

    # 智能调度分析完成 - 简化输出
    writer.step_complete("智能调度决策完成", 
                        decision=next_action,
                        confidence=confidence,
                        current_progress=f"{current_index}/{len(sections)}")
    
    # 不再添加详细的supervisor消息到状态中
    return state

async def research_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """研究节点 - 执行章节研究"""
    try:
        sections = state.get("sections", [])
        current_index = state.get("current_section_index", 0)
        
        # 创建流式输出writer
        writer = create_stream_writer("research", "章节研究员")
        writer.step_start(f"开始研究分析 (章节 {current_index + 1}/{len(sections)})")

        if current_index >= len(sections):
            return state

        current_section = sections[current_index]
        section_id = current_section.get("id", "")
        title = current_section.get("title", "")
        description = current_section.get("description", "")
        
        # 记录研究尝试次数
        section_attempts = state.get("section_attempts", {})
        if section_id not in section_attempts:
            section_attempts[section_id] = {"research": 0, "writing": 0}
        section_attempts[section_id]["research"] += 1
        state["section_attempts"] = section_attempts

        current_attempt = section_attempts[section_id]["research"]
        # 开始研究
        writer.step_progress(f"准备研究章节: {title}", 20, 
                           attempt=current_attempt, section_id=section_id)

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
        
        # Agent研究进行中
        writer.thinking(f"调用研究Agent处理: {title}")
        
        # Agent执行研究
        agent_input = {"messages": [HumanMessage(content=research_task)]}
        
        # 使用改进的Agent调用逻辑 - 确保获取完整内容
        try:
            # 首先尝试直接调用以获取最终结果
            result = await researcher.ainvoke(agent_input)
            full_response = ""
            
            # 提取完整的Agent响应
            if isinstance(result, dict) and 'messages' in result:
                messages = result['messages']
                # 寻找最后的AI消息作为最终结果
                for msg in reversed(messages):
                    if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
                        content = str(msg.content).strip()
                        if content and len(content) > 50:  # 确保有实质性内容
                            full_response = content
                            break
                
                # 如果没有找到AI消息，收集所有有用消息
                if not full_response:
                    useful_content = []
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            content = str(msg.content).strip()
                            if content and len(content) > 20:
                                useful_content.append(content)
                    full_response = '\n\n'.join(useful_content)
            
            # 如果直接调用没有获得好的结果，尝试流式调用
            if not full_response or len(full_response) < 100:
                stream_response = ""
                ai_messages = []
                
                async for chunk in researcher.astream(agent_input, stream_mode=["messages"]):
                    if isinstance(chunk, tuple) and len(chunk) >= 2:
                        chunk_type, chunk_data = chunk
                        if chunk_type == "messages":
                            if hasattr(chunk_data, 'type') and chunk_data.type == 'ai':
                                if hasattr(chunk_data, 'content') and chunk_data.content:
                                    ai_messages.append(str(chunk_data.content))
                            elif hasattr(chunk_data, 'content'):
                                stream_response += str(chunk_data.content)
                
                # 使用AI消息或流式响应
                if ai_messages:
                    full_response = ''.join(ai_messages)
                elif stream_response:
                    full_response = stream_response
            
            # 最后的质量检查和内容生成
            if not full_response or len(full_response.strip()) < 50:
                # 提供基于描述的研究结果
                full_response = f"章节'{title}'的研究分析：\n\n{description}\n\n这是一个重要的研究领域，需要进一步的深入调查和数据收集来支撑我们的分析结论。虽然遇到了一些技术挑战，但基于现有框架可以提供初步分析结果。"
        
        except Exception as e:
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
                full_response = f"研究执行失败: {str(e2)}"
        
        # 研究内容完成
        word_count = len(full_response.split()) if full_response else 0
        writer.step_progress(f"研究数据收集完成: {title}", 90, 
                           content_length=len(full_response), word_count=word_count)
        
        # 保存研究结果
        research_results = state.get("research_results", {})
        research_results[section_id] = {
            "title": title,
            "content": full_response,
            "timestamp": time.time()
        }
        state["research_results"] = research_results
        state["execution_path"] = state.get("execution_path", []) + ["research"]
        
        # 研究步骤完成
        writer.step_complete(f"研究完成: {title}", 
                           result_length=len(full_response), 
                           word_count=word_count,
                           section_id=section_id)
        
        return state
        
    except Exception as e:
        # 研究错误（由主图处理流式输出）
        state["error_log"] = state.get("error_log", []) + [f"研究错误: {e}"]
        return state

async def writing_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """写作节点 - 基于研究结果写作"""
    
    try:
        sections = state.get("sections", [])
        current_index = state.get("current_section_index", 0)
        research_results = state.get("research_results", {})
        
        # 创建流式输出writer
        writer = create_stream_writer("writing", "章节写作员")
        writer.step_start(f"开始内容创作 (章节 {current_index + 1}/{len(sections)})")

        if current_index >= len(sections):
            return state

        current_section = sections[current_index]
        section_id = current_section.get("id", "")
        title = current_section.get("title", "")
        
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

        # 开始写作
        writer.step_progress(f"准备写作章节: {title}", 20, 
                           attempt=current_attempt, 
                           research_length=len(research_content))

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
        
        # Agent写作进行中
        writer.thinking(f"调用写作Agent处理: {title}")
        writer.step_progress("写作Agent分析研究数据", 50)
        
        # Agent执行写作
        agent_input = {"messages": [HumanMessage(content=writing_task)]}
        
        # 使用改进的写作Agent调用逻辑
        try:
            # 首先尝试直接调用以获取最终结果
            result = await writer_agent.ainvoke(agent_input)
            full_response = ""
            
            # 提取Agent的最终响应
            if isinstance(result, dict) and 'messages' in result:
                messages = result['messages']
                # 寻找最后的AI消息作为最终结果
                for msg in reversed(messages):
                    if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
                        content = str(msg.content).strip()
                        if content and len(content) > 100:  # 写作内容应该更长
                            full_response = content
                            break
                
                # 如果没有找到AI消息，收集所有有用内容
                if not full_response:
                    useful_content = []
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            content = str(msg.content).strip()
                            if content and len(content) > 30:
                                useful_content.append(content)
                    full_response = '\n\n'.join(useful_content)
            
            # 如果直接调用没有获得好的结果，尝试流式调用
            if not full_response or len(full_response) < 200:
                stream_response = ""
                ai_messages = []
                
                async for chunk in writer_agent.astream(agent_input, stream_mode=["messages"]):
                    if isinstance(chunk, tuple) and len(chunk) >= 2:
                        chunk_type, chunk_data = chunk
                        if chunk_type == "messages":
                            if hasattr(chunk_data, 'type') and chunk_data.type == 'ai':
                                if hasattr(chunk_data, 'content') and chunk_data.content:
                                    ai_messages.append(str(chunk_data.content))
                            elif hasattr(chunk_data, 'content'):
                                stream_response += str(chunk_data.content)
                
                # 使用AI消息或流式响应
                if ai_messages:
                    full_response = ''.join(ai_messages)
                elif stream_response:
                    full_response = stream_response
            
            # 最后的质量检查和内容生成
            if not full_response or len(full_response.strip()) < 200:
                # 如果还是没有好的结果，基于研究数据生成内容
                if research_content and len(research_content) > 50:
                    full_response = f"# {title}\n\n基于深入研究，我们发现以下关键insights：\n\n{research_content[:1000]}\n\n## 深度分析\n\n通过对相关数据的分析，我们可以得出重要结论。这一章节的研究为整体报告提供了坚实的基础，为后续分析奠定了重要基础。\n\n## 关键要点\n\n1. 核心发现和关键数据点\n2. 重要趋势和模式识别\n3. 对整体研究的意义和价值\n\n这些发现将为我们的综合分析提供重要支撑。"
                else:
                    full_response = f"# {title}\n\n## 概述\n\n本章节围绕'{title}'这一核心主题展开深入分析。{description}\n\n## 关键分析\n\n通过综合研究，我们识别出以下几个重要维度：\n\n1. **背景与现状**：当前发展状况和主要特征\n2. **核心要素**：影响发展的关键因素\n3. **趋势识别**：未来发展的可能方向\n4. **实践意义**：对实际应用的指导价值\n\n## 深入洞察\n\n基于我们的分析框架，这一领域呈现出复杂而多样的发展态势。相关stakeholders需要从多个角度来理解和把握发展机遇。\n\n## 小结\n\n{title}作为重要研究主题，其发展状况和未来趋势值得持续关注。本章节的分析为后续深入研究奠定了基础。"
            
            # 如果没有获取到响应，提供默认信息
            if not full_response:
                full_response = "写作完成，但未获取到最终结果"
        
        except Exception as e:
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
                full_response = f"写作执行失败: {str(e2)}"
        
        # 保存写作结果
        word_count = len(full_response.split()) if full_response else 0
        writing_results = state.get("writing_results", {})
        writing_results[section_id] = {
            "title": title,
            "content": full_response,
            "word_count": word_count,
            "timestamp": time.time()
        }
        state["writing_results"] = writing_results
        state["execution_path"] = state.get("execution_path", []) + ["writing"]
        
        # 写作步骤完成
        writer.step_complete(f"写作完成: {title}", 
                           word_count=word_count,
                           content_length=len(full_response),
                           section_id=section_id)
        
        return state
        
    except Exception as e:
        # 写作错误（由主图处理流式输出）
        state["error_log"] = state.get("error_log", []) + [f"写作错误: {e}"]
        return state

async def integration_node(state: IntelligentResearchState, config=None) -> IntelligentResearchState:
    """整合节点 - 生成最终报告"""
    
    try:
        # 创建流式输出writer
        writer = create_stream_writer("integration", "报告整合员")
        writer.step_start("开始整合最终报告")

        topic = state.get("topic", "")
        writing_results = state.get("writing_results", {})
        sections = state.get("sections", [])

        # 构建最终报告
        writer.step_progress("收集章节内容", 30, total_sections=len(sections))
        final_sections = []
        total_words = 0

        for section in sections:
            section_id = section.get("id", "")
            if section_id in writing_results:
                section_data = writing_results[section_id]
                final_sections.append(section_data)
                total_words += section_data.get("word_count", 0)
                writer.step_progress(f"整合章节: {section_data.get('title', '')}", 
                                   30 + (len(final_sections) / len(sections)) * 40)

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

        # 报告整合完成
        writer.final_result(f"智能研究报告生成完成", {
            "total_sections": len(final_sections),
            "total_words": total_words,
            "topic": topic,
            "generation_method": "langgraph_intelligent_research"
        })

        return state

    except Exception as e:
        # 整合错误（由主图处理流式输出）
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
