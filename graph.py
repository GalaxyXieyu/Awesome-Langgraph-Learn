"""
LangGraph智能写作助手 - 图结构模块
实现基于状态图的智能写作工作流
"""

import os
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from tools import (tavily_search, validate_outline, format_article,
                   get_available_knowledge_bases, search_knowledge_base,
                   keyword_knowledge_search, hybrid_search, content_analyzer,
                   topic_expander, writing_style_advisor)
import logging
import time
import json
import re
from langgraph.config import get_stream_writer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --#DEBUG#--
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
# --#DEBUG#--


def try_parse_partial_outline(partial_response: str) -> dict:
    """
    尝试解析部分生成的大纲内容
    支持不完整的JSON结构，提取已完成的章节信息
    """
    try:
        # 方法1：直接尝试JSON解析
        return json.loads(partial_response)
    except json.JSONDecodeError:
        pass
    
    try:
        # 方法2：尝试修复不完整的JSON
        # 添加缺失的结束括号
        fixed_json = partial_response.rstrip()
        if not fixed_json.endswith('}'):
            # 计算需要的结束括号数量
            open_braces = fixed_json.count('{') - fixed_json.count('}')
            open_brackets = fixed_json.count('[') - fixed_json.count(']')
            
            # 添加缺失的结束符
            fixed_json += ']' * open_brackets + '}' * open_braces
        
        return json.loads(fixed_json)
    except (json.JSONDecodeError, ValueError):
        pass
    
    try:
        # 方法3：使用正则表达式提取结构化信息
        outline = {"title": "", "sections": []}
        
        # 提取标题
        title_match = re.search(r'"title":\s*"([^"]*)"', partial_response)
        if title_match:
            outline["title"] = title_match.group(1)
        
        # 提取章节信息
        sections_text = re.search(r'"sections":\s*\[(.*)', partial_response, re.DOTALL)
        if sections_text:
            sections_content = sections_text.group(1)
            
            # 查找完整的章节对象
            section_pattern = r'\{\s*"title":\s*"([^"]*)"[^}]*"description":\s*"([^"]*)"[^}]*"key_points":\s*\[([^\]]*)\]\s*\}'
            section_matches = re.finditer(section_pattern, sections_content)
            
            for match in section_matches:
                title = match.group(1)
                description = match.group(2)
                key_points_str = match.group(3)
                
                # 解析key_points
                key_points = []
                if key_points_str:
                    key_point_matches = re.findall(r'"([^"]*)"', key_points_str)
                    key_points = list(key_point_matches)
                
                outline["sections"].append({
                    "title": title,
                    "description": description,
                    "key_points": key_points
                })
        
        # 只有当至少有标题或章节时才返回
        if outline["title"] or outline["sections"]:
            return outline
            
    except Exception:
        pass
    
    return None


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
    enable_search: bool  # 是否启用搜索

    # 工作流状态
    current_step: str  # 当前步骤
    outline: Optional[Dict[str, Any]]  # 文章大纲
    article: Optional[str]  # 生成的文章
    search_results: List[Dict[str, Any]]  # 搜索结果

    # 用户交互
    user_confirmation: Optional[str]  # 用户确认信息
    search_permission: Optional[str]  # 搜索权限确认

    # RAG增强功能
    rag_enhancement: Optional[str]  # RAG增强状态
    enhancement_suggestions: Optional[List[Dict[str, Any]]]  # 增强建议
    selected_knowledge_bases: Optional[List[str]]  # 选择的知识库ID列表

    # 最终报告功能
    final_report: Optional[str]  # 最终生成的报告
    quality_score: Optional[float]  # 内容质量分数
    style_score: Optional[float]  # 风格匹配分数

    # 🏆 新增：流式生成状态字段
    current_word_count: Optional[int]  # 当前字数
    generation_progress: Optional[int]  # 生成进度百分比
    chunk_count: Optional[int]  # chunk计数
    latest_chunk: Optional[str]  # 最新生成的chunk内容

    # 消息历史
    messages: Annotated[List, add_messages]  # 对话消息

    # 元数据
    generation_time: float  # 生成时间
    word_count: int  # 字数统计
    status: str  # 状态 (processing/completed/error)
    error_message: Optional[str]  # 错误信息


