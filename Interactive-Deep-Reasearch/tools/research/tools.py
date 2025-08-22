"""
研究工具集合
包含所有研究员使用的工具
"""

from langchain_core.tools import tool


@tool
def web_search_tool(query: str, max_results: int = 3) -> str:
    """联网搜索工具 - 获取最新信息"""
    try:
        # 模拟搜索结果
        results = [
            f"关于{query}的最新研究显示，该领域正在快速发展。市场规模预计将在未来5年内增长150%。",
            f"{query}技术的核心突破在于算法优化。最新基准测试显示，性能提升了300%。",
            f"市场分析师预测，{query}相关产业将迎来爆发式增长，全球市场规模将达到500亿美元。"
        ]
        return "\n".join(results[:max_results])
    except Exception as e:
        return f"搜索失败: {str(e)}"


@tool
def industry_data_tool(industry: str) -> str:
    """行业数据工具 - 获取专业数据"""
    try:
        data = {
            "人工智能": "2023年全球AI市场规模达到1500亿美元，预计2025年将达到3900亿美元，年复合增长率38.1%",
            "区块链": "2023年全球区块链市场规模达到200亿美元，预计2025年将达到670亿美元",
            "云计算": "2023年全球云计算市场规模达到5450亿美元，预计2025年将达到8320亿美元"
        }
        return data.get(industry, f"{industry}行业数据：市场规模持续增长，技术创新加速")
    except Exception as e:
        return f"数据获取失败: {str(e)}"


@tool
def trend_analysis_tool(topic: str) -> str:
    """趋势分析工具 - 分析发展趋势"""
    try:
        return f"{topic}发展趋势：技术成熟度快速提升，市场接受度逐步增长，政策支持力度加大，投资热度持续高涨"
    except Exception as e:
        return f"趋势分析失败: {str(e)}"


@tool
def get_research_context_tool(query: str) -> str:
    """获取研究上下文工具 - 查询已有的研究结果"""
    try:
        # 这个工具需要在运行时动态绑定state数据
        # 在实际使用时会被替换为真实的查询函数
        return f"查询 '{query}' 的研究上下文：暂无数据，请使用其他工具获取信息"
    except Exception as e:
        return f"查询失败: {str(e)}"


# 导出所有工具
ALL_RESEARCH_TOOLS = [
    web_search_tool,
    industry_data_tool,
    trend_analysis_tool,
    get_research_context_tool
]
