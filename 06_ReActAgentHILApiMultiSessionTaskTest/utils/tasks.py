import asyncio
from fastapi import HTTPException
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
from typing import Dict, Any, Optional, List
from celery import Celery
import time
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool
from langchain_core.messages.utils import trim_messages
from .config import Config
from .llms import get_llm
from .tools import get_tools
from .models import AgentResponse
from .redis import RedisSessionManager, get_session_manager
from langgraph.types import interrupt, Command



# Author:@南哥AGI研习社 (B站 or YouTube 搜索“南哥AGI研习社”)


# 设置日志基本配置，级别为DEBUG或INFO
logger = logging.getLogger(__name__)
# 设置日志器级别为DEBUG
logger.setLevel(logging.DEBUG)
logger.handlers = []  # 清空默认处理器
# 使用ConcurrentRotatingFileHandler
handler = ConcurrentRotatingFileHandler(
    # 日志文件
    Config.LOG_FILE,
    # 日志文件最大允许大小为5MB，达到上限后触发轮转
    maxBytes=Config.MAX_BYTES,
    # 在轮转时，最多保留3个历史日志文件
    backupCount=Config.BACKUP_COUNT
)
# 设置处理器级别为DEBUG
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)


# 创建Celery实例
celery_app = Celery(
    # Celery应用名称
    main='01_backendServer',
    # 消息代理URL，使用Redis
    broker=Config.CELERY_BROKER_URL
)

# 设置Celery配置参数
celery_app.conf.update(
    # 任务序列化格式
    task_serializer='json',
    # 可接受的内容类型
    accept_content=['json'],
    # 结果序列化格式
    result_serializer='json',
    # 时区设置
    timezone='Asia/Shanghai',
    # 启用UTC时间
    enable_utc=True,
)


# 针对短期记忆修剪聊天历史消息 限制消息的token数量
def trimmed_messages_hook(state):
    """
    修剪聊天历史消息，限制消息的 token 数量

    Args:
        state: 包含消息的字典，通常包含 "messages" 键

    Returns:
        dict: 包含修剪后消息的字典，键为 "llm_input_messages"
    """
    trimmed_messages = trim_messages(
        messages=state["messages"],
        max_tokens=20,
        strategy="last",
        token_counter=len,
        start_on="human",
        allow_partial=False
    )
    return {"llm_input_messages": trimmed_messages}

# 读取指定用户长期记忆中的内容
async def read_long_term_info(user_id: str, store):
    """
    读取指定用户长期记忆中的内容

    Args:
        user_id: 用户的唯一标识

    Returns:
        Dict[str, Any]: 包含记忆内容和状态的响应
    """
    try:
        # 指定命名空间
        namespace = ("memories", user_id)

        # 搜索记忆内容
        memories = await store.asearch(namespace, query="")

        # 处理查询结果
        if memories is None:
            raise HTTPException(
                status_code=500,
                detail="查询返回无效结果，可能是存储系统错误。"
            )

        # 提取并拼接记忆内容
        long_term_info = " ".join(
            [d.value["data"] for d in memories if isinstance(d.value, dict) and "data" in d.value]
        ) if memories else ""

        # 记录查询成功的日志
        logger.info(f"成功获取用户ID: {user_id} 的长期记忆，内容长度: {len(long_term_info)} 字符")

        # 返回结构化响应
        return {
            "success": True,
            "user_id": user_id,
            "long_term_info": long_term_info,
            "message": "长期记忆获取成功" if long_term_info else "未找到长期记忆内容"
        }

    except Exception as e:
        # 处理其他未预期的错误
        logger.error(f"获取用户ID: {user_id} 的长期记忆时发生意外错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取长期记忆失败: {str(e)}"
        )

