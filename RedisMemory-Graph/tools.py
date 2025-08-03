"""
工具函数模块
包含聊天机器人相关的工具函数
"""

from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig


def chat_with_memory(app, message: str, thread_id: str = "default") -> str:
    """与机器人对话
    
    Args:
        app: 编译后的图
        message: 用户消息
        thread_id: 线程ID（用于区分不同会话）
    
    Returns:
        AI回复
    """
    from langchain_core.messages import HumanMessage
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # 调用图
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    # 返回最后一条消息
    return result["messages"][-1].content


def format_conversation_history(messages: list) -> str:
    """格式化对话历史
    
    Args:
        messages: 消息列表
        
    Returns:
        格式化后的对话历史字符串
    """
    formatted = []
    for msg in messages:
        if hasattr(msg, 'type'):
            if msg.type == 'human':
                formatted.append(f"👤 用户: {msg.content}")
            elif msg.type == 'ai':
                formatted.append(f"🤖 助手: {msg.content}")
            else:
                formatted.append(f"📝 {msg.type}: {msg.content}")
        else:
            formatted.append(f"📝 消息: {msg}")
    
    return "\n".join(formatted)


def validate_redis_connection(redis_url: str) -> bool:
    """验证 Redis 连接
    
    Args:
        redis_url: Redis 连接URL
        
    Returns:
        连接是否成功
    """
    try:
        import redis
        client = redis.from_url(redis_url)
        client.ping()
        return True
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False


def get_conversation_stats(app, thread_id: str) -> Dict[str, Any]:
    """获取对话统计信息
    
    Args:
        app: 编译后的图
        thread_id: 线程ID
        
    Returns:
        统计信息字典
    """
    try:
        # 获取对话历史
        config = {"configurable": {"thread_id": thread_id}}
        
        # 这里需要根据具体的 checkpointer 实现来获取历史
        # 简化版本，返回基本统计
        return {
            "thread_id": thread_id,
            "status": "active",
            "message_count": "unknown",  # 需要具体实现来获取
            "last_activity": "unknown"
        }
    except Exception as e:
        return {
            "thread_id": thread_id,
            "status": "error",
            "error": str(e)
        }


def create_test_messages() -> list:
    """创建测试消息列表
    
    Returns:
        测试消息列表
    """
    return [
        "你好！我叫小明。",
        "我刚才说我叫什么名字？",
        "请记住我喜欢编程。",
        "我有什么爱好？",
        "你能总结一下我们的对话吗？"
    ]


def print_separator(title: str = "", width: int = 50):
    """打印分隔线
    
    Args:
        title: 标题
        width: 宽度
    """
    if title:
        print(f"\n{'=' * width}")
        print(f"{title:^{width}}")
        print(f"{'=' * width}")
    else:
        print(f"{'=' * width}")


def measure_response_time(func, *args, **kwargs) -> tuple:
    """测量函数响应时间
    
    Args:
        func: 要测量的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        (结果, 耗时秒数)
    """
    import time
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    return result, end_time - start_time
