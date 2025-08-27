"""
通用中断节点模块
提供统一的中断处理机制，可以在任何图中复用
"""

import time
from typing import Dict, Any, Optional, List, Callable
from langchain_core.messages import AIMessage
from langgraph.prebuilt.interrupt import HumanInterrupt
from langgraph import types

# 导入必要的模块
from writer.core import create_workflow_processor


def create_interrupt_node(
    node_name: str,
    action_name: str,
    description_template: str,
    get_interrupt_data_func: Callable[[Dict[str, Any]], Dict[str, Any]],
    process_response_func: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None,
    allow_edit: bool = False,
    auto_approve_in_copilot: bool = True
):
    """
    创建统一的中断节点
    
    Args:
        node_name: 节点名称，用于日志和标识
        action_name: 动作名称，用于中断请求
        description_template: 描述模板，支持格式化
        get_interrupt_data_func: 从状态中提取中断数据的函数
        process_response_func: 处理用户响应的函数（可选）
        allow_edit: 是否允许编辑参数
        auto_approve_in_copilot: Copilot模式是否自动通过
    
    Returns:
        异步节点函数
    """
    
    async def interrupt_node(state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """统一的中断处理节点"""
        # 创建处理器
        processor = create_workflow_processor(node_name, f"{node_name}_中断处理")
        processor.writer.processing(f"开始{node_name}处理")
        
        start_time = time.time()
        mode = state.get("mode", "interactive")
        
        # Copilot模式处理
        if mode == "copilot" and auto_approve_in_copilot:
            processor.writer.processing("Copilot模式自动通过")

            # 如果有自定义响应处理函数，调用它
            if process_response_func:
                result = process_response_func(state, {"type": "auto_approve", "approved": True})
                state.update(result)

            processor.writer.processing("Copilot模式自动通过", auto_approved=True)
            
            # 添加自动通过消息
            if "messages" in state:
                state["messages"] = state.get("messages", []) + [
                    AIMessage(content=f"🤖 Copilot模式：{action_name}自动通过")
                ]
            
            return state
        
        # Interactive模式：使用统一的中断机制
        processor.writer.processing("准备用户确认...")
        
        # 获取中断数据
        try:
            interrupt_data = get_interrupt_data_func(state)
        except Exception as e:
            processor.writer.error(f"获取中断数据失败: {str(e)}", "InterruptDataError")
            return state
        
        # 格式化描述
        try:
            formatted_description = description_template.format(**interrupt_data)
        except Exception as e:
            formatted_description = f"{description_template}\n数据: {interrupt_data}"
        
        # 创建标准化的中断请求
        request: HumanInterrupt = {
            "action_request": {
                "action": action_name,
                "args": interrupt_data
            },
            "config": {
                "allow_accept": True,
                "allow_edit": allow_edit,
                "allow_respond": True
            },
            "description": f"{formatted_description}\n\n可选操作：\n- 输入 'yes' 确认通过\n- 输入 'no' 拒绝" + 
                          (f"\n- 输入 'edit' 修改参数" if allow_edit else "") +
                          "\n- 输入 'response' 提供自定义反馈",
        }
        
        processor.writer.processing("等待用户确认...")

        # 在中断前发送明确的中断消息
        processor.writer.interrupt(
            f"等待用户确认",
            message_type="interrupt_request",
            interrupt_content=formatted_description,
            node=node_name,
            action=action_name,
            args=interrupt_data,
            interrupt_id=f"{action_name}_{int(time.time() * 1000)}",
            interrupt_config={
                "allow_accept": True,
                "allow_edit": allow_edit,
                "allow_respond": True
            },
            timestamp=time.time()
        )

        # 调用统一的中断函数（这里会抛出Interrupt异常，暂停执行）
        response = types.interrupt(request)

        # 注意：下面的代码在中断时不会执行，只有在恢复执行时才会执行
        processor.writer.processing("处理用户响应...")
        
        # 标准化响应处理
        if response["type"] == "accept":
            approved = True
            result_data = {"approved": True, "type": "accept"}
            result_message = f"✅ {action_name}：确认通过"
            
        elif response["type"] == "reject":
            approved = False
            result_data = {"approved": False, "type": "reject"}
            result_message = f"❌ {action_name}：被拒绝"
            
        elif response["type"] == "edit" and allow_edit:
            # 编辑模式
            edited_args = response.get("args", {}).get("args", interrupt_data)
            approved = True
            result_data = {"approved": True, "type": "edit", "edited_args": edited_args}
            result_message = f"✏️ {action_name}：参数已修改并通过"
            
        elif response["type"] == "response":
            user_feedback_content = response.get("args", "")
            approved = True
            result_data = {"approved": True, "type": "response", "content": user_feedback_content}
            result_message = f"💬 {action_name}：用户反馈 - {user_feedback_content}"
            
        else:
            # 未知响应类型，默认拒绝
            approved = False
            result_data = {"approved": False, "type": "unknown", "raw_response": response}
            result_message = f"❓ {action_name}：未知响应，默认拒绝"
        
        # 如果有自定义响应处理函数，调用它
        if process_response_func:
            try:
                custom_result = process_response_func(state, result_data)
                if isinstance(custom_result, dict):
                    state.update(custom_result)
            except Exception as e:
                processor.writer.error(f"自定义响应处理失败: {str(e)}", "CustomResponseError")
        
        # 添加结果消息
        if "messages" in state:
            state["messages"] = state.get("messages", []) + [AIMessage(content=result_message)]
        
        # 记录执行时间
        execution_time = time.time() - start_time
        
        processor.writer.processing(
            result_message,
            approved=approved,
            response_data=result_data,
            action_name=action_name,
            execution_time=execution_time
        )
        
        return state
    
    return interrupt_node


def create_confirmation_node(
    node_name: str,
    title: str,
    message_template: str,
    get_data_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
):
    """
    创建简单的确认节点
    
    Args:
        node_name: 节点名称
        title: 确认标题
        message_template: 消息模板
        get_data_func: 获取数据的函数（可选）
    
    Returns:
        异步节点函数
    """
    
    def default_get_data(state: Dict[str, Any]) -> Dict[str, Any]:
        """默认的数据获取函数"""
        return {"title": title, "message": message_template}
    
    def default_process_response(state: Dict[str, Any], response_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认的响应处理函数"""
        # 更新状态中的确认信息
        if "confirmations" not in state:
            state["confirmations"] = {}
        
        state["confirmations"][node_name] = response_data
        return state
    
    return create_interrupt_node(
        node_name=node_name,
        action_name=f"confirm_{node_name}",
        description_template=message_template,
        get_interrupt_data_func=get_data_func or default_get_data,
        process_response_func=default_process_response,
        allow_edit=False,
        auto_approve_in_copilot=True
    )


def create_parameter_edit_node(
    node_name: str,
    action_name: str,
    description_template: str,
    get_params_func: Callable[[Dict[str, Any]], Dict[str, Any]],
    apply_params_func: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]
):
    """
    创建参数编辑节点
    
    Args:
        node_name: 节点名称
        action_name: 动作名称
        description_template: 描述模板
        get_params_func: 获取参数的函数
        apply_params_func: 应用参数的函数
    
    Returns:
        异步节点函数
    """
    
    def process_edit_response(state: Dict[str, Any], response_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理编辑响应"""
        if response_data.get("type") == "edit" and "edited_args" in response_data:
            # 应用编辑后的参数
            return apply_params_func(state, response_data["edited_args"])
        elif response_data.get("approved"):
            # 确认通过，使用原参数
            original_params = get_params_func(state)
            return apply_params_func(state, original_params)
        else:
            # 拒绝，不做任何更改
            return state
    
    return create_interrupt_node(
        node_name=node_name,
        action_name=action_name,
        description_template=description_template,
        get_interrupt_data_func=get_params_func,
        process_response_func=process_edit_response,
        allow_edit=True,
        auto_approve_in_copilot=True
    )
