"""
基础聊天示例
演示如何使用不同的存储后端创建具有记忆功能的聊天机器人
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from ..storage import BaseStorage, StorageType, StorageFactory
from ..config import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """聊天状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    session_id: str
    timestamp: datetime


def create_chat_graph(storage: BaseStorage, model_name: str = "gpt-4o-mini") -> StateGraph:
    """创建聊天图
    
    Args:
        storage: 存储后端实例
        model_name: 使用的模型名称
        
    Returns:
        StateGraph: 编译后的聊天图
    """
    
    # 初始化LLM
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        max_tokens=1000
    )
    
    def chat_node(state: ChatState) -> Dict[str, Any]:
        """聊天节点 - 处理用户消息并生成回复"""
        try:
            messages = state["messages"]
            
            # 添加系统提示
            system_message = AIMessage(content="""你是一个友好的AI助手。你能记住之前的对话内容，
            并基于上下文提供有帮助的回复。请保持对话的连贯性和友好的语调。""")
            
            # 如果是第一条消息，添加系统提示
            if len(messages) == 1:
                messages = [system_message] + messages
            
            # 调用LLM生成回复
            response = llm.invoke(messages)
            
            logger.info(f"生成回复: {response.content[:100]}...")
            
            return {
                "messages": [response],
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"聊天节点处理失败: {e}")
            error_message = AIMessage(content=f"抱歉，处理您的消息时出现了错误: {str(e)}")
            return {
                "messages": [error_message],
                "timestamp": datetime.now()
            }
    
    # 创建状态图
    workflow = StateGraph(ChatState)
    
    # 添加节点
    workflow.add_node("chat", chat_node)
    
    # 设置流程
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    # 编译图 - 根据存储类型选择合适的checkpointer
    if storage.get_storage_type() == StorageType.MEMORY:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
    elif storage.get_storage_type() == StorageType.REDIS:
        from langgraph.checkpoint.redis import RedisSaver
        # 使用您提供的远程Redis连接
        redis_url = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
        checkpointer = RedisSaver.from_conn_string(redis_url)
        checkpointer.setup()
    else:
        # 对于其他存储类型，暂时使用内存存储
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        logger.warning(f"存储类型 {storage.get_storage_type()} 暂未完全实现，使用内存存储")
    
    # 编译图
    app = workflow.compile(checkpointer=checkpointer)
    
    logger.info(f"聊天图创建完成，使用存储类型: {storage.get_storage_type().value}")
    return app