# 解析state消息列表进行格式化展示
async def parse_messages(messages: List[Any]) -> None:
    """
    解析消息列表，打印 HumanMessage、AIMessage 和 ToolMessage 的详细信息

    Args:
        messages: 包含消息的列表，每个消息是一个对象
    """
    print("=== 消息解析结果 ===")
    for idx, msg in enumerate(messages, 1):
        print(f"\n消息 {idx}:")
        # 获取消息类型
        msg_type = msg.__class__.__name__
        print(f"类型: {msg_type}")
        # 提取消息内容
        content = getattr(msg, 'content', '')
        print(f"内容: {content if content else '<空>'}")
        # 处理附加信息
        additional_kwargs = getattr(msg, 'additional_kwargs', {})
        if additional_kwargs:
            print("附加信息:")
            for key, value in additional_kwargs.items():
                if key == 'tool_calls' and value:
                    print("  工具调用:")
                    for tool_call in value:
                        print(f"    - ID: {tool_call['id']}")
                        print(f"      函数: {tool_call['function']['name']}")
                        print(f"      参数: {tool_call['function']['arguments']}")
                else:
                    print(f"  {key}: {value}")
        # 处理 ToolMessage 特有字段
        if msg_type == 'ToolMessage':
            tool_name = getattr(msg, 'name', '')
            tool_call_id = getattr(msg, 'tool_call_id', '')
            print(f"工具名称: {tool_name}")
            print(f"工具调用 ID: {tool_call_id}")
        # 处理 AIMessage 的工具调用和元数据
        if msg_type == 'AIMessage':
            tool_calls = getattr(msg, 'tool_calls', [])
            if tool_calls:
                print("工具调用:")
                for tool_call in tool_calls:
                    print(f"  - 名称: {tool_call['name']}")
                    print(f"    参数: {tool_call['args']}")
                    print(f"    ID: {tool_call['id']}")
            # 提取元数据
            metadata = getattr(msg, 'response_metadata', {})
            if metadata:
                print("元数据:")
                token_usage = metadata.get('token_usage', {})
                print(f"  令牌使用: {token_usage}")
                print(f"  模型名称: {metadata.get('model_name', '未知')}")
                print(f"  完成原因: {metadata.get('finish_reason', '未知')}")
        # 打印消息 ID
        msg_id = getattr(msg, 'id', '未知')
        print(f"消息 ID: {msg_id}")
        print("-" * 50)

# 处理智能体返回结果 可能是中断，也可能是最终结果
async def process_agent_result(
        session_id: str,
        task_id: str,
        result: Dict[str, Any],
        user_id: Optional[str] = None,
        session_manager: Optional[RedisSessionManager] = None
) -> AgentResponse:
    """
    处理智能体执行结果，统一处理中断和结果

    Args:
        session_id: 会话ID
        task_id: 任务ID
        result: 智能体执行结果
        user_id: 用户ID，如果提供，将更新会话状态
        session_manager: Redis会话管理器实例，用于更新会话状态

    Returns:
        AgentResponse: 标准化的响应对象
    """
    response = None
    try:
        # 检查是否有中断
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            # 确保中断数据有类型信息
            if "interrupt_type" not in interrupt_data:
                interrupt_data["interrupt_type"] = "unknown"
            # 返回中断信息
            response = AgentResponse(
                session_id=session_id,
                task_id=task_id,
                status="interrupted",
                interrupt_data=interrupt_data
            )
            logger.info(f"当前触发工具调用中断:{response}")
        # 如果没有中断，返回最终结果
        else:
            response = AgentResponse(
                session_id=session_id,
                task_id=task_id,
                status="completed",
                result=result
            )
            logger.info(f"最终智能体回复结果:{response}")

    except Exception as e:
        response = AgentResponse(
            session_id=session_id,
            task_id=task_id,
            status="error",
            message=f"处理智能体结果时出错: {str(e)}"
        )
        logger.error(f"处理智能体结果时出错:{response}")
    # 检查指定用户ID的指定session_id是否存在
    exists = await session_manager.session_id_exists(user_id, session_id)
    # 若存在 则更新状态数据
    if exists:
        await session_manager.update_session(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            status=response.status,
            last_query=None,
            last_response=response,
            last_updated=time.time(),
            ttl=Config.TTL
        )

    return response

