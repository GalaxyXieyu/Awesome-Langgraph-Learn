# LangGraph Runtime 运行时上下文完整指南

## 概述

LangGraph Runtime 是 LangGraph v0.6.0+ 引入的运行时上下文机制，为 Graph 执行提供统一的环境信息访问接口。它解决了在多个节点、工具和钩子函数之间共享静态配置（如用户ID、数据库连接、API密钥等）的问题。

通过 Runtime，你可以在不污染 State 的情况下，优雅地传递和访问运行环境相关的配置信息。

---

## 核心概念

### 什么是 Runtime？

Runtime 是一个**运行时对象**（`langgraph.runtime.Runtime`），它在 Graph 执行期间自动注入到工具、提示和钩子函数中，提供以下核心能力：

1. **Context（上下文）**：静态配置信息，如用户ID、数据库连接、权限信息等
2. **Store（存储）**：BaseStore 实例，用于长期记忆管理（跨会话数据）
3. **Stream Writer（流写入器）**：用于向"custom"流模式写入自定义事件

### Runtime vs State vs Config

理解三者的区别至关重要：

| 特性 | State | Runtime Context | RunnableConfig |
|------|-------|----------------|----------------|
| **用途** | 会话业务数据 | 运行环境配置 | 执行配置参数 |
| **内容** | 消息、结果、进度 | 用户ID、连接、密钥 | thread_id、metadata |
| **生命周期** | 动态变化 | 静态不变 | 每次调用传入 |
| **持久化** | ✅ 保存到 checkpoint | ❌ 不持久化 | 部分持久化 |
| **可序列化** | ✅ 必须可序列化 | ❌ 可以不可序列化 | ✅ 可序列化 |
| **适用场景** | 对话历史、中间结果 | 数据库连接、API密钥 | 线程ID、用户标识 |

**核心原则**：
- **State** 管理业务逻辑相关的动态数据
- **Runtime Context** 管理基础设施和环境配置
- **RunnableConfig** 管理执行参数和元数据

---

## 使用场景

Runtime 特别适合以下场景：

### 1. **多租户系统**
- 传递用户ID、租户ID
- 实现数据隔离和权限控制
- 跨节点统一访问用户信息

### 2. **数据库连接管理**
- 传递数据库连接池
- 避免在每个节点中重新建立连接
- 统一管理连接生命周期

### 3. **权限和安全**
- 传递用户权限信息
- API 密钥和认证令牌
- 敏感配置信息（不应出现在 State 中）

### 4. **长期记忆管理**
- 访问 Store 进行用户偏好存取
- 跨会话的数据共享
- 语义检索和知识库集成

### 5. **自定义流式输出**
- 向前端推送进度更新
- 工具执行状态通知
- 自定义事件流

---

## 配置与使用

### 基本配置（LangGraph v0.6.0+ 方式）

#### 1. 定义 Context Schema

```python
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class GraphContext:
    """Graph 运行时上下文定义"""
    user_id: str                           # 用户ID（必填）
    db_connection: Optional[Any] = None    # 数据库连接
    user_permissions: list = None          # 用户权限列表
    api_keys: dict = None                  # API密钥字典
    
    def __post_init__(self):
        """初始化默认值"""
        if self.user_permissions is None:
            self.user_permissions = []
        if self.api_keys is None:
            self.api_keys = {}
```

#### 2. 创建 Agent 时指定 Context Schema

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4",
    tools=[search_tool, calculator_tool],
    context_schema=GraphContext,  # 👈 指定 Context Schema
)
```

#### 3. 调用时传入 Context

```python
from src.infrastructure.database.connection_manager import DatabaseManager

# 准备运行时上下文
async with DatabaseManager.get_main_session() as db:
    context = GraphContext(
        user_id="user_123",
        db_connection=db,
        user_permissions=["read", "write"],
        api_keys={"openai": "sk-xxx"}
    )
    
    # 调用 Agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "查询我的数据"}]},
        context=context  # 👈 传入 context
    )
```

---

### 在不同位置访问 Runtime

Runtime 可以在以下位置访问：

#### 1. 在工具（Tools）中访问

```python
from langchain_core.tools import tool
from langgraph.runtime import get_runtime
from src.infrastructure.ai.graph.context import GraphContext

