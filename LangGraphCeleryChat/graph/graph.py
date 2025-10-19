"""
LangGraph智能写作助手 - 图结构模块
实现基于状态图的智能写作工作流
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from .tools import tavily_search, validate_outline, format_article
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
    },
    "rag": {
        "type": "rag_permission",
        "message_template": "是否需要为主题「{topic}」进行RAG知识库增强？", 
        "instructions": "请回复 'yes' 启用RAG增强，'no' 跳过",
        "state_key": "rag_permission",
        "copilot_message": "Copilot模式：自动启用RAG知识库增强"
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
    """写作助手的状态定义 - 精简版"""
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
    rag_permission: Optional[str]  # RAG增强权限确认

    # 消息历史
    messages: Annotated[List, add_messages]  # 对话消息

    # Checkpointer 支持
    checkpointer: Optional[Any]  # 用于状态持久化的 checkpointer


def create_llm() -> ChatOpenAI:
    """创建LLM实例 - 强制启用流式输出"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="",
    )


async def generate_outline_node(state: WritingState, config=None) -> WritingState:
    """
    大纲生成节点 - 修复流式处理
    """
    writer = get_stream_writer()
    writer({
        "event_type": "progress_update",
        "step": "outline_generation",
        "status": "开始生成大纲",
        "progress": 0,
        "timestamp": time.time()
    })

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
    
    writer({
        "event_type": "progress_update",
        "step": "outline_generation",
        "status": "正在生成大纲",
        "progress": 50,
        "timestamp": time.time()
    })

    input_data = {
        "topic": state['topic'],
        "style": state.get("style", "formal"),
        "language": state.get("language", "zh"),
        "format_instructions": parser.get_format_instructions()
    }
    
    outline_data = None
    async for chunk in llm_chain.astream(input_data, config=config):
        outline_data = chunk  # chunk已经是解析后的ArticleOutline对象
        
        writer({
            "step": "outline_generation", 
            "status": "正在生成大纲...",
            "progress": 100,
            "current_content": chunk,
            "total_chars": 2,  # 简化计数
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
    # 验证大纲
    validation_result = validate_outline.invoke({"outline": outline})

    writer({
        "event_type": "progress_update",
        "step": "outline_generation",
        "status": "大纲生成完成",
        "progress": 100,
        "outline": outline,
        "validation_score": validation_result.get('score', 0),
        "timestamp": time.time()
    })

    # 更新状态
    state["outline"] = outline
    state["status"] = "completed"
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"已生成文章大纲：\n标题：{outline['title']}\n章节数：{len(outline['sections'])}\n验证分数：{validation_result.get('score', 0)}")
    ]

    return state


def create_confirmation_node(config_key: str):
    """
    工厂函数：创建确认节点
    
    Args:
        config_key: 配置键，如 "outline", "search", "rag"
    
    Returns:
        确认节点函数
    """
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
        # interrupt()会暂停执行，直到用户恢复，然后返回用户的响应
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
rag_confirmation_node = create_confirmation_node("rag") 

def rag_enhancement_node(state: WritingState) -> WritingState:
    """RAG增强节点 - 实际执行RAG增强逻辑"""
    # 获取流式写入器
    try:
        writer = get_stream_writer()
        writer({"step": "rag_enhancement", "status": "开始RAG增强", "progress": 0})
    except Exception:
        writer = lambda _: None

    # 检查用户是否同意RAG增强
    rag_permission = state.get("rag_permission", "").lower().strip()

    if rag_permission == "yes":
        writer({"step": "rag_enhancement", "status": "执行RAG增强...", "progress": 50})

        # 这里可以添加实际的RAG增强逻辑
        # 例如：从知识库检索相关信息
        enhancement_suggestions = [
            {"content": "LangGraph是专为LLM应用设计的流程编排工具"},
            {"content": "Airflow是传统的数据工作流编排平台"},
            {"content": "两者在LLM应用中各有优势"}
        ]

        state.update({
            "enhancement_suggestions": enhancement_suggestions
        })

        writer({"step": "rag_enhancement", "status": "RAG增强完成", "progress": 100})
    else:
        writer({"step": "rag_enhancement", "status": "跳过RAG增强", "progress": 100})

    return state

