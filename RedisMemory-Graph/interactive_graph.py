"""
基于Redis存储的LangGraph智能写作助手
参考Interative-Report-Workflow，将内存存储替换为Redis存储
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.redis import RedisSaver
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import logging
import time
from langgraph.config import get_stream_writer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确认节点配置
CONFIRMATION_CONFIGS = {
    "outline": {
        "type": "outline_confirmation",
        "message_template": "请确认以下大纲是否满意：\n\n{outline_text}",
        "instructions": "请回复 'yes' 确认继续，或 'no' 重新生成大纲",
        "state_key": "user_confirmation",
        "copilot_message": "Copilot模式：自动确认大纲"
    },
    "search": {
        "type": "search_permission", 
        "message_template": "是否允许为主题「{topic}」进行联网搜索？",
        "instructions": "请回复 'yes' 允许搜索，'no' 跳过搜索",
        "state_key": "search_permission",
        "copilot_message": "Copilot模式：自动允许联网搜索"
    }
}

# 定义大纲数据模型
class OutlineSection(BaseModel):
    """大纲章节模型"""
    title: str = Field(description="章节标题")
    description: str = Field(description="章节描述")
    key_points: List[str] = Field(description="章节要点列表")

class ArticleOutline(BaseModel):
    """文章大纲模型"""
    title: str = Field(description="文章标题")
    sections: List[OutlineSection] = Field(description="章节列表")

class WritingState(TypedDict):
    """写作助手的状态定义"""
    # 基本信息
    topic: str  # 文章主题
    user_id: str  # 用户ID
    
    # 配置参数
    max_words: int  # 最大字数
    style: str  # 写作风格
    language: str  # 语言
    mode: str  # 运行模式：copilot（自动通过所有中断）或 interactive（交互模式）
    
    # 核心内容
    outline: Optional[Dict[str, Any]]  # 文章大纲
    article: Optional[str]  # 生成的文章
    search_results: List[Dict[str, Any]]  # 搜索结果
    
    # 用户交互
    user_confirmation: Optional[str]  # 用户确认信息
    search_permission: Optional[str]  # 搜索权限确认
    
    # 消息历史
    messages: Annotated[List, add_messages]  # 对话消息

def create_llm() -> ChatOpenAI:
    """创建LLM实例"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7
    )

