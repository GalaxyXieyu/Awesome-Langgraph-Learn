"""
多智能体系统
使用智能Supervisor进行动态调度和协作管理
支持异步执行和流式输出
"""



import json
import time
import asyncio
from typing import Dict, Any, List, TypedDict, Annotated, Optional, AsyncGenerator
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent.tools.tools import get_search_tools, get_analysis_tools, get_writing_tools
from agent.writer.writer import Collector, create_writer
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 状态定义
# ============================================================================

class MultiAgentState(TypedDict):
    """多智能体系统状态"""
    messages: Annotated[List, add_messages]  # 消息历史
    user_input: str  # 用户输入
    current_agent: str  # 当前执行的Agent
    execution_path: List[str]  # 执行路径记录
    agent_results: Dict[str, str]  # 各Agent执行结果
    final_result: str  # 最终输出结果
    iteration_count: int  # 当前迭代次数
    max_iterations: int  # 最大迭代次数
    context: Dict[str, Any]  # 上下文信息
    error_log: List[str]  # 错误日志记录
    supervisor_reasoning: str  # Supervisor推理过程
    next_action: str  # 下一步行动
    task_completed: bool  # 任务是否完成

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
# 专业化Agent创建
# ============================================================================

def create_agents():
    """创建专业化的agents"""
    llm = create_llm()
    
    # Search Agent - 专门负责搜索
    search_agent = create_react_agent(
        llm,
        tools=get_search_tools(),
        prompt="""你是一个搜索专家。你的任务是帮助用户搜索信息。

        你的能力：
        - 使用web_search工具进行网络搜索
        - 分析搜索结果的相关性和质量
        - 提供准确、有用的信息摘要

        工作原则：
        1. 理解用户的搜索意图
        2. 选择合适的搜索关键词
        3. 分析和筛选搜索结果
        4. 提供清晰、结构化的信息摘要

        请始终提供高质量、相关的搜索结果。"""
            )
    
    # Writing Agent - 专门负责写作
    writing_agent = create_react_agent(
        llm,
        tools=get_writing_tools(),
        prompt="""你是一个写作专家。你的任务是帮助用户生成高质量的内容。

        你的能力：
        - 使用content_writer工具生成各种风格的内容
        - 根据用户需求调整写作风格和长度
        - 创作结构清晰、逻辑严密的文章

        工作原则：
        1. 理解用户的写作需求和目标受众
        2. 选择合适的写作风格和结构
        3. 确保内容的准确性和可读性
        4. 提供有价值、有深度的内容

        请始终创作高质量、有价值的内容。"""
            )
    
    # Analysis Agent - 专门负责分析
    analysis_agent = create_react_agent(
        llm,
        tools=get_analysis_tools(),
        prompt="""你是一个分析专家。你的任务是帮助用户分析数据和文本。

        你的能力：
        - 使用text_analyzer工具进行文本分析
        - 使用calculator工具进行数学计算
        - 提供深入的分析见解和建议

        工作原则：
        1. 仔细理解分析需求
        2. 选择合适的分析方法和工具
        3. 提供准确、客观的分析结果
        4. 给出有价值的建议和见解

        请始终提供准确、有深度的分析结果。"""
            )
    
    return {
        "search": search_agent,
        "writing": writing_agent,
        "analysis": analysis_agent
    }

# ============================================================================
# 智能Supervisor节点
# ============================================================================