@tool
def query_user_preferences() -> str:
    """查询用户偏好设置"""
    # 获取 Runtime 对象
    runtime = get_runtime(GraphContext)
    
    # 访问用户ID
    user_id = runtime.context.user_id
    
    # 访问数据库连接
    db = runtime.context.db_connection
    
    # 使用 Store 获取长期记忆
    if runtime.store:
        prefs = await runtime.store.aget(
            namespace=("user_prefs", user_id),
            key="report_format"
        )
        if prefs:
            return prefs.value.get("text", "无偏好设置")
    
    return "未找到偏好设置"
```

#### 2. 在提示（Prompt）中访问

```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def personalized_system_prompt(request: ModelRequest) -> str:
    """根据用户信息动态生成系统提示"""
    # 从 Runtime 获取用户信息
    user_id = request.runtime.context.user_id
    permissions = request.runtime.context.user_permissions
    
    # 根据权限生成不同的提示
    if "admin" in permissions:
        return f"你是管理员助手，为用户 {user_id} 提供高级功能支持。"
    else:
        return f"你是普通用户助手，为用户 {user_id} 提供基础功能支持。"

# 应用到 Agent
agent = create_agent(
    model="openai:gpt-4",
    tools=[...],
    middleware=[personalized_system_prompt],
    context_schema=GraphContext
)
```

#### 3. 在 Pre/Post Model Hooks 中访问

```python
from langgraph.runtime import get_runtime

def pre_model_hook(state: State, *, config) -> State:
    """模型调用前的钩子函数"""
    runtime = get_runtime(GraphContext)
    
    # 记录用户操作日志
    logger.info(
        f"User {runtime.context.user_id} is calling model",
        extra={"permissions": runtime.context.user_permissions}
    )
    
    return state

def post_model_hook(state: State, *, config) -> State:
    """模型调用后的钩子函数"""
    runtime = get_runtime(GraphContext)
    
    # 保存对话历史到 Store
    if runtime.store:
        await runtime.store.aput(
            namespace=("chat_history", runtime.context.user_id),
            key=f"conversation_{state.get('thread_id')}",
            value={"messages": state["messages"]}
        )
    
    return state
```

#### 4. 在节点函数中访问（通过 config）

```python
from langchain_core.runnables import RunnableConfig

def my_node(state: State, config: RunnableConfig):
    """节点函数示例"""
    # 通过 config 获取 context 信息
    user_id = config.get("configurable", {}).get("user_id", "anonymous")
    
    # 执行业务逻辑
    result = process_with_user_context(state, user_id)
    
    return {"result": result}
```

---

## 本项目的实现方式

### 当前实现（基于 RunnableConfig）

本项目当前使用 RunnableConfig 传递 user_id，这是一种兼容性更好的方式：

```python
# backend/src/infrastructure/ai/graph/wrapper.py
async def _execute_stream(self, input_data: Dict[str, Any], thread_id: str, user_id: str):
    """流式执行"""
    # 准备配置
    run_config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "user_id": user_id,  # 👈 通过 configurable 传递
        },
        "metadata": {"user_id": user_id, "tags": tags},
    }
    
    # 执行
    stream = app.astream(state, config=run_config, stream_mode=["custom"])
```

在节点中访问：

```python
def my_node(state: State, config: RunnableConfig):
    user_id = config["configurable"]["user_id"]  # 👈 从 config 获取
    # ... 业务逻辑
```

### 升级到 Runtime Context（推荐未来方案）

如果要升级到 Runtime Context 方式，需要进行以下改造：

#### 第一步：创建 Context 定义

```python
# backend/src/infrastructure/ai/graph/context.py
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class AutoAgentsContext:
    """AutoAgents 全局运行时上下文"""
    user_id: str
    # 可以添加更多字段
    tenant_id: Optional[str] = None
    user_permissions: list = None
    
    def __post_init__(self):
        if self.user_permissions is None:
            self.user_permissions = []
```

#### 第二步：修改 GraphWrapper

```python
# backend/src/infrastructure/ai/graph/wrapper.py
async def _execute_stream(self, input_data: Dict[str, Any], thread_id: str, user_id: str):
    """流式执行（使用 Runtime Context）"""
    from src.infrastructure.ai.graph.context import AutoAgentsContext
    
    # 创建 Runtime Context
    context = AutoAgentsContext(user_id=user_id)
    
    run_config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "context": context,  # 👈 传入 context
        "metadata": {"user_id": user_id, "tags": tags},
    }
    
    stream = app.astream(state, config=run_config, stream_mode=["custom"])