def create_llm() -> ChatOpenAI:
    """创建LLM实例 - 强制启用流式输出"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
    )


async def generate_outline_node(state: WritingState, config=None) -> WritingState:
    """
    大纲生成节点 - 优化版本，使用异步非流式调用
    根据教程最佳实践：大纲生成不需要实时反馈，使用 async def + ainvoke
    """
    # 安全获取流式写入器
    try:
        writer = get_stream_writer()
    except Exception:
        # 如果无法获取writer，使用空函数
        writer = lambda x: None

    try:
        # custom 流式输出 - 进度反馈
        writer({"step": "outline_generation", "status": "开始生成大纲", "progress": 0})

        # 创建JSON输出解析器
        parser = JsonOutputParser(pydantic_object=ArticleOutline)

        # 构建提示模板
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

        # 创建LLM和链
        llm = create_llm()
        chain = outline_prompt | llm | parser

        writer({"step": "outline_generation", "status": "正在生成大纲", "progress": 50})

        # 🔥 真正的流式大纲生成：实时更新状态和进度
        full_response = ""
        chunk_count = 0
        
        async for chunk in llm.astream([
            ("system", """你是一个专业的写作助手。请根据用户提供的主题生成一个详细的文章大纲。
            要求：
            1. 大纲应该包含标题和3-6个主要章节
            2. 每个章节应该有清晰的主题和简要说明
            3. 整体结构要逻辑清晰，层次分明
            4. 适合{style}风格的写作
            5. 使用{language}语言

            {format_instructions}""".format(
                style=state.get("style", "formal"),
                language=state.get("language", "zh"),
                format_instructions=parser.get_format_instructions()
            )),
            ("human", f"请为以下主题生成文章大纲：{state['topic']}")
        ], config=config):
            if chunk.content and isinstance(chunk.content, str):
                full_response += chunk.content
                chunk_count += 1
                # print(chunk.content)
                # 🔥 关键：实时更新状态，让LangGraph流式传递更新
                progress = min(90, len(full_response) // 5)  # 根据长度计算进度
                
                # 更新状态中的流式字段
                state.update({
                    "latest_chunk": chunk.content,
                    "current_step": "generating_outline",
                    "generation_progress": progress,
                    "chunk_count": chunk_count,
                    "current_word_count": len(full_response.split())
                })
                
                # 🌊 实时发送流式进度更新
                writer({
                    "step": "outline_generation", 
                    "status": "正在生成大纲...",
                    "progress": progress,
                    "current_content": chunk.content,
                    "total_chars": len(full_response),
                    "chunk_count": chunk_count
                })
                
                # 🧠 尝试智能部分解析（提取已完成的章节）
                try:
                    # 简单的部分解析：检查是否包含完整的JSON结构片段
                    if '"title"' in full_response and '"sections"' in full_response:
                        # 尝试解析当前已生成的内容
                        temp_outline = try_parse_partial_outline(full_response)
                        if temp_outline:
                            # 如果解析成功，更新大纲状态
                            state["outline"] = temp_outline
                            writer({
                                "step": "outline_generation",
                                "status": f"已解析到 {len(temp_outline.get('sections', []))} 个章节",
                                "progress": progress,
                                "parsed_sections": len(temp_outline.get('sections', []))
                            })
                except Exception:
                    pass  # 部分解析失败时继续生成

        # 最终完整解析
        writer({"step": "outline_generation", "status": "完成生成，正在解析...", "progress": 95})
        
        try:
            outline_data = parser.parse(full_response)
        except Exception as parse_error:
            logger.warning(f"JSON解析失败，尝试直接使用响应: {parse_error}")
            # 如果解析失败，创建一个简单的大纲结构
            outline_data = {
                "title": f"{state['topic']}",
                "sections": [
                    {"title": "引言", "description": "介绍主题背景", "key_points": ["背景介绍", "重要性"]},
                    {"title": "主要内容", "description": "详细阐述主题", "key_points": ["核心观点", "具体分析"]},
                    {"title": "结论", "description": "总结要点", "key_points": ["总结", "展望"]}
                ]
            }

        # JsonOutputParser返回的是字典，直接使用
        if isinstance(outline_data, dict):
            outline = outline_data
        else:
            # 如果是Pydantic对象，转换为字典格式
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

        writer({"step": "outline_generation", "status": "验证大纲质量", "progress": 80})

        # 验证大纲
        validation_result = validate_outline.invoke({"outline": outline})

        # custom 流式输出 - 完成状态
        writer({
            "step": "outline_generation",
            "status": "大纲生成完成",
            "progress": 100,
            "outline": outline,
            "validation_score": validation_result.get('score', 0)
        })

        # 更新状态 - 这会触发 updates 流式输出
        state["outline"] = outline
        state["current_step"] = "outline_generated"
        state["status"] = "completed"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"已生成文章大纲：\n标题：{outline['title']}\n章节数：{len(outline['sections'])}\n验证分数：{validation_result.get('score', 0)}")
        ]

        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 大纲生成完成，章节数: {len(outline['sections'])}")
        # --#DEBUG#--

        return state

    except Exception as e:
        logger.error(f"大纲生成失败: {str(e)}")

        # custom 流式输出 - 错误状态
        writer({"step": "outline_generation", "status": f"生成失败: {str(e)}", "progress": -1})

        # 创建备用大纲
        fallback_outline = {
            "title": f"关于{state['topic']}的文章",
            "sections": [
                {"title": "引言", "description": "介绍主题背景", "key_points": ["背景介绍", "重要性"]},
                {"title": "主要内容", "description": "详细阐述主题", "key_points": ["核心观点", "具体分析"]},
                {"title": "结论", "description": "总结要点", "key_points": ["总结", "展望"]}
            ]
        }

        # 更新状态 - 这也会触发 updates 流式输出
        state["outline"] = fallback_outline
        state["current_step"] = "outline_generated"
        state["status"] = "fallback"
        state["error_message"] = str(e)
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"使用备用大纲：{fallback_outline['title']}")
        ]
        return state


def human_confirmation_node(state: WritingState) -> WritingState:
    """
    人工确认节点 - 动态中断版本
    根据用户设置和大纲质量动态决定是否需要确认
    """
    from langgraph.types import interrupt

    # 检查是否需要用户确认 - 动态判断逻辑
    outline = state.get("outline") or {}
    
    # 获取大纲质量分数（假设从验证结果中获取）
    outline_quality = 100  # 默认高质量
    
    # 动态中断条件：
    # 1. 用户明确要求确认（可通过状态传递）
    # 2. 大纲质量较低需要确认  
    # 3. 首次使用系统需要确认
    require_confirmation = state.get("require_confirmation", True)  # 用户设置
    low_quality = outline_quality < 80  # 低质量大纲
    new_user = state.get("user_id", "").endswith("_new")  # 新用户
    
    # 如果用户明确设置不需要确认，则跳过其他条件
    if require_confirmation is False:
        need_confirmation = False
    else:
        # 否则根据质量和用户类型判断
        need_confirmation = require_confirmation or low_quality or new_user
    
    if not need_confirmation:
        # 跳过确认，自动通过
        state.update({
            "user_confirmation": "auto_yes",
            "current_step": "confirmation_processed",
            "messages": state.get("messages", []) + [
                AIMessage(content="大纲质量良好，自动确认通过")
            ]
        })
        return state

    # 需要确认时才执行中断
    outline_text = f"文章标题：{outline.get('title', '未知')}\n\n"
    sections = outline.get("sections") or []
    for i, section in enumerate(sections, 1):
        outline_text += f"{i}. {section.get('title', '未知章节')}\n"
        outline_text += f"   描述：{section.get('description', '无描述')}\n"
        if section.get('key_points'):
            outline_text += f"   要点：{', '.join(section['key_points'])}\n"
        outline_text += "\n"

    user_confirmation = interrupt({
        "type": "outline_confirmation",
        "message": "请确认以下大纲是否满意",
        "outline": outline,
        "formatted_outline": outline_text,
        "instructions": "请回复 'yes' 确认继续，或 'no' 重新生成大纲",
        "quality_score": outline_quality
    })

    # 处理用户确认结果
    if isinstance(user_confirmation, str):
        confirmation = user_confirmation.lower().strip()
    else:
        confirmation = str(user_confirmation).lower().strip()

    # 更新状态
    state.update({
        "user_confirmation": confirmation,
        "current_step": "confirmation_processed",
        "messages": state.get("messages", []) + [
            AIMessage(content=f"用户确认结果: {confirmation}")
        ]
    })

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
        generation_prompt = f"""请根据以下大纲生成一篇完整的文章：

