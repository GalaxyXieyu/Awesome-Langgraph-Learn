# LangGraph Tasks Stream Mode 深度解析

## 📋 概述

`tasks` 是 LangGraph 提供的一种高级 stream mode,用于**在任务级别追踪工作流的执行状态**。本文档详细分析其功能、使用场景以及与项目中三段式 Writer 的对比。

---

## 🎯 Tasks Stream Mode 核心概念

### 定义

根据 LangGraph 官方文档：

> **"tasks"**: Emit events when tasks start and finish, including their results and errors.

### 关键特性

`tasks` stream mode 会在以下时机发送事件：

1. ✅ **任务开始** (Task Start)
2. ✅ **任务完成** (Task Finish)
3. ✅ **包含结果** (Results)
4. ✅ **包含错误** (Errors)

---

## 📊 Tasks Mode 详细分析

### 1. 事件结构

`tasks` 模式输出的事件包含以下信息：

```python
# 任务开始事件
{
    "event": "task_start",
    "name": "node_name",        # 节点/任务名称
    "task_id": "uuid",          # 任务唯一标识
    "timestamp": "iso8601",     # 开始时间戳
    "metadata": {...}           # 元数据
}

# 任务完成事件
{
    "event": "task_finish",
    "name": "node_name",
    "task_id": "uuid",
    "timestamp": "iso8601",
    "result": {...},            # 任务执行结果
    "error": null,              # 如果成功，error 为 null
    "duration": 1.23            # 执行时长（秒）
}

# 任务错误事件
{
    "event": "task_finish",
    "name": "node_name",
    "task_id": "uuid",
    "timestamp": "iso8601",
    "result": null,
    "error": {                  # 错误信息
        "type": "ErrorType",
        "message": "Error description",
        "traceback": "..."
    }
}
```

---

### 2. 使用示例

#### 基础用法

```python
from langgraph.graph import StateGraph, START, END

# 定义 graph
graph = StateGraph(State)
graph.add_node("planning", planning_node)
graph.add_node("searching", searching_node)
graph.add_node("analyzing", analyzing_node)
# ... 添加边

compiled = graph.compile()

# 使用 tasks stream mode
async for event in compiled.astream(
    input_data,
    stream_mode="tasks"  # 关键参数
):
    print(event)
```

#### 输出示例

```python
# 1. Planning 任务开始
{
    'event': 'task_start',
    'name': 'planning',
    'task_id': 'planning:abc123',
    'timestamp': '2025-10-13T10:00:00.000Z'
}

# 2. Planning 任务完成
{
    'event': 'task_finish',
    'name': 'planning',
    'task_id': 'planning:abc123',
    'timestamp': '2025-10-13T10:00:05.000Z',
    'result': {
        'plan_data': {...},
        'tasks': [...]
    },
    'error': None,
    'duration': 5.0
}

# 3. Searching 任务开始
{
    'event': 'task_start',
    'name': 'searching',
    'task_id': 'searching:def456',
    'timestamp': '2025-10-13T10:00:05.100Z'
}

# 4. Searching 任务完成
{
    'event': 'task_finish',
    'name': 'searching',
    'task_id': 'searching:def456',
    'timestamp': '2025-10-13T10:00:12.000Z',
    'result': {
        'search_results': {...}
    },
    'error': None,
    'duration': 6.9
}
```

---

### 3. 与其他 Stream Modes 对比

| 特性 | tasks | updates | values | custom |
|------|-------|---------|--------|--------|
| **粒度** | 任务级 | 节点级 | 完整状态 | 自定义 |
| **开始事件** | ✅ | ❌ | ❌ | ⚠️ 手动 |
| **结束事件** | ✅ | ❌ | ❌ | ⚠️ 手动 |
| **执行时长** | ✅ | ❌ | ❌ | ❌ |
| **错误捕获** | ✅ | ⚠️ | ⚠️ | ⚠️ 手动 |
| **结果数据** | ✅ | ✅ | ✅ | ⚠️ 手动 |
| **业务语义** | ⚠️ 有限 | ⚠️ 有限 | ❌ | ✅ 完全 |

---

## 🔍 Tasks Mode 的独特价值

### 1. 自动生命周期追踪

与 `updates` 模式不同，`tasks` 模式**自动提供开始和结束事件**：