```

#### 第三步：在工具中使用

```python
from langgraph.runtime import get_runtime
from src.infrastructure.ai.graph.context import AutoAgentsContext

@tool
def my_tool() -> str:
    runtime = get_runtime(AutoAgentsContext)
    user_id = runtime.context.user_id  # 👈 类型安全的访问
    
    # 访问 Store
    if runtime.store:
        data = await runtime.store.aget(("bucket", user_id), "key")
    
    return f"处理用户 {user_id} 的请求"
```

---

## Runtime Context 常见参数

### Context Schema 常见字段

```python
@dataclass
class ComprehensiveContext:
    """完整的 Context 示例"""
    
    # === 用户信息 ===
    user_id: str                              # 用户唯一标识
    tenant_id: Optional[str] = None           # 租户ID（多租户场景）
    username: Optional[str] = None            # 用户名
    user_email: Optional[str] = None          # 用户邮箱
    
    # === 权限与安全 ===
    user_permissions: list = None             # 用户权限列表
    user_roles: list = None                   # 用户角色列表
    is_admin: bool = False                    # 是否管理员
    
    # === 基础设施 ===
    db_connection: Optional[Any] = None       # 数据库连接
    redis_client: Optional[Any] = None        # Redis 客户端
    milvus_client: Optional[Any] = None       # Milvus 向量库客户端
    
    # === API 密钥 ===
    api_keys: dict = None                     # API密钥字典
    openai_api_key: Optional[str] = None      # OpenAI API Key
    anthropic_api_key: Optional[str] = None   # Anthropic API Key
    
    # === 业务配置 ===
    language: str = "zh-CN"                   # 用户语言偏好
    timezone: str = "Asia/Shanghai"           # 时区
    max_tokens: int = 4000                    # 最大token数
    temperature: float = 0.7                  # 温度参数
    
    # === 会话信息 ===
    session_id: Optional[str] = None          # 会话ID
    request_id: Optional[str] = None          # 请求ID（追踪）
    ip_address: Optional[str] = None          # 用户IP
    
    def __post_init__(self):
        """初始化默认值"""
        if self.user_permissions is None:
            self.user_permissions = []
        if self.user_roles is None:
            self.user_roles = []
        if self.api_keys is None:
            self.api_keys = {}
```

### 使用建议

根据实际需求选择字段：

```python
# 最小化 Context（推荐起点）
@dataclass
class MinimalContext:
    user_id: str

# 多租户场景
@dataclass
class MultiTenantContext:
    user_id: str
    tenant_id: str
    user_permissions: list = None

# 完整功能场景
@dataclass
class FullFeaturedContext:
    user_id: str
    db_connection: Any
    user_permissions: list
    api_keys: dict
    language: str = "zh-CN"
```

---

## 实际案例

### 案例 1：多租户数据隔离

```python
@dataclass
class TenantContext:
    user_id: str
    tenant_id: str
    user_roles: list = None

@tool
def query_tenant_data(query: str) -> str:
    """查询租户数据（自动隔离）"""
    runtime = get_runtime(TenantContext)
    
    user_id = runtime.context.user_id
    tenant_id = runtime.context.tenant_id
    
    # 数据库查询自动带上租户过滤
    async with DatabaseManager.get_main_session() as db:
        result = await db.execute(
            "SELECT * FROM data WHERE tenant_id = :tenant_id AND query = :query",
            {"tenant_id": tenant_id, "query": query}
        )
    
    return f"查询到 {len(result)} 条数据"
```

### 案例 2：权限控制

```python
@tool
def delete_sensitive_data(record_id: str) -> str:
    """删除敏感数据（需要管理员权限）"""
    runtime = get_runtime(GraphContext)
    
    # 检查权限
    if "admin" not in runtime.context.user_permissions:
        raise PermissionError("需要管理员权限")
    
    # 执行删除操作
    db = runtime.context.db_connection
    db.execute("DELETE FROM sensitive_data WHERE id = :id", {"id": record_id})
    
    return f"已删除记录 {record_id}"
```

### 案例 3：用户偏好记忆

```python
@tool
async def remember_user_preference(pref_key: str, pref_value: str) -> str:
    """记住用户偏好"""
    runtime = get_runtime(GraphContext)
    
    if not runtime.store:
        return "Store 未配置"
    
    user_id = runtime.context.user_id
    
    # 保存到 Store
    await runtime.store.aput(
        namespace=("user_prefs", user_id),
        key=pref_key,
        value={"text": pref_value, "timestamp": datetime.now().isoformat()}
    )
    
    return f"已保存偏好：{pref_key} = {pref_value}"