async def intelligent_supervisor_node(state: MultiAgentState, config=None) -> MultiAgentState:
    """智能Supervisor节点 - 使用统一的增强writer"""
    # 创建writer
    writer = create_writer("supervisor", "智能调度器")
    
    try:
        writer.step_start("开始智能调度分析")

        llm = create_llm()

        # 构建Supervisor的决策提示
        supervisor_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能的多智能体系统调度器。你需要分析用户需求，决定调用哪个Agent或是否结束流程。
            可用的Agents：
            1. search - 搜索专家：负责网络搜索、信息收集
            2. writing - 写作专家：负责内容生成、文章写作
            3. analysis - 分析专家：负责文本分析、数据计算

            决策规则：
            - 如果用户需要搜索信息、查找资料，选择 "search"
            - 如果用户需要计算、数学运算、数据分析，选择 "analysis"
            - 如果用户需要写作、生成内容、创作文章，选择 "writing"
            - 如果已经有足够的结果，选择 "finish"

            请只返回一个词作为决策结果，不要返回JSON格式：
            - search
            - analysis
            - writing
            - finish"""),
                        ("human", """
            用户输入：{user_input}
            当前执行路径：{execution_path}
            已有结果：{agent_results}

            请分析用户需求，只返回一个决策词：search、analysis、writing 或 finish
            """)
                    ])

        # 准备输入数据
        input_data = {
            "user_input": state.get("user_input", ""),
            "execution_path": state.get("execution_path", []),
            "agent_results": state.get("agent_results", {}),
            "iteration_count": state.get("iteration_count", 0),
            "max_iterations": state.get("max_iterations", 5),
            "context": state.get("context", {})
        }

        writer.step_progress("正在分析用户需求...", 30)

        # 流式调用LLM进行决策
        full_response = ""
        chunk_count = 0

        async for chunk in llm.astream(supervisor_prompt.format_messages(**input_data), config=config):
            if chunk.content and isinstance(chunk.content, str):
                full_response += chunk.content
                chunk_count += 1
                
                # 发送AI流式输出
                writer.ai_streaming(chunk.content, chunk_count)
                
                # 每5个chunk发送一次进度更新
                if chunk_count % 5 == 0:
                    progress = min(80, 30 + (chunk_count // 5) * 10)
                    writer.step_progress(
                        "正在分析决策...", 
                        progress,
                        current_reasoning=full_response[:200] + "..." if len(full_response) > 200 else full_response
                    )

        writer.step_progress("解析决策结果...", 85)

        # 解析LLM响应 - 简化版本，直接从响应中提取关键词
        content = full_response.lower().strip()

        # 直接匹配决策词
        if "search" in content:
            next_action = "search"
            reasoning = "检测到搜索需求"
        elif "analysis" in content:
            next_action = "analysis"
            reasoning = "检测到分析需求"
        elif "writing" in content:
            next_action = "writing"
            reasoning = "检测到写作需求"
        elif "finish" in content:
            next_action = "finish"
            reasoning = "任务完成"
        else:
            # 基于用户输入的智能判断
            user_input_lower = state.get("user_input", "").lower()
            if any(keyword in user_input_lower for keyword in ["搜索", "查找", "search", "find", "什么是", "介绍"]):
                next_action = "search"
                reasoning = "用户需要搜索信息"
            elif any(keyword in user_input_lower for keyword in ["计算", "分析", "统计", "数据", "情感", "calculate", "analyze"]):
                next_action = "analysis"
                reasoning = "用户需要分析计算"
            elif any(keyword in user_input_lower for keyword in ["写", "生成", "创作", "文章", "write", "generate"]):
                next_action = "writing"
                reasoning = "用户需要写作生成"
            else:
                next_action = "analysis"  # 默认使用分析
                reasoning = "默认使用分析处理"

        # 更新状态
        state["next_action"] = next_action
        state["supervisor_reasoning"] = reasoning
        state["execution_path"] = state.get("execution_path", []) + ["supervisor"]

        # 添加Supervisor的分析消息
        supervisor_message = f"""
        🧠 智能调度分析：
        - 决策：{next_action}
        - 理由：{reasoning}
        - 用户输入：{state.get('user_input', '')[:50]}...
        """

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=supervisor_message)
        ]

        # 发送AI完成消息
        writer.ai_complete(supervisor_message)
        
        # 发送步骤完成
        writer.step_complete(
            "智能调度分析完成",
            decision=next_action,
            reasoning=reasoning,
            confidence=0.8
        )

        logger.info(f"Supervisor决策: {next_action} - {reasoning}")

        return state

    except Exception as e:
        logger.error(f"Supervisor决策失败: {str(e)}")
        writer.error(f"决策失败: {str(e)}", "SupervisorError")
        # 错误处理：默认结束流程
        state["next_action"] = "finish"
        state["supervisor_reasoning"] = f"决策失败：{str(e)}"
        state["error_log"] = state.get("error_log", []) + [f"Supervisor错误: {str(e)}"]
        return state

# ============================================================================
# Agent执行节点
# ============================================================================

async def agent_execution_node(state: MultiAgentState) -> MultiAgentState:
    """执行选定的agent（增强writer版本）"""
    next_action = state.get("next_action")
    user_input = state.get("user_input", "")

    if next_action not in ["search", "writing", "analysis"]:
        return state

    # 创建writer
    writer = create_writer(f"{next_action}_agent", f"{next_action.title()} Agent")
    
    try:
        writer.step_start(f"开始执行{next_action}任务")

        # 创建agents
        agents = create_agents()
        agent = agents[next_action]

        # 构建Agent输入消息
        context_info = ""
        if state.get("agent_results"):
            context_info = f"\n\n已有信息：\n{json.dumps(state['agent_results'], ensure_ascii=False, indent=2)}"

        agent_input = f"{user_input}{context_info}"

        writer.step_progress(f"正在执行{next_action}任务...", 20)

        # 正确的 Agent 流式执行
        start_time = time.time()

        # 正确的 Agent 输入格式
        agent_input_dict = {"messages": [HumanMessage(content=agent_input)]}

        # 使用 Agent 的正常执行，但监控进度
        writer.step_progress(f"Agent开始执行{next_action}任务...", 30)
        # Agent 执行（使用流式处理）
        collector = Collector(writer)
        full_response = await collector.process_agent_stream(
            agent.astream(agent_input_dict, stream_mode=["updates","messages"]),
            next_action
        )

        execution_time = time.time() - start_time

        writer.step_progress("Agent执行完成", 90)

        writer.step_progress("处理执行结果...", 95)

        # 使用流式输出的结果
        result_text = full_response.strip() if full_response.strip() else "Agent执行完成"

        # 更新状态
        state["current_agent"] = next_action
        state["agent_results"] = state.get("agent_results", {})
        state["agent_results"][next_action] = result_text
        state["execution_path"] = state.get("execution_path", []) + [next_action]
        state["iteration_count"] = state.get("iteration_count", 0) + 1

        # 添加执行结果消息
        execution_message = f"""
            🤖 {next_action.title()} Agent 执行完成：
            ⏱️ 执行时间：{execution_time:.2f}秒
            📊 结果：{result_text[:300]}{'...' if len(result_text) > 300 else ''}
            """

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=execution_message)
        ]

        writer.step_complete(
            f"{next_action}任务执行完成",
            execution_time=execution_time,
            result_preview=result_text[:200] + "..." if len(result_text) > 200 else result_text,
            result_length=len(result_text)
        )

        logger.info(f"{next_action} Agent执行完成，耗时{execution_time:.2f}秒")

        return state

    except Exception as e:
        logger.error(f"Agent执行失败: {str(e)}")
        next_action = state.get("next_action", "unknown")
        error_msg = f"{next_action} Agent执行失败：{str(e)}"

        writer.error(f"{next_action} Agent执行失败: {str(e)}", "AgentExecutionError")

        state["error_log"] = state.get("error_log", []) + [error_msg]
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"❌ {error_msg}")
        ]
        return state

# ============================================================================
# 结果整合节点
# ============================================================================

async def result_integration_node(state: MultiAgentState, config=None) -> MultiAgentState:
    """结果整合节点 - 整合所有Agent的结果（增强writer版本）"""
    # 创建增强writer
    writer = create_writer("result_integration", "结果整合器")
    
    try:
        writer.step_start("开始结果整合")

        llm = create_llm()

        # 构建结果整合提示
        integration_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个结果整合专家。请将多个Agent的执行结果整合成一个完整、连贯的最终答案。
            整合原则：
            1. 保持信息的准确性和完整性
            2. 确保逻辑清晰、结构合理
            3. 去除重复信息，突出关键内容
            4. 提供有价值的综合见解

            请生成一个完整、专业的最终回答。"""),
                        ("human", """
            用户原始问题：{user_input}

            各Agent执行结果：
            {agent_results}

            执行路径：{execution_path}

            请整合以上信息，生成最终答案。
            """)
        ])

        # 准备整合数据
        agent_results = state.get("agent_results", {})
        agent_results_text = "\n\n".join([
            f"**{agent.title()} Agent结果：**\n{result}"
            for agent, result in agent_results.items()
        ])

        integration_data = {
            "user_input": state.get("user_input", ""),
            "agent_results": agent_results_text,
            "execution_path": " → ".join(state.get("execution_path", []))
        }

        writer.step_progress("正在整合结果...", 20)

        # 流式调用LLM进行结果整合
        final_result = ""
        chunk_count = 0

        async for chunk in llm.astream(integration_prompt.format_messages(**integration_data), config=config):
            if chunk.content and isinstance(chunk.content, str):
                final_result += chunk.content
                chunk_count += 1
                
                # 发送AI流式输出
                writer.ai_streaming(chunk.content, chunk_count)
                
                # 每5个chunk发送一次进度更新
                if chunk_count % 5 == 0:
                    progress = min(90, 20 + (chunk_count // 5) * 10)
                    writer.step_progress(
                        "正在生成最终结果...",
                        progress,
                        current_content=final_result[:300] + "..." if len(final_result) > 300 else final_result,
                        total_chars=len(final_result)
                    )

        # 更新状态
        state["final_result"] = final_result
        state["task_completed"] = True

        # 添加最终结果消息
        final_message = f"""
            🎯 最终整合结果：

            {final_result}

            ---
            📈 执行摘要：
            - 执行路径：{' → '.join(state.get('execution_path', []))}
            - 迭代次数：{state.get('iteration_count', 0)}
            - 参与Agent：{', '.join(agent_results.keys())}
        """

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=final_message)
        ]

        # 发送最终结果
        execution_summary = {
            "execution_path": state.get('execution_path', []),
            "iteration_count": state.get('iteration_count', 0),
            "agents_used": list(agent_results.keys())
        }
        
        writer.final_result(final_result, execution_summary)
        
        writer.step_complete(
            "结果整合完成",
            final_result_length=len(final_result),
            execution_summary=execution_summary
        )

        logger.info("结果整合完成")

        return state

    except Exception as e:
        logger.error(f"结果整合失败: {str(e)}")
        writer.error(f"结果整合失败: {str(e)}", "ResultIntegrationError")

        # 使用简单的结果整合作为后备
        agent_results = state.get("agent_results", {})
        if agent_results:
            final_result = "\n\n".join([
                f"**{agent.title()}结果：**\n{result}"
                for agent, result in agent_results.items()
            ])
        else:
            final_result = "抱歉，没有获得有效的执行结果。"

        state["final_result"] = final_result
        state["task_completed"] = True
        state["error_log"] = state.get("error_log", []) + [f"结果整合错误: {str(e)}"]
        return state

