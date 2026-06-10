# LG-07: 流式输出与实时监控

> **阶段**: LG-07 | **难度**: 中级-高级 | **预计时长**: 3-4 小时 | **依赖**: LG-01 ~ LG-06

## 学习目标

- 掌握 7 种 stream_mode 的区别与适用场景
- 使用 StreamWriter 推送自定义进度事件
- 组合多种 stream_mode 构建复杂的前端实时 UI
- 处理多 Agent 嵌套时的流式事件层级
- 实现 Token 级流式输出
- 掌握流式错误处理策略

```python
# 安装依赖（取消注释执行）
# !pip install -U langgraph langchain langchain-openai
```

---

## 1. Stream Mode 全景概览

LangGraph 1.x 提供 7 种 stream_mode：

```python
StreamMode = Literal[
    "values",       # 完整 State 快照
    "updates",      # 增量更新
    "messages",     # Token 级流式
    "custom",       # 自定义事件
    "tasks",        # 任务生命周期
    "checkpoints",  # Checkpoint 事件
    "debug",        # 调试事件
]
```

| 模式 | 何时推送 | 推送内容 | 适用场景 |
|------|---------|---------|---------|
| values | 每个超级步结束 | 完整 State | 状态面板、节点高亮 |
| updates | 每个超级步结束 | 节点返回的增量 | 带宽敏感、增量更新 |
| messages | LLM 生成每个 token | (AIMessageChunk, metadata) | 打字机效果、实时对话 |
| custom | Node 内调用 writer() | 你自定义的任何数据 | 进度条、业务通知 |
| tasks | 任务 start/finish | TaskPayload / TaskResultPayload | 执行监控、性能分析 |
| checkpoints | Checkpoint 创建 | CheckpointPayload | 状态恢复调试 |
| debug | 以上两种组合 | DebugPayload | 开发调试 |

---

## 2. 构建示例图（LiveWriter）

我们先构建一个用于演示各种 stream mode 的示例图。

```python
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
import time

class WriterState(TypedDict):
    topic: str
    outline: str
    content: str
    sources: list
    messages: Annotated[list, add]

def plan_outline(state: WriterState) -> dict:
    topic = state["topic"]
    print(f"[plan_outline] 为 '{topic}' 生成大纲...")
    time.sleep(0.3)
    outline = f"1. {topic}简介 2. 核心概念 3. 实战案例 4. 总结"
    return {"outline": outline, "messages": ["大纲规划完成"]}

def gather_sources(state: WriterState) -> dict:
    print("[gather_sources] 收集参考资料...")
    time.sleep(0.3)
    sources = [
        {"title": "LangGraph 官方文档", "url": "https://langchain-ai.github.io/langgraph/"},
        {"title": "AI Agent 设计模式", "url": "https://example.com/agent-patterns"},
    ]
    return {"sources": sources, "messages": ["资料收集完成"]}

def generate_content(state: WriterState) -> dict:
    print("[generate_content] 生成内容...")
    time.sleep(0.5)
    content = f"关于 {state['topic']} 的文章内容... {state['outline']}"
    return {"content": content, "messages": ["内容生成完成"]}

builder = StateGraph(WriterState)
builder.add_node("plan_outline", plan_outline)
builder.add_node("gather_sources", gather_sources)
builder.add_node("generate_content", generate_content)
builder.add_edge(START, "plan_outline")
builder.add_edge(START, "gather_sources")
builder.add_edge("plan_outline", "generate_content")
builder.add_edge("gather_sources", "generate_content")
builder.add_edge("generate_content", END)
writer_graph = builder.compile()
print("LiveWriter 图编译成功！")
```

```python
from IPython.display import Image, display
png_bytes = writer_graph.get_graph().draw_mermaid_png()
display(Image(data=png_bytes))
```

---

## 3. stream_mode="values" -- 完整状态快照

**概念**：每次超级步（step）结束后，推送当前完整的 State。

**适用场景**：
- 实时状态面板：显示当前执行到哪个节点
- 节点高亮：前端根据 State 变化高亮当前活跃的节点
- 完整的 State 可视化

**注意**：每次推送都是完整 State，不是增量。如果 State 很大（messages 很长），带宽消耗较大。

```python
print("=" * 60)
print("stream_mode='values' - 每次超级步后的完整 state")
print("=" * 60)
for chunk in writer_graph.stream(
    {"topic": "LangGraph 流式输出", "outline": "", "content": "", "sources": [], "messages": []},
    stream_mode="values"
):
    print("\n--- 状态快照 ---")
    for key, value in chunk.items():
        if value:
            display_value = value if len(str(value)) < 100 else str(value)[:100] + "..."
            print(f"  {key}: {display_value}")
```