# 筛选最近一次完整对话
def filter_last_human_conversation(data):
    if data['result'] is not None:
        # 获取 messages 列表
        messages = data['result']['messages']

        # 找到最后一个 type 为 human 的消息的索引
        last_human_index = -1
        for i, message in enumerate(messages):
            if message['type'] == 'human':
                last_human_index = i

        # 如果没找到 human 消息，返回原始结构但 messages 为空
        if last_human_index == -1:
            return {
                'session_id': data['session_id'],
                'status': data['status'],
                'timestamp': data['timestamp'],
                'message': data['message'],
                'result': {'messages': []}
            }

        # 筛选最后一个 human 消息及其后续消息
        filtered_messages = messages[last_human_index:]

        # 保留原始结构，只替换 messages
        return {
            'session_id': data['session_id'],
            'status': data['status'],
            'timestamp': data['timestamp'],
            'message': data['message'],
            'result': {'messages': filtered_messages}
        }
    # 若有中断数据
    elif data['interrupt_data'] is not None:
        return {
            'session_id': data['session_id'],
            'status': data['status'],
            'timestamp': data['timestamp'],
            'message': data['message'],
            'result': {'interrupt_data': data['interrupt_data']}
        }
    else:
        return {
            'session_id': data['session_id'],
            'status': data['status'],
            'timestamp': data['timestamp'],
            'message': data['message'],
            'result': {'messages': []}
        }


# 定义Celery任务：异步运行智能体
@celery_app.task
def invoke_agent_task(user_id: str, session_id: str, task_id: str, query: str, system_prompt: str):
    """
    异步运行智能体，处理用户请求并返回结果

    Args:
        user_id: 用户唯一标识
        session_id: 会话唯一标识
        task_id: 任务唯一标识
        query: 用户的问题
        system_prompt: 系统提示词

    Returns:
        dict: 智能体处理结果，转换为字典格式
    """
    # 异步执行智能体调用逻辑
    async def run_invoke():
        try:
            # 初始化Redis会话管理器
            session_manager = get_session_manager()

            # 更新会话状态为运行中
            await session_manager.update_session(
                user_id=user_id,
                session_id=session_id,
                task_id=task_id,
                status="running",
                last_query=query,
                last_updated=time.time(),
                ttl=Config.TTL
            )

            # 创建数据库连接池
            async with AsyncConnectionPool(
                conninfo=Config.DB_URI,
                min_size=Config.MIN_SIZE,
                max_size=Config.MAX_SIZE,
                kwargs={"autocommit": True, "prepare_threshold": 0}
            ) as pool:
                # 初始化短期记忆检查点
                checkpointer = AsyncPostgresSaver(pool)
                # 初始化长期记忆存储
                store = AsyncPostgresStore(pool)
                # 获取语言模型
                llm_chat, _ = get_llm(Config.LLM_TYPE)
                # 获取工具列表
                tools = await get_tools()

                # 创建ReAct智能体
                agent = create_react_agent(
                    model=llm_chat,
                    tools=tools,
                    pre_model_hook=trimmed_messages_hook,
                    checkpointer=checkpointer,
                    store=store
                )

                # 获取长期记忆
                system_message = system_prompt
                result = await read_long_term_info(user_id, store)
                # 检查返回结果是否成功
                if result.get("success", False):
                    long_term_info = result.get("long_term_info")
                    # 若获取到的内容不为空，拼接到系统提示词
                    if long_term_info:
                        system_message = f"{system_prompt}我的附加信息有:{long_term_info}"
                        logger.info(f"获取用户长期记忆，system_message的信息为:{system_message}")

                # 构造智能体输入消息体
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query}
                ]

                # 调用智能体
                result = await agent.ainvoke(
                    {"messages": messages},
                    config={"configurable": {"thread_id": task_id}}
                )

                # 解析返回的消息
                await parse_messages(result['messages'])
                # 处理智能体结果
                response = await process_agent_result(session_id, task_id, result, user_id, session_manager)

                # 对response进行处理 筛选出最近一次的完整对话更新到该task中
                logger.info(f"invoke_response:{response.model_dump()}")
                filtered_data = filter_last_human_conversation(response.model_dump())

                # 更新任务状态为完成并绑定用户和会话
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="completed",
                    # result=response.model_dump(),
                    result=filtered_data,
                    user_id=user_id,
                    session_id=session_id
                )

                return response.model_dump()

        except Exception as e:
            # 构造错误响应
            error_response = AgentResponse(
                session_id=session_id,
                task_id=task_id,
                status="error",
                message=f"处理请求时出错: {str(e)}"
            )
            # 更新会话状态为错误
            await session_manager.update_session(
                user_id=user_id,
                session_id=session_id,
                task_id=task_id,
                status="error",
                last_response=error_response,
                last_updated=time.time(),
                ttl=Config.TTL
            )
            # 更新任务状态为失败并绑定用户和会话
            await session_manager.set_task_status(
                task_id=task_id,
                status="failed",
                error=str(e),
                user_id=user_id,
                session_id=session_id
            )
            raise e
        finally:
            # 关闭Redis连接
            await session_manager.close()

    return asyncio.run(run_invoke())


