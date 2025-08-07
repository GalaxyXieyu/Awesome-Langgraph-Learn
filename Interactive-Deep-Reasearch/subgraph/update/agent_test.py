"""
Agent测试脚本 - 验证agent是否能正常工作
"""

import asyncio
from langchain_core.messages import HumanMessage
from graph import create_research_agents, create_llm
from tools import ALL_RESEARCH_TOOLS
from langgraph.prebuilt import create_react_agent

async def test_agent_basic():
    """基础Agent测试"""
    print("=" * 50)
    print("开始Agent基础测试")
    print("=" * 50)
    
    # 创建LLM
    llm = create_llm()
    
    # 创建简单的研究agent（使用字符串prompt）
    simple_agent = create_react_agent(
        llm,
        tools=ALL_RESEARCH_TOOLS,
        prompt="""你是一个研究员。请使用工具研究用户的问题。"""
    )
    
    # 测试输入
    test_input = {"messages": [HumanMessage(content="研究一下人工智能的发展现状")]}
    
    print(f"测试输入: {test_input}")
    print("\n开始Agent执行...")
    
    try:
        # 流式执行
        full_response = ""
        chunk_count = 0
        
        async for chunk in simple_agent.astream(test_input, stream_mode="messages"):
            chunk_count += 1
            print(f"Chunk {chunk_count}: 类型={type(chunk)}")
            
            if isinstance(chunk, tuple) and len(chunk) == 2:
                message, metadata = chunk
                msg_type = type(message).__name__
                print(f"  Message类型: {msg_type}")
                
                if hasattr(message, 'content'):
                    content = str(message.content)
                    if content.strip():
                        print(f"  内容: {content[:100]}...")
                        full_response += content
                        
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print(f"  工具调用: {message.tool_calls}")
        
        print(f"\n最终响应长度: {len(full_response)}")
        print(f"最终响应预览: {full_response[:200]}...")
        
        return full_response
        
    except Exception as e:
        print(f"Agent执行失败: {e}")
        return ""

async def test_current_agents():
    """测试当前的research agents"""
    print("=" * 50)
    print("测试当前的研究agents")
    print("=" * 50)
    
    # 创建当前的agents
    agents = create_research_agents()
    researcher = agents["researcher"]
    
    test_input = {"messages": [HumanMessage(content="研究人工智能技术发展现状")]}
    
    print("测试研究员Agent...")
    
    try:
        full_response = ""
        chunk_count = 0
        
        async for chunk in researcher.astream(test_input, stream_mode="messages"):
            chunk_count += 1
            print(f"研究员Chunk {chunk_count}: {type(chunk)}")
            
            if isinstance(chunk, tuple) and len(chunk) == 2:
                message, _ = chunk
                msg_type = type(message).__name__
                
                if hasattr(message, 'content') and message.content:
                    content = str(message.content)
                    full_response += content
                    print(f"  添加内容: {content[:50]}...")
        
        print(f"\n研究员最终响应长度: {len(full_response)}")
        print(f"研究员最终响应: {full_response[:200]}...")
        
        return full_response
        
    except Exception as e:
        print(f"研究员Agent测试失败: {e}")
        return ""

async def main():
    """主测试函数"""
    print("开始Agent测试...\n")
    
    # 测试1: 基础Agent
    basic_result = await test_agent_basic()
    
    print("\n" + "="*50 + "\n")
    
    # 测试2: 当前Agents
    current_result = await test_current_agents()
    
    print("\n" + "="*50)
    print("测试总结:")
    print(f"基础Agent响应长度: {len(basic_result)}")
    print(f"当前Agent响应长度: {len(current_result)}")
    
    if len(basic_result) > 0:
        print("✅ 基础Agent工作正常")
    else:
        print("❌ 基础Agent无响应")
    
    if len(current_result) > 0:
        print("✅ 当前Agent工作正常")
    else:
        print("❌ 当前Agent无响应")

if __name__ == "__main__":
    asyncio.run(main())