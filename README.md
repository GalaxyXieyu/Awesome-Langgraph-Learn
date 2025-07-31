# LangGraph智能写作助手系统

## 功能说明书

本系统是一个基于LangGraph构建的智能写作助手，支持人工干预的文章生成工作流。系统通过状态图管理整个写作流程，包括大纲生成、人工确认、文章生成和联网搜索等功能。

### 核心功能
- **智能大纲生成**：根据用户输入的主题自动生成文章大纲
- **人工确认机制**：支持human-in-the-loop，用户可以确认或修改大纲
- **智能文章生成**：使用create_react_agent生成高质量文章内容
- **联网搜索功能**：集成Tavily搜索工具，支持实时信息获取
- **流式输出**：所有生成过程支持流式返回，提升用户体验
- **状态持久化**：支持checkpointer，可恢复中断的工作流

## 使用方法

### 基本使用
```python
from graph import create_writing_assistant_graph, initialize_writing_state

# 创建图实例
graph = create_writing_assistant_graph()

# 初始化写作状态
initial_state = initialize_writing_state(
    topic="人工智能的发展趋势",
    user_id="user123",
    max_words=1000,
    style="formal",
    language="zh",
    enable_search=True
)

# 配置会话
config = {"configurable": {"thread_id": "writing_session_1"}}

# 流式执行 - 观察节点状态更新
for chunk in graph.stream(initial_state, config, stream_mode="updates"):
    print(chunk)
```

### 流式输出模式
LangGraph支持多种流式输出模式，让您实时观察写作过程：

#### 1. updates模式 - 观察节点状态
```python
# 观察每个节点的状态变化
for chunk in graph.stream(initial_state, config, stream_mode="updates"):
    for node_name, node_output in chunk.items():
        print(f"节点: {node_name}")
        print(f"状态: {node_output.get('status', 'processing')}")
```

#### 2. custom模式 - 观察自定义进度
```python
# 观察自定义的进度信息和状态数据
for chunk in graph.stream(initial_state, config, stream_mode="custom"):
    if isinstance(chunk, dict):
        step = chunk.get("step", "")
        progress = chunk.get("progress", 0)
        status = chunk.get("status", "")
        print(f"[{progress}%] {step}: {status}")
```

#### 3. messages模式 - 观察LLM token流
```python
# 观察LLM生成的每个token
for message_chunk, metadata in graph.stream(initial_state, config, stream_mode="messages"):
    if hasattr(message_chunk, 'content') and message_chunk.content:
        print(message_chunk.content, end="", flush=True)
```

#### 4. 多模式组合
```python
# 同时使用多种流式模式
for stream_mode, chunk in graph.stream(
    initial_state,
    config,
    stream_mode=["updates", "custom", "messages"]
):
    print(f"模式: {stream_mode}, 数据: {chunk}")
```

### 人工干预处理
```python
# 支持中断和恢复
for chunk in graph.stream(initial_state, config, stream_mode="updates"):
    for node_name, node_output in chunk.items():
        # 检查是否需要用户确认
        if node_output.get('current_step') == 'awaiting_confirmation':
            user_input = input("请确认大纲 (yes/no): ")
            graph.update_state(config, {"user_confirmation": user_input})

        # 检查是否需要搜索权限
        elif node_output.get('current_step') == 'awaiting_search_permission':
            search_input = input("是否允许联网搜索 (yes/no): ")
            graph.update_state(config, {"search_permission": search_input})
```

### 异步使用
```python
import asyncio

async def async_writing():
    # 异步流式执行
    async for chunk in graph.astream(initial_state, config, stream_mode="custom"):
        print(f"异步数据: {chunk}")

# 运行异步任务
asyncio.run(async_writing())
```

## 参数说明

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| topic | str | 是 | - | 文章主题 |
| user_id | str | 是 | - | 用户标识符 |
| max_words | int | 否 | 1000 | 文章最大字数 |
| style | str | 否 | "formal" | 写作风格 (formal/casual/academic) |
| language | str | 否 | "zh" | 输出语言 (zh/en) |
| enable_search | bool | 否 | True | 是否启用联网搜索 |

## 返回值说明

### 成功返回示例
```python
{
    "status": "completed",
    "outline": {
        "title": "人工智能的发展趋势",
        "sections": [
            {"title": "引言", "content": "..."},
            {"title": "当前发展状况", "content": "..."},
            {"title": "未来趋势预测", "content": "..."},
            {"title": "结论", "content": "..."}
        ]
    },
    "article": "完整的文章内容...",
    "search_results": [
        {"title": "相关搜索结果", "url": "...", "snippet": "..."}
    ],
    "word_count": 1200,
    "generation_time": 45.6
}
```

### 错误返回示例
```python
{
    "status": "error",
    "error_type": "ValidationError",
    "message": "主题不能为空",
    "code": "INVALID_TOPIC"
}
```

## 工作流程图

```
用户输入主题 → 生成大纲 → 人工确认 → 生成文章 → 联网搜索确认 → 完成输出
     ↓           ↓         ↓         ↓           ↓
   验证输入    AI生成    等待确认   React Agent   搜索工具
```

## 环境要求

- Python 3.8+
- LangGraph >= 0.1.0
- LangChain >= 0.1.0
- Tavily API Key
- OpenAI API Key (或其他LLM提供商)

## 安装依赖

```bash
pip install langgraph langchain tavily-python openai
```

## 配置说明

在使用前需要设置以下环境变量：
```bash
export OPENAI_API_KEY="your_openai_api_key"
export TAVILY_API_KEY="your_tavily_api_key"
```
# langgraph_learn