```python
# updates 模式 - 仅在节点完成后输出
async for chunk in graph.astream(input, stream_mode="updates"):
    print(chunk)
    # {'planning': {'plan_data': {...}}}  # 只有结果

# tasks 模式 - 完整生命周期
async for event in graph.astream(input, stream_mode="tasks"):
    if event['event'] == 'task_start':
        print(f"开始: {event['name']}")
    elif event['event'] == 'task_finish':
        print(f"完成: {event['name']}, 耗时: {event['duration']}s")
```

### 2. 内置错误处理

```python
async for event in graph.astream(input, stream_mode="tasks"):
    if event['event'] == 'task_finish':
        if event['error']:
            # 自动捕获并结构化错误信息
            print(f"任务失败: {event['name']}")
            print(f"错误类型: {event['error']['type']}")
            print(f"错误信息: {event['error']['message']}")
        else:
            print(f"任务成功: {event['name']}")
```

### 3. 性能监控

```python
# 收集每个节点的执行时长
durations = {}

async for event in graph.astream(input, stream_mode="tasks"):
    if event['event'] == 'task_finish':
        durations[event['name']] = event['duration']

# 分析性能瓶颈
slowest = max(durations.items(), key=lambda x: x[1])
print(f"最慢的节点: {slowest[0]}, 耗时: {slowest[1]}s")
```

---

## 🤔 Tasks Mode 与三段式 Writer 对比

### 相似之处

| 功能 | Tasks Mode | 三段式 Writer |
|------|-----------|---------------|
| **开始信号** | ✅ task_start | ✅ status="start" |
| **结束信号** | ✅ task_finish | ✅ status="end" |
| **执行状态** | ✅ start/finish | ✅ start/processing/end |

### 关键差异

#### 1. **语义层级**

**Tasks Mode**:
- 关注**节点/任务级别**的执行
- 缺少业务语义（thinking/tool_call/plan 等）
- 适合系统级监控

**三段式 Writer**:
- 关注**业务消息级别**的输出
- 丰富的消息类型分类
- 适合用户界面展示

#### 2. **中间状态**

**Tasks Mode**:
```python
# 只有 start 和 finish
task_start → task_finish
```

**三段式 Writer**:
```python
# 支持多次 processing
start → processing → processing → processing → end
         (seq=1)      (seq=2)      (seq=3)
```

#### 3. **消息类型**

**Tasks Mode**:
```python
# 统一的事件结构
{
    'event': 'task_finish',
    'name': 'searching',
    'result': {...}  # 原始节点返回值
}
```

**三段式 Writer**:
```python
# 多样化的消息类型
{
    'message_type': 'search',  # 语义化类型
    'status': 'end',
    'data': {
        'query': [...],
        'results': {...},
        'results_count': 10
    }
}
```

---

## 💡 Tasks Mode 的最佳使用场景

### ✅ 适合的场景

#### 1. 系统性能监控

```python
# 监控每个节点的执行时长
async for event in graph.astream(input, stream_mode="tasks"):
    if event['event'] == 'task_finish':
        # 记录到监控系统
        monitor.record_duration(
            node=event['name'],
            duration=event['duration']
        )
```

#### 2. 错误追踪与报警

```python
async for event in graph.astream(input, stream_mode="tasks"):
    if event['event'] == 'task_finish' and event['error']:
        # 发送报警
        alert_system.send_alert(
            severity="error",
            node=event['name'],
            error_type=event['error']['type'],
            traceback=event['error']['traceback']
        )
```

#### 3. 进度条实现（简单场景）

```python
total_tasks = 5  # planning, searching, analyzing, coding, writing
completed = 0

async for event in graph.astream(input, stream_mode="tasks"):
    if event['event'] == 'task_finish':
        completed += 1
        progress = int((completed / total_tasks) * 100)
        print(f"进度: {progress}%")
```

### ❌ 不适合的场景

#### 1. 复杂的用户界面反馈

```python
# Tasks Mode 缺少业务语义
{
    'event': 'task_finish',
    'name': 'analyzing',
    'result': {'analysis_data': {...}}
}

# 前端需要手动解析和分类
# 而 Writer 直接提供:
{
    'message_type': 'content',  # 明确的类型
    'format': {'type': 'markdown'},
    'content': '## 分析结果\n...'
}
```

#### 2. 流式 LLM 输出

```python
# Tasks Mode 只在任务结束时输出完整结果
# 无法实现逐 token 流式显示

# 需要使用 messages mode 或 custom mode (Writer)
```