async def generate_outline_node(state: WritingState, config=None) -> WritingState:
    """大纲生成节点"""
    writer = get_stream_writer()
    writer({"step": "outline_generation", "status": "开始生成大纲", "progress": 0})

    parser = JsonOutputParser(pydantic_object=ArticleOutline)
    
    outline_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的写作助手。请根据用户提供的主题生成一个详细的文章大纲。
        要求：
        1. 大纲应该包含标题和3-6个主要章节
        2. 每个章节应该有清晰的主题和简要说明
        3. 整体结构要逻辑清晰，层次分明
        4. 适合{style}风格的写作
        5. 使用{language}语言

        {format_instructions}"""),
        ("human", "请为以下主题生成文章大纲：{topic}")
    ])

    llm_chain = outline_prompt | create_llm() | parser
    
    writer({"step": "outline_generation", "status": "正在生成大纲", "progress": 50})

    input_data = {
        "topic": state['topic'],
        "style": state.get("style", "formal"),
        "language": state.get("language", "zh"),
        "format_instructions": parser.get_format_instructions()
    }
    
    outline_data = None
    async for chunk in llm_chain.astream(input_data, config=config):
        outline_data = chunk
        
        writer({
            "step": "outline_generation", 
            "status": "正在生成大纲...",
            "progress": 100,
            "current_content": chunk,
            "total_chars": 2,
            "chunk_count": 1
        })
    
    # 如果没有获得有效结果，创建默认大纲
    if not outline_data:
        outline_data = {
            "title": f"{state['topic']}",
            "sections": [
                {"title": "引言", "description": "介绍主题背景", "key_points": ["背景介绍", "重要性"]},
                {"title": "主要内容", "description": "详细阐述主题", "key_points": ["核心观点", "具体分析"]},
                {"title": "结论", "description": "总结要点", "key_points": ["总结", "展望"]}
            ]
        }

    # 处理解析结果
    if isinstance(outline_data, dict):
        outline = outline_data
    else:
        outline = {
            "title": outline_data.title,
            "sections": [
                {
                    "title": section.title,
                    "description": section.description,
                    "key_points": section.key_points
                }
                for section in outline_data.sections
            ]
        }

    writer({
        "step": "outline_generation",
        "status": "大纲生成完成",
        "progress": 100,
        "outline": outline
    })

    # 更新状态
    state["outline"] = outline
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"已生成文章大纲：\n标题：{outline['title']}\n章节数：{len(outline['sections'])}")
    ]

    return state

def create_confirmation_node(config_key: str):
    """工厂函数：创建确认节点"""
    config = CONFIRMATION_CONFIGS[config_key]
    
    def confirmation_node(state: WritingState) -> WritingState:
        from langgraph.types import interrupt
        
        mode = state.get("mode", "interactive")
        
        # copilot模式自动通过
        if mode == "copilot":
            state.update({
                config["state_key"]: "yes",
                "messages": state.get("messages", []) + [
                    AIMessage(content=config["copilot_message"])
                ]
            })
            return state
        
        # 构建消息内容
        if config_key == "outline":
            # 构建大纲展示文本
            outline = state.get("outline") or {}
            outline_text = f"文章标题：{outline.get('title', '未知')}\n\n"
            sections = outline.get("sections") or []
            for i, section in enumerate(sections, 1):
                outline_text += f"{i}. {section.get('title', '未知章节')}\n"
                outline_text += f"   描述：{section.get('description', '无描述')}\n"
                if section.get('key_points'):
                    outline_text += f"   要点：{', '.join(section['key_points'])}\n"
                outline_text += "\n"
            message = config["message_template"].format(outline_text=outline_text)
        else:
            topic = state.get("topic", "")
            message = config["message_template"].format(topic=topic)
        
        # interactive模式需要用户确认
        user_response = interrupt({
            "type": config["type"],
            "message": message,
            "instructions": config["instructions"]
        })

        # 处理用户确认结果
        confirmation = user_response.lower().strip() if isinstance(user_response, str) else str(user_response).lower().strip()

        # 更新状态
        state.update({
            config["state_key"]: confirmation,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"{config['type']}确认结果: {confirmation}")
            ]
        })

        return state
    
    return confirmation_node

# 创建确认节点实例
outline_confirmation_node = create_confirmation_node("outline")
search_confirmation_node = create_confirmation_node("search")

def simple_search_node(state: WritingState) -> WritingState:
    """简化的搜索节点"""
    writer = get_stream_writer()
    
    # 检查搜索权限
    if state.get("search_permission") != "yes":
        writer({"step": "search_execution", "status": "跳过搜索", "progress": 100})
        state.update({"search_results": []})
        return state

    writer({"step": "search_execution", "status": "模拟搜索", "progress": 50})
    
    # 模拟搜索结果
    topic = state.get("topic", "")
    mock_results = [
        {"title": f"{topic}相关资料1", "snippet": f"关于{topic}的详细介绍...", "url": "https://example1.com"},
        {"title": f"{topic}相关资料2", "snippet": f"{topic}的应用案例...", "url": "https://example2.com"},
        {"title": f"{topic}相关资料3", "snippet": f"{topic}的发展趋势...", "url": "https://example3.com"}
    ]
    
    writer({"step": "search_execution", "status": "搜索完成", "progress": 100})
    
    state.update({
        "search_results": mock_results,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"搜索完成，获得 {len(mock_results)} 个相关资料。")
        ]
    })
    
    return state

async def article_generation_node(state: WritingState, config=None) -> WritingState:
    """文章生成节点"""
    try:
        start_time = time.time()

        # 创建LLM
        llm = create_llm()

        # 构建文章生成提示
        outline = state.get("outline") or {}
        outline_text = f"标题：{outline.get('title', '')}\n"

        sections = outline.get("sections") or []
        for i, section in enumerate(sections, 1):
            outline_text += f"{i}. {section.get('title', '')}\n"
            outline_text += f"   {section.get('description', '')}\n"
            if section.get('key_points'):
                outline_text += f"   要点：{', '.join(section['key_points'])}\n"

        # 添加搜索结果到提示中
        search_results = state.get("search_results", [])
        search_context = ""
        if search_results:
            search_context = "\n\n参考资料：\n"
            for i, result in enumerate(search_results[:3], 1):
                search_context += f"{i}. {result.get('title', '')}: {result.get('snippet', '')}\n"

        # 构建生成指令
        generation_prompt = f"""
            请根据以下大纲生成一篇完整的文章：

            {outline_text}

            {search_context}

            要求：
            1. 文章风格：{state.get('style', 'formal')}
            2. 语言：{state.get('language', 'zh')}
            3. 目标字数：约{state.get('max_words', 1000)}字
            4. 内容要求：逻辑清晰、论证充分、语言流畅
            5. 如果有参考资料，请合理引用和整合

            请生成完整的文章内容。
        """

        # 获取流式写入器
        writer = get_stream_writer()
        writer({"step": "article_generation", "status": "开始生成文章", "progress": 0})

        # 创建消息
        messages = [HumanMessage(content=generation_prompt)]

        # 流式生成文章
        full_article = ""
        chunk_count = 0

        writer({"step": "article_generation", "status": "正在生成文章...", "progress": 10})

        async for chunk in llm.astream(messages, config=config):
            if chunk.content and isinstance(chunk.content, str):
                full_article += chunk.content
                chunk_count += 1

                # 每10个chunk发送一次进度更新
                if chunk_count % 10 == 0:
                    progress = min(90, 10 + (chunk_count // 10) * 5)
                    writer({
                        "step": "article_generation",
                        "status": "正在生成文章...",
                        "progress": progress,
                        "current_content": full_article,
                        "total_chars": len(full_article),
                        "chunk_count": chunk_count
                    })

        # 计算生成时间
        generation_time = time.time() - start_time

        # 更新最终状态
        state.update({
            "article": full_article,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"文章生成完成！\n字数：{len(full_article)}\n生成时间：{generation_time:.1f}秒")
            ]
        })

        writer({
            "step": "article_generation",
            "status": "文章生成完成",
            "progress": 100,
            "current_content": full_article,
            "total_chars": len(full_article),
            "chunk_count": chunk_count
        })

        return state

    except Exception as e:
        logger.error(f"文章生成失败: {str(e)}")
        state.update({
            "messages": state.get("messages", []) + [
                AIMessage(content=f"文章生成失败: {str(e)}")
            ]
        })
        return state

# 路由函数
def route_after_confirmation(state: WritingState) -> str:
    """确认后的路由逻辑"""
    user_confirmation = (state.get("user_confirmation") or "").lower().strip()

    if user_confirmation == "yes":
        return "search_confirmation"
    elif user_confirmation == "no":
        return "generate_outline"
    else:
        return "search_confirmation"

def route_after_search_confirmation(state: WritingState) -> str:
    """搜索确认后的路由逻辑"""
    search_permission = (state.get("search_permission") or "").lower().strip()

    if search_permission == "yes":
        return "search_execution"
    else:
        return "article_generation"

def should_continue_after_search(_: WritingState) -> str:
    """搜索完成后的路由逻辑"""
    return "article_generation"

def create_redis_writing_assistant_graph():
    """创建基于Redis存储的智能写作助手图"""
    workflow = StateGraph(WritingState)

    # 添加节点
    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("outline_confirmation", outline_confirmation_node)
    workflow.add_node("search_confirmation", search_confirmation_node)
    workflow.add_node("search_execution", simple_search_node)
    workflow.add_node("article_generation", article_generation_node)

    # 设置起始节点
    workflow.add_edge(START, "generate_outline")

    # 添加边
    workflow.add_edge("generate_outline", "outline_confirmation")

    # 大纲确认后的条件路由
    workflow.add_conditional_edges(
        "outline_confirmation",
        route_after_confirmation,
        {
            "search_confirmation": "search_confirmation",
            "generate_outline": "generate_outline"
        }
    )

    # 搜索确认后的条件路由
    workflow.add_conditional_edges(
        "search_confirmation",
        route_after_search_confirmation,
        {
            "search_execution": "search_execution",
            "article_generation": "article_generation"
        }
    )

    # 搜索完成后直接生成文章
    workflow.add_conditional_edges(
        "search_execution",
        should_continue_after_search,
        {
            "article_generation": "article_generation"
        }
    )

    # 文章生成完成后结束
    workflow.add_edge("article_generation", END)

    # 🔥 关键改动：使用Redis存储替代内存存储
    redis_url = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
    checkpointer = RedisSaver.from_conn_string(redis_url)
    checkpointer.setup()

    print(f"✅ 使用Redis存储: {redis_url}")

    # 编译图
    app = workflow.compile(checkpointer=checkpointer)

    return app

# 便捷函数
def run_writing_assistant(topic: str, mode: str = "interactive", thread_id: str = "default"):
    """运行写作助手"""
    app = create_redis_writing_assistant_graph()

    # 初始状态
    initial_state = {
        "topic": topic,
        "user_id": "demo_user",
        "max_words": 1000,
        "style": "formal",
        "language": "zh",
        "mode": mode,
        "outline": None,
        "article": None,
        "search_results": [],
        "user_confirmation": None,
        "search_permission": None,
        "messages": [HumanMessage(content=f"请为主题「{topic}」生成文章")]
    }

    # 配置
    config = {"configurable": {"thread_id": thread_id}}

    # 运行
    try:
        result = app.invoke(initial_state, config=config)
        return result
    except Exception as e:
        logger.error(f"运行写作助手失败: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # 测试运行
    print("🚀 Redis写作助手演示")
    print("=" * 40)

    # 创建图
    app = create_redis_writing_assistant_graph()

    # 测试状态
    test_state = {
        "topic": "人工智能的发展趋势",
        "user_id": "test_user",
        "max_words": 800,
        "style": "academic",
        "language": "zh",
        "mode": "copilot",  # 自动模式，不需要用户交互
        "messages": []
    }

    config = {"configurable": {"thread_id": "redis_test_001"}}

    try:
        print("开始生成文章...")
        result = app.invoke(test_state, config=config)

        if "article" in result and result["article"]:
            print(f"\n✅ 文章生成成功！")
            print(f"标题: {result.get('outline', {}).get('title', '未知')}")
            print(f"字数: {len(result['article'])}")
            print(f"文章预览: {result['article'][:200]}...")
        else:
            print("❌ 文章生成失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
