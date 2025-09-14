"""
MCP 客户端管理器
负责管理与 MCP 服务的连接和通信
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

class MCPClientManager:
    """MCP 客户端管理器"""
    
    def __init__(self):
        self.client: Optional[MultiServerMCPClient] = None
        self._connection_status = {
            "bing_search": False,
            "chart_generator": False
        }
        
    async def initialize(self) -> bool:
        """
        初始化 MCP 客户端连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 配置 MCP 服务器连接
            server_connections = {
                "bing_search": {
                    "url": "https://mcp.api-inference.modelscope.net/211a13459d3c4f/sse",
                    "transport": "sse"
                },
                "chart_generator": {
                    "url": "https://mcp.api-inference.modelscope.net/8381bd2e2a8e4c/sse", 
                    "transport": "sse"
                }
            }
            
            # 创建多服务器客户端
            self.client = MultiServerMCPClient(server_connections)
            
            # 测试连接
            await self._test_connections()
            
            logger.info("MCP 客户端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"MCP 客户端初始化失败: {e}")
            self.client = None
            return False
    
    async def _test_connections(self):
        """测试 MCP 服务器连接"""
        if not self.client:
            return
            
        try:
            # 获取可用工具列表来测试连接
            tools = await self.client.get_tools()
            
            # 检查每个服务的工具
            bing_tools = [t for t in tools if 'search' in t.name.lower()]
            chart_tools = [t for t in tools if 'chart' in t.name.lower() or 'graph' in t.name.lower()]
            
            self._connection_status["bing_search"] = len(bing_tools) > 0
            self._connection_status["chart_generator"] = len(chart_tools) > 0
            
            logger.info(f"MCP 连接状态: {self._connection_status}")
            
        except Exception as e:
            logger.warning(f"MCP 连接测试失败: {e}")
            self._connection_status = {k: False for k in self._connection_status}
    
    async def call_bing_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        调用 Bing 搜索 MCP 服务
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.client or not self._connection_status["bing_search"]:
            raise Exception("Bing 搜索 MCP 服务不可用")
        
        try:
            # 获取搜索工具
            tools = await self.client.get_tools()
            search_tool = next((t for t in tools if 'search' in t.name.lower()), None)
            
            if not search_tool:
                raise Exception("未找到搜索工具")
            
            # 调用搜索工具
            result = await search_tool.ainvoke({
                "query": query,
                "max_results": max_results
            })
            
            # 格式化结果
            if isinstance(result, list):
                return result[:max_results]
            elif isinstance(result, dict):
                return [result]
            else:
                return [{"content": str(result), "query": query}]
                
        except Exception as e:
            logger.error(f"Bing 搜索调用失败: {e}")
            raise Exception(f"搜索服务调用失败: {e}")
    
    async def call_chart_generator(self, data: Dict[str, Any], chart_type: str = "bar") -> Dict[str, Any]:
        """
        调用图表生成 MCP 服务
        
        Args:
            data: 图表数据
            chart_type: 图表类型
            
        Returns:
            Dict: 图表数据和配置
        """
        if not self.client or not self._connection_status["chart_generator"]:
            raise Exception("图表生成 MCP 服务不可用")
        
        try:
            # 获取图表工具
            tools = await self.client.get_tools()
            chart_tool = next((t for t in tools if 'chart' in t.name.lower() or 'graph' in t.name.lower()), None)
            
            if not chart_tool:
                raise Exception("未找到图表工具")
            
            # 调用图表工具
            result = await chart_tool.ainvoke({
                "data": data,
                "chart_type": chart_type
            })
            
            return {
                "chart_data": result,
                "chart_type": chart_type,
                "status": "success"
            }
                
        except Exception as e:
            logger.error(f"图表生成调用失败: {e}")
            raise Exception(f"图表服务调用失败: {e}")
    
    def get_connection_status(self) -> Dict[str, bool]:
        """获取连接状态"""
        return self._connection_status.copy()
    
    async def close(self):
        """关闭 MCP 客户端连接"""
        if self.client:
            try:
                # 注意：MultiServerMCPClient 可能没有 close 方法
                # 这里只是重置状态
                self.client = None
                self._connection_status = {k: False for k in self._connection_status}
                logger.info("MCP 客户端已关闭")
            except Exception as e:
                logger.error(f"关闭 MCP 客户端失败: {e}")

# 全局客户端管理器实例
mcp_client_manager = MCPClientManager()

async def get_mcp_client() -> MCPClientManager:
    """获取 MCP 客户端管理器实例"""
    if mcp_client_manager.client is None:
        await mcp_client_manager.initialize()
    return mcp_client_manager