---

## 4. stream_mode="updates" -- 增量更新

**概念**：只推送每个节点返回的增量数据（即节点函数的返回值）。

**vs. values**：

| | values | updates |
|--|--------|---------|
| 推送内容 | 完整 State | 仅节点返回值 |
| 数据量 | 大（包含所有字段） | 小（仅变化的部分） |
| 前端处理 | 直接替换整个 State | 需要 merge 到现有 State |
| 适用 | State 小、需要完整视图 | State 大、带宽敏感 |

**适用场景**：带宽敏感的前端（移动端）、只需要增量更新的场景。

```python
print("=" * 60)
print("stream_mode='updates' - 仅返回变化的字段")
print("=" * 60)
for chunk in writer_graph.stream(
    {"topic": "LangGraph 流式输出", "outline": "", "content": "", "sources": [], "messages": []},
    stream_mode="updates"
):
    print("\n--- 增量更新 ---")
    for node_name, node_state in chunk.items():
        print(f"  节点 '{node_name}' 返回了更新:")
        for key, value in node_state.items():
            if value:
                display_value = value if len(str(value)) < 80 else str(value)[:80] + "..."
                print(f"    {key}: {display_value}")
```

---

## 5. stream_mode="messages" -- Token 级流式（重点）

**概念**：LLM 每生成一个 token，立即推送到前端。这是实现打字机效果的核心。

**关键点**：
1. messages 模式只捕获通过 LangChain ChatModel 调用产生的 token
2. 每个 chunk 都带有 metadata，告诉你这个 token 来自哪个节点、第几步
3. 如果节点内直接 return 字符串（不走 LLM），不会触发 messages 事件

**适用场景**：打字机效果（ChatGPT 风格）、实时对话机器人、长文本生成时的用户等待体验。

下面从课程数据文件读取一组 stream 事件，观察 messages 模式的结构和消费方式。

```python
from pathlib import Path
import json
from langchain_core.messages import AIMessageChunk

stream_data_path = Path("stream_events_data.json")
if not stream_data_path.exists():
    stream_data_path = Path("turtorial/LG-07-streaming/stream_events_data.json")

stream_data = json.loads(stream_data_path.read_text(encoding="utf-8"))
message_tokens = stream_data["message_tokens"]

print("=" * 60)
print("stream_mode='messages' - Token 级流式")
print("=" * 60)

full_text = ""
for i, token in enumerate(message_tokens):
    chunk = {
        "type": "messages",
        "ns": (),
        "data": (
            AIMessageChunk(content=token),
            {"langgraph_step": 3, "langgraph_node": "writer", "langgraph_triggers": ["researcher"]},
        ),
    }
    msg, metadata = chunk["data"]
    full_text += msg.content
    print(f"Token {i+1:2d}: '{msg.content}' | 来自节点: {metadata['langgraph_node']}")

print(f"\n拼接结果: {full_text}")
print("\n注意: messages 模式的 token 是增量，前端需要 text += new_token，不是 text = new_token")
```

### 真实 LLM 的 messages 模式使用

```python
from langchain_openai import ChatOpenAI

# 需要设置 OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4", streaming=True)

# 在图中使用 LLM 节点
def llm_node(state):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 使用 messages stream mode
async for chunk in graph.astream(
    {"messages": [HumanMessage("写一篇文章")]},
    stream_mode="messages",
):
    msg, metadata = chunk["data"]
    print(f"来自节点: {metadata['langgraph_node']}")
    print(f"Token: {msg.content}")
```

---

## 6. stream_mode="custom" -- 自定义事件

**概念**：在 Node 函数内部，通过 StreamWriter 主动推送任意自定义数据。

**关键点**：
- writer 是自动注入的--只要在 Node 函数签名中声明 writer 参数，LangGraph 就会自动传入
- 只有在 stream_mode="custom" 或包含 custom 的组合中，writer 的调用才会生效

**适用场景**：进度条（百分比）、业务通知（资料检索中...）、中间结果预览。

