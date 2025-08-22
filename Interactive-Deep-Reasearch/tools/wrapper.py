"""
简单工具包装器
支持human-in-loop和mode配置，完全参考参考文件实现
"""

import logging
from typing import List, Dict, Any, Union, Callable, Optional
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt
from langgraph.types import interrupt


async def wrap_interactive_tools(
    tool: Union[Callable, BaseTool], 
    state: Optional[Dict[str, Any]] = None,
    interrupt_config: Optional[HumanInterruptConfig] = None
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

    # 检测模式
    mode = "copilot"
    if state:
        state_mode = state.get("mode", "copilot") 
        if hasattr(state_mode, 'value'):
            mode = state_mode.value.lower()
        else:
            mode = str(state_mode).lower()

    # Copilot模式：直接执行，无需确认
    if mode == "copilot":
        @create_tool(
            tool.name,
            description=tool.description,
            args_schema=tool.args_schema
        )
        async def copilot_tool(config: RunnableConfig, **tool_input):
            try:
                result = await tool.ainvoke(input=tool_input)
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
        async def interactive_tool(config: RunnableConfig, **tool_input):
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
            response = interrupt(request)

            # 完全参考参考文件的响应处理逻辑
            if response["type"] == "accept":
                try:
                    tool_response = await tool.ainvoke(input=tool_input)
                    return tool_response
                except Exception as e:
                    return f"工具执行失败: {str(e)}"

            elif response["type"] == "edit":
                # 如果是编辑，更新工具输入参数为响应中提供的参数
                tool_input = response["args"]["args"]
                try:
                    tool_response = await tool.ainvoke(input=tool_input)
                    return tool_response
                except Exception as e:
                    return f"工具执行失败: {str(e)}"

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
    state: Optional[Dict[str, Any]] = None
) -> List[BaseTool]:
    """
    批量包装工具 - 简化版本，直接返回包装后的工具列表
    """
    interactive_tools = []
    for tool in tools:
        try:
            interactive_tool = await wrap_interactive_tools(tool, state)
            interactive_tools.append(interactive_tool)
        except Exception as e:
            continue
    return interactive_tools