def run_chat_example(storage_type: str = "redis", interactive: bool = True) -> None:
    """运行聊天示例
    
    Args:
        storage_type: 存储类型 ("memory", "redis", "postgres", "sqlite")
        interactive: 是否启用交互模式
    """
    
    print("🤖 LangGraph 会话存储演示 - 智能聊天机器人")
    print("=" * 60)
    
    try:
        # 创建存储实例
        if storage_type == "redis":
            # 使用您提供的远程Redis连接
            connection_string = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
        elif storage_type == "memory":
            connection_string = "memory://"
        else:
            connection_string = f"{storage_type}://localhost"
        
        storage = StorageFactory.create(storage_type, connection_string)
        
        # 测试连接
        print(f"📡 测试 {storage_type.upper()} 连接...")
        if storage.test_connection():
            print(f"✅ {storage_type.upper()} 连接成功！")
        else:
            print(f"❌ {storage_type.upper()} 连接失败！")
            return
        
        # 创建聊天图
        print("🔧 创建聊天图...")
        chat_graph = create_chat_graph(storage)
        
        # 配置会话
        session_config = {
            "configurable": {
                "thread_id": f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        print(f"🎯 会话ID: {session_config['configurable']['thread_id']}")
        print(f"💾 存储类型: {storage_type.upper()}")
        print("\n" + "=" * 60)
        
        if interactive:
            # 交互模式
            print("💬 开始对话！输入 'quit' 或 'exit' 退出")
            print("📝 输入 'stats' 查看存储统计信息")
            print("🔄 输入 'clear' 清空对话历史")
            print("-" * 60)
            
            while True:
                try:
                    user_input = input("\n👤 您: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', '退出']:
                        print("👋 再见！")
                        break
                    
                    if user_input.lower() == 'stats':
                        # 显示存储统计信息
                        stats = storage.get_stats() if hasattr(storage, 'get_stats') else {}
                        print(f"\n📊 存储统计信息:")
                        for key, value in stats.items():
                            print(f"   {key}: {value}")
                        continue
                    
                    if user_input.lower() == 'clear':
                        # 创建新的会话ID
                        session_config["configurable"]["thread_id"] = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        print(f"🔄 已创建新会话: {session_config['configurable']['thread_id']}")
                        continue
                    
                    if not user_input:
                        continue
                    
                    # 创建初始状态
                    initial_state = {
                        "messages": [HumanMessage(content=user_input)],
                        "user_id": "demo_user",
                        "session_id": session_config["configurable"]["thread_id"],
                        "timestamp": datetime.now()
                    }
                    
                    # 调用聊天图
                    print("🤔 思考中...")
                    result = chat_graph.invoke(initial_state, session_config)
                    
                    # 显示回复
                    if result and "messages" in result:
                        last_message = result["messages"][-1]
                        if isinstance(last_message, AIMessage):
                            print(f"🤖 助手: {last_message.content}")
                        else:
                            print(f"🤖 助手: {last_message}")
                    else:
                        print("🤖 助手: 抱歉，我没有理解您的消息。")
                
                except KeyboardInterrupt:
                    print("\n👋 再见！")
                    break
                except Exception as e:
                    print(f"❌ 处理消息时出错: {e}")
                    logger.error(f"交互模式错误: {e}")
        
        else:
            # 演示模式 - 预设对话
            demo_messages = [
                "你好！",
                "我叫小明，请记住我的名字。",
                "你能告诉我今天的天气吗？",
                "我刚才告诉你我的名字是什么？",
                "谢谢你的帮助！"
            ]
            
            print("🎭 演示模式 - 预设对话")
            print("-" * 60)
            
            for i, message in enumerate(demo_messages, 1):
                print(f"\n👤 用户 ({i}/{len(demo_messages)}): {message}")
                
                # 创建初始状态
                initial_state = {
                    "messages": [HumanMessage(content=message)],
                    "user_id": "demo_user",
                    "session_id": session_config["configurable"]["thread_id"],
                    "timestamp": datetime.now()
                }
                
                try:
                    # 调用聊天图
                    result = chat_graph.invoke(initial_state, session_config)
                    
                    # 显示回复
                    if result and "messages" in result:
                        last_message = result["messages"][-1]
                        if isinstance(last_message, AIMessage):
                            print(f"🤖 助手: {last_message.content}")
                        else:
                            print(f"🤖 助手: {last_message}")
                    
                    # 短暂暂停
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 处理消息失败: {e}")
                    logger.error(f"演示模式错误: {e}")
        
        # 显示最终统计
        print("\n" + "=" * 60)
        print("📊 会话统计:")
        if hasattr(storage, 'get_stats'):
            stats = storage.get_stats()
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        print(f"✅ 演示完成！存储类型: {storage_type.upper()}")
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        logger.error(f"聊天示例错误: {e}")
    
    finally:
        # 清理资源
        try:
            if 'storage' in locals():
                storage.close()
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


async def run_async_chat_example(storage_type: str = "redis") -> None:
    """运行异步聊天示例"""
    
    print("🚀 异步聊天演示")
    print("=" * 40)
    
    try:
        # 创建存储实例
        if storage_type == "redis":
            connection_string = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
        else:
            connection_string = f"{storage_type}://localhost"
        
        storage = StorageFactory.create(storage_type, connection_string)
        
        # 异步测试连接
        if await storage.atest_connection():
            print(f"✅ {storage_type.upper()} 异步连接成功！")
        else:
            print(f"❌ {storage_type.upper()} 异步连接失败！")
            return
        
        # 创建聊天图
        chat_graph = create_chat_graph(storage)
        
        # 异步对话示例
        messages = ["你好！", "请介绍一下你自己", "你能记住我们的对话吗？"]
        
        session_config = {
            "configurable": {
                "thread_id": f"async_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        for message in messages:
            print(f"\n👤 用户: {message}")
            
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "user_id": "async_user",
                "session_id": session_config["configurable"]["thread_id"],
                "timestamp": datetime.now()
            }
            
            # 异步调用
            result = chat_graph.invoke(initial_state, session_config)
            
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    print(f"🤖 助手: {last_message.content}")
        
        print("\n✅ 异步演示完成！")
        
    except Exception as e:
        print(f"❌ 异步演示失败: {e}")
        logger.error(f"异步聊天示例错误: {e}")


if __name__ == "__main__":
    import sys
    
    # 解析命令行参数
    storage_type = sys.argv[1] if len(sys.argv) > 1 else "redis"
    interactive = "--demo" not in sys.argv
    
    print(f"🎯 使用存储类型: {storage_type.upper()}")
    print(f"🎮 模式: {'交互模式' if interactive else '演示模式'}")
    
    # 运行示例
    run_chat_example(storage_type, interactive)