```python
from langgraph.config import get_stream_writer
import time

class CustomState(TypedDict):
    topic: str
    progress: int

def node_with_progress(state: CustomState) -> dict:
    """使用 get_stream_writer() 发送自定义事件"""
    topic = state["topic"]
    writer = get_stream_writer()

    sources = ["财经数据", "新闻", "竞品分析", "专家观点"]
    for i, source in enumerate(sources):
        writer({"type": "progress", "source": source, "percent": (i + 1) / len(sources) * 100, "status": "searching"})
        time.sleep(0.2)
        writer({"type": "progress", "source": source, "percent": (i + 1) / len(sources) * 100, "status": "completed"})

    return {"progress": 100}

custom_builder = StateGraph(CustomState)
custom_builder.add_node("node_with_progress", node_with_progress)
custom_builder.add_edge(START, "node_with_progress")
custom_builder.add_edge("node_with_progress", END)
custom_graph = custom_builder.compile()

print("=" * 60)
print("stream_mode='custom' - 自定义进度事件")
print("=" * 60)
for event in custom_graph.stream({"topic": "实时任务", "progress": 0}, stream_mode="custom"):
    data = event["data"]
    print(f"[{data['status']:>10}] {data['source']:<10} - {data['percent']:.0f}%")
```

---

## 7. stream_mode="tasks" -- 任务生命周期

**概念**：自动追踪每个任务（节点）的生命周期：start -> finish，包含执行时长和错误信息。

**独特价值**：
1. 自动生命周期追踪：无需在 Node 内手动 yield，自动发送 start/finish
2. 内置错误捕获：失败时 error 字段包含完整错误信息
3. 性能监控：通过 start 和 finish 的时间差，计算每个节点的执行时长

**vs. custom**：

| | tasks | custom |
|--|-------|--------|
| 推送时机 | 自动（start/finish） | 手动（Node 内调用 writer） |
| 数据内容 | 系统级（节点名、ID、错误） | 业务级（进度百分比、中间结果） |
| 粒度 | 节点级 | 任意（可多次推送） |
| 适用 | 监控、调试 | 用户界面反馈 |

```python
print("=" * 60)
print("stream_mode='tasks' - 任务生命周期追踪")
print("=" * 60)

task_timings = {}
for chunk in writer_graph.stream(
    {"topic": "LangGraph 流式输出", "outline": "", "content": "", "sources": [], "messages": []},
    stream_mode="tasks"
):
    data = chunk["data"]
    if "result" not in data:
        task_timings[data["id"]] = time.time()
        print(f"▶️  节点开始: {data['name']} (id={data['id']})")
    else:
        start_time = task_timings.pop(data["id"], time.time())
        duration = time.time() - start_time
        if data["error"]:
            print(f"❌ 节点失败: {data['name']}, 错误: {data['error']}")
        else:
            print(f"✅ 节点完成: {data['name']} (耗时: {duration:.3f}s)")
```

---

## 8. stream_mode="debug" -- 调试事件

**概念**：组合了 checkpoints + tasks，提供最详细的调试信息。

**适用场景**：
- 开发阶段调试图的执行流程
- 排查 State 在哪个步骤发生了变化
- 配合 LangGraph Studio 的可视化调试

**注意**：生产环境不建议开启，数据量太大。

```python
print("=" * 60)
print("stream_mode='debug' - 调试事件（生产环境不建议使用）")
print("=" * 60)

event_count = 0
for chunk in writer_graph.stream(
    {"topic": "LangGraph 调试", "outline": "", "content": "", "sources": [], "messages": []},
    stream_mode="debug"
):
    event_count += 1
    if chunk["type"] == "debug":
        print(f"[{event_count:2d}] debug event received")

print(f"\n共收到 {event_count} 个 debug 事件")
print("说明: debug = checkpoints + tasks，提供最详细的调试信息")
```

---

## 9. 多 Mode 组合与事件过滤

### 9.1 组合多种 Stream Mode

可以同时获取 messages（打字机）和 custom（进度条）等多种模式的事件。

```python
print("=" * 60)
print("组合 stream_mode=['messages', 'custom', 'tasks']")
print("=" * 60)

class ComboState(TypedDict):
    text: str
    status: str

def combo_node(state: ComboState) -> dict:
    writer = get_stream_writer()
    writer({"type": "progress", "message": "开始处理...", "percent": 0})
    time.sleep(0.1)
    writer({"type": "progress", "message": "处理中...", "percent": 50})
    time.sleep(0.1)
    writer({"type": "progress", "message": "处理完成！", "percent": 100})
    return {"text": "处理结果", "status": "done"}

combo_builder = StateGraph(ComboState)
combo_builder.add_node("combo_node", combo_node)
combo_builder.add_edge(START, "combo_node")
combo_builder.add_edge("combo_node", END)
combo_graph = combo_builder.compile()

for mode, chunk in combo_graph.stream({"text": "", "status": ""}, stream_mode=["custom", "tasks"]):
    if mode == "custom":
        data = chunk["data"]
        print(f"[CUSTOM] {data['type']}: {data['message']} ({data['percent']}%)")
    elif mode == "tasks":
        data = chunk["data"]
        if "result" not in data:
            print(f"[TASKS]  开始: {data['name']}")
        else:
            print(f"[TASKS]  完成: {data['name']}")
    else:
        print(f"[{mode}] {chunk}")
```

