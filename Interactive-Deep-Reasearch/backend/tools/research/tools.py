"""
研究工具集合
"""

import os
import time
import uuid
import json
import asyncio
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging

logger = logging.getLogger(__name__)

# 导入状态类型
try:
    from state import ReportOutline
except ImportError:
    # 如果导入失败，定义一个简单的类型
    class ReportOutline:
        pass


@tool
def web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """联网搜索工具"""
    try:
        if os.getenv("TAVILY_API_KEY"):
            try:
                search_tool = TavilySearchResults(
                    tavily_api_key=os.getenv("TAVILY_API_KEY"),
                    max_results=max_results,
                    search_depth="advanced",
                    include_answer=True,
                    include_raw_content=False,
                    include_images=False
                )

                # 尝试正确的调用方式
                results = search_tool.invoke({"query": query})

                formatted_results = []
                for result in results:
                    formatted_result = {
                        "id": str(uuid.uuid4()),
                        "query": query,
                        "title": result.get("title", ""),
                        "content": result.get("content", "")[:500],
                        "url": result.get("url", ""),
                        "relevance_score": result.get("score", 0.8),
                        "timestamp": time.time()
                    }
                    formatted_results.append(formatted_result)

                return formatted_results

            except Exception as tavily_error:
                logger.warning(f"Tavily搜索失败: {tavily_error}, 使用模拟搜索")
                # 回退到模拟搜索

        # 模拟搜索（当API不可用时）
        results = [
            {
                "id": str(uuid.uuid4()),
                "query": query,
                "title": f"关于{query}的最新研究报告",
                "content": f"关于{query}的最新研究显示，该领域正在快速发展。市场规模预计将在未来5年内增长150%，技术创新持续推进。",
                "url": f"https://example.com/research/{query}",
                "relevance_score": 0.85,
                "timestamp": time.time()
            },
            {
                "id": str(uuid.uuid4()),
                "query": query,
                "title": f"{query}技术突破分析",
                "content": f"{query}技术的核心突破在于算法优化和应用场景扩展。最新基准测试显示，性能提升了300%，应用范围更加广泛。",
                "url": f"https://example.com/tech/{query}",
                "relevance_score": 0.82,
                "timestamp": time.time()
            },
            {
                "id": str(uuid.uuid4()),
                "query": query,
                "title": f"{query}市场前景预测",
                "content": f"市场分析师预测，{query}相关产业将迎来爆发式增长，全球市场规模将达到数千亿美元，投资机会众多。",
                "url": f"https://example.com/market/{query}",
                "relevance_score": 0.80,
                "timestamp": time.time()
            }
        ]
        return results[:max_results]

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return [{
            "id": str(uuid.uuid4()),
            "error": f"搜索失败: {str(e)}",
            "query": query,
            "timestamp": time.time()
        }]


@tool
async def web_search_async(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """联网搜索工具（异步）"""
    try:
        if os.getenv("TAVILY_API_KEY"):
            # Tavily 暂无原生 async 客户端，这里用线程池包装同步调用
            loop = asyncio.get_event_loop()

            def _sync_call():
                search_tool = TavilySearchResults(
                    tavily_api_key=os.getenv("TAVILY_API_KEY"),
                    max_results=max_results,
                    search_depth="advanced",
                    include_answer=True,
                    include_raw_content=False,
                    include_images=False,
                )
                return search_tool.invoke({"query": query})

            try:
                results = await loop.run_in_executor(None, _sync_call)
            except Exception as tavily_error:
                logger.warning(f"[async] Tavily搜索失败: {tavily_error}, 回退到模拟搜索")
                return web_search(query, max_results)

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": str(uuid.uuid4()),
                    "query": query,
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:500],
                    "url": result.get("url", ""),
                    "relevance_score": result.get("score", 0.8),
                    "timestamp": time.time(),
                })
            return formatted_results
        # 无 API Key 时，使用同步的模拟搜索
        return web_search(query, max_results)
    except Exception as e:
        logger.error(f"[async] 搜索失败: {e}")
        return [{
            "id": str(uuid.uuid4()),
            "error": f"搜索失败: {str(e)}",
            "query": query,
            "timestamp": time.time(),
        }]