@tool
async def recall_user_preference(pref_key: str) -> str:
    """回忆用户偏好"""
    runtime = get_runtime(GraphContext)
    
    if not runtime.store:
        return "Store 未配置"
    
    user_id = runtime.context.user_id
    
    # 从 Store 读取
    item = await runtime.store.aget(
        namespace=("user_prefs", user_id),
        key=pref_key
    )
    
    if item:
        return item.value.get("text", "无内容")
    return "未找到该偏好"
```

### 案例 4：自定义流式输出

```python
async def processing_node(state: State, *, config):
    """带进度通知的处理节点"""
    runtime = get_runtime(GraphContext)
    
    # 发送开始通知
    if runtime.stream:
        await runtime.stream.awrite({
            "type": "progress",
            "message": "开始处理数据...",
            "progress": 0
        })
    
    # 模拟处理过程
    for i in range(1, 11):
        await asyncio.sleep(0.5)
        
        # 发送进度更新
        if runtime.stream:
            await runtime.stream.awrite({
                "type": "progress",
                "message": f"处理中... {i*10}%",
                "progress": i * 10
            })
    
    # 发送完成通知
    if runtime.stream:
        await runtime.stream.awrite({
            "type": "progress",
            "message": "处理完成！",
            "progress": 100
        })
    
    return {"result": "处理完成"}
```

---

## 最佳实践

### 1. Context 字段选择原则

```python
# ✅ 好的做法：只放运行时不变的配置
@dataclass
class GoodContext:
    user_id: str              # 用户ID
    db_connection: Any        # 数据库连接
    api_key: str              # API密钥

# ❌ 不好的做法：放入会变化的业务数据
@dataclass
class BadContext:
    user_id: str
    current_question: str     # 会变化，应该在 State 中
    intermediate_result: str  # 会变化，应该在 State 中
    message_count: int        # 会变化，应该在 State 中
```

### 2. 敏感信息处理

```python
@dataclass
class SecureContext:
    user_id: str
    api_keys: dict  # 不会被序列化到 checkpoint
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """安全获取API密钥"""
        return self.api_keys.get(provider)
    
    def __repr__(self):
        """避免日志中泄露密钥"""
        return f"SecureContext(user_id={self.user_id}, api_keys=***)"
```

### 3. 懒加载资源

```python
@dataclass
class LazyContext:
    user_id: str
    _db_connection: Optional[Any] = None
    
    @property
    def db_connection(self) -> Any:
        """懒加载数据库连接"""
        if self._db_connection is None:
            self._db_connection = create_db_connection()
        return self._db_connection
```

### 4. 类型安全访问

```python
from typing import TypeVar, Type

T = TypeVar('T')

def safe_get_runtime(context_type: Type[T]) -> T:
    """类型安全的 Runtime 获取"""
    try:
        return get_runtime(context_type)
    except Exception as e:
        logger.error(f"获取 Runtime 失败: {e}")
        # 返回默认 Context
        return context_type(user_id="anonymous")
```

---

## 与其他机制的对比

### Runtime Context vs State

```python
# State：动态的业务数据
class MyState(TypedDict):
    messages: list[BaseMessage]   # 对话历史
    current_step: str             # 当前步骤
    intermediate_results: dict    # 中间结果
    errors: list[str]             # 错误列表

# Runtime Context：静态的环境配置
@dataclass
class MyContext:
    user_id: str                  # 用户ID
    db_connection: Any            # 数据库连接
    user_permissions: list        # 用户权限
```

### Runtime Context vs RunnableConfig

```python
# RunnableConfig：执行参数
config = {
    "configurable": {
        "thread_id": "session_123",   # 线程ID
        "user_id": "user_456",        # 用户标识
    },
    "metadata": {
        "tags": ["production"],       # 标签
    }
}

# Runtime Context：结构化的环境信息
context = GraphContext(
    user_id="user_456",
    db_connection=db,
    user_permissions=["read", "write"]
)
```

**建议**：
- RunnableConfig 适合传递简单的标识符和元数据
- Runtime Context 适合传递复杂的对象和配置

---

## 迁移指南

### 从 RunnableConfig 迁移到 Runtime Context

#### 迁移前（当前方式）

```python
# 传递方式
run_config = {
    "configurable": {
        "user_id": user_id,
        "tenant_id": tenant_id,
    }
}