### 9.2 事件过滤：Namespace

所有 StreamPart 都包含 ns（namespace）字段，用于标识事件来源的图层级。

- ()：顶层图（根图）
- ("subgraph",)：名为 "subgraph" 的子图
- ("supervisor", "weather_expert")：supervisor 图中的 weather_expert 子图

**注意**：要接收子图的事件，必须设置 subgraphs=True。

```python
# Namespace 过滤示例
print("=" * 60)
print("Namespace 过滤示例")
print("=" * 60)

namespace_events = stream_data["namespace_events"]

for event in namespace_events:
    ns = tuple(event["ns"])
    if not ns:
        print(f"[ROOT]   {event['data']['msg']}")
    elif len(ns) == 1:
        print(f"[SUB]    {event['data']['msg']} (来自: {ns[0]})")
    else:
        path = " -> ".join(ns)
        print(f"[NESTED] {event['data']['msg']} (路径: {path})")

print("\n使用 subgraphs=True 开启子图事件流:")
print("  async for chunk in graph.astream(input, stream_mode='values', subgraphs=True)")
```

---

## 10. 多 Agent 嵌套时的 Stream 事件

### 10.1 问题场景

当你使用 create_supervisor 或 create_swarm 时，图结构是嵌套的。默认情况下，stream() 只返回顶层图的事件。子图内部发生了什么，你是看不到的。

### 10.2 解决方案：subgraphs=True

```python
# 多 Agent 嵌套的 stream 事件
print("=" * 60)
print("多 Agent 嵌套 Stream 事件示例")
print("=" * 60)

from langchain_core.messages import AIMessageChunk

nested_events = []
for item in stream_data["nested_events"]:
    ns = tuple(item["ns"])
    if item["type"] == "messages":
        nested_events.append({
            "type": "messages",
            "ns": ns,
            "data": (AIMessageChunk(content=item["content"]), item.get("metadata", {})),
        })
    else:
        nested_events.append({"type": "tasks", "ns": ns, "data": item["data"]})

for event in nested_events:
    ns = event["ns"]
    event_type = event["type"]
    source = "[顶层图]" if not ns else f"[子图: {' -> '.join(ns)}]"
    if event_type == "messages":
        msg = event["data"][0]
        print(f"{source} Token: '{msg.content}'")
    elif event_type == "tasks":
        data = event["data"]
        if "result" not in data:
            print(f"{source} 任务开始: {data['name']}")
        else:
            print(f"{source} 任务完成: {data['name']}")

print("\n前端处理策略:")
print("  - 顶层图事件: 主面板显示")
print("  - 子图事件: 可折叠的详情面板")
```

---

## 11. astream_events 详解（v2/v3）

LangGraph 提供 astream_events，可以看到每个 LLM token 的生成过程，是最细粒度的事件流。

### v2 API（稳定版）

```python
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

async def demo_astream_events():
    class SimpleState(TypedDict):
        text: str

    def node_a(state: SimpleState) -> dict:
        return {"text": state["text"] + " [经过节点A]"}

    def node_b(state: SimpleState) -> dict:
        return {"text": state["text"] + " [经过节点B]"}

    simple_builder = StateGraph(SimpleState)
    simple_builder.add_node("node_a", node_a)
    simple_builder.add_node("node_b", node_b)
    simple_builder.add_edge(START, "node_a")
    simple_builder.add_edge("node_a", "node_b")
    simple_builder.add_edge("node_b", END)
    simple_graph = simple_builder.compile()

    print("=" * 60)
    print("astream_events - 最细粒度事件流 (version='v2')")
    print("=" * 60)

    event_count = 0
    async for event in simple_graph.astream_events({"text": "Hello LangGraph"}, version="v2"):
        event_count += 1
        kind = event.get("event", "")
        name = event.get("name", "")
        if kind.startswith("on_chain"):
            print(f"[Chain]  {kind:<30} | name={name}")
        elif kind.startswith("on_node"):
            print(f"[Node]   {kind:<30} | name={name}")
        elif kind.startswith("on_chat_model"):
            print(f"[LLM]    {kind:<30} | name={name}")
        elif kind.startswith("on_tool"):
            print(f"[Tool]   {kind:<30} | name={name}")
        else:
            print(f"[Other]  {kind:<30} | name={name}")

    print(f"\n共捕获 {event_count} 个事件")
    print("\n说明:")
    print("  - on_chain_start/end:  图/子图的生命周期")
    print("  - on_node_start/end:   节点的开始和结束")
    print("  - on_chat_model_*:     LLM 调用")
    print("  - on_tool_start/end:   工具调用")
    print("  - 当使用真实 ChatOpenAI 时，还会看到 on_chat_model_stream (token 级)")

await demo_astream_events()
```