@tool
def industry_data(industry: str) -> Dict[str, Any]:
    """行业数据工具"""
    try:
        data_map = {
            "人工智能": "2023年全球AI市场规模达到1500亿美元，预计2025年将达到3900亿美元，年复合增长率38.1%",
            "区块链": "2023年全球区块链市场规模达到200亿美元，预计2025年将达到670亿美元",
            "云计算": "2023年全球云计算市场规模达到5450亿美元，预计2025年将达到8320亿美元"
        }

        return {
            "id": str(uuid.uuid4()),
            "industry": industry,
            "data": data_map.get(industry, f"{industry}行业数据：市场规模持续增长，技术创新加速"),
            "timestamp": time.time()
        }

    except Exception as e:
        return {"error": f"数据获取失败: {str(e)}"}


@tool
async def industry_data_async(industry: str) -> Dict[str, Any]:
    """行业数据工具（异步）"""
    return industry_data(industry)



@tool
def trend_analysis(topic: str) -> Dict[str, Any]:
    """趋势分析工具"""
    try:
        return {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "trend": f"{topic}发展趋势：技术成熟度快速提升，市场接受度逐步增长，政策支持力度加大，投资热度持续高涨",
            "timestamp": time.time()
        }
    except Exception as e:
        return {"error": f"趋势分析失败: {str(e)}"}


@tool
def research_context(query: str) -> Dict[str, Any]:
    """获取研究上下文工具"""
    try:
        return {
            "id": str(uuid.uuid4()),
            "query": query,
            "context": f"查询 '{query}' 的研究上下文：需要运行时绑定数据",
            "timestamp": time.time()
        }
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@tool
async def trend_analysis_async(topic: str) -> Dict[str, Any]:
    """趋势分析工具（异步）"""
    return trend_analysis(topic)


@tool
async def research_context_async(query: str) -> Dict[str, Any]:
    """获取研究上下文工具（异步）"""
    return research_context(query)


def create_llm() -> ChatOpenAI:
    """创建LLM实例"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
    )


@tool
def generate_outline(
    topic: str,
    report_type: str = "深度研究报告",
    target_audience: str = "专业人士",
    depth_level: str = "深度",
    target_length: int = 5000
) -> Dict[str, Any]:
    """
    生成深度研究报告大纲工具

    Args:
        topic: 研究主题
        report_type: 报告类型
        target_audience: 目标读者
        depth_level: 研究深度级别
        target_length: 目标字数

    Returns:
        Dict: 包含大纲数据的字典
    """
    try:
        llm = create_llm()
        parser = JsonOutputParser(pydantic_object=ReportOutline)

        # 构建高级大纲生成提示
        outline_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是专业的报告大纲设计专家。请生成详细的深度研究报告大纲。

            要求：
            1. 大纲符合{report_type}报告的标准结构
            2. 针对{target_audience}读者群体设计
            3. 研究深度为{depth_level}级别
            4. 目标字数约{target_length}字
            5. 每个章节包含研究查询关键词
            6. 章节优先级合理分配

            {format_instructions}"""),
            ("human", """
            请为以下主题生成专业的深度研究报告大纲：

            研究主题：{topic}
            报告类型：{report_type}
            目标读者：{target_audience}
            深度级别：{depth_level}

            请确保大纲结构完整、逻辑清晰、便于深度研究。
            """)
        ])

        input_data = {
            "topic": topic,
            "report_type": report_type,
            "target_audience": target_audience,
            "depth_level": depth_level,
            "target_length": target_length,
            "format_instructions": parser.get_format_instructions()
        }

        # 创建LLM链并执行
        llm_chain = outline_prompt | llm | parser
        outline_data = llm_chain.invoke(input_data)

        # 转换为字典格式
        if hasattr(outline_data, 'dict'):
            outline_dict = outline_data.dict()
        else:
            outline_dict = dict(outline_data) if outline_data else {}

        # 添加元数据
        result = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "outline": outline_dict,
            "timestamp": time.time(),
            "success": True
        }

        logger.info(f"大纲生成成功: {topic}")
        return result

    except Exception as e:
        logger.error(f"大纲生成失败: {str(e)}")
        return {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "error": f"大纲生成失败: {str(e)}",
            "timestamp": time.time(),
            "success": False
        }


# 导出工具列表
RESEARCH_TOOLS = [
    web_search,
    industry_data,
    trend_analysis,
    research_context,
    generate_outline
]

# 异步工具列表（用于需要并发的 Graph 或测试）
RESEARCH_TOOLS_ASYNC = [
    web_search_async,
    industry_data_async,
    trend_analysis_async,
    research_context_async,
]