# ============================================================================
# 路由函数
# ============================================================================

def route_after_supervisor(state: MultiAgentState) -> str:
    """Supervisor决策后的路由"""
    next_action = state.get("next_action", "finish")

    if next_action in ["search", "writing", "analysis"]:
        return "agent_execution"
    else:
        return "result_integration"

def route_after_agent_execution(state: MultiAgentState) -> str:
    """Agent执行后的路由"""
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)

    # 检查是否达到最大迭代次数，直接进行结果整合
    if iteration_count >= max_iterations:
        return "result_integration"

    # 继续让Supervisor决策下一步
    return "supervisor"



def should_end(state: MultiAgentState) -> str:
    """判断是否应该结束"""
    if state.get("task_completed", False):
        return END
    else:
        return "supervisor"

# ============================================================================
# 图构建
# ============================================================================

def create_multi_agent_graph():
    """创建多智能体工作流图，LangGraph Studio会自动处理持久化"""
    workflow = StateGraph(MultiAgentState)

    # 添加节点
    workflow.add_node("supervisor", intelligent_supervisor_node)
    workflow.add_node("agent_execution", agent_execution_node)
    workflow.add_node("result_integration", result_integration_node)

    # 设置起始节点
    workflow.add_edge(START, "supervisor") 

    # 添加条件路由
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "agent_execution": "agent_execution",
            "result_integration": "result_integration"
        }
    )

    workflow.add_conditional_edges(
        "agent_execution",
        route_after_agent_execution,
        {
            "supervisor": "supervisor",
            "result_integration": "result_integration"
        }
    )

    # 结果整合后结束
    workflow.add_edge("result_integration", END)

    # 编译图，不使用自定义checkpointer（LangGraph Studio会自动处理）
    app = workflow.compile()

    return app

