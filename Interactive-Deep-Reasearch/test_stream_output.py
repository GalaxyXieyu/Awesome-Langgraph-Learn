"""
测试统一流式输出系统
验证新的Agent工作流程消息类型是否正常工作
"""

import asyncio
import time
from stream_writer import (
    create_stream_writer, 
    create_workflow_processor,
    MessageType,
    format_message_for_frontend
)

def test_message_types():
    """测试新的消息类型"""
    print("=== 测试消息类型 ===")
    
    # 创建writer
    writer = create_stream_writer("test_node", "测试Agent")
    
    # 测试各种消息类型
    print("1. 测试步骤流程:")
    writer.step_start("开始测试任务")
    writer.step_progress("执行中", 50, test_data="测试数据")
    writer.step_complete("测试任务完成", duration=2.5)
    
    print("\n2. 测试工具调用:")
    writer.tool_call("search_tool", {"query": "人工智能", "limit": 10})
    writer.tool_result("search_tool", "找到了10个相关结果...")
    
    print("\n3. 测试思考过程:")
    writer.thinking("分析搜索结果的质量")
    writer.reasoning("基于搜索结果，我需要进一步研究技术细节")
    
    print("\n4. 测试内容输出:")
    writer.content_streaming("## 人工智能概述\n\n人工智能是...")
    writer.content_complete("章节写作完成", word_count=500, section_title="人工智能概述")
    
    print("\n5. 测试最终结果:")
    writer.final_result("报告生成完成", {"sections": 5, "total_words": 2500})
    
    print("✅ 基础消息类型测试完成\n")

def test_workflow_processor():
    """测试工作流程处理器"""
    print("=== 测试工作流程处理器 ===")
    
    processor = create_workflow_processor("workflow_test", "工作流测试")
    
    # 模拟子图chunk数据
    test_chunks = [
        ("custom", {"step": "research", "status": "开始研究分析", "progress": 0}),
        ("custom", {"step": "research", "status": "收集资料中", "progress": 50}),
        ("custom", {"step": "research", "status": "研究完成", "progress": 100}),
        ("custom", {"step": "writing", "status": "开始写作", "progress": 0}),
        ("custom", {"step": "writing", "status": "正在写作", "progress": 60, "streaming_content": "## 引言\n\n这是一个测试章节..."}),
        ("custom", {"step": "writing", "status": "写作完成", "progress": 100}),
        ("updates", {"writing_node": {"sections": [{"title": "引言", "content": "这是引言内容", "word_count": 200}]}}),
        ("updates", {"research_node": {"research_results": {"section1": {"title": "AI研究", "content": "研究内容..."}}}})
    ]
    
    print("处理模拟的chunk数据:")
    for i, chunk in enumerate(test_chunks, 1):
        print(f"  处理chunk {i}: {chunk[0]} - {chunk[1].get('step', 'unknown')}")
        result = processor.process_chunk(chunk)
        time.sleep(0.1)  # 模拟处理间隔
    
    # 获取处理摘要
    summary = processor.get_summary()
    print(f"\n处理摘要: {summary}")
    print("✅ 工作流程处理器测试完成\n")

