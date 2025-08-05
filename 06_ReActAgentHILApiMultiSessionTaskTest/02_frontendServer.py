import uuid
import requests
import json
import traceback
from typing import Dict, Any, Optional
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from rich.progress import Progress



# Author:@南哥AGI研习社 (B站 or YouTube 搜索“南哥AGI研习社”)


# 创建自定义主题
custom_theme = Theme({
    "info": "cyan bold",
    "warning": "yellow bold",
    "success": "green bold",
    "error": "red bold",
    "heading": "magenta bold underline",
    "highlight": "blue bold",
})


# 初始化Rich控制台
console = Console(theme=custom_theme)

# 后端API地址
API_BASE_URL = "http://localhost:8001"


# 调用API接口获取当前系统内全部的会话状态信息
def get_system_info():
    """
    获取系统信息

    Args:

    Returns:
        服务端返回的结果
    """
    response = requests.get(f"{API_BASE_URL}/system/info")

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取系统信息失败: {response.status_code} - {response.text}")

# 调用API接口运行智能体并返回任务ID
def invoke_agent(user_id: str, session_id: str, task_id: str, query: str, system_message: str = "你会使用工具来帮助用户。如果工具使用被拒绝，请提示用户。"):
    """
    调用智能体处理查询，并等待完成或中断

    Args:
        user_id: 用户唯一标识
        session_id: 会话唯一标识
        query: 用户待查询的问题
        system_message: 系统提示词

    Returns:
        服务端返回的结果
    """
    # 发送请求到后端API
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "task_id": task_id,
        "query": query,
        "system_message": system_message
    }
    response = requests.post(f"{API_BASE_URL}/agent/invoke", json=payload)
    if response.status_code == 200:
        # console.print("[info]原始结果数据结构:[/info]")
        # console.print(response.json())
        return response.json()
    else:
        raise Exception(f"API调用失败: {response.status_code} - {response.text}")

# 调用API接口恢复被中断的智能体运行并等待运行完成或再次中断并返回任务ID
def resume_agent(user_id: str, session_id: str, task_id: str, response_type: str, args: Optional[Dict[str, Any]] = None):
    """
    发送响应以恢复智能体执行

    Args:
        user_id: 用户唯一标识
        session_id: 用户的会话唯一标识
        response_type: 响应类型：accept(允许调用), edit(调整工具参数，此时args中携带修改后的调用参数), response(直接反馈信息，此时args中携带修改后的调用参数)，reject(不允许调用)
        args: 如果是edit, response类型，可能需要额外的参数

    Returns:
        服务端返回的结果
    """
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "task_id": task_id,
        "response_type": response_type,
        "args": args
    }
    response = requests.post(f"{API_BASE_URL}/agent/resume", json=payload)
    if response.status_code == 200:
        # console.print("[info]原始结果数据结构:[/info]")
        # console.print(response.json())
        return response.json()
    else:
        raise Exception(f"API调用失败: {response.status_code} - {response.text}")

# 调用API接口获取指定用户ID的指定会话ID的所有task_id
def get_session_task_ids(user_id: str, session_id: str):
    """
    获取智能体状态

    Args:
        user_id: 用户唯一标识
        session_id：会话唯一标识

    Returns:
        服务端返回的结果
    """
    response = requests.get(f"{API_BASE_URL}/agent/tasks/{user_id}/{session_id}")

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取智能体状态失败: {response.status_code} - {response.text}")

# 调用API接口写入指定用户长期记忆内容
def write_long_term(user_id: str, memory_info: str):
    """
    写入指定用户长期记忆内容

    Args:
        user_id: 用户唯一标识
        memory_info: 写入的内容

    Returns:
        服务端返回的结果
    """
    # 发送请求到后端API
    payload = {
        "user_id": user_id,
        "memory_info": memory_info
    }

    console.print("[info]正在发送请求写入指定用户长期记忆内容，请稍候...[/info]")

    with Progress() as progress:
        task = progress.add_task("[cyan]写入长期记忆处理中...", total=None)
        response = requests.post(f"{API_BASE_URL}/agent/write/longterm", json=payload)
        progress.update(task, completed=100)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API调用失败: {response.status_code} - {response.text}")

