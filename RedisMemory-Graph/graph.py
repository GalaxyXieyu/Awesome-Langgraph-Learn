"""
LangGraph 会话存储演示图
简单的聊天机器人，支持不同的存储后端
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# 导入不同的存储后端
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver


class ChatState(TypedDict):
    """聊天状态"""
    messages: Annotated[List[BaseMessage], add_messages]


def create_chat_bot(storage_type: str = "memory") -> StateGraph:
    """创建聊天机器人图
    
    Args:
        storage_type: 存储类型 ("memory", "redis")
    
    Returns:
        编译后的聊天图
    """
    
    # 初始化LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7
    )
    
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
    
    # 根据存储类型选择checkpointer
    if storage_type == "redis":
        # 使用您的远程Redis
        redis_url = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
        checkpointer = RedisSaver.from_conn_string(redis_url)
        checkpointer.setup()
        print(f"✅ 使用Redis存储: {redis_url}")
    else:
        # 默认使用内存存储
        checkpointer = MemorySaver()
        print("✅ 使用内存存储")
    
    # 编译图
    app = workflow.compile(checkpointer=checkpointer)
    return app


def chat_with_memory(app, message: str, thread_id: str = "default"):
    """与机器人对话
    
    Args:
        app: 编译后的图
        message: 用户消息
        thread_id: 线程ID（用于区分不同会话）
    
    Returns:
        AI回复
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # 调用图
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    # 返回最后一条消息
    return result["messages"][-1].content


if __name__ == "__main__":
    # 简单测试
    print("🤖 LangGraph 会话存储演示")
    print("=" * 40)
    
    # 创建Redis版本的聊天机器人
    app = create_chat_bot("redis")
    
    # 测试对话
    messages = [
        "你好！我叫小明。",
        "我刚才说我叫什么名字？",
        "请记住我喜欢编程。",
        "我有什么爱好？"
    ]
    
    thread_id = "test_session_001"
    
    for msg in messages:
        print(f"\n👤 用户: {msg}")
        response = chat_with_memory(app, msg, thread_id)
        print(f"🤖 助手: {response}")
    
    print("\n✅ 演示完成！")
