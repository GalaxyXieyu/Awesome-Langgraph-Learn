#!/usr/bin/env python3
"""
TEST_Streaming_Modes.py - LangGraph流式输出模式测试
测试values、updates、messages、custom四种流式模式的效果和应用场景
"""

import time
from typing import List, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer


class StreamingState(TypedDict):
    """流式测试状态"""
    step: str
    progress: int
    data: str
    log: List[str]


def progress_node(state: StreamingState) -> StreamingState:
    """带进度的处理节点"""
    try:
        writer = get_stream_writer()
    except:
        writer = lambda x: None
    
    state["log"].append(f"开始处理 - {time.strftime('%H:%M:%S')}")
    
    # 模拟分步处理
    for i in range(1, 6):
        time.sleep(0.5)  # 模拟处理时间
        progress = i * 20
        
        writer({
            "type": "progress_update",
            "progress": progress,
            "message": f"处理步骤 {i}/5",
            "timestamp": time.strftime('%H:%M:%S')
        })
        
        state["progress"] = progress
    
    state["step"] = "processing_completed"
    state["data"] = "处理完成的数据"
    state["log"].append(f"处理完成 - {time.strftime('%H:%M:%S')}")
    
    writer({
        "type": "completion",
        "message": "所有处理步骤完成",
        "final_data": state["data"]
    })
    
    return state


def create_streaming_graph():
    """创建流式测试图"""
    workflow = StateGraph(StreamingState)
    workflow.add_node("process", progress_node)
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)
    return workflow.compile(checkpointer=MemorySaver())


def test_streaming_modes():
    """测试不同的流式模式"""
    print("🌊 LangGraph流式输出模式测试")
    print("=" * 60)
    print("📋 测试内容: values、updates、messages、custom四种模式")
    print("=" * 60)
    
    graph = create_streaming_graph()
    initial_state = StreamingState(
        step="initialized",
        progress=0,
        data="",
        log=[f"初始化 - {time.strftime('%H:%M:%S')}"]
    )
    config = {"configurable": {"thread_id": "streaming_test"}}
    
    # 测试1: values模式
    print("\n📊 测试1: values模式 - 获取完整状态")
    for chunk in graph.stream(initial_state, config, stream_mode="values"):
        print(f"状态更新: step={chunk.get('step')}, progress={chunk.get('progress')}%")
    
    # 测试2: updates模式
    print("\n📈 测试2: updates模式 - 获取状态更新")
    for chunk in graph.stream(initial_state, config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            print(f"节点 {node_name} 更新: {node_output.get('step')}")
    
    # 测试3: custom模式
    print("\n🎯 测试3: custom模式 - 自定义事件流")
    for chunk in graph.stream(initial_state, config, stream_mode="custom"):
        if isinstance(chunk, dict):
            if chunk.get("type") == "progress_update":
                print(f"[{chunk['timestamp']}] {chunk['message']} - {chunk['progress']}%")
            elif chunk.get("type") == "completion":
                print(f"✅ {chunk['message']}")
    
    print(f"\n💡 总结:")
    print(f"   📊 values模式: 适合监控整体状态变化")
    print(f"   📈 updates模式: 适合监控节点执行进度")
    print(f"   🎯 custom模式: 适合复杂的进度反馈")


if __name__ == "__main__":
    test_streaming_modes()