# 调用API接口获取指定用户当前会话和任务ID的对应的状态数据
def get_agent_status(user_id: str, session_id: str, task_id: str):
    """
    获取智能体状态

    Args:
        user_id: 用户唯一标识
        session_id：会话唯一标识

    Returns:
        服务端返回的结果
    """
    response = requests.get(f"{API_BASE_URL}/agent/status/{user_id}/{session_id}/{task_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取智能体状态失败: {response.status_code} - {response.text}")

# 调用API接口获取指定用户ID的最近一次修改的会话ID
def get_user_active_sessionid(user_id: str):
    """
    获取系统信息

    Args:
        user_id: 用户唯一标识

    Returns:
        服务端返回的结果
    """
    response = requests.get(f"{API_BASE_URL}/agent/active/sessionid/{user_id}")

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取系统信息失败: {response.status_code} - {response.text}")

# 调用API接口获取指定用户ID的所有session_id
def get_user_sessionids(user_id: str):
    """
    获取系统信息

    Args:
        user_id: 用户唯一标识

    Returns:
        服务端返回的结果
    """
    response = requests.get(f"{API_BASE_URL}/agent/sessionids/{user_id}")

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取系统信息失败: {response.status_code} - {response.text}")

# 调用API接口删除指定用户当前会话
def delete_agent_session(user_id: str, session_id: str):
    """
    删除用户会话

    Args:
        user_id: 用户唯一标识

    Returns:
        服务端返回的结果
    """
    response = requests.delete(f"{API_BASE_URL}/agent/session/{user_id}/{session_id}")

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        # 会话不存在也算成功
        return {"status": "success", "message": f"用户 {user_id}:{session_id} 的会话不存在"}
    else:
        raise Exception(f"删除会话失败: {response.status_code} - {response.text}")


# 显示会话的详细信息，包括会话状态、上次查询、响应数据等
def display_session_info(status_response):
    """
    显示会话的详细信息，包括会话状态、上次查询、响应数据等

    参数:
        status_response: 会话状态响应数据
    """
    # 基本会话信息面板
    user_id = status_response["user_id"]
    session_id = status_response.get("session_id", "未知")
    task_id = status_response.get("task_id", "未知")
    status = status_response["status"]
    last_query = status_response.get("last_query", "无")
    last_updated = status_response.get("last_updated")

    # 构建信息面板内容
    panel_content = [
        f"用户ID: {user_id}",
        f"会话ID: {session_id}",
        f"任务ID: {task_id}",
        f"状态: [bold]{status}[/bold]",
        f"上次查询: {last_query}"
    ]

    # 添加时间戳
    if last_updated:
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_updated))
        panel_content.append(f"上次更新: {time_str}")

    # 根据状态设置合适的面板样式
    if status == "interrupted":
        border_style = "yellow"
        title = "[warning]中断会话[/warning]"
    elif status == "completed":
        border_style = "green"
        title = "[success]完成会话[/success]"
    elif status == "error":
        border_style = "red"
        title = "[error]错误会话[/error]"
    elif status == "running":
        border_style = "blue"
        title = "[info]运行中会话[/info]"
    elif status == "idle":
        border_style = "cyan"
        title = "[info]空闲会话[/info]"
    else:
        border_style = "white"
        title = "[info]未知状态会话[/info]"

    # 显示基本面板
    console.print(Panel(
        "\n".join(panel_content),
        title=title,
        border_style=border_style
    ))

    # 显示额外的响应数据
    if status_response.get("last_response"):
        last_response = status_response["last_response"]

        # 根据会话状态显示不同的响应数据
        if status == "completed" and last_response.get("result"):
            result = last_response["result"]
            if "messages" in result:
                final_message = result["messages"][-1]
                console.print(Panel(
                    Markdown(final_message["content"]),
                    title="[success]上次智能体回答[/success]",
                    border_style="green"
                ))

        elif status == "interrupted" and last_response.get("interrupt_data"):
            interrupt_data = last_response["interrupt_data"]
            message = interrupt_data.get("description", "需要您的输入")
            console.print(Panel(
                message,
                title=f"[warning]中断消息[/warning]",
                border_style="yellow"
            ))

        elif status == "error":
            error_msg = last_response.get("message", "未知错误")
            console.print(Panel(
                error_msg,
                title="[error]错误信息[/error]",
                border_style="red"
            ))