### v3 API（实验性）

LangGraph 1.x 引入了 astream_events(version="v3")，提供比传统 stream_mode 更灵活的事件流：

```python
# v3 API（实验性）
run = await app.astream_events(input, version="v3")

# 并发读取不同类型的投影
async for chunk in run.output:
    print(f"State: {chunk}")

async for event in run.interrupts:
    print(f"中断: {event}")
```

**v3 的特点**：
1. 返回 AsyncGraphRunStream，支持并发投影
2. 自动包含所有子图事件（不需要 subgraphs=True）
3. 内置 StreamMux 自动分类事件

**注意**：v3 是实验性 API，可能变化。生产环境建议使用稳定的 stream_mode。

---

## 12. 前端 SSE/Websocket 协议对接

### 12.1 流式 vs 非流式：业务决策矩阵

不是所有输出都需要流式。错误的流式策略会带来两个问题：
1. 该流的不流 -> 用户盯着白屏等 10 秒，体验差
2. 不该流的也流 -> 前端频繁重绘、带宽浪费、代码复杂

| 场景 | 是否流式 | 理由 | 典型消息类型 |
|------|---------|------|------------|
| LLM 生成自然语言内容 | **必须流式** | 消除等待焦虑、提升 perceived speed | content |
| 思考过程/推理链 | **建议流式** | 让用户看到「AI 在思考」，建立信任 | thinking |
| 工具调用参数 | **非流式** | 结构化数据，一次性展示更高效 | tool_call |
| 工具执行结果 | **非流式** | 结果完整性要求高，片段无意义 | tool_result |
| 错误信息 | **非流式** | 错误需要立即、完整呈现，不能逐字蹦 | error |
| 中断/审批请求 | **非流式** | 需要用户立即做决策，必须完整展示 | interrupt |
| 计划/步骤列表 | **视情况** | 短计划非流式，长计划可流式 | plan |
| 进度通知 | **非流式** | 百分比/状态变更，一次性推送即可 | processing |

**核心原则**：
> **「人读的东西流式，机器读的东西非流式」**。LLM 生成的自然语言是给人看的，流式能提升体验；工具调用、错误码是给程序处理的，非流式更简洁。

### 12.2 三段式流式协议（Start -> Processing -> End）

对于必须流式的消息，推荐采用**三段式协议**：

第一次推送 start（空内容，状态:开始）-> 中间 N 次推送 processing（内容增量，状态:处理中）-> 最后一次推送 end（空内容，状态:结束）

| 阶段 | 作用 | 前端行为 |
|------|------|---------|
| start | 占位。告知前端「这个流开始了」，创建消息容器 | 插入空消息气泡/进度条 |
| processing | 内容。实际的数据增量 | 追加到容器内，更新打字机效果 |
| end | 收尾。告知前端「这个流结束了」，可以做后续操作 | 移除光标、启用复制按钮、触发摘要 |

### 12.3 消息信封设计（MessageEnvelope）

统一的消息结构，让前端处理逻辑极简：

```python
# 消息信封设计示例
print("=" * 60)
print("消息信封 (MessageEnvelope) 设计")
print("=" * 60)

message_envelope = {
    "message_type": "content",
    "content": "实际文本内容",
    "status": "processing",
    "message_id": "msg_abc123",
    "node_name": "writer",
    "agent_name": "deepresearch",
    "agent_hierarchy": ["supervisor", "researcher"],
    "process_step": "3/5",
    "timestamp": 1716643200.0,
    "format": {"type": "markdown", "code_language": "python"},
    "data": {"delta": "增量文本", "mode": "append"},
    "metadata": {"finish_reason": "stop", "source_type": "llm"}
}

import json
print(json.dumps(message_envelope, indent=2, ensure_ascii=False))

print("\n前端解析逻辑:")
print("function handleMessage(envelope) {")
print("    const renderer = getRenderer(envelope.message_type);")
print("    switch(envelope.status) {")
print("        case 'start': renderer.createPlaceholder(envelope.message_id); break;")
print("        case 'processing': renderer.appendContent(envelope.message_id, envelope.content); break;")
print("        case 'end': renderer.finalize(envelope.message_id); break;")
print("    }")
print("    const container = getContainer(envelope.agent_hierarchy);")
print("    container.render(renderer);")
print("}")
```