async def article_generation_node(state: WritingState, config=None) -> WritingState:
    """
    文章生成节点 - 使用正确的LangGraph流式方法
    关键：在节点内使用LLM链，让LangGraph自动捕获流式输出
    """
    try:
        start_time = time.time()

        # 创建LLM链 - 关键是让LangGraph能直接调用这个链
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
            for i, result in enumerate(search_results[:5], 1):  # 限制使用前5个结果
                search_context += f"{i}. {result.get('title', '')}: {result.get('snippet', '')}\n"

        # 添加RAG增强内容
        enhancement_suggestions = state.get("enhancement_suggestions", [])
        rag_context = ""
        if enhancement_suggestions:
            rag_context = "\n\n知识库增强内容：\n"
            for i, suggestion in enumerate(enhancement_suggestions[:3], 1):
                rag_context += f"{i}. {suggestion.get('content', '')}\n"

        # 构建生成指令
        generation_prompt = f"""
            请根据以下大纲生成一篇完整的文章：

            {outline_text}

            {search_context}

            {rag_context}

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
        
        # 流式生成文章，实时发送进度
        full_article = ""
        chunk_count = 0
        
        writer({"step": "article_generation", "status": "正在生成文章...", "progress": 10})
        
        async for chunk in llm.astream(messages, config=config):
            if chunk.content and isinstance(chunk.content, str):
                full_article += chunk.content
                # 实时传递真实的 token chunk
                writer({
                    "step": "article_generation_chunk",
                    "token": chunk.content
                })

        # 格式化文章
        formatted_result = format_article.invoke({
            "content": full_article,
            "style": state.get("style", "formal")
        })

        # 计算生成时间
        generation_time = time.time() - start_time

        # 格式化文章进度
        writer({"step": "article_generation", "status": "正在格式化文章...", "progress": 95})

        # 更新最终状态
        state.update({
            "article": formatted_result.get("formatted_content", full_article),
            "messages": state.get("messages", []) + [
                AIMessage(content=f"文章生成完成！\n字数：{formatted_result.get('word_count', len(full_article))}\n生成时间：{generation_time:.1f}秒")
            ]
        })

        writer({
            "step": "article_generation",
            "status": "文章生成完成",
            "progress": 100,
            "current_content": formatted_result.get("formatted_content", full_article),
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

def search_execution_node(state: WritingState) -> WritingState:
    """
    搜索执行节点 - 修复版本，保持同步以支持工具调用
    搜索节点主要调用工具，保持同步即可
    """
    try:
        writer = get_stream_writer()

        # 检查搜索权限
        if state.get("search_permission") != "yes":
            writer({"step": "search_execution", "status": "跳过搜索", "progress": 100})
            state.update({
                "search_results": [],
            })
            return state

        writer({"step": "search_execution", "status": "开始搜索", "progress": 0})

        # 构建搜索查询
        topic = state.get("topic", "")
        outline = state.get("outline") or {}

        # 基于主题和大纲构建搜索关键词
        search_queries = [topic]

        # 添加章节相关的搜索词
        sections = outline.get("sections") or []
        for section in sections[:3]:  # 限制搜索数量
            section_title = section.get("title", "")
            if section_title and section_title not in search_queries:
                search_queries.append(f"{topic} {section_title}")

        writer({
            "step": "search_execution",
            "status": f"准备搜索 {len(search_queries)} 个查询",
            "progress": 10,
            "queries": search_queries
        })

        # 执行搜索
        all_search_results = []
        for i, query in enumerate(search_queries):
            try:
                progress = 10 + (i / len(search_queries)) * 70
                writer({
                    "step": "search_execution",
                    "status": f"搜索: {query}",
                    "progress": int(progress),
                    "current_query": query
                })

                results = tavily_search.invoke({"query": query, "max_results": 3})
                if isinstance(results, list):
                    all_search_results.extend(results)
                    writer({
                        "step": "search_execution",
                        "status": f"找到 {len(results)} 个结果",
                        "progress": int(progress + 5),
                        "query_results": len(results)
                    })


            except Exception as search_error:
                logger.warning(f"搜索查询 '{query}' 失败: {search_error}")
                writer({
                    "step": "search_execution",
                    "status": f"搜索失败: {query}",
                    "progress": int(progress),
                    "error": str(search_error)
                })
                continue

        writer({"step": "search_execution", "status": "处理搜索结果", "progress": 85})

        # 去重和限制结果数量
        unique_results = []
        seen_urls = set()
        for result in all_search_results:
            url = result.get("url", "")
            if url and url not in seen_urls and len(unique_results) < 10:
                seen_urls.add(url)
                unique_results.append(result)

        writer({
            "step": "search_execution",
            "status": "搜索完成",
            "progress": 100,
            "total_results": len(unique_results),
            "results_preview": [r.get("title", "") for r in unique_results[:3]]
        })

        # 更新状态
        state.update({
            "search_results": unique_results,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"搜索完成，获得 {len(unique_results)} 个相关资料。")
            ]
        })


        return state

    except Exception as e:
        logger.error(f"搜索执行失败: {str(e)}")
        writer({"step": "search_execution", "status": f"搜索失败: {str(e)}", "progress": -1})
        state.update({
            "status": "error",
            "error_message": f"搜索执行失败: {str(e)}",
        })
        return state

def route_after_confirmation(state: WritingState) -> str:
    """
    确认后的路由逻辑 - 根据用户确认结果决定下一步
    """
    user_confirmation = (state.get("user_confirmation") or "").lower().strip()


    if user_confirmation == "yes":
        return "rag_confirmation"  # 先到RAG确认节点
    elif user_confirmation == "no":
        return "generate_outline"  # 重新生成大纲
    else:
        # 这种情况不应该发生，因为interrupt()会等待有效输入
        return "rag_confirmation"

def route_after_rag_enhancement(_: WritingState) -> str:
    """
    RAG增强后的路由逻辑
    """
    # 无论RAG增强结果如何，都继续到搜索确认
    return "search_confirmation"

def route_after_search_confirmation(state: WritingState) -> str:
    """
    搜索确认后的路由逻辑 - 根据搜索权限决定是否执行搜索
    """
    search_permission = (state.get("search_permission") or "").lower().strip()


    if search_permission == "yes":
        return "search_execution"
    else:
        return "article_generation"  # 直接生成文章

def should_continue_after_search(_: WritingState) -> str:
    """
    搜索完成后的路由逻辑 - 搜索完成后直接进入文章生成
    """
    return "article_generation"

def create_writing_assistant_graph():
    """
    创建智能写作助手的状态图 - 支持自定义流式写入器

    Args:
        custom_stream_writer: 自定义流式写入器函数，用于将流式数据写入 Redis Streams

    Returns:
        编译后的状态图
    """
    workflow = StateGraph(WritingState)

    # 添加节点
    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("outline_confirmation", outline_confirmation_node)
    workflow.add_node("rag_confirmation", rag_confirmation_node)  # 独立的RAG确认节点
    workflow.add_node("rag_enhancement", rag_enhancement_node)
    workflow.add_node("search_confirmation", search_confirmation_node)
    workflow.add_node("search_execution", search_execution_node)
    workflow.add_node("article_generation", article_generation_node)

    # 设置起始节点
    workflow.add_edge(START, "generate_outline")

    # 添加边
    workflow.add_edge("generate_outline", "outline_confirmation")

    # 人工确认后的条件路由
    workflow.add_conditional_edges(
        "outline_confirmation",
        route_after_confirmation,
        {
            "rag_confirmation": "rag_confirmation",  # 先到RAG确认
            "generate_outline": "generate_outline"
        }
    )

    # RAG确认后的路由
    workflow.add_edge("rag_confirmation", "rag_enhancement")

    # RAG增强后的条件路由
    workflow.add_conditional_edges(
        "rag_enhancement",
        route_after_rag_enhancement,
        {
            "search_confirmation": "search_confirmation"
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

    # 返回未编译的工作流，让调用者管理 checkpointer
    return workflow

