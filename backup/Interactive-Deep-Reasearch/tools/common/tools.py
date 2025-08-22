"""
核心工具模块
为深度研究报告生成系统提供基础工具
"""

import os
import uuid
import time
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 搜索工具
# ============================================================================

@tool
def advanced_web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    高级网络搜索工具
    使用Tavily进行深度网络搜索
    
    Args:
        query: 搜索查询词
        max_results: 最大返回结果数
    
    Returns:
        格式化的搜索结果列表
    """
    try:
        search_tool = TavilySearchResults(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
            include_images=False
        )
        
        results = search_tool.invoke({"query": query})
        
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": str(uuid.uuid4()),
                "query": query,
                "source_type": "web",
                "title": result.get("title", ""),
                "content": result.get("content", "")[:500],  # 限制内容长度
                "url": result.get("url", ""),
                "relevance_score": result.get("score", 0.8),
                "timestamp": time.time()
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"网络搜索完成: {query}, 获得 {len(formatted_results)} 个结果")
        return formatted_results
        
    except Exception as e:
        logger.error(f"网络搜索失败: {str(e)}")
        return [{
            "id": str(uuid.uuid4()),
            "error": f"搜索失败: {str(e)}",
            "query": query,
            "timestamp": time.time()
        }]

# ============================================================================
# 分析工具
# ============================================================================

@tool
def content_analyzer(text: str) -> Dict[str, Any]:
    """
    内容分析工具
    对文本进行基础分析
    
    Args:
        text: 待分析文本
        
    Returns:
        分析结果字典
    """
    try:
        if not text or len(text.strip()) < 10:
            return {"error": "文本内容过短，无法进行有效分析"}
        
        # 基础统计
        word_count = len(text.replace(" ", ""))
        sentence_count = len([s for s in text.split("。") if s.strip()])
        
        # 简单的关键词提取
        stop_words = {"的", "是", "在", "有", "和", "与", "或", "但", "而", "了", "着", "过"}
        words = [w for w in text if w not in stop_words and len(w) > 1]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        analysis_result = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "basic_stats": {
                "word_count": word_count,
                "sentence_count": sentence_count,
            },
            "keywords": [{"word": word, "frequency": freq} for word, freq in top_keywords],
        }
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"内容分析失败: {str(e)}")
        return {"error": f"内容分析失败: {str(e)}"}

# ============================================================================
# 工具集合函数
# ============================================================================

def get_all_tools():
    """获取所有工具"""
    return [
        advanced_web_search,
        content_analyzer,
    ]

def validate_tool_environment() -> Dict[str, Any]:
    """验证工具环境配置"""
    config_status = {
        "tavily_api_available": bool(os.getenv("TAVILY_API_KEY")),
        "openai_api_available": bool(os.getenv("OPENAI_API_KEY")),
        "tools_loaded": len(get_all_tools()),
        "timestamp": time.time()
    }
    
    logger.info(f"工具环境验证完成: {config_status}")
    return config_status