"""
Human-in-the-Loop包装器
基于LangGraph的interrupt机制实现工具调用的人工审查功能
"""

import logging
from typing import Callable, Any, Dict
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from langgraph.prebuilt.interrupt import HumanInterrupt, HumanInterruptConfig

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
    description_template: str = None
) -> BaseTool:
    """
    为工具添加人工审查（human-in-the-loop）功能
    
    Args:
        tool: 可调用对象或 BaseTool 对象
        interrupt_config: 可选的人工中断配置
        description_template: 自定义描述模板
        
    Returns:
        BaseTool: 一个带有人工审查功能的 BaseTool 对象
    """
    # 检查传入的工具是否为 BaseTool 的实例
    if not isinstance(tool, BaseTool):
        # 如果不是 BaseTool，则将可调用对象转换为 BaseTool 对象
        tool = create_tool(tool)
    
    # 默认描述模板
    if description_template is None:
        description_template = (
            "准备调用 {tool_name} 工具：\n"
            "- 参数: {tool_input}\n\n"
            "请选择操作：\n"
            "- 输入 'yes' 接受工具调用\n"
            "- 输入 'no' 拒绝工具调用\n"
            "- 输入 'edit' 修改工具参数后调用\n"
            "- 输入 'response' 不调用工具直接反馈信息"
        )

    # 使用 create_tool 装饰器定义一个新的工具函数
    @create_tool(
        f"{tool.name}_with_hil",
        description=f"带有人工审查的{tool.description}",
        args_schema=tool.args_schema
    )
    async def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        """带有人工中断逻辑的工具调用函数"""
        
        # 创建人工中断请求
        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": description_template.format(
                tool_name=tool.name,
                tool_input=tool_input
            ),
        }
        
        # 调用 interrupt 函数，获取人工审查的响应
        response = interrupt(request)
        logger.info(f"收到人工审查响应: {response}")
        
        # 处理不同类型的响应
        if response["type"] == "accept":
            logger.info(f"工具调用已批准，执行 {tool.name}")
            try:
                result = await tool.ainvoke(input=tool_input)
                logger.info(f"工具执行结果: {result}")
                return result
            except Exception as e:
                error_msg = f"工具调用失败: {e}"
                logger.error(error_msg)
                return error_msg
                
        elif response["type"] == "edit":
            logger.info("使用修改后的参数执行工具")
            updated_input = response["args"]["args"]
            try:
                result = await tool.ainvoke(input=updated_input)
                logger.info(f"工具执行结果: {result}")
                return result
            except Exception as e:
                error_msg = f"工具调用失败: {e}"
                logger.error(error_msg)
                return error_msg
                
        elif response["type"] == "reject":
            logger.info("工具调用被拒绝")
            return "该工具调用被用户拒绝，请尝试其他方法。"
            
        elif response["type"] == "response":
            logger.info("用户提供了直接响应")
            user_feedback = response["args"]
            return f"用户反馈: {user_feedback}"
            
        else:
            raise ValueError(f"不支持的中断响应类型: {response['type']}")
    
    return call_tool_with_interrupt


# 示例工具定义
@create_tool("search_web", description="搜索网络信息的工具")
async def search_web(query: str) -> str:
    """
    模拟网络搜索工具
    
    Args:
        query: 搜索查询
        
    Returns:
        搜索结果
    """
    return f"搜索结果：关于'{query}'的相关信息..."


@create_tool("calculate", description="计算数学表达式的工具")
async def calculate(expression: str) -> str:
    """
    模拟计算工具
    
    Args:
        expression: 数学表达式
        
    Returns:
        计算结果
    """
    try:
        # 简单的计算示例（实际应用中需要更安全的实现）
        result = eval(expression)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"


@create_tool("send_email", description="发送邮件的工具")
async def send_email(to: str, subject: str, body: str) -> str:
    """
    模拟发送邮件工具
    
    Args:
        to: 收件人
        subject: 邮件主题
        body: 邮件内容
        
    Returns:
        发送结果
    """
    return f"邮件已发送至 {to}，主题：{subject}"


# 获取带有human-in-loop的工具列表
async def get_hil_tools():
    """获取所有带有human-in-loop功能的工具"""
    tools = []
    
    # 为每个工具添加human-in-loop包装
    tools.append(await add_human_in_the_loop(search_web))
    tools.append(await add_human_in_the_loop(calculate))
    tools.append(await add_human_in_the_loop(send_email))
    
    return tools