### 12.4 SSE 后端实现示例

```python
# SSE (Server-Sent Events) 后端实现示例
print("=" * 60)
print("SSE 后端实现示例 (FastAPI)")
print("=" * 60)

print("""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

async def stream_events(input_data: dict):
    async for mode, chunk in graph.astream(
        input_data,
        stream_mode=['messages', 'custom', 'tasks'],
        subgraphs=True
    ):
        envelope = {
            'message_type': mode,
            'data': chunk['data'],
            'ns': chunk.get('ns', ()),
            'timestamp': time.time()
        }
        yield f"data: {json.dumps(envelope)}\n\n"
    yield f"data: {json.dumps({'status': 'done'})}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: dict):
    return StreamingResponse(
        stream_events(request),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )
""")

print("\n前端 JavaScript 消费 SSE:")
print("const eventSource = new EventSource('/chat/stream');")
print("eventSource.onmessage = (event) => {")
print("    const data = JSON.parse(event.data);")
print("    if (data.status === 'done') { eventSource.close(); return; }")
print("    switch(data.message_type) {")
print("        case 'messages': appendToken(data.data[0].content); break;")
print("        case 'custom': updateProgress(data.data); break;")
print("        case 'tasks': updateTaskStatus(data.data); break;")
print("    }")
print("};")
print("eventSource.onerror = (error) => {")
print("    console.error('SSE error:', error);")
print("    eventSource.close();")
print("};")
```

---

## 13. 流式错误处理

流式场景下的错误处理比同步调用更复杂--错误可能在流的任何时刻发生。

### 13.1 常见错误场景

| 错误类型 | 发生时机 | 处理策略 |
|---------|---------|---------|
| LLM API 错误 | token 生成过程中 | 返回已生成内容 + 错误标记 |
| 节点执行错误 | 节点函数内 | tasks mode 自动捕获 error 字段 |
| 网络中断 | 流式传输中 | 前端检测断连，支持重试 |
| 超时 | 长时间无输出 | 设置超时阈值，优雅终止 |
| 状态验证失败 | 超级步结束后 | 返回错误信息，终止后续执行 |

### 13.2 错误处理代码示例

```python
# 流式错误处理示例
print("=" * 60)
print("流式错误处理策略")
print("=" * 60)

class ErrorState(TypedDict):
    text: str
    error_count: int

def flaky_node(state: ErrorState) -> dict:
    import random
    if random.random() < 0.3:
        raise RuntimeError("模拟的节点错误")
    return {"text": state["text"] + " [成功处理]"}

error_builder = StateGraph(ErrorState)
error_builder.add_node("flaky", flaky_node)
error_builder.add_edge(START, "flaky")
error_builder.add_edge("flaky", END)
error_graph = error_builder.compile()

print("\n策略 1: try-except 捕获流式错误")
print("-" * 40)
for attempt in range(3):
    try:
        print(f"尝试 {attempt + 1}...")
        for chunk in error_graph.stream({"text": "", "error_count": 0}, stream_mode="values"):
            print(f"  收到: {chunk}")
        print("  成功！")
        break
    except Exception as e:
        print(f"  错误: {e}")
        if attempt == 2:
            print("  已达到最大重试次数，放弃")

print("\n策略 2: tasks mode 自动错误捕获")
print("-" * 40)
for chunk in error_graph.stream({"text": "", "error_count": 0}, stream_mode="tasks"):
    data = chunk["data"]
    if "result" in data:
        if data["error"]:
            print(f"节点 '{data['name']}' 失败: {data['error']}")
        else:
            print(f"节点 '{data['name']}' 成功完成")

print("\n策略 3: 前端错误处理")
print("-" * 40)
print("// 前端 SSE 错误处理")
print("eventSource.onerror = (error) => {")
print("    showErrorToast('连接中断，正在重试...');")
print("    if (retryCount < 3) { retryCount++; setTimeout(() => reconnect(), 1000); }")
print("    else { showErrorToast('连接失败，请刷新页面重试'); eventSource.close(); }")
print("};")
```

---

## 14. 案例驱动：LiveWriter 完整流式实现

实时写作助手：用户输入主题 -> AI 并行检索资料 -> 逐段生成文章 -> 实时显示进度。

| 概念 | LiveWriter 中的体现 |
|------|-------------------|
| values | 实时状态面板显示当前执行到哪个节点 |
| updates | 段落进度条只接收新增的内容 |
| messages | 打字机效果，逐字生成文章 |
| custom | 自定义进度事件：「大纲完成 100%」「资料检索中...」 |
| tasks | 并行任务的执行状态（pending->running->completed） |

