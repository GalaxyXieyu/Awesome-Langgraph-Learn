"""
MCP 工具定义
提供 Bing 搜索和图表生成的 MCP 工具适配器
支持与现有工具包装器的完美集成
"""

import uuid
import time
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

from .client import get_mcp_client

logger = logging.getLogger(__name__)

@tool
async def bing_search_mcp(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Bing搜索工具 - 基于MCP服务
    
    使用 MCP 服务进行真实的联网搜索，替代模拟搜索数据
    支持交互式确认和参数编辑
    
    Args:
        query: 搜索查询词
        max_results: 最大结果数量，默认10个
        
    Returns:
        List[Dict]: 搜索结果列表，包含标题、内容、URL等信息
    """
    try:
        # 获取 MCP 客户端
        client_manager = await get_mcp_client()
        
        if not client_manager.client:
            logger.warning("MCP 客户端不可用，回退到原始搜索工具")
            return await _fallback_search(query, max_results)
        
        # 调用 MCP 搜索服务
        raw_results = await client_manager.call_bing_search(query, max_results)
        
        # 格式化搜索结果，确保与现有格式兼容
        formatted_results = []
        for i, result in enumerate(raw_results[:max_results]):
            formatted_result = {
                "id": str(uuid.uuid4()),
                "query": query,
                "title": result.get("title", f"搜索结果 {i+1}"),
                "content": result.get("content", result.get("snippet", ""))[:800],
                "url": result.get("url", result.get("link", "")),
                "relevance_score": result.get("score", result.get("relevance", 0.8)),
                "timestamp": time.time(),
                "source": "bing_mcp",
                "source_type": "web_search"
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"Bing MCP 搜索成功: {query}, 返回 {len(formatted_results)} 个结果")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Bing MCP 搜索失败: {e}")
        # 回退到原始搜索工具
        return await _fallback_search(query, max_results)

@tool  
async def create_chart_mcp(
    data: Dict[str, Any], 
    chart_type: str = "bar",
    title: str = "",
    x_label: str = "",
    y_label: str = ""
) -> Dict[str, Any]:
    """
    图表生成工具 - 基于MCP服务
    
    使用 MCP 服务生成各种类型的数据图表
    支持交互式确认和参数编辑
    
    Args:
        data: 图表数据，格式为 {"labels": [...], "values": [...]} 或其他格式
        chart_type: 图表类型，支持 "bar", "line", "pie", "scatter" 等
        title: 图表标题
        x_label: X轴标签
        y_label: Y轴标签
        
    Returns:
        Dict: 图表数据和配置信息
    """
    try:
        # 获取 MCP 客户端
        client_manager = await get_mcp_client()
        
        if not client_manager.client:
            logger.warning("MCP 客户端不可用，回退到模拟图表生成")
            return _fallback_chart(data, chart_type, title, x_label, y_label)
        
        # 调用 MCP 图表服务
        chart_config = {
            "data": data,
            "type": chart_type,
            "options": {
                "title": title,
                "x_label": x_label,
                "y_label": y_label
            }
        }
        
        chart_result = await client_manager.call_chart_generator(chart_config, chart_type)
        
        # 格式化图表结果
        formatted_result = {
            "id": str(uuid.uuid4()),
            "chart_type": chart_type,
            "title": title or f"{chart_type.upper()} 图表",
            "chart_data": chart_result.get("chart_data", data),
            "chart_config": {
                "type": chart_type,
                "title": title,
                "x_label": x_label,
                "y_label": y_label,
                "responsive": True,
                "animation": {
                    "duration": 1200,
                    "easing": "easeOutQuart"
                }
            },
            "timestamp": time.time(),
            "source": "chart_mcp",
            "status": "success"
        }
        
        logger.info(f"MCP 图表生成成功: {chart_type}, 标题: {title}")
        return formatted_result
        
    except Exception as e:
        logger.error(f"MCP 图表生成失败: {e}")
        # 回退到模拟图表生成
        return _fallback_chart(data, chart_type, title, x_label, y_label)

async def _fallback_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    """搜索回退函数，当 MCP 服务不可用时使用"""
    logger.info(f"使用本地 MCP 服务进行搜索: {query}")
    
    try:
        # 尝试使用本地 MCP 服务器
        from .local_server import get_local_mcp_server
        server = await get_local_mcp_server()
        return await server.search_bing(query, max_results)
    except Exception as e:
        logger.error(f"本地 MCP 服务也失败: {e}")
        
        # 最终回退到模拟数据
        return [
            {
                "id": str(uuid.uuid4()),
                "query": query,
                "title": f"关于{query}的搜索结果 #{i+1}",
                "content": f"这是关于{query}的详细信息。由于搜索服务暂时不可用，这里显示的是模拟数据。当服务恢复后，将提供真实的搜索结果。",
                "url": f"https://example.com/search?q={query}&result={i+1}",
                "relevance_score": 0.8 - i * 0.1,
                "timestamp": time.time(),
                "source": "fallback",
                "source_type": "web_search",
                "error": "搜索服务不可用"
            }
            for i in range(min(max_results, 3))
        ]

async def _fallback_chart_async(data: Dict[str, Any], chart_type: str, title: str, x_label: str, y_label: str) -> Dict[str, Any]:
    """异步图表回退函数"""
    logger.info(f"使用本地 MCP 服务生成图表: {chart_type}")
    
    try:
        # 尝试使用本地 MCP 服务器
        from .local_server import get_local_mcp_server
        server = await get_local_mcp_server()
        return await server.create_chart(data, chart_type, title, x_label, y_label)
    except Exception as e:
        logger.error(f"本地 MCP 图表服务失败: {e}")
        return _fallback_chart_sync(data, chart_type, title, x_label, y_label)

def _fallback_chart_sync(data: Dict[str, Any], chart_type: str, title: str, x_label: str, y_label: str) -> Dict[str, Any]:
    """同步图表回退函数"""
    return {
        "id": str(uuid.uuid4()),
        "chart_type": chart_type,
        "title": title or f"{chart_type.upper()} 图表",
        "chart_data": data,
        "chart_config": {
            "type": chart_type,
            "title": title,
            "x_label": x_label,
            "y_label": y_label,
            "responsive": True,
            "animation": {
                "duration": 1200,
                "easing": "easeOutQuart"
            }
        },
        "timestamp": time.time(),
        "source": "fallback",
        "status": "fallback",
        "message": "图表服务暂时不可用，显示模拟数据"
    }

def _fallback_chart(data: Dict[str, Any], chart_type: str, title: str, x_label: str, y_label: str) -> Dict[str, Any]:
    """图表回退函数，当 MCP 服务不可用时使用"""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果在异步环境中，使用同步回退
            return _fallback_chart_sync(data, chart_type, title, x_label, y_label)
        else:
            return asyncio.run(_fallback_chart_async(data, chart_type, title, x_label, y_label))
    except Exception as e:
        logger.error(f"异步图表回退失败: {e}")
        return _fallback_chart_sync(data, chart_type, title, x_label, y_label)

# 导出 MCP 工具列表
MCP_TOOLS = [
    bing_search_mcp,
    create_chart_mcp
]