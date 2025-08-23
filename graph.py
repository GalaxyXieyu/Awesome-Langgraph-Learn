"""
研究图定义模块
创建带有human-in-loop功能的深度研究图
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import os

from state import ResearchState
from human_in_loop_wrapper import get_hil_tools


# 初始化LLM
def get_llm():
    """获取LLM实例"""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )


async def research_planner(state: ResearchState) -> Dict[str, Any]:
    """研究规划节点"""
    print(f"\n=== 研究规划阶段 ===")
    print(f"主题: {state['topic']}")
    
    llm = get_llm()
    
    # 构建规划提示
    planning_prompt = f"""
    你是一个专业的研究规划师。请为以下主题制定详细的研究计划：

    研究主题：{state['topic']}

    请分析这个主题需要哪些方面的研究，并制定具体的研究步骤。
    你可以使用以下工具来辅助研究：
    - search_web: 搜索网络信息
    - calculate: 进行数学计算
    - send_email: 发送邮件通知

    请提供一个详细的研究计划。
    """
    
    # 调用LLM生成规划
    response = await llm.ainvoke([HumanMessage(content=planning_prompt)])
    
    return {
        "messages": [response],
        "current_step": "planning_complete",
        "research_results": [f"研究计划：{response.content}"]
    }


async def research_executor(state: ResearchState) -> Dict[str, Any]:
    """研究执行节点"""
    print(f"\n=== 研究执行阶段 ===")
    
    llm = get_llm()
    
    # 获取带有human-in-loop的工具
    tools = await get_hil_tools()
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 构建执行提示
    execution_prompt = f"""
    基于之前的研究计划，现在开始执行具体的研究任务。

    研究主题：{state['topic']}
    
    之前的研究结果：
    {chr(10).join(state['research_results'])}

    请使用可用的工具来收集更多信息。每次工具调用都会经过人工审查。
    
    开始执行研究任务，使用search_web工具搜索相关信息。
    """
    
    # 调用带工具的LLM
    response = await llm_with_tools.ainvoke([HumanMessage(content=execution_prompt)])
    
    return {
        "messages": [response],
        "current_step": "execution_in_progress"
    }


async def research_summarizer(state: ResearchState) -> Dict[str, Any]:
    """研究总结节点"""
    print(f"\n=== 研究总结阶段 ===")
    
    llm = get_llm()
    
    # 构建总结提示
    summary_prompt = f"""
    请对以下研究进行总结：

    研究主题：{state['topic']}
    
    研究过程和结果：
    {chr(10).join(state['research_results'])}
    
    消息历史：
    {chr(10).join([msg.content for msg in state['messages'] if hasattr(msg, 'content')])}

    请提供一个全面的研究总结报告。
    """
    
    response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
    
    return {
        "messages": [response],
        "current_step": "completed",
        "completed": True,
        "research_results": state['research_results'] + [f"最终总结：{response.content}"]
    }


def should_continue(state: ResearchState) -> str:
    """决定是否继续研究"""
    current_step = state.get("current_step", "start")
    
    if current_step == "start":
        return "plan"
    elif current_step == "planning_complete":
        return "execute"
    elif current_step == "execution_in_progress":
        # 检查是否有工具调用
        last_message = state["messages"][-1] if state["messages"] else None
        if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        else:
            return "summarize"
    elif current_step == "completed":
        return END
    else:
        return "summarize"


def create_deep_research_graph():
    """创建深度研究图"""
    
    # 创建状态图
    workflow = StateGraph(ResearchState)
    
    # 添加节点
    workflow.add_node("planner", research_planner)
    workflow.add_node("executor", research_executor)
    workflow.add_node("summarizer", research_summarizer)
    
    # 创建工具节点（异步获取工具）
    async def create_tool_node():
        tools = await get_hil_tools()
        return ToolNode(tools)
    
    # 注意：这里需要在运行时创建工具节点
    # 我们将在编译时处理这个问题
    
    # 添加边
    workflow.add_edge(START, "planner")
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "plan": "planner",
            "execute": "executor",
            "summarize": "summarizer",
            END: END
        }
    )
    workflow.add_conditional_edges(
        "executor", 
        should_continue,
        {
            "tools": "tools",
            "summarize": "summarizer",
            END: END
        }
    )
    workflow.add_conditional_edges(
        "summarizer",
        should_continue,
        {
            END: END
        }
    )
    
    return workflow


async def create_deep_research_graph_with_tools():
    """创建带有工具的深度研究图"""
    workflow = StateGraph(ResearchState)
    
    # 添加节点
    workflow.add_node("planner", research_planner)
    workflow.add_node("executor", research_executor)
    workflow.add_node("summarizer", research_summarizer)
    
    # 获取工具并创建工具节点
    tools = await get_hil_tools()
    workflow.add_node("tools", ToolNode(tools))
    
    # 添加边
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_conditional_edges(
        "executor",
        should_continue,
        {
            "tools": "tools",
            "summarize": "summarizer"
        }
    )
    workflow.add_edge("tools", "summarizer")
    workflow.add_edge("summarizer", END)
    
    return workflow