# 检查用户会话状态并尝试恢复
def check_and_restore_session(user_id: str, session_id: str, task_id: str):
    """
    检查用户会话状态并尝试恢复

    参数:
        user_id: 用户ID
        session_id: 会话ID
        task_id: 任务ID

    返回:
        tuple: (是否有活跃会话, 会话状态响应)
    """
    try:
        # 调用API接口获取指定用户当前会话和任务ID的对应的状态数据
        status_response = get_agent_status(user_id, session_id, task_id)

        # 如果没有找到会话
        if status_response["status"] == "not_found":
            console.print("[info]没有找到现有会话状态数据，基于当前会话开始继续查询…[/info]")
            return False, None

        # 显示会话详细信息
        console.print(Panel(
            f"用户ID: {user_id}\n"
            f"会话ID: {status_response.get('session_id', '未知')}\n"
            f"任务ID: {status_response.get('task_id', '未知')}\n"
            f"状态: [bold]{status_response['status']}[/bold]\n"
            f"上次查询: {status_response.get('last_query', '无')}\n"
            f"上次更新: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status_response['last_updated'])) if status_response.get('last_updated') else '未知'}\n",
            title="[info]发现现有会话[/info]",
            border_style="cyan"
        ))

        # 显示会话的详细信息
        display_session_info(status_response)

        # 根据会话状态进行自动处理
        if status_response["status"] == "interrupted":
            console.print(Panel(
                "会话处于中断状态，需要您的响应才能继续。\n"
                "系统将自动恢复上次的中断点，您需要提供决策。",
                title="[warning]会话已中断[/warning]",
                border_style="yellow"
            ))

            # 如果有上次的响应且包含中断数据
            if (status_response.get("last_response") and
                    status_response["last_response"].get("interrupt_data")):

                # 显示中断类型和相关信息
                interrupt_data = status_response["last_response"]["interrupt_data"]

                action_request = interrupt_data.get("action_request","未知中断")
                tool = action_request.get("action","未知工具")
                args = action_request.get("args","未知参数")
                console.print(f"[info]相关工具: {tool}[/info]")
                console.print(f"[info]工具参数: {args}[/info]")

                # 自动恢复中断处理
                console.print("[info]自动恢复中断处理...[/info]")
                return True, status_response
            else:
                console.print("[warning]中断状态会话缺少必要的中断数据，无法恢复[/warning]")
                console.print("[info]将创建新会话[/info]")
                return False, None

        if status_response["status"] == "completed":
            console.print(Panel(
                "会话已完成，上次响应结果可用。\n"
                "系统将显示上次结果并自动开启新会话。",
                title="[success]会话已完成[/success]",
                border_style="green"
            ))

            # 显示上次的结果
            if (status_response.get("last_response") and
                    status_response["last_response"].get("result")):

                # 提取并显示结果
                last_result = status_response["last_response"]["result"]
                if "messages" in last_result:
                    final_message = last_result["messages"][-1]

                    console.print(Panel(
                        Markdown(final_message["content"]),
                        title="[success]上次智能体回答[/success]",
                        border_style="green"
                    ))

            console.print("[info]基于当前会话开始继续...[/info]")
            return False, None

        elif status_response["status"] == "error":
            # 获取错误信息
            error_msg = "未知错误"
            if status_response.get("last_response"):
                error_msg = status_response["last_response"].get("message", "未知错误")

            console.print(Panel(
                f"上次会话发生错误: {error_msg}\n"
                "系统将自动开始新会话。",
                title="[error]会话错误[/error]",
                border_style="red"
            ))

            console.print("[info]自动开始新会话...[/info]")
            return False, None

        elif status_response["status"] == "running":
            console.print(Panel(
                "会话正在运行中，这可能是因为:\n"
                "1. 另一个客户端正在使用此会话\n"
                "2. 上一次会话异常终止，状态未更新\n"
                "系统将自动等待会话状态变化。",
                title="[warning]会话运行中[/warning]",
                border_style="yellow"
            ))

            # 自动等待会话状态变化
            console.print("[info]自动等待会话状态变化...[/info]")
            with Progress() as progress:
                task = progress.add_task("[cyan]等待会话完成...", total=None)
                max_attempts = 30  # 最多等待30秒
                attempt_count = 0

                for i in range(max_attempts):
                    attempt_count = i
                    # 调用API接口获取指定用户当前会话和任务ID的对应的状态数据
                    current_status = get_agent_status(user_id, session_id, task_id)
                    if current_status["status"] != "running":
                        progress.update(task, completed=100)
                        console.print(f"[success]会话状态已更新为: {current_status['status']}[/success]")
                        break
                    time.sleep(1)

                # 如果等待超时
                if attempt_count >= max_attempts - 1:
                    console.print("[warning]等待超时，会话可能仍在运行[/warning]")
                    console.print("[info]为避免冲突，将创建新会话[/info]")
                    return False, None

                # 获取最新状态（递归调用）
                return check_and_restore_session(user_id, session_id, task_id)

        elif status_response["status"] == "idle":
            console.print(Panel(
                "会话处于空闲状态，准备接收新查询。\n"
                "系统将自动使用现有会话。",
                title="[info]会话空闲[/info]",
                border_style="blue"
            ))

            # 自动使用现有会话
            console.print("[info]自动使用现有会话[/info]")
            return True, status_response

        else:
            # 未知状态
            console.print(Panel(
                f"会话处于未知状态: {status_response['status']}\n"
                "系统将自动创建新会话以避免潜在问题。",
                title="[warning]未知状态[/warning]",
                border_style="yellow"
            ))

            console.print("[info]自动创建新会话...[/info]")
            return False, None

    except Exception as e:
        console.print(f"[error]检查会话状态时出错: {str(e)}[/error]")
        console.print(traceback.format_exc())
        console.print("[info]将创建新会话[/info]")
        return False, None

