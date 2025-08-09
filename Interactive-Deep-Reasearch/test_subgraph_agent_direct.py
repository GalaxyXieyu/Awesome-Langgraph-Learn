#!/usr/bin/env python3
"""
直接测试subgraph中Agent的工具调用
专门验证AgentStreamCollector能否正确检测和显示工具调用
"""
import asyncio
import time
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'subgraph/update'))

from subgraph.update.graph import create_research_agents, IntelligentResearchState
from stream_writer import create_agent_stream_collector
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

async def test_agent_tool_calls():
    """直接测试Agent的工具调用检测"""
    print("🚀 开始直接测试subgraph中Agent的工具调用检测...")
    
    # 创建研究agents
    agents = create_research_agents()
    researcher = agents["researcher"]
    
    print(f"✅ 成功创建研究Agent，可用工具：{len(researcher.tools)}个")
    for tool in researcher.tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # 创建Agent流收集器
    collector = create_agent_stream_collector("test_research", "测试研究员")
    
    # 创建一个会触发工具调用的任务
    research_task = """
    请使用工具搜索"人工智能在医疗领域的最新发展"相关信息。
    
    要求：
    1. 使用web_search_tool搜索最新信息
    2. 使用trend_analysis_tool分析发展趋势
    3. 基于工具结果提供综合分析
    
    请确保调用工具来获取详细信息。
    """
    
    agent_input = {"messages": [HumanMessage(content=research_task)]}
    
    print(f"\n📋 研究任务: {research_task[:100]}...")
    print("\n开始执行Agent流式处理，监控工具调用...")
    
    try:
        # 使用AgentStreamCollector处理Agent流
        full_response = await collector.process_agent_stream(
            researcher.astream(agent_input, stream_mode=["updates", "messages"]),
            "测试研究员"
        )
        
        print(f"\n✅ Agent执行完成！")
        print(f"📊 执行统计:")
        print(f"  - 处理的chunk数: {collector.chunk_count}")
        print(f"  - 使用的工具数: {len(collector.tools_used)}")
        print(f"  - 工具列表: {collector.tools_used}")
        print(f"  - 响应长度: {len(full_response)}字符")
        
        if collector.tools_used:
            print(f"\n🎉 成功！检测到 {len(collector.tools_used)} 个工具调用:")
            for i, tool in enumerate(collector.tools_used, 1):
                print(f"  {i}. {tool}")
        else:
            print(f"\n❌ 失败！未检测到任何工具调用")
            print("可能的原因:")
            print("  - Agent没有调用工具")
            print("  - 工具调用检测逻辑有问题")
            print("  - 流式数据解析错误")
        
        print(f"\n📝 最终响应:")
        print(f"{'='*60}")
        print(full_response[:500] + ("..." if len(full_response) > 500 else ""))
        print(f"{'='*60}")
        
        return len(collector.tools_used) > 0
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_tool_call():
    """简单的工具调用测试"""
    print("\n" + "="*60)
    print("🔧 开始简单工具调用测试...")
    
    # 创建一个更简单的任务，确保会调用工具
    agents = create_research_agents()
    researcher = agents["researcher"]
    
    collector = create_agent_stream_collector("simple_test", "简单测试")
    
    simple_task = "请使用web_search_tool搜索'AI医疗应用'，只搜索一次就够了。"
    agent_input = {"messages": [HumanMessage(content=simple_task)]}
    
    print(f"简单任务: {simple_task}")
    
    try:
        result = await collector.process_agent_stream(
            researcher.astream(agent_input, stream_mode=["updates", "messages"]),
            "简单测试员"
        )
        
        print(f"工具调用数: {len(collector.tools_used)}")
        print(f"工具列表: {collector.tools_used}")
        
        return len(collector.tools_used) > 0
        
    except Exception as e:
        print(f"简单测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 Agent工具调用检测测试")
    print("="*60)
    
    async def run_tests():
        # 测试1：完整的研究任务
        success1 = await test_agent_tool_calls()
        
        # 测试2：简单工具调用
        success2 = await test_simple_tool_call()
        
        print(f"\n📊 测试结果总结:")
        print(f"  - 完整研究任务: {'✅ 成功' if success1 else '❌ 失败'}")
        print(f"  - 简单工具调用: {'✅ 成功' if success2 else '❌ 失败'}")
        
        if success1 or success2:
            print(f"\n🎉 测试成功！AgentStreamCollector能够检测工具调用")
        else:
            print(f"\n⚠️  测试失败！需要进一步调试工具调用检测逻辑")
    
    asyncio.run(run_tests())

if __name__ == "__main__":
    main()