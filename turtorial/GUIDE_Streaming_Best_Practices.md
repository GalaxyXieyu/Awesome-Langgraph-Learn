# LangGraph 流式输出最佳实践指南

## 🌊 核心概念

LangGraph提供多种流式输出模式，让开发者可以实时获取工作流的执行状态和结果。

## 📊 流式模式对比

| 模式 | 用途 | 返回内容 | 适用场景 |
|------|------|----------|----------|
| `values` | 获取完整状态 | 完整的状态对象 | 监控整体状态变化 |
| `updates` | 获取状态更新 | 节点更新的增量 | 监控节点执行进度 |
| `messages` | 获取消息流 | 消息对象流 | 聊天和对话场景 |
| `custom` | 自定义事件 | 自定义事件数据 | 复杂的进度反馈 |

## 🔧 基础用法

### 1. Values模式
```python
for chunk in graph.stream(state, stream_mode="values"):
    print(f"当前状态: {chunk}")
```

### 2. Updates模式
```python
for chunk in graph.stream(state, stream_mode="updates"):
    for node_name, node_output in chunk.items():
        print(f"节点 {node_name} 更新: {node_output}")
```

### 3. Custom模式
```python
def my_node(state):
    writer = get_stream_writer()
    writer({"progress": 50, "message": "处理中..."})
    return state

for chunk in graph.stream(state, stream_mode="custom"):
    if "progress" in chunk:
        print(f"进度: {chunk['progress']}%")
```

## 💡 最佳实践

### ✅ 推荐做法
1. **选择合适的模式** - 根据需求选择最适合的流式模式
2. **合理的更新频率** - 避免过于频繁的状态更新
3. **丰富的进度信息** - 提供有意义的进度反馈
4. **错误处理** - 在流式输出中包含错误信息

### ❌ 避免的做法
1. **过度使用custom模式** - 简单场景使用updates即可
2. **频繁的小更新** - 影响性能和用户体验
3. **缺少错误处理** - 流式输出中断时的处理

## 🎯 实际应用示例

### 进度条实现
```python
def progress_node(state):
    writer = get_stream_writer()
    
    for i in range(1, 6):
        # 执行处理步骤
        time.sleep(0.5)
        progress = i * 20
        
        writer({
            "type": "progress",
            "progress": progress,
            "message": f"步骤 {i}/5"
        })
    
    return state

# 使用
for chunk in graph.stream(state, stream_mode="custom"):
    if chunk.get("type") == "progress":
        print(f"[{chunk['progress']}%] {chunk['message']}")
```

### 实时日志输出
```python
def logging_node(state):
    writer = get_stream_writer()
    
    writer({"type": "log", "level": "info", "message": "开始处理"})
    
    try:
        # 执行业务逻辑
        result = process_data(state["data"])
        writer({"type": "log", "level": "success", "message": "处理完成"})
    except Exception as e:
        writer({"type": "log", "level": "error", "message": str(e)})
    
    return state
```

## 🚀 高级技巧

### 1. 条件流式输出
```python
def conditional_streaming_node(state):
    writer = get_stream_writer()
    
    if state.get("verbose", False):
        writer({"message": "详细模式：开始处理"})
    
    # 处理逻辑
    return state
```

### 2. 多类型事件流
```python
def multi_event_node(state):
    writer = get_stream_writer()
    
    # 进度事件
    writer({"type": "progress", "value": 25})
    
    # 状态事件
    writer({"type": "status", "message": "正在分析数据"})
    
    # 结果事件
    writer({"type": "result", "data": processed_data})
    
    return state
```

### 3. 异步流式输出
```python
async def async_streaming_node(state, config):
    writer = get_stream_writer()
    
    async for chunk in async_process(state["data"]):
        writer({"chunk": chunk, "timestamp": time.time()})
    
    return state
```

## 📋 测试和调试

### 流式输出测试
```python
def test_streaming():
    events = []
    
    for chunk in graph.stream(state, stream_mode="custom"):
        events.append(chunk)
    
    # 验证事件序列
    assert len(events) > 0
    assert events[0]["type"] == "start"
    assert events[-1]["type"] == "complete"
```

### 调试技巧
```python
def debug_streaming_node(state):
    writer = get_stream_writer()
    
    # 调试信息
    writer({
        "type": "debug",
        "node": "debug_streaming_node",
        "state_keys": list(state.keys()),
        "timestamp": time.time()
    })
    
    return state
```

## 🎉 总结

流式输出是提升用户体验的关键技术，通过合理使用不同的流式模式，可以为用户提供实时的反馈和进度信息。选择合适的模式，提供有意义的进度信息，是成功实现流式输出的关键。
