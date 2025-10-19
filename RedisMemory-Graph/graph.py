"""
LangGraph 会话存储演示图
简单的聊天机器人，支持不同的存储后端
"""

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# 导入不同的存储后端
from langgraph.checkpoint.memory import MemorySaver

# 导入官方 Redis 支持
from langgraph.checkpoint.redis import RedisSaver
REDIS_AVAILABLE = True


class ChatState(TypedDict):
    """聊天状态"""
    messages: Annotated[List[BaseMessage], add_messages]


def create_llm():
    """创建LLM实例"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
    )


def create_chat_bot_with_redis(redis_url: Optional[str] = None):
    """创建使用 Redis 存储的聊天机器人

    Args:
        redis_url: Redis 连接URL

    Returns:
        编译后的聊天图和 RedisSaver 上下文管理器
    """
    if redis_url is None:
        redis_url = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"

    # 使用统一的 LLM 配置
    llm = create_llm()
    print("✅ 使用 Qwen2.5-72B 模型")

    def chat_node(state: ChatState):
        """聊天节点"""
        messages = state["messages"]

        # 添加系统消息（如果是第一条消息）
        if len(messages) == 1:
            system_msg = AIMessage(content="你是一个友好的AI助手，能记住对话历史。")
            messages = [system_msg] + messages

        # 调用LLM
        response = llm.invoke(messages)
        return {"messages": [response]}

    # 创建图
    workflow = StateGraph(ChatState)
    workflow.add_node("chat", chat_node)
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)

    # 返回工作流和 Redis URL，让调用者管理上下文
    return workflow, redis_url