# 处理工具使用审批类型的中断
def handle_tool_interrupt(interrupt_data, user_id, session_id, task_id):
    """
    处理工具使用审批类型的中断

    参数:
        interrupt_data: 中断数据
        user_id: 用户ID
        session_id: 会话ID
        task_id: 任务ID

    返回:
        处理后的响应
    """
    message = interrupt_data.get("description", "需要您的输入")

    # 显示工具使用审批提示
    console.print(Panel(
        f"{message}",
        title=f"[warning]智能体需要您的决定[/warning]",
        border_style="yellow"
    ))

    # 获取用户输入
    user_input = Prompt.ask("[highlight]您的选择[/highlight]")

    # 处理用户输入
    try:
        while True:
            if user_input.lower() == "yes":
                # 调用API接口恢复被中断的智能体运行并等待运行完成或再次中断并返回任务ID
                response = resume_agent(user_id, session_id, task_id, "accept")
                break
            elif user_input.lower() == "no":
                # 调用API接口恢复被中断的智能体运行并等待运行完成或再次中断并返回任务ID
                response = resume_agent(user_id, session_id, task_id,"reject")
                break
            elif user_input.lower() == "edit":
                # 获取新的查询内容
                new_query = Prompt.ask("[highlight]请调整新的参数[/highlight]")
                # 调用API接口恢复被中断的智能体运行并等待运行完成或再次中断并返回任务ID
                response = resume_agent(user_id, session_id, task_id,"edit", args={"args": json.loads(new_query)})
                break
            elif user_input.lower() == "response":
                # 获取新的查询内容
                new_query = Prompt.ask("[highlight]不调用工具直接反馈信息[/highlight]")
                # 调用API接口恢复被中断的智能体运行并等待运行完成或再次中断并返回任务ID
                response = resume_agent(user_id, session_id, task_id,"response", args={"args": new_query})
                break
            else:
                console.print("[error]无效输入，请输入 'yes'、'no' 、'edit' 或 'response'[/error]")
                user_input = Prompt.ask("[highlight]您的选择[/highlight]")

        # 重新获取用户输入（维持当前响应不变）
        return process_agent_response(response, user_id)

    except Exception as e:
        console.print(f"[error]处理响应时出错: {str(e)}[/error]")
        return None