# 访问方式
def node(state, config):
    user_id = config["configurable"]["user_id"]
    tenant_id = config["configurable"]["tenant_id"]
```

#### 迁移后（Runtime 方式）

```python
# 传递方式
context = GraphContext(user_id=user_id, tenant_id=tenant_id)
run_config = {"context": context}

# 访问方式
@tool
def my_tool():
    runtime = get_runtime(GraphContext)
    user_id = runtime.context.user_id      # 类型安全
    tenant_id = runtime.context.tenant_id  # 自动补全
```

#### 渐进式迁移策略

```python
# 同时支持两种方式（过渡期）
def hybrid_node(state, config):
    # 优先使用 Runtime
    try:
        runtime = get_runtime(GraphContext)
        user_id = runtime.context.user_id
    except:
        # 降级到 config
        user_id = config["configurable"]["user_id"]
    
    # 业务逻辑...
```

---

## 常见问题与排查

### Q1: 为什么需要 Runtime Context？

**A**: 三个主要原因：
1. **关注点分离**：State 只关注业务数据，Context 管理环境配置
2. **类型安全**：通过 dataclass 提供类型检查和自动补全
3. **安全性**：Context 不会被序列化到 checkpoint，适合存放敏感信息

### Q2: Runtime Context 会被持久化吗？

**A**: **不会**。Runtime Context 只在当前执行期间存在，不会保存到数据库。这正是它的优势——可以安全地存放数据库连接、API密钥等不可序列化的对象。

### Q3: 如何在非工具函数中访问 Runtime？

**A**: 使用 `get_runtime()` 函数：

```python
from langgraph.runtime import get_runtime

def anywhere_in_code():
    runtime = get_runtime(GraphContext)
    user_id = runtime.context.user_id
```

### Q4: Runtime 和 Store 的关系？

**A**: Runtime 提供对 Store 的访问接口：

```python
runtime = get_runtime(GraphContext)
if runtime.store:
    data = await runtime.store.aget(namespace, key)
```

Store 需要在编译时注入：
```python
graph = builder.compile(
    checkpointer=saver,
    store=store  # 👈 注入 Store
)
```

### Q5: 本项目是否需要升级到 Runtime Context？

**A**: **短期不需要**。当前基于 RunnableConfig 的方式已经足够且稳定。

**建议升级时机**：
- 需要传递复杂对象（如数据库连接）
- 需要类型安全和IDE自动补全
- 团队熟悉 LangGraph v0.6.0+ 新特性

---

## 总结

LangGraph Runtime 提供了优雅的运行时上下文管理机制：

✅ **清晰的关注点分离**：State 管业务，Context 管环境  
✅ **类型安全**：通过 dataclass 实现强类型和自动补全  
✅ **安全性**：敏感信息不会被持久化  
✅ **统一访问**：在工具、提示、钩子中一致的访问方式  
✅ **Store 集成**：方便访问长期记忆  

**核心要点**：
- 使用 `context_schema` 定义 Context 结构
- 调用时通过 `context=...` 传入
- 在工具/提示/钩子中通过 `get_runtime()` 访问
- Context 不会被序列化，适合存放连接和密钥
- 与 State 和 RunnableConfig 各司其职

---

## 官方参考

- **Runtime 参考文档**：https://langchain-ai.github.io/langgraph/reference/runtime/
- **LangChain Runtime 指南**：https://docs.langchain.com/oss/python/langchain/runtime
- **创建 Agent 文档**：https://docs.langchain.com/oss/python/langgraph/overview

---

## 本项目集成建议

### 短期方案（继续使用 RunnableConfig）

```python
# 当前实现已经很好，无需修改
run_config = {
    "configurable": {
        "thread_id": thread_id,
        "user_id": user_id,
    }
}
```

### 长期方案（升级到 Runtime Context）

```python
# 1. 创建 Context 定义
# backend/src/infrastructure/ai/graph/context.py
@dataclass
class AutoAgentsContext:
    user_id: str
    tenant_id: Optional[str] = None

# 2. 修改 GraphWrapper 注入 Context
context = AutoAgentsContext(user_id=user_id)
run_config = {"context": context}

# 3. 在工具中使用
@tool
def my_tool():
    runtime = get_runtime(AutoAgentsContext)
    user_id = runtime.context.user_id
```

---

**最后提醒**：Runtime Context 是可选的高级特性，当前基于 config 的方式已经满足大多数需求。建议在团队熟悉后再考虑迁移。