#### 3. 工具调用流程展示

```python
# Tasks Mode 无法区分工具调用和工具结果
# Writer 提供专门的 tool_call 和 tool_result 类型
```

---

## 🔄 混合使用策略

### 推荐组合：tasks + custom

```python
async for stream_mode, chunk in graph.astream(
    input,
    stream_mode=["tasks", "custom"]  # 组合使用
):
    if stream_mode == "tasks":
        # 用于系统监控
        if chunk['event'] == 'task_start':
            monitor.start_timer(chunk['task_id'])
        elif chunk['event'] == 'task_finish':
            monitor.end_timer(
                task_id=chunk['task_id'],
                duration=chunk['duration'],
                error=chunk['error']
            )
    
    elif stream_mode == "custom":
        # 用于用户界面
        # Writer 发出的业务消息
        yield chunk  # 直接转发给前端
```

---

## 📈 实际应用案例

### 案例 1: 自动进度追踪增强

```python
# 在 GraphWrapper 中增强进度追踪

async def _execute_stream(self, input_data, thread_id, user_id):
    stream = app.astream(
        state,
        config=run_config,
        stream_mode=["custom", "tasks"]  # 组合使用
    )
    
    task_registry = {}  # 追踪任务状态
    
    async for mode, chunk in stream:
        if mode == "tasks":
            # 自动记录任务执行信息
            if chunk['event'] == 'task_start':
                task_registry[chunk['task_id']] = {
                    'name': chunk['name'],
                    'start_time': chunk['timestamp'],
                    'status': 'running'
                }
            
            elif chunk['event'] == 'task_finish':
                task_info = task_registry.get(chunk['task_id'], {})
                task_info.update({
                    'status': 'completed' if not chunk['error'] else 'failed',
                    'end_time': chunk['timestamp'],
                    'duration': chunk['duration'],
                    'error': chunk['error']
                })
                
                # 自动更新数据库中的任务状态
                await self.repository.update_task_node_status(
                    task_id=thread_id,
                    node_name=chunk['name'],
                    status=task_info['status'],
                    duration=chunk['duration']
                )
        
        elif mode == "custom":
            # Writer 的消息，正常转发
            yield chunk
```

### 案例 2: 性能分析仪表板

```python
class PerformanceAnalyzer:
    def __init__(self):
        self.metrics = {
            'node_durations': {},
            'error_counts': {},
            'total_runs': 0
        }
    
    async def analyze_run(self, graph, input_data):
        """分析单次运行的性能"""
        node_timings = []
        
        async for event in graph.astream(
            input_data,
            stream_mode="tasks"
        ):
            if event['event'] == 'task_finish':
                node_timings.append({
                    'node': event['name'],
                    'duration': event['duration'],
                    'error': bool(event['error'])
                })
        
        return self._generate_report(node_timings)
    
    def _generate_report(self, timings):
        """生成性能报告"""
        total_time = sum(t['duration'] for t in timings)
        
        return {
            'total_duration': total_time,
            'node_breakdown': {
                t['node']: {
                    'duration': t['duration'],
                    'percentage': (t['duration'] / total_time) * 100
                }
                for t in timings
            },
            'bottleneck': max(timings, key=lambda x: x['duration'])['node']
        }
```

### 案例 3: 智能降级策略

```python
async def execute_with_fallback(graph, input_data):
    """基于 tasks 模式的智能降级"""
    failed_nodes = set()
    
    async for event in graph.astream(
        input_data,
        stream_mode="tasks"
    ):
        if event['event'] == 'task_finish' and event['error']:
            failed_nodes.add(event['name'])
            
            # 根据失败的节点动态调整策略
            if event['name'] == 'searching':
                print("搜索失败，使用缓存数据")
                # 触发降级逻辑
            
            elif event['name'] == 'analyzing':
                print("分析失败，使用简化分析")
                # 使用备用分析方法
```

---

## 🎯 与项目整合建议

### 短期建议（不破坏现有架构）

#### 1. 在 GraphWrapper 中添加 tasks 模式支持