# 处理智能体响应，包括处理中断和显示结果
def process_agent_response_resume(response, user_id):
    # 防御性检查，确保response不为空
    if not response:
        console.print("[error]收到空响应，无法处理[/error]")
        return None

    try:
        session_id = response["session_id"]
        task_id = response["task_id"]
        status = response["status"]
        timestamp = response.get("timestamp", time.time())

        # 显示时间戳和会话ID（便于调试和跟踪）
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        console.print(f"[info]响应时间: {time_str} | 会话ID: {session_id}[/info]")

        # 处理不同状态
        if status == "interrupted":
            # 获取中断数据
            interrupt_data = response.get("interrupt_data", {})

            try:
                # 进入中断处理函数
                return handle_tool_interrupt(interrupt_data, user_id, session_id, task_id)

            except Exception as e:
                console.print(f"[error]处理中断响应时出错: {str(e)}[/error]")
                console.print(f"[info]中断状态已保存，您可以稍后恢复会话[/info]")
                console.print(traceback.format_exc())
                return None

        elif status == "completed":
            # 显示结果
            result = response.get("result", {})
            if result and "messages" in result:
                final_message = result["messages"][-1]
                console.print(Panel(
                    Markdown(final_message["content"]),
                    title="[success]智能体回答[/success]",
                    border_style="green"
                ))
            else:
                console.print("[warning]智能体没有返回有效的消息[/warning]")
                if isinstance(result, dict):
                    pass
                    # console.print("[info]原始结果数据结构:[/info]")
                    # console.print(result)

            return result

        elif status == "error":
            # 显示错误信息
            error_msg = response.get("message", "未知错误")
            console.print(Panel(
                f"{error_msg}",
                title="[error]处理过程中出错[/error]",
                border_style="red"
            ))
            return None

        elif status == "running":
            # 处理正在运行状态
            console.print("[info]智能体正在处理您的请求，请稍候...[/info]")
            return response

        elif status == "idle":
            # 处理空闲状态
            console.print("[info]智能体处于空闲状态，准备接收新的请求[/info]")
            return response

        else:
            # 其他未知状态
            console.print(f"[warning]智能体处于未知状态: {status} - {response.get('message', '无消息')}[/warning]")
            return response

    except KeyError as e:
        console.print(f"[error]响应格式错误，缺少关键字段 {e}[/error]")
        return None
    except Exception as e:
        console.print(f"[error]处理智能体响应时出现未预期错误: {str(e)}[/error]")
        console.print(traceback.format_exc())
        return None

# 处理智能体响应，包括处理中断和显示结果
def process_agent_response(response, user_id):
    # 防御性检查，确保response不为空
    if not response:
        console.print("[error]收到空响应，无法处理[/error]")
        return None

    try:
        console.print(f"[info]收到响应数据:{response}[/info]")
        session_id = response["session_id"]
        task_id = response["task_id"]
        timestamp = response.get("timestamp", time.time())

        # 显示时间戳和会话ID（便于调试和跟踪）
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        console.print(f"[info]响应时间: {time_str} | 会话ID: {session_id} | 任务ID: {task_id}[/info]")

        return task_id

    except KeyError as e:
        console.print(f"[error]响应格式错误，缺少关键字段 {e}[/error]")
        return None
    except Exception as e:
        console.print(f"[error]处理智能体响应时出现未预期错误: {str(e)}[/error]")
        console.print(traceback.format_exc())
        return None