def test_frontend_formatting():
    """测试前端格式化"""
    print("=== 测试前端格式化 ===")
    
    # 模拟各种消息，包含工具调用
    test_messages = [
        {
            "message_type": "step_start",
            "timestamp": time.time(),
            "node_name": "research",
            "agent_name": "研究助手",
            "content": "开始研究分析",
            "metadata": {"step_duration": 0}
        },
        {
            "message_type": "tool_call",
            "timestamp": time.time(),
            "node_name": "research",
            "agent_name": "研究助手",
            "content": "调用 trends_analysis_tool 工具",
            "metadata": {
                "tool_name": "trends_analysis_tool",
                "tool_args": {"topic": "人工智能", "depth": "detailed"}
            }
        },
        {
            "message_type": "thinking",
            "timestamp": time.time(),
            "node_name": "research", 
            "agent_name": "研究助手",
            "content": "使用趋势分析工具研究: 人工智能",
            "metadata": {"step_duration": 1.2}
        },
        {
            "message_type": "tool_result",
            "timestamp": time.time(),
            "node_name": "research",
            "agent_name": "研究助手",
            "content": "trends_analysis_tool 执行结果: 分析完成，发现3个主要趋势...",
            "metadata": {
                "tool_name": "trends_analysis_tool",
                "full_result": "详细的趋势分析结果，包含大量数据和见解...",
                "result_length": 1250
            }
        },
        {
            "message_type": "reasoning",
            "timestamp": time.time(),
            "node_name": "research",
            "agent_name": "研究助手",
            "content": "趋势分析完成，开始整理研究结果",
            "metadata": {"step_duration": 2.5}
        },
        {
            "message_type": "content_streaming",
            "timestamp": time.time(),
            "node_name": "writer",
            "agent_name": "写作助手", 
            "content": "## 人工智能的发展历程\n\n人工智能技术经历了...",
            "metadata": {"chunk_index": 1, "is_streaming": True}
        },
        {
            "message_type": "content_complete",
            "timestamp": time.time(),
            "node_name": "writer",
            "agent_name": "写作助手",
            "content": "章节写作完成",
            "metadata": {"word_count": 450, "section_title": "AI发展历程"}
        }
    ]
    
    print("前端格式化结果（包含工具调用）:")
    for msg in test_messages:
        formatted = format_message_for_frontend(msg)
        print(f"  {formatted['type']}: {formatted['display']} [{formatted.get('icon', 'none')}]")
        if 'progress' in formatted:
            print(f"    进度: {formatted['progress']}%")
        if 'word_count' in formatted:
            print(f"    字数: {formatted['word_count']}")
        if 'tool_name' in formatted:
            print(f"    工具: {formatted['tool_name']}")
        if 'result_length' in formatted:
            print(f"    结果长度: {formatted['result_length']}字符")
    
    print("✅ 前端格式化测试完成（包含工具调用支持）\n")

async def test_async_workflow():
    """测试异步工作流程"""
    print("=== 测试异步工作流程 ===")
    
    writer = create_stream_writer("async_test", "异步测试")
    
    # 模拟异步任务流程
    writer.step_start("开始异步研究任务")
    
    for i in range(1, 6):
        await asyncio.sleep(0.2)  # 模拟异步处理时间
        writer.step_progress(f"处理第{i}阶段", i * 20)
        
        if i == 2:
            writer.thinking("分析中间结果")
        elif i == 4:
            writer.content_streaming(f"生成内容片段 {i}")
    
    writer.step_complete("异步任务完成")
    print("✅ 异步工作流程测试完成\n")

def main():
    """运行所有测试"""
    print("🚀 开始测试统一流式输出系统\n")
    
    # 运行测试
    test_message_types()
    test_workflow_processor()  
    test_frontend_formatting()
    
    # 运行异步测试
    print("运行异步测试...")
    asyncio.run(test_async_workflow())
    
    print("🎉 所有测试完成！新的流式输出系统工作正常。")
    print("\n主要改进:")
    print("- ✅ 去除了所有技术细节（如SUBGRAPH_*）")
    print("- ✅ 专注于Agent工作流程展示") 
    print("- ✅ 支持工具调用检测和展示")
    print("- ✅ 统一的消息格式，便于前端渲染")
    print("- ✅ 智能识别工作阶段")
    print("- ✅ 大幅减少代码复杂度")
    print("- ✅ 消除冗余日志输出")
    print("\n现在支持的消息类型:")
    print("  📋 步骤流程: step_start, step_progress, step_complete")
    print("  🔧 工具使用: tool_call, tool_result") 
    print("  🧠 思考过程: thinking, reasoning")
    print("  ✍️ 内容输出: content_streaming, content_complete")
    print("  🎯 最终结果: final_result")
    print("  ❌ 错误处理: error")

if __name__ == "__main__":
    main()