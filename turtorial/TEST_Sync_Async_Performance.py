#!/usr/bin/env python3
"""
TEST_Sync_Async_Performance.py - LangGraph同步异步性能对比测试
测试不同组合方式的兼容性、性能和流式效果
重要发现: LLM调用方式决定流式效果，Graph流式模式只是传输管道
"""

import time
import asyncio
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


class PerformanceTestState(TypedDict):
    """性能测试状态定义"""
    input_text: str
    result: str
    current_step: str
    performance_data: Dict[str, Any]


def create_mock_llm_response(text: str, delay: float = 1.0) -> str:
    """模拟LLM响应"""
    time.sleep(delay)
    return f"处理结果: {text} (耗时 {delay}s)"


async def create_mock_llm_response_async(text: str, delay: float = 1.0) -> str:
    """模拟异步LLM响应"""
    await asyncio.sleep(delay)
    return f"异步处理结果: {text} (耗时 {delay}s)"


def mock_llm_stream(text: str, chunk_count: int = 5):
    """模拟LLM流式响应"""
    words = text.split()
    chunk_size = max(1, len(words) // chunk_count)
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        time.sleep(0.3)  # 模拟生成延迟
        yield chunk_text


async def mock_llm_astream(text: str, chunk_count: int = 5):
    """模拟异步LLM流式响应"""
    words = text.split()
    chunk_size = max(1, len(words) // chunk_count)
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        await asyncio.sleep(0.3)  # 模拟生成延迟
        yield chunk_text


# 场景1: def + invoke + stream (假流式)
def sync_node_with_invoke(state: PerformanceTestState) -> PerformanceTestState:
    """同步节点 + 模拟invoke调用"""
    start_time = time.time()
    
    # 模拟invoke调用
    response = create_mock_llm_response(state["input_text"], 1.0)
    
    end_time = time.time()
    
    state["result"] = response
    state["current_step"] = "sync_invoke_completed"
    state["performance_data"] = {
        "method": "sync_invoke",
        "response_time": end_time - start_time,
        "streaming": False,
        "user_experience": "差 - 需要等待完成"
    }
    
    return state


# 场景2: def + stream + stream (真流式)
def sync_node_with_stream(state: PerformanceTestState) -> PerformanceTestState:
    """同步节点 + 模拟stream调用"""
    start_time = time.time()
    first_chunk_time = None
    full_response = ""
    
    # 模拟stream调用
    for chunk in mock_llm_stream(state["input_text"]):
        if first_chunk_time is None:
            first_chunk_time = time.time()
        full_response += chunk + " "
    
    end_time = time.time()
    
    state["result"] = full_response.strip()
    state["current_step"] = "sync_stream_completed"
    state["performance_data"] = {
        "method": "sync_stream",
        "total_time": end_time - start_time,
        "first_chunk_time": first_chunk_time - start_time if first_chunk_time else 0,
        "streaming": True,
        "user_experience": "好 - 实时看到输出"
    }
    
    return state


# 场景3: async def + ainvoke + astream (异步非流式)
async def async_node_with_ainvoke(state: PerformanceTestState, config=None) -> PerformanceTestState:
    """异步节点 + 模拟ainvoke调用"""
    start_time = time.time()
    
    # 模拟ainvoke调用
    response = await create_mock_llm_response_async(state["input_text"], 1.0)
    
    end_time = time.time()
    
    state["result"] = response
    state["current_step"] = "async_invoke_completed"
    state["performance_data"] = {
        "method": "async_invoke",
        "response_time": end_time - start_time,
        "streaming": False,
        "user_experience": "好 - 异步性能优秀"
    }
    
    return state


# 场景4: async def + astream + astream (异步流式 - 最佳)
async def async_node_with_astream(state: PerformanceTestState, config=None) -> PerformanceTestState:
    """异步节点 + 模拟astream调用"""
    start_time = time.time()
    first_chunk_time = None
    full_response = ""
    
    # 模拟astream调用
    async for chunk in mock_llm_astream(state["input_text"]):
        if first_chunk_time is None:
            first_chunk_time = time.time()
        full_response += chunk + " "
    
    end_time = time.time()
    
    state["result"] = full_response.strip()
    state["current_step"] = "async_stream_completed"
    state["performance_data"] = {
        "method": "async_stream",
        "total_time": end_time - start_time,
        "first_chunk_time": first_chunk_time - start_time if first_chunk_time else 0,
        "streaming": True,
        "user_experience": "🏆 最佳 - 异步+流式"
    }
    
    return state


def create_test_graphs():
    """创建测试图"""
    graphs = {}
    
    # 场景1: 同步invoke
    workflow1 = StateGraph(PerformanceTestState)
    workflow1.add_node("process", sync_node_with_invoke)
    workflow1.set_entry_point("process")
    workflow1.add_edge("process", END)
    graphs["sync_invoke"] = workflow1.compile(checkpointer=MemorySaver())
    
    # 场景2: 同步stream
    workflow2 = StateGraph(PerformanceTestState)
    workflow2.add_node("process", sync_node_with_stream)
    workflow2.set_entry_point("process")
    workflow2.add_edge("process", END)
    graphs["sync_stream"] = workflow2.compile(checkpointer=MemorySaver())
    
    # 场景3: 异步invoke
    workflow3 = StateGraph(PerformanceTestState)
    workflow3.add_node("process", async_node_with_ainvoke)
    workflow3.set_entry_point("process")
    workflow3.add_edge("process", END)
    graphs["async_invoke"] = workflow3.compile(checkpointer=MemorySaver())
    
    # 场景4: 异步stream
    workflow4 = StateGraph(PerformanceTestState)
    workflow4.add_node("process", async_node_with_astream)
    workflow4.set_entry_point("process")
    workflow4.add_edge("process", END)
    graphs["async_stream"] = workflow4.compile(checkpointer=MemorySaver())
    
    return graphs


def test_sync_scenarios():
    """测试同步场景"""
    print("⚡ 同步场景性能测试")
    print("-" * 40)
    
    graphs = create_test_graphs()
    initial_state = PerformanceTestState(
        input_text="这是测试文本用于验证同步异步调用效果",
        result="",
        current_step="initialized",
        performance_data={}
    )
    
    # 测试场景1: sync invoke
    print("📍 场景1: def + invoke + stream (假流式)")
    result1 = graphs["sync_invoke"].invoke(initial_state, {"configurable": {"thread_id": "test1"}})
    perf1 = result1["performance_data"]
    print(f"   方法: {perf1['method']}")
    print(f"   响应时间: {perf1['response_time']:.2f}s")
    print(f"   流式效果: {'✅' if perf1['streaming'] else '❌'}")
    print(f"   用户体验: {perf1['user_experience']}")
    
    # 测试场景2: sync stream
    print("\n📍 场景2: def + stream + stream (真流式)")
    result2 = graphs["sync_stream"].invoke(initial_state, {"configurable": {"thread_id": "test2"}})
    perf2 = result2["performance_data"]
    print(f"   方法: {perf2['method']}")
    print(f"   总时间: {perf2['total_time']:.2f}s")
    print(f"   首chunk时间: {perf2['first_chunk_time']:.2f}s")
    print(f"   流式效果: {'✅' if perf2['streaming'] else '❌'}")
    print(f"   用户体验: {perf2['user_experience']}")


async def test_async_scenarios():
    """测试异步场景"""
    print("\n🚀 异步场景性能测试")
    print("-" * 40)
    
    graphs = create_test_graphs()
    initial_state = PerformanceTestState(
        input_text="这是测试文本用于验证同步异步调用效果",
        result="",
        current_step="initialized",
        performance_data={}
    )
    
    # 测试场景3: async invoke
    print("📍 场景3: async def + ainvoke + astream (异步非流式)")
    result3 = await graphs["async_invoke"].ainvoke(initial_state, {"configurable": {"thread_id": "test3"}})
    perf3 = result3["performance_data"]
    print(f"   方法: {perf3['method']}")
    print(f"   响应时间: {perf3['response_time']:.2f}s")
    print(f"   流式效果: {'✅' if perf3['streaming'] else '❌'}")
    print(f"   用户体验: {perf3['user_experience']}")
    
    # 测试场景4: async stream
    print("\n📍 场景4: async def + astream + astream (异步流式)")
    result4 = await graphs["async_stream"].ainvoke(initial_state, {"configurable": {"thread_id": "test4"}})
    perf4 = result4["performance_data"]
    print(f"   方法: {perf4['method']}")
    print(f"   总时间: {perf4['total_time']:.2f}s")
    print(f"   首chunk时间: {perf4['first_chunk_time']:.2f}s")
    print(f"   流式效果: {'✅' if perf4['streaming'] else '❌'}")
    print(f"   用户体验: {perf4['user_experience']}")


def main():
    """主测试函数"""
    print("🎯 LangGraph同步异步性能对比测试")
    print("=" * 70)
    print("🔬 核心发现: LLM调用方式决定流式效果，Graph流式模式只是传输管道")
    print("=" * 70)
    
    # 测试同步场景
    test_sync_scenarios()
    
    # 测试异步场景
    asyncio.run(test_async_scenarios())
    
    print("\n💡 性能对比总结:")
    print("   ❌ def + invoke(): 假流式，用户体验差")
    print("   ✅ def + stream(): 真流式，用户体验好")
    print("   ⚡ async def + ainvoke(): 异步性能，非流式")
    print("   🏆 async def + astream(): 异步流式，最佳体验")
    
    print("\n🎯 最佳实践:")
    print("   需要流式输出 → 使用 stream() 或 astream()")
    print("   需要高并发 → 使用 async def + ainvoke/astream")
    print("   最佳组合 → async def + astream() + graph.astream()")


if __name__ == "__main__":
    main()