# 主函数，运行客户端
def main():
    console.print(Panel(
        "前端客户端模拟服务(异步任务调度)",
        title="[heading]ReAct Agent智能体交互演示系统[/heading]",
        border_style="magenta"
    ))

    try:
        # 调用API接口获取当前系统内全部的会话状态信息
        system_info = get_system_info()
        console.print(f"[info]当前系统内全部会话总计: {system_info['sessions_count']}[/info]")
        if system_info['active_users']:
            console.print(f"[info]系统内全部用户及用户会话: {system_info['active_users']}[/info]")
    except Exception:
        console.print("[warning]无法获取当前系统内全部的会话状态信息，但这不影响使用[/warning]")

    # 输入用户ID
    default_user_id = f"user_{int(time.time())}"
    user_id = Prompt.ask("[info]请输入用户ID[/info] (新ID将创建新用户，已有ID将恢复使用该用户)", default=default_user_id)

    try:
        # 调用API接口获取指定用户ID的最近一次修改的会话ID
        active_session_id = get_user_active_sessionid(user_id)
        # 若存在 则直接使用该会话ID创建任务
        if active_session_id["active_session_id"]:
            session_id = active_session_id["active_session_id"]
            # 创建新的任务ID
            task_id = str(uuid.uuid4())
            console.print(f"[info]将为你打开最近一次会话继续，会话ID为 {session_id} [/info]")
        # 若不存在 则创建新会话
        else:
            # 创建新的会话ID和任务ID
            session_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())
            console.print(f"[info]将为你打开一个全新会话，会话ID为 {session_id} [/info]")
    except Exception:
        console.print("[warning]无法获取指定用户ID的最近一次修改的会话ID，但这不影响使用[/warning]")

    # 初始化状态 是否存在待恢复的现有会话及会话状态数据
    has_active_session = False
    session_status = None

    # 主交互循环
    while True:
        try:
            # 若存在待恢复的现有会话及会话状态数据进行会话恢复处理
            if has_active_session and session_status:
                # 若是中断状态则处理中断
                if session_status["status"] == "interrupted":
                    console.print("[info]自动处理中断的会话...[/info]")
                    if "last_response" in session_status and session_status["last_response"]:
                        # 使用process_agent_response_resume处理之前的中断
                        result = process_agent_response_resume(session_status["last_response"], user_id)
                        # 调用API接口获取指定用户当前会话和任务ID的对应的状态数据
                        current_status = get_agent_status(user_id, session_id, task_id)
                        # 如果通过处理中断后完成了本次会话查询，自动创建新的查询
                        if current_status["status"] == "completed":
                            # 显示完成消息
                            console.print("[success]本次查询已完成[/success]")
                            console.print("[info]自动开始新的查询...[/info]")
                            has_active_session = False
                            session_status = None
                        else:
                            has_active_session = True
                            session_status = current_status

            # 获取用户查询
            query = Prompt.ask(
                "\n[info]请输入您的问题[/info] (输入 'exit' 退出，输入 'status' 查询状态，输入 'new' 开始新会话，输入 'history' 恢复历史会话，输入 'setting' 偏好设置)",
                default="你好")

            # 处理特殊命令 退出
            if query.lower() == 'exit':
                console.print("[info]感谢使用，再见！[/info]")
                break

            # 处理特殊命令 指定用户开启一个新会话
            elif query.lower() == 'new':
                session_id = str(uuid.uuid4())
                has_active_session = False
                session_status = None
                console.print(f"[info]将为你打开一个全新会话，会话ID为 {session_id}[/info]")
                continue

            # 处理特殊命令 指定用户使用历史会话
            elif query.lower() == 'history':
                try:
                    # 调用API接口获取指定用户ID的所有session_id
                    session_ids = get_user_sessionids(user_id)
                    # 若存在会话ID 则选择某个历史会话恢复
                    if session_ids['session_ids']:
                        console.print(f"[info]当前用户{user_id}的历史会话有: {session_ids['session_ids']}[/info]")
                        # 输入用户的会话ID
                        session_id = Prompt.ask("[info]请输入历史会话ID[/info] (这里演示请输入历史会话ID自动恢复会话)")
                        # 调用API接口获取指定用户ID的指定会话ID的所有task_id
                        task_ids = get_session_task_ids(user_id, session_id)
                        # 若存在任务ID 则选择某个历史任务恢复或查看详情
                        if task_ids['task_ids']:
                            console.print(f"[info]当前会话{session_id}的历史任务有: {task_ids['task_ids']}[/info]")
                            # 输入用户的任务ID
                            task_id = Prompt.ask("[info]请输入历史任务ID[/info] (这里演示请输入历史任务ID自动恢复任务)")
                            # 调用API接口获取指定用户当前会话和任务ID的对应的状态数据
                            latest_status = get_agent_status(user_id, session_id, task_id)
                            # 若状态为中断则尝试自动恢复现有会话
                            if latest_status["status"] == "interrupted":
                                # 检查会话是否存在并尝试自动恢复现有会话
                                has_active_session, session_status = check_and_restore_session(user_id, session_id, task_id)
                                continue
                            # 若状态为非中断
                            # console.print(f"[info]任务ID为 {task_id}的状态数据为:{latest_status}[/info]")
                            console.print(Panel(
                                renderable=f"用户ID: {latest_status['user_id']}\n"
                                f"会话ID: {latest_status['session_id']}\n"
                                f"任务ID: {latest_status['task_id']}\n"
                                f"会话状态: {latest_status['status']}\n"
                                f"上次更新: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest_status['last_updated'])) if latest_status.get('last_updated') else '未知'}\n"
                                f"上次查询: {latest_status['last_query'] or '无'}\n"
                                f"上次响应: {latest_status['last_response'] or '无'}\n",
                                title="[info]当前会话状态[/info]",
                                border_style="cyan"
                            ))
                            # 在当前选择的会话中开启一个新任务
                            has_active_session = False
                            session_status = None
                            console.print(f"[info]将为你打开一个全新任务，任务ID为 {task_id}[/info]")
                            continue
                        # 若不存在任务ID 在当前选择的会话中开启一个新任务
                        else:
                            has_active_session = False
                            session_status = None
                            console.print(f"[info]将为你打开一个全新任务，任务ID为 {task_id}[/info]")
                            continue
                    # 若不存在会话ID 则开启一个新会话
                    else:
                        session_id = str(uuid.uuid4())
                        has_active_session = False
                        session_status = None
                        console.print(f"[info]将为你打开一个全新会话，会话ID为 {session_id}[/info]")
                        continue

                except Exception:
                    has_active_session = False
                    session_status = None
                    console.print("[warning]无法获取指定用户ID的所有session_id，但这不影响使用[/warning]")
                    continue

            # 处理特殊命令 指定用户保存偏好设置到长期记忆
            elif query.lower() == 'setting':
                try:
                    memory_info = Prompt.ask("[info]请输入需要存储到长期记忆中的偏好设置内容[/info]")
                    # 写入指定用户长期记忆内容
                    response = write_long_term(user_id, memory_info)
                    # 写入后则继续查询
                    console.print(f"[info]用户 {user_id} 写入数据完成，继续查询…[/info]")
                    has_active_session = False
                    session_status = None
                    continue
                except Exception:
                    console.print("[warning]无法写入长期记忆，但这不影响使用[/warning]")
                    has_active_session = False
                    session_status = None
                    continue

            console.print("[info]正在提交查询，请求运行智能体...[/info]")
            task_id = str(uuid.uuid4())
            # 调用API接口运行智能体并返回任务ID
            response = invoke_agent(user_id, session_id, task_id, query)
            # 处理智能体返回的响应
            result = process_agent_response(response, user_id)
            console.print(f"[info]本次查询任务已成功提交，任务ID为 {result} ,请输入 history 特殊指令查看任务完成情况[/info]")

        except KeyboardInterrupt:
            console.print("\n[warning]用户中断，正在退出...[/warning]")
            console.print("[info]会话状态已保存，可以在下次使用相同用户ID恢复[/info]")
            break

        except Exception as e:
            console.print(f"[error]运行过程中出错: {str(e)}[/error]")
            console.print(traceback.format_exc())
            task_id = str(uuid.uuid4())
            has_active_session = False
            session_status = None
            continue



if __name__ == "__main__":
    main()