```python
print("=" * 60)
print("LiveWriter 完整流式实现")
print("=" * 60)

class LiveWriterState(TypedDict):
    topic: str
    outline: str
    sources: list
    content: str
    progress: int

def live_plan(state: LiveWriterState) -> dict:
    writer = get_stream_writer()
    writer({"type": "progress", "stage": "plan", "message": "正在规划大纲...", "percent": 10})
    time.sleep(0.3)
    writer({"type": "progress", "stage": "plan", "message": "大纲规划完成", "percent": 25})
    return {"outline": f"1. {state['topic']}简介\n2. 核心概念\n3. 实战案例\n4. 总结"}

def live_research(state: LiveWriterState) -> dict:
    writer = get_stream_writer()
    sources = ["官方文档", "技术博客", "开源项目"]
    for i, source in enumerate(sources):
        pct = 25 + (i + 1) / len(sources) * 25
        writer({"type": "progress", "stage": "research", "message": f"正在检索 {source}...", "percent": pct})
        time.sleep(0.2)
    return {"sources": sources}

def live_write(state: LiveWriterState) -> dict:
    writer = get_stream_writer()
    writer({"type": "progress", "stage": "write", "message": "开始撰写文章...", "percent": 60})
    time.sleep(0.3)
    writer({"type": "progress", "stage": "write", "message": "文章撰写完成", "percent": 100})
    return {"content": f"关于 {state['topic']} 的完整文章..."}

live_builder = StateGraph(LiveWriterState)
live_builder.add_node("plan", live_plan)
live_builder.add_node("research", live_research)
live_builder.add_node("write", live_write)
live_builder.add_edge(START, "plan")
live_builder.add_edge(START, "research")
live_builder.add_edge("plan", "write")
live_builder.add_edge("research", "write")
live_builder.add_edge("write", END)
live_graph = live_builder.compile()

print("\n执行 LiveWriter（组合 custom + tasks 模式）:\n")
for mode, chunk in live_graph.stream(
    {"topic": "LangGraph 流式输出", "outline": "", "sources": [], "content": "", "progress": 0},
    stream_mode=["custom", "tasks"]
):
    if mode == "custom":
        data = chunk["data"]
        bar = "█" * int(data["percent"] / 5) + "░" * (20 - int(data["percent"] / 5))
        print(f"[{data['stage']:>8}] {bar} {data['percent']:>3.0f}% | {data['message']}")
    elif mode == "tasks":
        data = chunk["data"]
        if "result" not in data:
            print(f"[TASK]     节点 '{data['name']}' 开始执行")
        else:
            status = "✅" if not data["error"] else "❌"
            print(f"[TASK]     节点 '{data['name']}' 执行完成 {status}")
```

---

## 15. 常见误区与注意事项

| 坑 | 现象 | 预警话术 |
|----|------|---------|
| 用 values 做打字机效果 | 每次推送完整 State，前端需要 diff 才能知道新增了什么 | 打字机效果必须用 messages mode，values 不适合 token 级流式。 |
| 忘记前端拼接 token | 每个 token 覆盖了上一个，只显示最后一个字 | messages mode 的 token 是增量，前端需要 text += new_token，不是 text = new_token。 |
| custom writer 不在 Node 中 | 自定义事件没有推送 | custom mode 的 writer 必须在 Node 函数内部调用，且图要用 astream。 |
| 子图事件没出来 | 只看到顶层图的事件，子图内部黑盒 | 嵌套多 Agent 时，必须设置 subgraphs=True 才能看到子图内部事件。 |
| 混淆 sync/async | stream 和 astream 混用导致不流式 | 异步图必须用 astream，同步图用 stream。LangGraph 的流式依赖 async generator。 |
| 组合 mode 时没解包 | 只返回了一个值，不知道是哪种 mode | 组合 stream_mode 时，每次迭代返回 (mode, chunk) 元组，需要解包。 |
| v3 API 不稳定 | 代码在新版本 LangGraph 中失效 | astream_events(version='v3') 是实验性 API，生产环境建议用稳定的 stream_mode。 |

### 调试技巧

1. 打印每个 event：先不用前端，直接在终端 print(event) 观察事件结构
2. 区分 event 类型：event["type"] 字段标识事件类型
3. 检查 namespace：event["ns"] 告诉你事件来自哪个图层级
4. 用 Gradio 快速验证：Gradio 的 chatbot 组件原生支持流式消息

---

## 16. 阶段小结

### 核心要点回顾