# 定义Celery任务：异步运行智能体
@celery_app.task
def resume_agent_task(user_id: str, session_id: str, task_id: str, command_data: str):
    """
    异步运行智能体，处理用户请求并返回结果

    Args:
        user_id: 用户唯一标识
        session_id: 会话唯一标识
        task_id: 任务唯一标识
        query: 用户的问题
        system_prompt: 系统提示词

    Returns:
        dict: 智能体处理结果，转换为字典格式
    """
    # 异步执行智能体调用逻辑
    async def resume_invoke():
        try:
            # 初始化Redis会话管理器
            session_manager = get_session_manager()

            # 创建数据库连接池
            async with AsyncConnectionPool(
                conninfo=Config.DB_URI,
                min_size=Config.MIN_SIZE,
                max_size=Config.MAX_SIZE,
                kwargs={"autocommit": True, "prepare_threshold": 0}
            ) as pool:
                # 初始化短期记忆检查点
                checkpointer = AsyncPostgresSaver(pool)
                # 初始化长期记忆存储
                store = AsyncPostgresStore(pool)
                # 获取语言模型
                llm_chat, _ = get_llm(Config.LLM_TYPE)
                # 获取工具列表
                tools = await get_tools()

                # 创建ReAct智能体
                agent = create_react_agent(
                    model=llm_chat,
                    tools=tools,
                    pre_model_hook=trimmed_messages_hook,
                    checkpointer=checkpointer,
                    store=store
                )

                # 调用智能体
                result = await agent.ainvoke(
                    Command(resume=command_data),
                    config={"configurable": {"thread_id": task_id}}
                )

                # 解析返回的消息
                await parse_messages(result['messages'])
                # 处理智能体结果
                response = await process_agent_result(session_id, task_id, result, user_id, session_manager)

                # 对response进行处理 筛选出最近一次的完整对话更新到该task中
                logger.info(f"resume_response:{response.model_dump()}")
                filtered_data = filter_last_human_conversation(response.model_dump())

                # 更新任务状态为完成并绑定用户和会话
                await session_manager.set_task_status(
                    task_id=task_id,
                    status="completed",
                    # result=response.model_dump(),
                    result=filtered_data,
                    user_id=user_id,
                    session_id=session_id
                )

                return response.model_dump()

        except Exception as e:
            # 构造错误响应
            error_response = AgentResponse(
                session_id=session_id,
                task_id=task_id,
                status="error",
                message=f"处理请求时出错: {str(e)}"
            )
            # 更新会话状态为错误
            await session_manager.update_session(
                user_id=user_id,
                session_id=session_id,
                task_id=task_id,
                status="error",
                last_response=error_response,
                last_updated=time.time(),
                ttl=Config.TTL
            )
            # 更新任务状态为失败并绑定用户和会话
            await session_manager.set_task_status(
                task_id=task_id,
                status="failed",
                error=str(e),
                user_id=user_id,
                session_id=session_id
            )
            raise e
        finally:
            # 关闭Redis连接
            await session_manager.close()

    return asyncio.run(resume_invoke())