# ============================================================================
# 便捷函数
# ============================================================================

async def run_multi_agent_system_async(
    user_input: str,
    max_iterations: int = 5,
    context: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    异步运行多智能体系统

    Args:
        user_input: 用户输入
        max_iterations: 最大迭代次数
        context: 上下文信息
        thread_id: 线程ID，用于会话持久化

    Returns:
        执行结果
    """
    try:
        # 创建图（不使用checkpointer，LangGraph Studio会自动处理）
        app = create_multi_agent_graph()

        # 初始化状态
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "current_agent": "",
            "execution_path": [],
            "agent_results": {},
            "final_result": "",
            "iteration_count": 0,
            "max_iterations": max_iterations,
            "context": context or {},
            "error_log": [],
            "supervisor_reasoning": "",
            "next_action": "",
            "task_completed": False
        }

        # 配置（如果需要thread_id）
        config = {"configurable": {"thread_id": thread_id or f"thread_{int(time.time())}"}} if thread_id else {}

        # 异步运行工作流
        start_time = time.time()
        result = await app.ainvoke(initial_state, config=config if config else None)
        execution_time = time.time() - start_time

        # 构建返回结果
        return {
            "success": True,
            "user_input": user_input,
            "final_result": result.get("final_result", ""),
            "execution_path": result.get("execution_path", []),

            "execution_time": execution_time,
            "agent_results": result.get("agent_results", {}),
            "iteration_count": result.get("iteration_count", 0),
            "error_log": result.get("error_log", []),
            "metadata": {
                "total_iterations": result.get("iteration_count", 0),
                "max_iterations": max_iterations,
                "supervisor_reasoning": result.get("supervisor_reasoning", ""),
                "messages_count": len(result.get("messages", []))
            }
        }

    except Exception as e:
        logger.error(f"多智能体系统执行失败: {str(e)}")
        return {
            "success": False,
            "error_type": "SystemExecutionError",
            "error_message": str(e),
            "user_input": user_input,
            "partial_results": {}
        }

async def stream_multi_agent_system(
    user_input: str,
    max_iterations: int = 5,
    context: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    异步流式运行多智能体系统

    Args:
        user_input: 用户输入
        max_iterations: 最大迭代次数
        context: 上下文信息
        thread_id: 线程ID，用于会话持久化

    Yields:
        流式执行结果
    """
    try:
        # 创建图（不使用checkpointer，LangGraph Studio会自动处理）
        app = create_multi_agent_graph()

        # 初始化状态
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "current_agent": "",
            "execution_path": [],
            "agent_results": {},
            "final_result": "",

            "iteration_count": 0,
            "max_iterations": max_iterations,
            "context": context or {},
            "error_log": [],
            "supervisor_reasoning": "",
            "next_action": "",
            "task_completed": False
        }

        # 配置（如果需要thread_id）
        config = {"configurable": {"thread_id": thread_id or f"thread_{int(time.time())}"}} if thread_id else {}

        # 异步流式执行
        start_time = time.time()
        async for chunk in app.astream(initial_state, config=config if config else None):
            # 计算当前执行时间
            current_time = time.time() - start_time

            # 构建流式输出
            stream_chunk = {
                "type": "chunk",
                "timestamp": time.time(),
                "execution_time": current_time,
                "chunk_data": chunk
            }

            # 如果是最终结果，添加完整摘要
            if any("final_result" in node_data for node_data in chunk.values() if isinstance(node_data, dict)):
                stream_chunk["type"] = "final"
                stream_chunk["summary"] = {
                    "total_execution_time": current_time,
                    "user_input": user_input
                }

            yield stream_chunk

    except Exception as e:
        logger.error(f"流式执行失败: {str(e)}")
        yield {
            "type": "error",
            "timestamp": time.time(),
            "error_type": "StreamExecutionError",
            "error_message": str(e),
            "user_input": user_input
        }

def run_multi_agent_system(
    user_input: str,
    max_iterations: int = 5,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    同步运行多智能体系统（兼容性函数）

    Args:
        user_input: 用户输入
        max_iterations: 最大迭代次数
        context: 上下文信息

    Returns:
        执行结果
    """
    return asyncio.run(run_multi_agent_system_async(user_input, max_iterations, context))

# 导出给LangGraph Studio使用的graph实例
graph = create_multi_agent_graph()

if __name__ == "__main__":
    result = run_multi_agent_system("计算 2+3*4 的结果", max_iterations=2)
    if result["success"]:
        print(f"✅ 同步执行成功: {result['final_result'][:100]}...")
    else:
        print(f"❌ 同步执行失败: {result['error_message']}")
