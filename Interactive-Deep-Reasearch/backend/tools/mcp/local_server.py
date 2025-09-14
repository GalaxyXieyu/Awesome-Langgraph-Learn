#!/usr/bin/env python3
"""
简单的本地 MCP 服务器演示
提供搜索和图表生成功能
"""

import json
import asyncio
import logging
from typing import Any, Dict, List
import uuid
import time

# 模拟搜索数据
MOCK_SEARCH_DATA = [
    {
        "title": "2024年人工智能发展趋势报告",
        "content": "人工智能技术在2024年呈现快速发展态势，大语言模型、计算机视觉、自动驾驶等领域都有重大突破。预计到2025年，AI市场规模将达到5000亿美元。",
        "url": "https://ai-research.com/trends-2024",
        "source": "AI Research Institute",
        "relevance": 0.95
    },
    {
        "title": "机器学习在医疗健康领域的应用前景",
        "content": "机器学习技术正在革命性地改变医疗健康行业，从疾病诊断到药物研发，都展现出巨大潜力。AI辅助诊断的准确率已经超过90%。",
        "url": "https://healthcare-ai.org/applications",
        "source": "Healthcare AI Organization", 
        "relevance": 0.88
    },
    {
        "title": "深度学习算法优化与性能提升",
        "content": "新一代深度学习算法在模型压缩、推理加速、能耗优化等方面取得显著进展。Transformer架构的改进使得模型效率提升了30%。",
        "url": "https://deeplearning-research.net/optimization",
        "source": "Deep Learning Research Network",
        "relevance": 0.82
    },
    {
        "title": "AI伦理与可信人工智能发展",
        "content": "随着AI技术广泛应用，AI伦理和可信度成为关键议题。各国正在制定相关法规，确保AI技术的安全可控发展。",
        "url": "https://ai-ethics.gov/trustworthy-ai",
        "source": "AI Ethics Committee",
        "relevance": 0.79
    },
    {
        "title": "边缘计算与AI芯片创新突破",
        "content": "边缘AI芯片技术快速发展，功耗降低50%，计算性能提升3倍。这将推动IoT设备智能化和实时AI应用的普及。",
        "url": "https://edge-ai.tech/chip-innovation",
        "source": "Edge AI Technology",
        "relevance": 0.76
    }
]

class LocalMCPServer:
    """本地 MCP 服务器模拟"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def search_bing(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """模拟 Bing 搜索"""
        await asyncio.sleep(0.5)  # 模拟网络延迟
        
        # 基于查询过滤数据
        query_lower = query.lower()
        filtered_results = []
        
        for item in MOCK_SEARCH_DATA:
            if any(word in item["title"].lower() or word in item["content"].lower() 
                   for word in query_lower.split()):
                result = {
                    "id": str(uuid.uuid4()),
                    "query": query,
                    "title": item["title"],
                    "content": item["content"][:800],
                    "url": item["url"],
                    "relevance_score": item["relevance"],
                    "timestamp": time.time(),
                    "source": "local_mcp",
                    "source_type": "web_search"
                }
                filtered_results.append(result)
                
        # 按相关性排序并限制结果数量
        filtered_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return filtered_results[:max_results]
    
    async def create_chart(self, data: Dict[str, Any], chart_type: str, 
                          title: str = "", x_label: str = "", y_label: str = "") -> Dict[str, Any]:
        """模拟图表生成"""
        await asyncio.sleep(0.3)  # 模拟处理时间
        
        chart_result = {
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
            "source": "local_mcp",
            "status": "success"
        }
        
        return chart_result

# 全局实例
_local_server = LocalMCPServer()

async def get_local_mcp_server():
    """获取本地 MCP 服务器实例"""
    return _local_server

if __name__ == "__main__":
    # 测试本地服务器
    async def test():
        server = await get_local_mcp_server()
        
        print("🔍 测试搜索功能...")
        results = await server.search_bing("人工智能", 3)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   相关性: {result['relevance_score']}")
        
        print("\n📊 测试图表功能...")
        chart_data = {"labels": ["2021", "2022", "2023"], "values": [100, 150, 200]}
        chart = await server.create_chart(chart_data, "bar", "测试图表", "年份", "数值")
        print(f"图表: {chart['title']} ({chart['chart_type']})")
        
    asyncio.run(test())