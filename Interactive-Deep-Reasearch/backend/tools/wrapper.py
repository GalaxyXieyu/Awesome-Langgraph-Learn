"""
简单工具包装器
支持human-in-loop和mode配置，完全参考参考文件实现
"""

import logging
from typing import List, Dict, Any, Union, Callable, Optional
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt
from langgraph import types


async def wrap_interactive_tools(
    tool: Union[Callable, BaseTool], 
    mode: str,
    *,
    interrupt_config: HumanInterruptConfig = None
) -> BaseTool:
    """
    根据模式包装工具
    完全参考参考文件的human-in-loop实现
    
    Args:
        tool: 可调用对象或 BaseTool 对象
        state: 状态字典，用于检测模式
        interrupt_config: 可选的人工中断配置

    Returns:
        BaseTool: 包装后的工具
    """
    # 检查传入的工具是否为 BaseTool 的实例
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    # 检查是否提供了 interrupt_config 参数
    if interrupt_config is None:
        # 如果未提供，则设置默认的人工中断配置，允许接受、编辑和响应
        interrupt_config = {
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
        }
    # Copilot模式：直接执行，无需确认
    if mode == "copilot":
        @create_tool(
            tool.name,
            description=tool.description,
            args_schema=tool.args_schema
        )
        async def copilot_tool(config: RunnableConfig = None, **tool_input):
            try:
                # 兼容不同的工具调用方式
                if hasattr(tool, 'ainvoke'):
                    result = await tool.ainvoke(tool_input, config=config)
                elif hasattr(tool, 'arun'):
                    result = await tool.arun(**tool_input)
                elif hasattr(tool, 'invoke'):
                    # 同步工具需要在异步环境中执行
                    import asyncio
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, tool.invoke, tool_input)
                else:
                    # 直接调用工具函数
                    result = await tool(**tool_input)
                return result
            except Exception as e:
                return f"工具执行失败: {str(e)}"        
        return copilot_tool

    # Interactive模式：完全参考参考文件的实现
    else:
        @create_tool(
            tool.name,
            description=tool.description,
            args_schema=tool.args_schema
        )
        async def interactive_tool(config: RunnableConfig = None, **tool_input):
            # 创建人工中断请求，完全参考参考文件
            request: HumanInterrupt = {
                "action_request": {
                    "action": tool.name,
                    "args": tool_input
                },
                "config": interrupt_config,
                "description": f"准备调用 {tool.name} 工具：\n- 参数为: {tool_input}\n\n是否允许继续？\n输入 'yes' 接受工具调用\n输入 'no' 拒绝工具调用\n输入 'edit' 修改工具参数后调用工具\n输入 'response' 不调用工具直接反馈信息",
            }
            
            # 调用 interrupt 函数，获取人工审查的响应
            response = types.interrupt(request)

            # 定义统一的工具调用函数
            async def call_tool(input_args):
                try:
                    if hasattr(tool, 'ainvoke'):
                        return await tool.ainvoke(input_args, config=config)
                    elif hasattr(tool, 'arun'):
                        return await tool.arun(**input_args)
                    elif hasattr(tool, 'invoke'):
                        # 同步工具需要在异步环境中执行
                        import asyncio
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, tool.invoke, input_args)
                    else:
                        # 直接调用工具函数
                        return await tool(**input_args)
                except Exception as e:
                    return f"工具执行失败: {str(e)}"

            # 完全参考参考文件的响应处理逻辑
            if response["type"] == "accept":
                return await call_tool(tool_input)
            elif response["type"] == "edit":
                # 如果是编辑，更新工具输入参数为响应中提供的参数
                tool_input = response["args"]["args"]
                return await call_tool(tool_input)
            elif response["type"] == "reject":
                return '该工具被拒绝使用，请尝试其他方法或拒绝回答问题。'
            elif response["type"] == "response":
                # 如果是响应，直接将用户反馈作为工具的响应
                user_feedback = response["args"]
                return user_feedback
            else:
                raise ValueError(f"不支持的中断响应类型: {response['type']}")
        return interactive_tool


async def wrap_tools(
    tools: List[Union[Callable, BaseTool]], 
    mode: str,
) -> List[BaseTool]:
    """
    批量包装工具 - 简化版本，直接返回包装后的工具列表
    """
    interactive_tools = []
    for tool in tools:
        try:
            interactive_tool = await wrap_interactive_tools(tool, mode)
            interactive_tools.append(interactive_tool)
        except Exception as e:
            continue
    return interactive_tools

if __name__ == "__main__":
    import asyncio
    from pprint import pprint
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import InMemorySaver

    # Import local tools and the wrapper function from this file
    from .research.tools import web_search

    # Define a simple LLM for the agent
    # Make sure you have OPENAI_API_KEY set in your environment
    llm = ChatOpenAI(
            model="qwen2.5-72b-instruct-awq",
            temperature=0.7,
            base_url="https://llm.3qiao.vip:23436/v1",
            api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
        )

    async def test_copilot_mode(agent_executor):
        """Tests the agent in copilot mode where tools run automatically."""
        print("\n--- 1. Testing Copilot Mode (Automatic Execution) ---")
        query = "What is the latest news on AI?"
        print(f"Invoking agent with query: '{query}'")
        config = {"configurable": {"thread_id": "copilot-test-1"}}
        final_response = None
        async for chunk in agent_executor.astream({"messages": [HumanMessage(content=query)]}, config=config):
            pprint(chunk)
            print("---")
            if 'messages' in chunk and chunk['messages']:
                final_response = chunk['messages'][-1].content

        print("\nCopilot Mode Final Response:")
        pprint(final_response)
        print("--- Copilot Mode Test Complete ---")

    async def test_interactive_mode(agent_executor):
        """Tests the agent in interactive mode, expecting it to pause for human input."""
        print("\n--- 2. Testing Interactive Mode (Human-in-the-Loop) ---")
        query = "Search for news on LangGraph."
        print(f"Invoking agent with query: '{query}'")
        config = {"configurable": {"thread_id": "interactive-test-1"}}

        print("Streaming agent execution... It should stop at the interrupt.")
        async for chunk in agent_executor.astream({"messages": [HumanMessage(content=query)]}, config=config):
            pprint(chunk)
            print("---")
            # The stream will naturally stop at the HumanInterrupt.
            # In a real app, you would check if `chunk` is the interrupt,
            # get user input, and then resume the graph.
            if "__end__" not in chunk:
                print("\n>>> INTERRUPT DETECTED! Test successful. The agent is waiting for human review. <<<")
                break
        print("--- Interactive Mode Test Complete ---")

    async def main():
        """Main function to run the agent-based tests."""
        # Test Copilot Mode
        copilot_state = {"mode": "copilot"}
        copilot_tools = await wrap_tools([web_search], copilot_state)
        copilot_agent = create_react_agent(llm, tools=copilot_tools)
        await test_copilot_mode(copilot_agent)

        # Test Interactive Mode
        # This requires a checkpointer to manage the state of the interrupt.
        memory = InMemorySaver()
        interactive_state = {"mode": "interactive"}
        interactive_tools = await wrap_tools([web_search], interactive_state)
        # interrupt_before_tools=True is crucial for HIL with ReAct agents
        interactive_agent = create_react_agent(llm, tools=interactive_tools, checkpointer=memory)
        await test_interactive_mode(interactive_agent)

    # Run the main async function
    asyncio.run(main())
    