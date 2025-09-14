"""
MCP 集成测试脚本
用于测试 Bing 搜索和图表生成 MCP 工具的集成
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.mcp.client import get_mcp_client
from tools.mcp.tools import bing_search_mcp, create_chart_mcp
from tools import get_mcp_tools

async def test_mcp_client():
    """测试 MCP 客户端基础功能"""
    print("🔧 测试 MCP 客户端初始化...")
    
    try:
        client_manager = await get_mcp_client()
        status = client_manager.get_connection_status()
        
        print(f"✅ MCP 客户端状态: {status}")
        
        if status["bing_search"]:
            print("🔍 Bing 搜索服务已连接")
        else:
            print("❌ Bing 搜索服务未连接")
            
        if status["chart_generator"]:
            print("📊 图表生成服务已连接")
        else:
            print("❌ 图表生成服务未连接")
            
        return client_manager
        
    except Exception as e:
        print(f"❌ MCP 客户端测试失败: {e}")
        return None

async def test_bing_search():
    """测试 Bing 搜索工具"""
    print("\n🔍 测试 Bing 搜索工具...")
    
    try:
        # 直接测试工具
        results = await bing_search_mcp.ainvoke({
            "query": "人工智能发展趋势",
            "max_results": 3
        })
        
        print(f"✅ 搜索成功，返回 {len(results)} 个结果:")
        for i, result in enumerate(results[:2], 1):
            print(f"  {i}. {result.get('title', 'N/A')}")
            print(f"     来源: {result.get('source', 'N/A')}")
            print(f"     相关性: {result.get('relevance_score', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Bing 搜索测试失败: {e}")
        return False

async def test_chart_generation():
    """测试图表生成工具"""
    print("\n📊 测试图表生成工具...")
    
    try:
        # 模拟图表数据
        test_data = {
            "labels": ["2020", "2021", "2022", "2023", "2024"],
            "values": [100, 150, 200, 300, 450]
        }
        
        result = await create_chart_mcp.ainvoke({
            "data": test_data,
            "chart_type": "bar",
            "title": "AI 市场增长趋势",
            "x_label": "年份",
            "y_label": "市场规模(亿美元)"
        })
        
        print(f"✅ 图表生成成功:")
        print(f"  类型: {result.get('chart_type', 'N/A')}")
        print(f"  标题: {result.get('title', 'N/A')}")
        print(f"  来源: {result.get('source', 'N/A')}")
        print(f"  状态: {result.get('status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 图表生成测试失败: {e}")
        return False

async def test_interactive_mode():
    """测试交互模式下的工具包装"""
    print("\n🤝 测试交互模式工具包装...")
    
    try:
        # 获取交互模式的 MCP 工具
        interactive_tools = await get_mcp_tools("interactive")
        
        print(f"✅ 获取到 {len(interactive_tools)} 个交互模式工具:")
        for tool in interactive_tools:
            print(f"  - {tool.name}: {tool.description}")
            
        return True
        
    except Exception as e:
        print(f"❌ 交互模式测试失败: {e}")
        return False

async def test_copilot_mode():
    """测试副驾驶模式下的工具包装"""
    print("\n⚡ 测试副驾驶模式工具包装...")
    
    try:
        # 获取副驾驶模式的 MCP 工具
        copilot_tools = await get_mcp_tools("copilot")
        
        print(f"✅ 获取到 {len(copilot_tools)} 个副驾驶模式工具:")
        for tool in copilot_tools:
            print(f"  - {tool.name}: {tool.description}")
            
        return True
        
    except Exception as e:
        print(f"❌ 副驾驶模式测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始 MCP 集成测试...\n")
    
    # 统计测试结果
    test_results = []
    
    # 1. 测试 MCP 客户端
    client_manager = await test_mcp_client()
    test_results.append(client_manager is not None)
    
    # 2. 测试搜索工具
    search_result = await test_bing_search()
    test_results.append(search_result)
    
    # 3. 测试图表生成
    chart_result = await test_chart_generation()
    test_results.append(chart_result)
    
    # 4. 测试交互模式
    interactive_result = await test_interactive_mode()
    test_results.append(interactive_result)
    
    # 5. 测试副驾驶模式  
    copilot_result = await test_copilot_mode()
    test_results.append(copilot_result)
    
    # 关闭客户端
    if client_manager:
        await client_manager.close()
    
    # 总结测试结果
    print(f"\n📊 测试总结:")
    print(f"✅ 通过: {sum(test_results)}/{len(test_results)} 项测试")
    
    if all(test_results):
        print("🎉 所有 MCP 集成测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())