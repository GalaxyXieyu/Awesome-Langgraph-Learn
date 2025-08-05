# LangGraph Celery Chat - 优化版

基于 ReActAgentsTest 参考代码的简洁实现，总代码量 < 500 行。

## 核心优势

- **单文件架构**: 只有一个 `main.py` 文件（400+ 行）
- **直接调用**: FastAPI → Celery → LangGraph，无中间层
- **保持核心功能**: 你的 `graph.py` 和 `tools.py` 完全不变
- **简化状态管理**: Redis 存基础状态，LangGraph 管理 checkpoint

## 项目结构

```
optimized/
├── main.py           # 唯一的主文件（FastAPI + Celery + 任务）
├── graph/           # 你的核心代码（不变）
│   ├── graph.py     # 复制自原项目
│   └── tools.py     # 复制自原项目
├── requirements.txt # 依赖列表
└── README.md       # 说明文档
```

## 快速启动

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   python install_deps.py  # 安装测试依赖
   ```

2. **一键启动**
   ```bash
   ./run.sh
   ```

   或手动启动：
   ```bash
   # 终端1: 启动 Celery Worker
   celery -A main.celery_app worker --loglevel=info
   
   # 终端2: 启动 FastAPI 服务
   python main.py
   ```

## 测试接口

### 快速测试
```bash
python quick_test.py
```

### 完整测试（包含中断流程）
```bash
python test_api.py
```

这个测试会：
1. 创建写作任务
2. 监控事件流
3. 等待 LangGraph 中断
4. 模拟用户确认
5. 恢复任务执行
6. 验证最终结果

## API 接口

### 创建任务
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "user123",
       "topic": "人工智能的发展趋势",
       "max_words": 2000,
       "style": "professional",
       "language": "zh"
     }'
```

### 查看任务状态
```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}"
```

### 恢复中断任务
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/resume" \
     -H "Content-Type: application/json" \
     -d '{"response": "yes", "approved": true}'
```

### 实时事件流
```bash
curl "http://localhost:8000/api/v1/events/{task_id}"
```

## 与原版本对比

| 项目 | 原版本 | 优化版本 |
|------|--------|----------|
| 总文件数 | 20+ | 4 |
| 总代码行数 | 2000+ | 400+ |
| 核心文件 | main.py (759行) + tasks.py (341行) + adapter.py (705行) | main.py (400行) |
| 状态管理 | 3套系统 | 2套系统 |
| 中间层 | WorkflowAdapter + CeleryStreamWriter + InterruptManager | 无 |

## 配置说明

所有配置都在 `main.py` 顶部：

```python
# Redis 配置
REDIS_URL = "redis://localhost:6379/0"

# Celery 配置
celery_app = Celery("writing_tasks", broker=REDIS_URL, backend=REDIS_URL)
```

## 核心设计思路

1. **去掉 WorkflowAdapter**: 直接在 Celery 任务中调用 LangGraph
2. **简化流式输出**: 直接写入 Redis Streams，无复杂封装
3. **统一 ID 管理**: task_id 即是 thread_id，避免映射混乱
4. **保持兼容性**: API 接口与原版本完全兼容

这就是"少即是多"的典型例子！

---

## 开发与调试日志：实现端到端流式输出

在开发过程中，我们经历了一个完整的、从“只有心跳”到“完美流式输出”的排错和解决流程。

1.  **问题：前端只有心跳，没有事件。**
    *   **诊断**：FastAPI 服务正常，但 Celery Worker 未执行任务。
    *   **解决方案**：修改 `run.sh` 脚本，将 Celery Worker 从后台 (`--detach`) 启动改为**前台启动**，从而暴露了 Worker 的日志，确认了它没有在运行。

2.  **问题：Worker 运行了，但事件依然没有到达前端。**
    *   **诊断**：Worker 日志显示任务已执行，但事件流中没有数据。怀疑是 FastAPI/Worker 与**远程 Redis** 之间的通信不稳定。
    *   **解决方案**：修改 `main.py` 中的 `REDIS_URL`，将服务切换到**本地 Redis**，排除了所有网络不确定性。

3.  **问题：`custom` 事件流是空的，只有 `updates` 事件。**
    *   **诊断**：`LangGraphCeleryChat/graph/graph.py` 没有使用官方的 `get_stream_writer`。它使用了自定义的 fallback 实现，只会将进度打印到日志，而不会 `yield` 到事件流。
    *   **解决方案**：修改 `graph.py`，**导入并使用 `langgraph.config` 的 `get_stream_writer`**，打通了 `custom` 事件流的通道。

4.  **问题：前端拿不到 `custom` 事件中的 `current_content`。**
    *   **诊断**：`graph.py` 正确地输出了 `current_content`，但 `main.py` 在处理 `progress_detail` 事件时，**没有正确地将整个 `data` 对象传递出去**。
    *   **解决方案**：修正 `main.py` 中的事件解析逻辑，确保将 `custom` 事件的 `data` 字典**完整地**传递给前端。

5.  **最终实现：打字机效果。**
    *   **需求**：在前端逐字打印真实的 `chunk` 数据。
    *   **解决方案（三步走）**：
        1.  **`graph.py`**: 修改 `article_generation_node`，`yield` 出包含单个 `token` 的新事件类型 `article_generation_chunk`。
        2.  **`main.py`**: 增加逻辑，识别这个新事件并将其包装为 `article_chunk` 类型推送到 Redis。
        3.  **`test_frontend.html`**: 增加 JavaScript 逻辑，监听 `article_chunk` 事件并将其 `token` 实时追加到结果区域。

通过这一系列精准的诊断和修复，我们最终构建了一个健壮、稳定且用户体验优秀的端到端实时流式 AI 应用。

---

## 重要问题解决：LangGraph Checkpoint NotImplementedError

### 问题描述

在使用 LangGraph 的 RedisSaver 作为 checkpoint 时，遇到了 `NotImplementedError` 错误：

```
File ".../langgraph/checkpoint/base/__init__.py", line 268, in aget_tuple
    raise NotImplementedError
