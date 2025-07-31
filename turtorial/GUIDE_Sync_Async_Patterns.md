# LangGraph 同步异步模式指南

## ⚡ 核心发现

**重要结论**: LLM的调用方式决定流式效果，Graph的流式模式只是传输管道。

## 📊 五种组合方式对比

| 组合方式 | 响应时间 | 首token时间 | 流式效果 | 推荐度 |
|----------|----------|-------------|----------|--------|
| `def` + `invoke()` + `stream()` | 2.55s | - | ❌ 假流式 | 不推荐 |
| `def` + `stream()` + `stream()` | 30.56s | 0.30s | ✅ 真流式 | ✅ 推荐 |
| `def` + `invoke()` + `astream()` | 2.36s | - | ❌ 假流式 | 不推荐 |
| `async def` + `ainvoke()` + `astream()` | 28.52s | - | ❌ 非流式 | 高并发场景 |
| `async def` + `astream()` + `astream()` | 51.08s | 0.29s | 🏆 异步流式 | 🏆 最推荐 |

## 🎯 决策指南

```
需要流式输出？
├─ 是 → 需要高并发？
│   ├─ 是 → 🏆 async def + llm.astream() + graph.astream()
│   └─ 否 → ✅ def + llm.stream() + graph.stream()
└─ 否 → 需要高并发？
    ├─ 是 → ✅ async def + llm.ainvoke() + graph.astream()
    └─ 否 → ⚠️ def + llm.invoke() + graph.stream()
```

## 🔧 实现模板

### 🏆 最推荐：异步流式输出
```python
async def async_streaming_node(state, config):
    llm = ChatOpenAI(...)
    
    full_response = ""
    # 异步流式调用 - 最佳组合
    async for chunk in llm.astream(messages, config):
        if chunk.content:
            full_response += chunk.content
            # Token会自动通过LangGraph流式传输
    
    return {"result": full_response}

# 调用方式
async for chunk in graph.astream(state, stream_mode="updates"):
    print(f"节点更新: {chunk}")
```

### ✅ 推荐：同步流式输出
```python
def streaming_node(state):
    llm = ChatOpenAI(...)
    
    full_response = ""
    for chunk in llm.stream(messages):  # 关键：使用stream()
        if chunk.content:
            full_response += chunk.content
    
    return {"result": full_response}

# 调用方式
for chunk in graph.stream(state, stream_mode="updates"):
    print(f"节点更新: {chunk}")
```

### ✅ 高并发异步（非流式）
```python
async def async_node(state, config):
    llm = ChatOpenAI(...)
    response = await llm.ainvoke(messages, config)  # 传递config
    return {"result": response.content}

# 调用方式
async for chunk in graph.astream(state, stream_mode="updates"):
    print(chunk)
```

### ⚠️ 简单同步（非流式）
```python
def sync_node(state):
    llm = ChatOpenAI(...)
    response = llm.invoke(messages)
    return {"result": response.content}

# 调用方式
for chunk in graph.stream(state, stream_mode="updates"):
    print(chunk)
```

## 💡 最佳实践

### ✅ 推荐做法

1. **异步优先**
```python
# 高并发场景使用异步
async def high_performance_node(state, config):
    tasks = [llm.ainvoke(msg, config) for msg in messages]
    results = await asyncio.gather(*tasks)
    return {"results": results}
```

2. **流式优先**
```python
# 需要实时反馈时使用流式
def real_time_node(state):
    for chunk in llm.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
```

3. **正确传递config**
```python
# 异步调用必须传递config
async def correct_async_node(state, config):
    response = await llm.ainvoke(messages, config)  # ✅ 正确
    return {"result": response.content}
```

### ❌ 避免的做法

1. **异步环境中的同步阻塞**
```python
# ❌ 错误：同步调用阻塞异步环境
def blocking_node(state):
    response = llm.invoke(messages)  # 阻塞异步环境
    return {"result": response.content}

# 在异步环境中使用
async for chunk in graph.astream(state):  # 被阻塞
    print(chunk)
```

2. **假流式输出**
```python
# ❌ 错误：以为graph.stream()就是流式
def fake_streaming_node(state):
    response = llm.invoke(messages)  # 仍然是一次性调用
    return {"result": response.content}

# 即使使用graph.stream()，仍然不是真正流式
for chunk in graph.stream(state):  # 用户仍需等待LLM完成
    print(chunk)
```

3. **忘记传递config**
```python
# ❌ 错误：异步调用忘记传递config
async def incorrect_async_node(state, config):
    response = await llm.ainvoke(messages)  # 缺少config参数
    return {"result": response.content}
```

## 🧪 性能测试

### 测试流式效果
```python
import time

def test_streaming_effect():
    start_time = time.time()
    token_times = []
    
    for chunk in llm.stream(messages):
        if chunk.content:
            elapsed = time.time() - start_time
            token_times.append(elapsed)
            print(f"[{elapsed:.2f}s] Token: '{chunk.content}'")
    
    # 检查流式特征
    if len(token_times) > 1:
        intervals = [token_times[i] - token_times[i-1] 
                    for i in range(1, len(token_times))]
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval < 0.5:
            print("✅ 确认为真正的流式输出")
        else:
            print("⚠️ 可能不是真正的流式输出")
```

### 性能基准测试
```python
async def benchmark_async_vs_sync():
    # 异步测试
    start = time.time()
    async_result = await llm.ainvoke(messages)
    async_time = time.time() - start
    
    # 同步测试
    start = time.time()
    sync_result = llm.invoke(messages)
    sync_time = time.time() - start
    
    print(f"异步耗时: {async_time:.2f}s")
    print(f"同步耗时: {sync_time:.2f}s")
```

## 🎯 场景选择

### 1. 聊天机器人
```python
# 推荐：同步流式
def chat_node(state):
    for chunk in llm.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
```

### 2. 批量处理
```python
# 推荐：异步并发
async def batch_processing_node(state, config):
    tasks = [process_item(item, config) for item in state["items"]]
    results = await asyncio.gather(*tasks)
    return {"results": results}
```

### 3. 实时写作助手
```python
# 推荐：异步流式
async def writing_assistant_node(state, config):
    full_article = ""
    async for chunk in llm.astream(messages, config):
        if chunk.content:
            full_article += chunk.content
            # 实时显示写作进度
    return {"article": full_article}
```

### 4. 数据分析
```python
# 推荐：异步非流式
async def analysis_node(state, config):
    analysis = await llm.ainvoke(analysis_prompt, config)
    return {"analysis": analysis.content}
```

## 📋 调试检查清单

- [ ] 确认LLM调用方式（invoke vs stream vs ainvoke vs astream）
- [ ] 验证节点函数类型（def vs async def）
- [ ] 检查graph调用方式（stream vs astream）
- [ ] 确认config参数传递（异步调用必需）
- [ ] 测试流式效果（首token时间）
- [ ] 验证异步兼容性（无同步阻塞）

## 🎉 总结

选择合适的同步异步组合是优化LangGraph应用性能和用户体验的关键。记住核心原则：**LLM调用方式决定流式效果，异步调用提升并发性能**。