```python
# src/infrastructure/ai/graph/wrapper.py

async def _execute_stream(self, input_data, thread_id, user_id):
    # 默认使用 custom + tasks 组合
    stream = app.astream(
        state,
        config=run_config,
        stream_mode=["custom", "tasks"]  # 新增 tasks
    )
    
    async for mode, chunk in stream:
        if mode == "custom":
            # 现有的 Writer 消息
            yield chunk
        
        elif mode == "tasks":
            # 新增：自动记录性能数据
            await self._handle_task_event(chunk, thread_id)
```

#### 2. 添加性能监控

```python
async def _handle_task_event(self, event, task_id):
    """处理 tasks 模式事件"""
    if event['event'] == 'task_finish':
        # 记录到监控系统
        await self.monitor.record_node_execution(
            task_id=task_id,
            node_name=event['name'],
            duration=event['duration'],
            success=not event['error']
        )
```

### 中期建议（增强功能）

#### 1. 自动进度推断

```python
# Writer 可以利用 tasks 事件自动更新进度
class StreamWriter:
    def _auto_update_progress_from_tasks(self, task_event):
        """从 tasks 事件自动更新进度"""
        if task_event['event'] == 'task_finish':
            # 自动推断任务完成，更新 plan
            self.plan(
                tasks=self._infer_tasks_from_nodes(),
                current_task_id=task_event['name'],
                overall_progress=self._calculate_progress()
            )
```

#### 2. 错误自动恢复

```python
async def execute_with_retry(graph, input_data):
    """基于 tasks 模式的自动重试"""
    max_retries = 3
    retry_count = {}
    
    async for event in graph.astream(
        input_data,
        stream_mode="tasks"
    ):
        if event['event'] == 'task_finish' and event['error']:
            node_name = event['name']
            retry_count[node_name] = retry_count.get(node_name, 0) + 1
            
            if retry_count[node_name] < max_retries:
                # 触发重试
                print(f"节点 {node_name} 失败，第 {retry_count[node_name]} 次重试")
```

### 长期建议（架构优化）

#### 1. 统一事件系统

```python
# 创建统一的事件转换层
class EventAdapter:
    """将 tasks 事件转换为 Writer 格式"""
    
    def adapt_task_start(self, task_event):
        """task_start → Writer start 消息"""
        return {
            'message_type': 'processing',
            'status': 'start',
            'node': task_event['name'],
            'timestamp': task_event['timestamp'],
            'data': {
                'task_id': task_event['task_id']
            }
        }
    
    def adapt_task_finish(self, task_event):
        """task_finish → Writer end 消息"""
        return {
            'message_type': 'processing',
            'status': 'end',
            'node': task_event['name'],
            'timestamp': task_event['timestamp'],
            'data': {
                'duration': task_event['duration'],
                'error': task_event['error']
            }
        }
```

---

## 📊 总结与建议

### ✅ Tasks Mode 的价值

1. **自动生命周期追踪** - 无需手动发送 start/end 事件
2. **内置错误处理** - 自动捕获并结构化错误信息
3. **性能监控** - 自动记录每个节点的执行时长
4. **简化进度追踪** - 节点级别的进度反馈

### ⚠️ Tasks Mode 的局限

1. **缺少业务语义** - 不支持 thinking/tool_call/plan 等分类
2. **粒度固定** - 只能在节点级别，无法细粒度控制
3. **不支持流式** - 无法实现 LLM 逐 token 输出
4. **前端适配成本** - 需要额外转换为业务消息

### 🎯 最终建议

**推荐策略**: **保留三段式 Writer + 补充 tasks 模式用于监控**

```python
# 最佳实践
stream_mode=["custom", "tasks"]

# custom - 用于业务消息（Writer）
# tasks  - 用于系统监控和性能分析
```

**不推荐**: 完全替换 Writer 为 tasks 模式
- ❌ 会丢失业务语义
- ❌ 前端需要大量适配
- ❌ 无法支持复杂的流式场景

---

## 📚 相关文档

- [LangGraph Stream Mode 详解](./langgraph-stream-mode-guide.md)
- [LangGraph Agents 开发指南](./langgraph-agents-development-guide.md)
- [Writer 模块架构说明](../../src/infrastructure/ai/graph/writer/README.md)
- [优化记录](./optimized.md)

---

## 🔗 参考资源

- [LangGraph Streaming Documentation](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [LangGraph Graph Reference](https://langchain-ai.github.io/langgraph/reference/graphs/)
- [LangGraph Python SDK Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)

---

**最后更新**: 2025-10-13  
**文档版本**: 1.0  
**作者**: AutoAgents 团队