1. **values = 完整状态快照**：每次超级步后推送完整 State，适合状态面板
2. **updates = 增量更新**：只推送节点返回值，适合带宽敏感场景
3. **messages = token 级流式**：LLM 每生成一个 token 就推送，适合打字机效果
4. **custom = 自定义事件**：Node 内通过 writer() 主动推送，适合进度条
5. **tasks = 任务生命周期**：自动追踪节点 start/finish，适合监控
6. **checkpoints = 检查点事件**：用于状态恢复调试
7. **debug = 组合调试**：checkpoints + tasks，数据量最大
8. **多 Agent 嵌套**：设置 subgraphs=True 接收子图事件，通过 ns 区分来源
9. **组合使用**：stream_mode=["messages", "custom"] 可同时实现打字机+进度条

### Stream Mode 选型决策树

```
你需要什么样的实时反馈？
|
|-- 需要看 LLM 逐字生成？
|   └─ messages ✅
|
|-- 需要显示进度百分比？
|   └─ custom ✅（Node 内 writer 推送）
|
|-- 需要知道节点什么时候开始/结束？
|   └─ tasks ✅
|
|-- 需要显示当前 State 全貌？
|   └─ values ✅
|
|-- 只需要增量数据，省带宽？
|   └─ updates ✅
|
└-- 多种需求都要？
    └─ stream_mode=["messages", "custom", "tasks"] ✅
```

### 记忆口诀

> **values 看全局，updates 看变化，messages 看逐字，custom 看进度，tasks 看生命周期，subgraphs=True 看嵌套。**

---

## 17. Cheat Sheet（速查表）

```python
# ===== 基础用法 =====

# 1. values - 完整状态
async for chunk in graph.astream(input, stream_mode="values"):
    state = chunk["data"]  # 完整 State

# 2. updates - 增量更新
async for chunk in graph.astream(input, stream_mode="updates"):
    update = chunk["data"]  # {node_name: node_output}

# 3. messages - Token 级流式
async for chunk in graph.astream(input, stream_mode="messages"):
    msg, metadata = chunk["data"]
    token = msg.content
    node = metadata["langgraph_node"]

# 4. custom - 自定义事件（Node 内）
def my_node(state, writer):  # writer 自动注入
    writer({"type": "progress", "percent": 50})
    return {...}

async for chunk in graph.astream(input, stream_mode="custom"):
    event = chunk["data"]

# 5. tasks - 任务生命周期
async for chunk in graph.astream(input, stream_mode="tasks"):
    data = chunk["data"]
    if "result" not in data:
        print(f"开始: {data['name']}")  # Task Start
    else:
        print(f"完成: {data['name']}, 错误: {data['error']}")  # Task Finish

# ===== 组合用法 =====

# 组合多种模式
async for mode, chunk in graph.astream(
    input,
    stream_mode=["messages", "custom", "tasks"]
):
    if mode == "messages":
        # 处理 token
        pass
    elif mode == "custom":
        # 处理进度
        pass

# 子图事件（必须设置 subgraphs=True）
async for chunk in graph.astream(
    input,
    stream_mode="values",
    subgraphs=True  # 关键！
):
    ns = chunk["ns"]  # () = 顶层, ("sub",) = 子图

# ===== 前端协议 =====

# 三段式消息信封
{
    "message_type": "content",      # content/thinking/tool_call/error/...
    "content": "文本内容",
    "status": "processing",         # start / processing / end
    "message_id": "msg_abc123",
    "node_name": "writer",
    "agent_hierarchy": [],
}
```

---

## 18. 课后练习

### 练习 1：组合 values + custom 模式

构建一个带进度条的写作助手，同时显示完整状态和进度百分比。

```python
# 提示: stream_mode=["values", "custom"]
# 需要解包 (mode, chunk) 元组
```

### 练习 2：使用 astream_events 统计节点耗时

使用 astream_events(version="v2") 捕获 on_node_start 和 on_node_end 事件，计算每个节点的执行时长。

### 练习 3：实现 token 级打字机效果

接入真实 LLM API（如 OpenAI），实现 ChatGPT 风格的打字机效果。

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(model="gpt-4", streaming=True)
# 在图中使用 LLM 节点，然后用 stream_mode="messages" 消费
```

### 练习 4：多 Agent 嵌套事件处理

使用 create_supervisor 构建一个包含多个子 Agent 的系统，设置 subgraphs=True，根据 ns 字段区分事件来源并分别处理。

### 练习 5：SSE 后端实现

用 FastAPI 实现一个 SSE 端点，将 LangGraph 的流式输出转发到前端。

---

**下一节**: LG-08 多智能体系统与复杂工作流 -- DeepResearch Agent