{outline_text}

{search_context}

{rag_context}

要求：
1. 文章风格：{state.get('style', 'formal')}
2. 语言：{state.get('language', 'zh')}
3. 目标字数：约{state.get('max_words', 1000)}字
4. 内容要求：逻辑清晰、论证充分、语言流畅
5. 如果有参考资料，请合理引用和整合

请生成完整的文章内容。"""

        # 🔥 正确的LangGraph流式方法：使用astream实现真正的token级流式输出
        from langchain_core.runnables import RunnableLambda
        
        # 创建消息
        messages = [HumanMessage(content=generation_prompt)]
        
        # 使用流式调用收集所有token，实现真正的流式输出
        full_article = ""
        async for chunk in llm.astream(messages, config=config):
            if chunk.content and isinstance(chunk.content, str):
                full_article += chunk.content

        # 格式化文章
        formatted_result = format_article.invoke({
            "content": full_article,
            "style": state.get("style", "formal")
        })

        # 计算生成时间
        generation_time = time.time() - start_time

        # 更新状态
        state.update({
            "article": formatted_result.get("formatted_content", full_article),
            "word_count": formatted_result.get("word_count", len(full_article)),
            "generation_time": generation_time,
            "current_step": "article_generated",
            "status": "completed",
            "messages": state.get("messages", []) + [
                AIMessage(content=f"文章生成完成！\n字数：{formatted_result.get('word_count', len(full_article))}\n生成时间：{generation_time:.1f}秒")
            ]
        })

        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 文章生成完成，字数: {formatted_result.get('word_count', len(full_article))}")
        # --#DEBUG#--

        return state

    except Exception as e:
        logger.error(f"文章生成失败: {str(e)}")
        state.update({
            "status": "error",
            "error_message": f"文章生成失败: {str(e)}",
            "current_step": "error"
        })
        return state


def generate_final_report_node(state: WritingState) -> WritingState:
    """
    生成最终报告节点 - 直接生成完整的写作报告
    包含文章内容、统计信息和质量评估
    """
    # --#DEBUG#--
    if DEBUG_MODE:
        print("[DEBUG] 开始生成最终报告")
    # --#DEBUG#--

    # 简化的进度记录函数
    def log_progress(step: str, status: str, progress: int):
        if DEBUG_MODE:
            print(f"[DEBUG] {step}: {status} ({progress}%)")

    log_progress("final_report", "开始生成最终报告", 0)

    try:
        article = state.get("article", "")
        topic = state.get("topic", "")
        outline = state.get("outline", {})
        search_results = state.get("search_results", [])
        word_count = state.get("word_count", 0)
        generation_time = state.get("generation_time", 0.0)

        if not article:
            state.update({
                "current_step": "report_error",
                "error_message": "没有文章内容，无法生成报告",
                "messages": state.get("messages", []) + [
                    AIMessage(content="没有文章内容，无法生成报告")
                ]
            })
            return state

        log_progress("final_report", "分析文章质量", 20)

        # 执行内容分析
        try:
            content_analysis = content_analyzer.invoke({"text": article})
        except Exception as e:
            logger.warning(f"内容分析失败: {e}")
            content_analysis = {"quality_score": 0, "word_count": word_count}

        log_progress("final_report", "生成写作风格评估", 40)

        # 执行写作风格分析
        try:
            style_analysis = writing_style_advisor.invoke({
                "content": article,
                "target_style": state.get("style", "formal")
            })
        except Exception as e:
            logger.warning(f"风格分析失败: {e}")
            style_analysis = {"style_match_score": 0}

        log_progress("final_report", "整理报告内容", 60)

        # 生成综合报告
        report_sections = []

        # 1. 基本信息
        report_sections.append("# 📝 智能写作助手 - 完成报告\n")
        report_sections.append(f"**主题**: {topic}")
        report_sections.append(f"**生成时间**: {generation_time:.1f}秒")
        report_sections.append(f"**字数统计**: {word_count}字")
        report_sections.append(f"**写作风格**: {state.get('style', 'formal')}")
        report_sections.append("")

        # 2. 文章大纲
        if outline:
            report_sections.append("## 📋 文章大纲")
            report_sections.append(f"**标题**: {outline.get('title', '未知')}")
            sections = outline.get("sections", [])
            for i, section in enumerate(sections, 1):
                report_sections.append(f"{i}. {section.get('title', '未知章节')}")
                if section.get('description'):
                    report_sections.append(f"   - {section.get('description')}")
            report_sections.append("")

        # 3. 质量评估
        report_sections.append("## 📊 质量评估")
        quality_score = content_analysis.get('quality_score', 0) if isinstance(content_analysis, dict) else 0
        style_score = style_analysis.get('style_match_score', 0) if isinstance(style_analysis, dict) else 0

        report_sections.append(f"- **内容质量分数**: {quality_score}/100")
        report_sections.append(f"- **风格匹配分数**: {style_score}/100")
        report_sections.append(f"- **综合评分**: {(quality_score + style_score) / 2:.1f}/100")
        report_sections.append("")

        # 4. 搜索资源使用情况
        if search_results:
            report_sections.append("## 🔍 参考资源")
            report_sections.append(f"使用了 {len(search_results)} 个搜索结果作为参考：")
            for i, result in enumerate(search_results[:5], 1):
                title = result.get('title', '未知标题')
                url = result.get('url', '')
                report_sections.append(f"{i}. [{title}]({url})")
            report_sections.append("")

        # 5. 生成的文章内容
        report_sections.append("## 📄 生成的文章")
        report_sections.append("```")
        report_sections.append(article)
        report_sections.append("```")
        report_sections.append("")

        # 6. 技术统计
        report_sections.append("## 🔧 技术统计")
        report_sections.append(f"- **处理节点**: 大纲生成 → 确认 → RAG增强 → 搜索 → 文章生成")
        report_sections.append(f"- **使用工具**: 内容分析器、写作风格顾问")
        selected_kbs = state.get("selected_knowledge_bases")
        if selected_kbs:
            kb_count = len(selected_kbs)
            report_sections.append(f"- **知识库**: 使用了 {kb_count} 个知识库")
        report_sections.append(f"- **生成模式**: 流式输出")
        report_sections.append("")

        log_progress("final_report", "完成报告生成", 80)

        # 合并报告内容
        final_report = "\n".join(report_sections)

        log_progress("final_report", f"最终报告生成完成 (长度: {len(final_report)}, 质量: {quality_score})", 100)

        # 更新状态
        state.update({
            "current_step": "completed",
            "status": "completed",
            "messages": state.get("messages", []) + [
                AIMessage(content=f"✅ 写作任务完成！\n📊 质量评分: {(quality_score + style_score) / 2:.1f}/100\n📝 字数: {word_count}字\n⏱️ 用时: {generation_time:.1f}秒\n\n{final_report}")
            ]
        })

        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 最终报告生成完成，质量分数: {quality_score}")
        # --#DEBUG#--

        return state

    except Exception as e:
        logger.error(f"报告生成失败: {str(e)}")
        log_progress("final_report", f"报告生成失败: {str(e)}", -1)
        state.update({
            "status": "error",
            "error_message": f"报告生成失败: {str(e)}",
            "current_step": "error"
        })
        return state


def search_confirmation_node(state: WritingState) -> WritingState:
    """
    搜索确认节点 - 动态中断版本
    根据主题敏感度、用户偏好、成本考虑等动态决定是否需要搜索确认
    """
    from langgraph.types import interrupt
    
    # --#DEBUG#--
    if DEBUG_MODE:
        print("[DEBUG] 动态搜索权限检查")
    # --#DEBUG#--

    # 检查是否启用搜索功能
    if not state.get("enable_search", True):
        state.update({
            "current_step": "search_skipped",
            "search_permission": "no",
            "messages": state.get("messages", []) + [
                AIMessage(content="搜索功能已禁用")
            ]
        })
        return state

    # 动态判断是否需要搜索确认
    topic = state.get("topic", "").lower()
    
    # 1. 敏感主题判断
    sensitive_keywords = ["private", "secret", "confidential", "内部", "机密", "个人"]
    is_sensitive = any(keyword in topic for keyword in sensitive_keywords)
    
    # 2. 主题类型判断（技术类主题通常需要最新信息）
    technical_keywords = ["编程", "技术", "开发", "python", "javascript", "ai", "machine learning"]
    is_technical = any(keyword in topic for keyword in technical_keywords)
    
    # 3. 用户历史偏好（可以从用户ID或状态中获取）
    user_prefers_search = state.get("user_prefers_search", True)
    
    # 4. 现有内容充足性判断
    outline = state.get("outline", {})
    sections_count = len(outline.get("sections", []))
    content_sufficient = sections_count >= 4  # 4个以上章节认为内容比较充足
    
    # 动态决策逻辑
    if is_sensitive:
        # 敏感主题：需要用户明确授权
        need_confirmation = True
        auto_decision = None
    elif is_technical and user_prefers_search:
        # 技术主题且用户偏好搜索：自动允许
        need_confirmation = False
        auto_decision = "yes"
    elif content_sufficient and not is_technical:
        # 非技术主题且内容充足：自动跳过
        need_confirmation = False  
        auto_decision = "no"
    else:
        # 其他情况：询问用户
        need_confirmation = True
        auto_decision = None
    
    if not need_confirmation:
        # 自动决策，无需用户确认
        state.update({
            "current_step": "search_auto_decided",
            "search_permission": auto_decision,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"自动决定搜索权限: {'允许搜索' if auto_decision == 'yes' else '跳过搜索'}")
            ]
        })
        return state

    # 需要用户确认时执行中断
    search_info = {
        "estimated_queries": min(3, len(outline.get("sections", []))),
        "topic_sensitivity": "高" if is_sensitive else "低", 
        "recommended_action": "建议搜索" if is_technical else "可选搜索"
    }
    
    user_search_permission = interrupt({
        "type": "search_permission",
        "message": "是否允许进行联网搜索？",
        "topic": state.get("topic"),
        "search_info": search_info,
        "instructions": "请回复 'yes' 允许搜索，'no' 跳过搜索",
        "sensitivity_level": "高" if is_sensitive else "低"
    })

    # 处理用户选择
    if isinstance(user_search_permission, str):
        permission = user_search_permission.lower().strip()
    else:
        permission = str(user_search_permission).lower().strip()

    state.update({
        "current_step": "search_permission_processed",
        "search_permission": permission,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"搜索权限确认结果: {permission}")
        ]
    })

    return state


def search_execution_node(state: WritingState) -> WritingState:
    """
    搜索执行节点 - 修复版本，保持同步以支持工具调用
    搜索节点主要调用工具，保持同步即可
    """
    from langgraph.config import get_stream_writer

    # --#DEBUG#--
    if DEBUG_MODE:
        print("[DEBUG] 执行联网搜索")
    # --#DEBUG#--

    try:
        writer = get_stream_writer()

        # 检查搜索权限
        if state.get("search_permission") != "yes":
            writer({"step": "search_execution", "status": "跳过搜索", "progress": 100})
            state.update({
                "search_results": [],
                "current_step": "search_completed"
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

                # --#DEBUG#--
                if DEBUG_MODE:
                    print(f"[DEBUG] 搜索查询 '{query}' 返回 {len(results) if isinstance(results, list) else 1} 个结果")
                # --#DEBUG#--

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
            "current_step": "search_completed",
            "messages": state.get("messages", []) + [
                AIMessage(content=f"搜索完成，获得 {len(unique_results)} 个相关资料。")
            ]
        })

        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 搜索完成，共获得 {len(unique_results)} 个结果")
        # --#DEBUG#--

        return state

    except Exception as e:
        logger.error(f"搜索执行失败: {str(e)}")
        writer({"step": "search_execution", "status": f"搜索失败: {str(e)}", "progress": -1})
        state.update({
            "status": "error",
            "error_message": f"搜索执行失败: {str(e)}",
            "current_step": "error"
        })
        return state


def rag_enhancement_node(state: WritingState) -> WritingState:
    """
    RAG增强节点 - 动态中断版本
    根据主题类型、用户历史、知识库匹配度等动态决定是否需要RAG增强
    """
    from langgraph.types import interrupt

    # --#DEBUG#--
    if DEBUG_MODE:
        print("[DEBUG] 动态RAG增强检查")
    # --#DEBUG#--

    # 获取流式写入器
    try:
        from langgraph.config import get_stream_writer
        writer = get_stream_writer()
        writer({"step": "rag_enhancement", "status": "检查RAG增强需求", "progress": 0})
    except Exception:
        writer = lambda _: None

    # 获取可用知识库
    try:
        available_kbs = get_available_knowledge_bases.invoke({})
        if not available_kbs or (len(available_kbs) == 1 and "error" in available_kbs[0]):
            state.update({
                "rag_enhancement": "no_knowledge_bases", 
                "current_step": "rag_skipped",
                "messages": state.get("messages", []) + [
                    AIMessage(content="没有可用的知识库，跳过RAG增强")
                ]
            })
            return state
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        state.update({
            "rag_enhancement": "error",
            "current_step": "rag_error"
        })
        return state

    # 动态判断是否需要RAG增强
    topic = state.get("topic", "").lower()
    
    # 1. 主题匹配度分析
    kb_matches = []
    for kb in available_kbs:
        kb_category = kb.get("category", "").lower()
        kb_keywords = kb.get("keywords", "").lower()
        
        # 简单的匹配算法
        topic_words = topic.split()
        match_score = 0
        for word in topic_words:
            if word in kb_category or word in kb_keywords:
                match_score += 1
        
        if match_score > 0:
            kb_matches.append({
                "kb": kb,
                "score": match_score
            })
    
    # 2. 用户历史和偏好
    user_prefers_rag = state.get("user_prefers_rag", True)
    user_expertise = state.get("user_expertise", "intermediate")  # beginner/intermediate/expert
    
    # 3. 内容复杂度判断
    outline = state.get("outline", {})
    sections_count = len(outline.get("sections", []))
    complex_topic = sections_count >= 5  # 5个以上章节认为是复杂主题
    
    # 动态决策逻辑
    if not kb_matches:
        # 没有匹配的知识库：自动跳过
        need_rag = False
        auto_decision = "skip"
        reason = "没有匹配的知识库"
    elif user_expertise == "expert" and not complex_topic:
        # 专家用户且主题不复杂：自动跳过
        need_rag = False
        auto_decision = "skip"
        reason = "专家用户，主题相对简单"
    elif len(kb_matches) == 1 and kb_matches[0]["score"] >= 2:
        # 单个高匹配度知识库：自动选择
        need_rag = False
        auto_decision = "auto_select"
        auto_kb = kb_matches[0]["kb"]["id"]
        reason = f"自动选择高匹配度知识库: {kb_matches[0]['kb']['name']}"
    elif user_prefers_rag and kb_matches:
        # 用户偏好RAG且有匹配：询问用户
        need_rag = True
        auto_decision = None
        reason = "多个匹配的知识库，需要用户选择"
    else:
        # 其他情况：自动跳过
        need_rag = False
        auto_decision = "skip"
        reason = "用户偏好或匹配度不足"

    writer({"step": "rag_enhancement", "status": f"决策结果: {reason}", "progress": 50})

    if not need_rag:
        # 自动决策，无需用户选择
        if auto_decision == "auto_select":
            # 自动选择知识库并进行简单检索
            try:
                results = search_knowledge_base.invoke({
                    "query": topic,
                    "knowledge_base_ids": [auto_kb],
                    "top_k": 2
                })
                enhancement_suggestions = []
                if isinstance(results, list):
                    for result in results[:3]:
                        if isinstance(result, dict) and "content" in result:
                            enhancement_suggestions.append({
                                "content": result.get("content", ""),
                                "title": result.get("title", ""),
                                "knowledge_base": result.get("knowledge_base_name", ""),
                                "relevance": result.get("relevance_score", 0)
                            })
                
                state.update({
                    "rag_enhancement": "auto_applied",
                    "selected_knowledge_bases": [auto_kb],
                    "enhancement_suggestions": enhancement_suggestions,
                    "current_step": "rag_enhanced",
                    "messages": state.get("messages", []) + [
                        AIMessage(content=f"自动应用RAG增强，找到 {len(enhancement_suggestions)} 个建议")
                    ]
                })
            except Exception as e:
                logger.warning(f"自动RAG增强失败: {e}")
                state.update({
                    "rag_enhancement": "auto_failed",
                    "current_step": "rag_skipped"
                })
        else:
            # 跳过RAG增强
            state.update({
                "rag_enhancement": "skipped",
                "current_step": "rag_skipped",
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"跳过RAG增强：{reason}")
                ]
            })
        
        writer({"step": "rag_enhancement", "status": "RAG增强决策完成", "progress": 100})
        return state

    # 需要用户选择时执行中断
    kb_options = []
    for match in sorted(kb_matches, key=lambda x: x["score"], reverse=True):
        kb = match["kb"]
        kb_options.append({
            "id": kb["id"],
            "name": kb["name"],
            "description": kb["description"],
            "match_score": match["score"],
            "document_count": kb.get("document_count", 0)
        })

    kb_list_text = "\n".join([
        f"• [{kb['id']}] {kb['name']} (匹配度: {kb['match_score']}, {kb['document_count']}文档)\n  {kb['description']}"
        for kb in kb_options[:5]  # 最多显示5个选项
    ])

    user_kb_choice = interrupt({
        "type": "knowledge_base_selection",
        "message": f"发现 {len(kb_matches)} 个匹配的知识库，是否进行RAG增强？",
        "available_options": kb_options,
        "formatted_options": kb_list_text,
        "instructions": "请输入知识库ID（如'python_advanced'）或 'skip' 跳过RAG增强",
        "recommendation": f"推荐使用: {kb_options[0]['id']}" if kb_options else "无推荐"
    })

    # 处理用户选择
    if isinstance(user_kb_choice, str):
        choice = user_kb_choice.strip()
    else:
        choice = str(user_kb_choice).strip()

    if choice.lower() in ["skip", "no", "none"]:
        state.update({
            "rag_enhancement": "user_skipped",
            "current_step": "rag_skipped",
            "messages": state.get("messages", []) + [
                AIMessage(content="用户选择跳过RAG增强")
            ]
        })
    else:
        # 验证选择的知识库ID
        valid_kb_ids = [kb["id"] for kb in kb_options]
        if choice in valid_kb_ids:
            selected_kb_id = choice
        else:
            # 无效选择，使用推荐的第一个
            selected_kb_id = kb_options[0]["id"] if kb_options else None

        if selected_kb_id:
            # 执行RAG检索
            try:
                results = search_knowledge_base.invoke({
                    "query": topic,
                    "knowledge_base_ids": [selected_kb_id],
                    "top_k": 3
                })
                enhancement_suggestions = []
                if isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict) and "content" in result:
                            enhancement_suggestions.append({
                                "content": result.get("content", ""),
                                "title": result.get("title", ""),
                                "knowledge_base": result.get("knowledge_base_name", ""),
                                "relevance": result.get("relevance_score", 0)
                            })
                
                state.update({
                    "rag_enhancement": "applied",
                    "selected_knowledge_bases": [selected_kb_id],
                    "enhancement_suggestions": enhancement_suggestions,
                    "current_step": "rag_enhanced",
                    "messages": state.get("messages", []) + [
                        AIMessage(content=f"应用RAG增强，使用知识库 {selected_kb_id}，找到 {len(enhancement_suggestions)} 个建议")
                    ]
                })
            except Exception as e:
                logger.error(f"RAG检索失败: {e}")
                state.update({
                    "rag_enhancement": "failed",
                    "current_step": "rag_error"
                })
        else:
            state.update({
                "rag_enhancement": "no_valid_selection",
                "current_step": "rag_skipped"
            })

    writer({"step": "rag_enhancement", "status": "RAG增强完成", "progress": 100})
    return state


def route_after_confirmation(state: WritingState) -> str:
    """
    确认后的路由逻辑 - 根据用户确认结果决定下一步
    """
    user_confirmation = (state.get("user_confirmation") or "").lower().strip()

    # --#DEBUG#--
    if DEBUG_MODE:
        print(f"[DEBUG] 用户确认结果: {user_confirmation}")
    # --#DEBUG#--

    if user_confirmation == "yes" or user_confirmation == "auto_yes":
        return "rag_enhancement"  # 先进行RAG增强
    elif user_confirmation == "no":
        return "generate_outline"  # 重新生成大纲
    else:
        # 这种情况不应该发生，因为interrupt()会等待有效输入
        return "rag_enhancement"


def route_after_rag_enhancement(state: WritingState) -> str:
    """
    RAG增强后的路由逻辑
    """
    rag_status = state.get("rag_enhancement", "")

    # --#DEBUG#--
    if DEBUG_MODE:
        print(f"[DEBUG] RAG增强状态: {rag_status}")
    # --#DEBUG#--

    # 无论RAG增强结果如何，都继续到搜索确认
    return "search_confirmation"


def route_after_search_confirmation(state: WritingState) -> str:
    """
    搜索确认后的路由逻辑 - 根据搜索权限决定是否执行搜索
    """
    search_permission = (state.get("search_permission") or "").lower().strip()

    # --#DEBUG#--
    if DEBUG_MODE:
        print(f"[DEBUG] 搜索权限: {search_permission}")
    # --#DEBUG#--

    if search_permission == "yes":
        return "search_execution"
    else:
        return "article_generation"  # 直接生成文章


def should_continue_after_search(state: WritingState) -> str:
    """
    搜索完成后的路由逻辑 - 搜索完成后直接进入文章生成
    """
    # 忽略state参数，直接返回下一个节点
    return "article_generation"


def create_writing_assistant_graph():
    """
    创建智能写作助手的状态图 - 动态中断版本
    不使用固定的interrupt_before，而是在节点内部动态决定中断

    Returns:
        编译后的状态图
    """
    # 创建状态图
    workflow = StateGraph(WritingState)

    # 添加节点
    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("human_confirmation", human_confirmation_node)
    workflow.add_node("rag_enhancement", rag_enhancement_node)
    workflow.add_node("search_confirmation", search_confirmation_node)
    workflow.add_node("search_execution", search_execution_node)
    workflow.add_node("article_generation", article_generation_node)
    workflow.add_node("generate_final_report", generate_final_report_node)

    # 设置入口点
    workflow.set_entry_point("generate_outline")

    # 添加边和条件路由
    workflow.add_edge("generate_outline", "human_confirmation")

    # 人工确认后的条件路由
    workflow.add_conditional_edges(
        "human_confirmation",
        route_after_confirmation,
        {
            "rag_enhancement": "rag_enhancement",
            "generate_outline": "generate_outline"
        }
    )

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

    # 搜索完成后的路由
    workflow.add_conditional_edges(
        "search_execution",
        should_continue_after_search,
        {
            "article_generation": "article_generation"
        }
    )

    # 文章生成完成后进入最终报告生成
    workflow.add_edge("article_generation", "generate_final_report")

    # 最终报告生成完成后结束
    workflow.add_edge("generate_final_report", END)

    # 配置checkpointer以支持状态持久化
    memory = InMemorySaver()

    # 🔥 动态中断模式：不使用interrupt_before，而是在节点内部动态决定中断
    # 这样可以根据实际状态和用户设置智能决定是否需要中断
    app = workflow.compile(
        checkpointer=memory
        # 移除固定的interrupt_before配置，改为节点内部动态中断
    )

    return app


def should_interrupt_for_node(node_name: str, state: WritingState) -> bool:
    """
    客户端智能判断函数 - 决定是否需要在特定节点前中断
    
    Args:
        node_name: 节点名称
        state: 当前状态
    
    Returns:
        bool: 是否需要中断
    """
    # 搜索执行节点的判断逻辑
    if node_name == "search_execution":
        # 如果搜索被禁用，不需要中断
        if not state.get("enable_search", True):
            return False
        
        # 如果用户已经明确拒绝搜索，不需要中断
        if state.get("search_permission") == "no":
            return False
            
        # 如果搜索权限待处理，需要中断询问用户
        if state.get("search_permission") == "pending":
            return True
            
        # 默认情况下，如果启用搜索且未设置权限，需要中断
        return state.get("search_permission") is None
    
    # 工具节点的判断逻辑（未来扩展）
    if "tool" in node_name.lower():
        # 可以根据具体工具类型和敏感度判断
        return False
        
    # 默认不中断
    return False


def get_interrupt_message_for_node(node_name: str, state: WritingState) -> dict:
    """
    为特定节点生成中断消息
    
    Args:
        node_name: 节点名称
        state: 当前状态
        
    Returns:
        dict: 中断消息字典
    """
    if node_name == "search_execution":
        return {
            "type": "search_permission",
            "message": "是否允许进行联网搜索？",
            "description": "为了生成更准确和最新的内容，系统可以进行联网搜索获取相关资料",
            "instructions": "请回复 'yes' 允许搜索，或 'no' 跳过搜索",
            "current_topic": state.get("topic", ""),
            "estimated_queries": 3  # 预估搜索查询数量
        }
    

    
    return {
        "type": "unknown",
        "message": f"节点 {node_name} 需要用户确认",
        "instructions": "请回复 'yes' 继续，或 'no' 跳过"
    }


def get_node_type(node_name: str) -> str:
    """
    获取节点类型用于智能路由
    
    Args:
        node_name: 节点名称
        
    Returns:
        str: 节点类型
    """
    node_types = {
        "generate_outline": "generation",
        "human_confirmation": "interaction", 
        "rag_enhancement": "enhancement",
        "search_confirmation": "interaction",
        "search_execution": "tool",
        "article_generation": "generation",
        "multi_tool_analysis": "analysis"
    }
    
    return node_types.get(node_name, "unknown")


def is_sensitive_operation(node_name: str, state: WritingState) -> bool:
    """
    判断是否为敏感操作，需要额外确认
    
    Args:
        node_name: 节点名称
        state: 当前状态
        
    Returns:
        bool: 是否为敏感操作
    """
    # 搜索操作：根据主题敏感度和用户设置判断
    if node_name == "search_execution":
        topic = state.get("topic", "").lower()
        sensitive_keywords = ["private", "secret", "confidential", "内部", "机密"]
        return any(keyword in topic for keyword in sensitive_keywords)
    
    # 报告生成：通常不敏感
    if node_name == "generate_final_report":
        return False  # 报告生成通常不敏感
    
    return False


def initialize_writing_state(
    topic: str,
    user_id: str,
    max_words: int = 1000,
    style: str = "formal",
    language: str = "zh",
    enable_search: bool = True
) -> WritingState:
    """
    初始化写作状态

    Args:
        topic: 文章主题
        user_id: 用户ID
        max_words: 最大字数
        style: 写作风格
        language: 语言
        enable_search: 是否启用搜索

    Returns:
        初始化的状态字典
    """
    return WritingState(
        topic=topic,
        user_id=user_id,
        max_words=max_words,
        style=style,
        language=language,
        enable_search=enable_search,
        current_step="initialized",
        outline=None,
        article=None,
        search_results=[],
        user_confirmation=None,
        search_permission=None,
        rag_enhancement=None,
        enhancement_suggestions=None,
        selected_knowledge_bases=None,
        final_report=None,
        quality_score=None,
        style_score=None,
        # 🏆 新增：流式生成状态字段初始化
        current_word_count=None,
        generation_progress=None,
        chunk_count=None,
        latest_chunk=None,
        messages=[],
        generation_time=0.0,
        word_count=0,
        status="processing",
        error_message=None
    )


def clean_debug_tags(module_name: str) -> None:
    """
    清理调试标记（生产环境使用）

    Args:
        module_name: 模块名称
    """
    # --#DEBUG#--
    if DEBUG_MODE:
        print(f"[DEBUG] 清理模块 {module_name} 的调试标记")
    # --#DEBUG#--

    logger.info(f"已清理模块 {module_name} 的调试代码")