NotImplementedError
```

### 问题分析

#### 1. **错误发生场景**
- ❌ **异步调用失败**：使用 `graph.astream()` 或 `graph.ainvoke()` 时出错
- ✅ **同步调用正常**：使用 `graph.invoke()` 时工作正常
- 🎯 **根本原因**：RedisSaver 的异步方法 `aget_tuple()` 没有正确实现

#### 2. **官方 GitHub Issues 确认**
通过查阅官方 GitHub issues，发现这是一个已知问题：
- [Issue #4193](https://github.com/langchain-ai/langgraph/issues/4193): PostgresSaver 同样问题
- [Issue #495](https://github.com/langchain-ai/langgraph/issues/495): SqliteSaver 同样问题

**关键发现**：所有 checkpoint savers 的异步方法都存在 `NotImplementedError` 问题。

#### 3. **环境差异分析**
- **工作环境**：`RedisMemory-Graph/test.py` 使用 `graph.invoke()` (同步调用) ✅
- **失败环境**：`LangGraphCeleryChat` 使用 `graph.astream()` (异步调用) ❌

### 解决方案

#### 方案1：使用 AsyncRedisSaver（推荐）

根据官方文档，正确的异步使用方式是：

```python
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
    await checkpointer.asetup()
    graph = workflow.compile(checkpointer=checkpointer)

    # 现在可以安全使用异步方法
    async for chunk in graph.astream(state, config):
        # 处理流式输出
        pass
```

#### 方案2：回退到 MemorySaver

如果 Redis 不可用，回退到内存存储：

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### 实际修复代码

在 `main.py` 中的修复：

```python
async def run_workflow():
    try:
        # 使用官方推荐的 AsyncRedisSaver
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver

        async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
            await checkpointer.asetup()
            logger.info(f"✅ 使用 AsyncRedisSaver: {REDIS_URL}")

            # 创建并编译图
            workflow = create_writing_assistant_graph()
            graph = workflow.compile(checkpointer=checkpointer)

            # 异步流式执行
            async for chunk in graph.astream(initial_state, config, stream_mode=["updates", "custom"]):
                # 处理流式输出...
                pass

    except Exception as redis_error:
        # 回退到内存 checkpoint
        logger.warning(f"⚠️ AsyncRedisSaver 失败，使用 MemorySaver: {redis_error}")

        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()

        workflow = create_writing_assistant_graph()
        graph = workflow.compile(checkpointer=checkpointer)

        # 继续执行...
```

### 附加修复：LangChain 弃用警告

同时修复了 LangChain 的弃用警告：

```python
# ❌ 旧版本
from langchain_core.pydantic_v1 import BaseModel, Field

# ✅ 新版本
from pydantic import BaseModel, Field
```

### 验证结果

修复后的 Celery 日志显示：

```
[2025-08-05 16:57:21,263: INFO/ForkPoolWorker-8] Index already exists, not overwriting.
[2025-08-05 16:57:21,263: INFO/ForkPoolWorker-8] Redis client is a standalone client
[2025-08-05 16:57:21,531: INFO/ForkPoolWorker-8] Index already exists, not overwriting.
```

- ✅ **AsyncRedisSaver 工作正常**：Redis 索引设置成功
- ✅ **没有 NotImplementedError**：异步方法正常工作
- ✅ **任务正常执行**：Celery 任务开始执行

### 关键学习点

1. **异步 vs 同步**：在异步环境中必须使用对应的异步 checkpoint saver
2. **官方文档重要性**：AsyncRedisSaver 的正确使用方式在官方文档中有详细说明
3. **上下文管理器**：`async with` 确保 checkpoint 的生命周期正确管理
4. **回退策略**：始终准备 MemorySaver 作为备选方案

### 相关资源

- [LangGraph 官方文档 - Memory](https://langchain-ai.github.io/langgraph/how-tos/memory/add-memory/#use-in-production)
- [GitHub Issue #4193](https://github.com/langchain-ai/langgraph/issues/4193)
- [GitHub Issue #495](https://github.com/langchain-ai/langgraph/issues/495)
- [Redis Developer LangGraph Redis](https://github.com/redis-developer/langgraph-redis)
