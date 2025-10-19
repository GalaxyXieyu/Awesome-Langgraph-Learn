# LangGraph Cache 缓存机制完整指南

## 概述

LangGraph 的缓存（Cache）机制是一个强大的性能优化工具，允许你缓存节点（Node）的计算结果，避免重复执行耗时或昂贵的操作。通过合理使用缓存，可以显著提升应用的响应速度并降低 API 调用成本。

LangGraph 支持两种主要的缓存类型：
- **节点级缓存（Node-level Caching）**：缓存特定节点的执行结果
- **LLM 调用缓存（LLM Call Caching）**：缓存大语言模型的调用结果

本文档主要关注 LangGraph 的节点级缓存机制。

---

## 核心概念

### 什么是节点级缓存？

节点级缓存（Node-level Caching）是 LangGraph 提供的一种机制，它可以基于节点的**输入**来缓存节点的执行结果。当相同的输入再次传入该节点时，LangGraph 会直接从缓存中返回结果，而不是重新执行节点函数。

### 工作原理

1. **缓存键生成**：根据节点的输入（state）生成缓存键（默认使用输入的哈希值）
2. **缓存查找**：执行节点前，先检查缓存中是否存在对应的结果
3. **缓存命中**：如果找到缓存，直接返回缓存结果
4. **缓存未命中**：如果未找到缓存，执行节点函数，并将结果存入缓存
5. **缓存过期**：根据配置的 TTL（Time To Live）自动清理过期缓存

---

## 使用场景

节点级缓存特别适合以下场景：

### 1. **耗时的计算操作**
- 复杂的数据处理和分析
- 大规模数据查询
- 机器学习模型推理

### 2. **昂贵的 API 调用**
- 第三方服务调用（计费 API）
- 大语言模型（LLM）调用
- 数据库密集型查询

### 3. **重复性高的操作**
- 相同参数的重复查询
- 静态数据的获取
- 配置信息的加载

### 4. **开发和测试环境**
- 加速开发调试流程
- 减少测试环境的 API 成本
- 提高单元测试执行效率

---

## 配置与使用

### 基本配置

#### 1. 导入必要的模块

```python
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver  # 内存缓存
from langgraph.types import CachePolicy
from typing_extensions import TypedDict
```

#### 2. 定义 State

```python
class State(TypedDict):
    items: list[str]
    result: str
```

#### 3. 配置缓存策略并添加节点

```python
# 创建缓存实例
cache = MemorySaver()

# 创建图构建器
builder = StateGraph(State)

# 定义节点函数（模拟耗时操作）
def expensive_operation(state: State):
    """模拟一个耗时 3 秒的操作"""
    import time
    time.sleep(3)
    return {"result": "处理完成", "items": state["items"] + ["新项目"]}

# 添加带缓存策略的节点
builder.add_node(
    "expensive_node",
    expensive_operation,
    cache_policy=CachePolicy(ttl=120)  # TTL 为 120 秒
)

# 添加边
builder.add_edge(START, "expensive_node")

# 编译图并传入缓存
graph = builder.compile(cache=cache)
```

#### 4. 执行图

```python
import time

# 第一次执行（缓存未命中，耗时约 3 秒）
start = time.time()
result1 = graph.invoke({"items": ["项目1"]})
print(f"第一次执行耗时: {time.time() - start:.2f}秒")
# 输出: 第一次执行耗时: 3.01秒

# 第二次执行（缓存命中，几乎瞬间返回）
start = time.time()
result2 = graph.invoke({"items": ["项目1"]})
print(f"第二次执行耗时: {time.time() - start:.4f}秒")
# 输出: 第二次执行耗时: 0.0050秒
```

---

### 高级配置

#### 自定义缓存键函数（key_func）

有时你可能需要自定义缓存键的生成逻辑，例如：
- 忽略某些不重要的字段（如随机 ID、时间戳）
- 基于特定字段生成缓存键
- 实现语义相似性缓存

```python
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage

def custom_key_func(args):
    """
    自定义缓存键函数
    只基于消息内容和位置生成缓存键，忽略消息 ID
    """
    state = args[0]  # 第一个参数是 state
    messages = state.get("messages", [])
    
    # 基于消息内容和索引生成键
    key_parts = []
    for idx, msg in enumerate(messages):
        if isinstance(msg, BaseMessage):
            key_parts.append(f"{idx}:{msg.content}")
        else:
            key_parts.append(f"{idx}:{msg}")
    
    import json
    return json.dumps(key_parts)

# 使用自定义缓存键函数
builder.add_node(
    "smart_node",
    node_function,
    cache_policy=CachePolicy(
        ttl=300,  # 5 分钟
        key_func=custom_key_func
    )
)
```

#### 不同的缓存后端

LangGraph 支持多种缓存后端：

##### 1. 内存缓存（MemorySaver）

适合开发和测试环境，进程重启后缓存丢失。

```python
from langgraph.checkpoint.memory import MemorySaver

cache = MemorySaver()
graph = builder.compile(cache=cache)
```

##### 2. Redis 缓存

适合生产环境，支持分布式部署和持久化。

```python
from langgraph_checkpoint_redis import RedisSaver
from redis import Redis

# 连接 Redis
redis_client = Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# 创建 Redis 缓存
cache = RedisSaver(redis_client)
graph = builder.compile(cache=cache)
```

##### 3. PostgreSQL 缓存

适合已使用 PostgreSQL 的应用，与数据库集成更紧密。

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 创建 PostgreSQL 连接
connection_string = "postgresql://user:password@localhost:5432/dbname"
cache = PostgresSaver.from_conn_string(connection_string)

graph = builder.compile(cache=cache)
```

---

## CachePolicy 参数详解

`CachePolicy` 类用于配置节点的缓存策略，主要参数如下：

### ttl（Time To Live）- 缓存生存时间详解

#### 什么是 TTL？

**TTL（Time To Live，生存时间）** 是缓存数据的"保质期"。就像食品有保质期一样，缓存数据也需要设置一个有效期限。

- **类型**：`int`（秒）或 `None`
- **单位**：秒（seconds）
- **默认值**：`None`（永不过期，不推荐）

#### TTL 的工作原理

```python
import time
from datetime import datetime, timedelta

# 当你设置 TTL = 300（5分钟）时：
cache_policy = CachePolicy(ttl=300)

# LangGraph 会这样处理：
created_at = datetime.now()  # 假设：2025-10-13 14:00:00
expires_at = created_at + timedelta(seconds=300)  # 过期时间：2025-10-13 14:05:00

# 存储到数据库时：
cache_record = {
    "timestamp": "2025-10-13 14:00:00",
    "expires_at": "2025-10-13 14:05:00",  # 5分钟后过期
    "result": "缓存的结果"
}

# 读取缓存时检查：
if datetime.now() < expires_at:  # 当前时间 < 过期时间
    return "缓存有效！返回缓存结果"
else:
    return "缓存已过期！需要重新执行"
```

#### TTL 设置建议

```python
# 实时数据（几乎不缓存）
CachePolicy(ttl=30)      # 30 秒 - 股票价格、实时天气

# 短期缓存
CachePolicy(ttl=300)     # 5 分钟 - 用户在线状态、简单查询
CachePolicy(ttl=600)     # 10 分钟 - 数据库查询结果

# 中期缓存  
CachePolicy(ttl=1800)    # 30 分钟 - LLM 对话结果
CachePolicy(ttl=3600)    # 1 小时 - 文章列表、商品信息

# 长期缓存
CachePolicy(ttl=86400)   # 24 小时 - 配置信息、静态数据
CachePolicy(ttl=604800)  # 7 天 - 历史数据、归档信息

# 永久缓存（慎用！）
CachePolicy(ttl=None)    # 永不过期 - 仅用于完全不变的数据
```

#### TTL 计算助手

```python
# 便捷的时间计算
from datetime import timedelta

def calculate_ttl(**kwargs):
    """
    便捷计算 TTL 秒数
    
    示例：
        calculate_ttl(minutes=5)  # 300 秒
        calculate_ttl(hours=2)    # 7200 秒
        calculate_ttl(days=1)     # 86400 秒
    """
    delta = timedelta(**kwargs)
    return int(delta.total_seconds())

# 使用示例
CachePolicy(ttl=calculate_ttl(minutes=30))  # 30 分钟
CachePolicy(ttl=calculate_ttl(hours=2))     # 2 小时
CachePolicy(ttl=calculate_ttl(days=1))      # 1 天
```

### key_func（缓存键生成函数）

- **类型**：`Callable`
- **说明**：自定义缓存键生成逻辑
- **默认值**：使用输入的哈希值

```python
def my_key_func(args):
    state = args[0]
    # 只基于特定字段生成键
    return f"{state['user_id']}:{state['query']}"

CachePolicy(ttl=300, key_func=my_key_func)
```

---

## 最佳实践

### 1. 合理设置 TTL

```python
# 静态数据：长 TTL
CachePolicy(ttl=86400)  # 24 小时

# 半静态数据：中等 TTL
CachePolicy(ttl=3600)   # 1 小时

# 动态数据：短 TTL
CachePolicy(ttl=300)    # 5 分钟

# 实时数据：不缓存或极短 TTL
CachePolicy(ttl=30)     # 30 秒
```

### 2. 选择合适的缓存后端

| 场景 | 推荐缓存后端 | 原因 |
|------|------------|------|
| 本地开发 | MemorySaver | 简单快速 |
| 生产环境（单机） | PostgresSaver | 持久化，与主数据库集成 |
| 生产环境（分布式） | RedisSaver | 支持集群，高性能 |
| 测试环境 | MemorySaver | 快速清理，隔离性好 |

### 3. 避免缓存的场景

以下场景**不建议**使用缓存：

- 包含随机性的操作（如生成随机数、UUID）
- 依赖当前时间的计算
- 有副作用的操作（如数据库写入、文件修改）
- 用户特定的敏感操作（需要实时权限检查）

### 4. 监控缓存性能

```python
import time
import logging

def monitored_node(state):
    start = time.time()
    # 执行实际逻辑
    result = expensive_operation(state)
    duration = time.time() - start
    
    logging.info(f"节点执行耗时: {duration:.4f}秒")
    return result
```

### 5. 缓存失效策略

```python
from datetime import datetime

def cache_key_with_version(args):
    """带版本号的缓存键，方便强制刷新"""
    state = args[0]
    version = "v1.0.0"  # 修改版本号可强制刷新所有缓存
    return f"{version}:{hash(str(state))}"

CachePolicy(ttl=3600, key_func=cache_key_with_version)
```

---

## 实际案例

### 案例 1：缓存 LLM 调用

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.types import CachePolicy
from langgraph.checkpoint.memory import MemorySaver

# 定义带 LLM 的节点
def llm_node(state: MessagesState):
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 构建图
builder = StateGraph(MessagesState)
builder.add_node(
    "llm_call",
    llm_node,
    cache_policy=CachePolicy(
        ttl=1800,  # 30 分钟
        key_func=lambda args: str(args[0]["messages"][-1].content)
    )
)
builder.add_edge(START, "llm_call")

graph = builder.compile(cache=MemorySaver())

# 第一次调用（实际调用 API）
result1 = graph.invoke({"messages": [("user", "什么是 LangGraph？")]})

# 第二次调用（从缓存返回，节省费用）
result2 = graph.invoke({"messages": [("user", "什么是 LangGraph？")]})
```

### 案例 2：缓存数据库查询

```python
def database_query_node(state):
    """模拟数据库查询"""
    import psycopg2
    conn = psycopg2.connect("dbname=mydb")
    cursor = conn.cursor()
    
    query = state["query"]
    cursor.execute(query)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {"results": results}

# 添加缓存策略
builder.add_node(
    "db_query",
    database_query_node,
    cache_policy=CachePolicy(
        ttl=600,  # 10 分钟
        key_func=lambda args: args[0]["query"]  # 基于 SQL 查询缓存
    )
)
```

### 案例 3：条件性缓存

```python
def conditional_cache_key(args):
    """
    条件性缓存：只对特定类型的请求启用缓存
    """
    state = args[0]
    
    # 对只读操作启用缓存
    if state.get("operation") == "read":
        return f"read:{state['query']}"
    
    # 对写操作返回唯一键（不会命中缓存）
    import uuid
    return str(uuid.uuid4())

CachePolicy(ttl=300, key_func=conditional_cache_key)
```

---

## 与 LangChain LLM Cache 的区别

LangGraph 的节点级缓存与 LangChain 的 LLM Cache 是不同的：

| 特性 | LangGraph Node Cache | LangChain LLM Cache |
|------|---------------------|---------------------|
| 缓存粒度 | 节点级别 | LLM 调用级别 |
| 配置位置 | 图编译时 | 全局设置 |
| 缓存内容 | 整个节点的输出 | LLM 响应 |
| 适用范围 | 任何节点函数 | 仅 LLM 调用 |
| TTL 支持 | ✅ | ✅ |
| 自定义键 | ✅ | 部分支持 |

两者可以结合使用：

```python
from langchain.globals import set_llm_cache
from langchain_community.cache import RedisCache

# 设置 LangChain 的 LLM 缓存
set_llm_cache(RedisCache(redis_=redis_client))

# 同时使用 LangGraph 的节点缓存
graph = builder.compile(cache=MemorySaver())
```

---

## 缓存自动删除机制详解

### 什么节点会被自动删除？

并不是"节点"被删除，而是**节点的缓存结果**会被自动删除。具体来说：

#### 1. **过期的缓存记录**

当缓存的 TTL 时间到期后，该缓存记录会被标记为"已过期"并在后续被删除。

```python
# 例子：设置 TTL = 300 秒（5 分钟）
builder.add_node(
    "weather_node",
    get_weather_function,
    cache_policy=CachePolicy(ttl=300)  # 5 分钟后过期
)

# 时间线：
# 14:00:00 - 第一次执行，缓存结果，expires_at = 14:05:00
# 14:03:00 - 第二次执行，缓存未过期，直接返回缓存
# 14:06:00 - 第三次执行，缓存已过期，重新执行并更新缓存
#            旧的缓存记录会被删除或覆盖
```

#### 2. **被覆盖的缓存记录**

当相同的输入再次执行时，新的结果会覆盖旧的缓存。

```python
# PostgreSQL 中的 UPSERT 操作
INSERT INTO checkpoints (...)
VALUES (...)
ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id)
DO UPDATE SET  -- 覆盖旧记录
    checkpoint = EXCLUDED.checkpoint,
    metadata = EXCLUDED.metadata;
```

---

### 什么时候会自动执行删除？

缓存删除有 **3 种触发时机**：

#### 触发时机 1：读取时检查（惰性删除）

```python
# 每次读取缓存时都会检查是否过期
async def check_cache(cache_key, node_name):
    # 从数据库读取缓存
    record = await db.query(
        "SELECT * FROM checkpoints WHERE thread_id = %s",
        f"cache_{cache_key}"
    )
    
    if record:
        expires_at = record['metadata']['expires_at']
        
        # 检查是否过期
        if datetime.now() > datetime.fromisoformat(expires_at):
            # ✅ 发现过期，立即删除
            await db.execute(
                "DELETE FROM checkpoints WHERE thread_id = %s",
                f"cache_{cache_key}"
            )
            return None  # 返回空，触发重新执行
        
        return record['checkpoint']['result']  # 返回缓存
    
    return None
```

**特点**：
- 只在访问时检查
- 不会主动扫描所有缓存
- 性能开销小

#### 触发时机 2：定期清理任务（主动删除）

```python
import asyncio
from datetime import datetime

async def scheduled_cache_cleanup(saver, interval_seconds=3600):
    """
    定期清理过期缓存
    默认每小时执行一次
    """
    while True:
        print(f"🧹 开始清理过期缓存 - {datetime.now()}")
        
        # 批量删除所有过期记录
        result = await saver.conn.execute("""
            DELETE FROM checkpoints 
            WHERE checkpoint_ns = 'node_cache'
              AND (metadata->>'expires_at')::timestamp < NOW()
        """)
        
        deleted_count = result.split()[-1]  # 提取删除数量
        print(f"✅ 清理完成，删除了 {deleted_count} 条过期缓存")
        
        # 等待下次清理
        await asyncio.sleep(interval_seconds)

# 启动清理任务（在后台运行）
asyncio.create_task(scheduled_cache_cleanup(saver, interval_seconds=3600))
```

**特点**：
- 定期扫描所有缓存
- 批量删除过期记录
- 防止数据库膨胀

#### 触发时机 3：写入时覆盖（更新删除）

```python
# 当新的执行结果产生时
async def store_cache(cache_key, node_name, new_result):
    # 使用 UPSERT 操作
    await db.execute("""
        INSERT INTO checkpoints (
            thread_id, checkpoint_ns, checkpoint_id,
            checkpoint, metadata
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id)
        DO UPDATE SET
            checkpoint = EXCLUDED.checkpoint,  -- 新结果覆盖旧结果
            metadata = EXCLUDED.metadata       -- 新的过期时间
    """, ...)
    
    # 结果：旧缓存被"覆盖删除"
```

**特点**：
- 相同输入产生新结果时触发
- 旧数据被新数据替换
- 自动更新过期时间

---

### 完整的删除流程图

```mermaid
graph TB
    A[节点执行] --> B{检查缓存}
    B -->|缓存存在| C{检查TTL}
    C -->|未过期| D[返回缓存结果]
    C -->|已过期| E[删除过期缓存]
    E --> F[重新执行节点]
    B -->|缓存不存在| F
    F --> G[存储新缓存]
    G --> H[设置过期时间]
    
    I[定期清理任务] --> J[扫描所有缓存]
    J --> K{检查过期时间}
    K -->|已过期| L[批量删除]
    K -->|未过期| M[保留]
    L --> N[下次清理]
    M --> N
```

---

### 实际删除示例

#### 示例 1：TTL 过期自动删除

```python
from langgraph.types import CachePolicy
import time

# 设置 10 秒 TTL 的缓存
builder.add_node(
    "quick_cache_node",
    expensive_function,
    cache_policy=CachePolicy(ttl=10)  # 10 秒过期
)

graph = builder.compile(cache=saver)

# 第一次执行
print("⏰ 14:00:00 - 第一次执行")
result1 = graph.invoke({"query": "test"})
print(f"结果: {result1}")
# 缓存创建：expires_at = 14:00:10

# 5 秒后执行
time.sleep(5)
print("\n⏰ 14:00:05 - 第二次执行（缓存有效）")
result2 = graph.invoke({"query": "test"})
print(f"✅ 从缓存返回: {result2}")
# 缓存仍然有效

# 再等 6 秒（总共 11 秒）
time.sleep(6)
print("\n⏰ 14:00:11 - 第三次执行（缓存过期）")
result3 = graph.invoke({"query": "test"})
print(f"❌ 缓存已过期，重新执行: {result3}")
# 旧缓存被删除，创建新缓存：expires_at = 14:00:21
```

#### 示例 2：手动清理过期缓存

```python
# 立即清理所有过期缓存
async def manual_cleanup(saver):
    result = await saver.conn.execute("""
        DELETE FROM checkpoints 
        WHERE checkpoint_ns = 'node_cache'
          AND (metadata->>'expires_at')::timestamp < NOW()
        RETURNING checkpoint_id
    """)
    
    print(f"清理了以下节点的过期缓存: {result}")

# 执行清理
await manual_cleanup(saver)
```

#### 示例 3：查看即将过期的缓存

```python
# 查询接下来 5 分钟内将过期的缓存
query = """
    SELECT 
        checkpoint_id as node_name,
        (metadata->>'expires_at')::timestamp as expires_at,
        (metadata->>'expires_at')::timestamp - NOW() as time_remaining
    FROM checkpoints 
    WHERE checkpoint_ns = 'node_cache'
      AND (metadata->>'expires_at')::timestamp BETWEEN NOW() AND NOW() + INTERVAL '5 minutes'
    ORDER BY expires_at ASC
"""

result = await saver.conn.fetch(query)
for row in result:
    print(f"节点 {row['node_name']} 将在 {row['time_remaining']} 后过期")
```

---

### 防止意外删除的建议

#### 1. **合理设置 TTL**
```python
# ❌ 错误：TTL 太短，缓存几乎无用
CachePolicy(ttl=1)  # 1 秒就过期

# ✅ 正确：根据数据更新频率设置
CachePolicy(ttl=300)  # 5 分钟，适合中等动态数据
```

#### 2. **监控缓存使用情况**
```python
# 查看缓存命中率
query = """
    SELECT 
        checkpoint_id,
        COUNT(*) as access_count,
        COUNT(CASE WHEN (metadata->>'expires_at')::timestamp > NOW() 
              THEN 1 END) as hit_count
    FROM checkpoints 
    WHERE checkpoint_ns = 'node_cache'
    GROUP BY checkpoint_id
"""
```

#### 3. **关键缓存使用长 TTL**
```python
# 对于昂贵的操作，使用更长的 TTL
builder.add_node(
    "expensive_ml_model",
    ml_inference,
    cache_policy=CachePolicy(ttl=86400)  # 24 小时
)
```

---

## 注意事项与限制

### 1. 缓存一致性

- 缓存的数据可能与实际数据不一致（尤其是长 TTL）
- 对实时性要求高的场景需谨慎使用

### 2. 内存占用

- MemorySaver 会占用应用内存
- 大量缓存可能导致内存溢出
- 建议生产环境使用 Redis 或 PostgreSQL

### 3. 缓存穿透

```python
# 避免缓存穿透：对空结果也进行缓存
def safe_node(state):
    result = query_data(state["id"])
    if result is None:
        result = {"empty": True}  # 缓存空结果
    return {"data": result}
```

### 4. 缓存雪崩

```python
import random

# 添加随机偏移避免缓存同时失效
def random_ttl():
    base_ttl = 3600
    offset = random.randint(-300, 300)
    return base_ttl + offset

CachePolicy(ttl=random_ttl())
```

---

## 调试与诊断

### 启用缓存日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("langgraph.cache")
logger.setLevel(logging.DEBUG)
```

### 查看缓存命中率

```python
class CacheMonitor:
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    def get_hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

monitor = CacheMonitor()
```

---

## 总结

LangGraph 的缓存机制是一个强大的性能优化工具，通过合理配置可以：

✅ **提升响应速度**：避免重复计算，加快执行效率  
✅ **降低成本**：减少 API 调用次数和计费  
✅ **改善用户体验**：更快的响应时间  
✅ **简化开发**：统一的缓存 API，易于集成  

**核心要点**：
- 使用 `CachePolicy` 配置 TTL 和缓存键
- 根据场景选择合适的缓存后端
- 避免缓存有副作用或实时性要求高的操作
- 监控缓存性能和命中率

---

## PostgreSQL Cache 存储机制深度解析

### 缓存 vs 检查点的概念区分

在深入了解 PostgreSQL 存储机制之前，首先要明确两个重要概念：

#### 1. **Node Caching（节点缓存）**
- **用途**：缓存节点计算结果，避免重复执行
- **生命周期**：基于 TTL，可跨会话复用
- **存储位置**：与 saver/checkpointer **相同的后端**
- **触发条件**：相同输入的重复调用

#### 2. **Checkpointing（检查点）**
- **用途**：保存图执行的状态快照，支持恢复和人工干预
- **生命周期**：持久化存储，支持会话恢复
- **存储位置**：PostgreSQL 数据库表
- **触发条件**：每次节点执行后自动保存

**关键理解**：Node Cache 和 Checkpointing **共享同一个存储后端**，但服务于不同的目的。

---

### PostgreSQL 存储架构

当你使用 `PostgresSaver` 作为 saver 时，LangGraph 会在 PostgreSQL 中创建以下表结构：

#### 核心表结构

```sql
-- 1. 迁移版本控制表
CREATE TABLE checkpoint_migrations (
    v INTEGER NOT NULL PRIMARY KEY
);

-- 2. 检查点主表（存储状态快照）
CREATE TABLE checkpoints (
    thread_id             TEXT    NOT NULL,    -- 会话/线程 ID
    checkpoint_ns         TEXT    NOT NULL DEFAULT '', -- 命名空间
    checkpoint_id         TEXT    NOT NULL,    -- 检查点 ID
    parent_checkpoint_id  TEXT,               -- 父检查点 ID（支持分支）
    type                  TEXT,               -- 检查点类型
    checkpoint            JSONB   NOT NULL,    -- 状态数据（JSON 格式）
    metadata              JSONB   NOT NULL DEFAULT '{}', -- 元数据
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- 3. 二进制数据表（存储大对象）
CREATE TABLE checkpoint_blobs (
    thread_id     TEXT    NOT NULL,
    checkpoint_ns TEXT    NOT NULL DEFAULT '',
    channel       TEXT    NOT NULL,           -- 数据通道
    version       TEXT    NOT NULL,           -- 版本号
    type          TEXT    NOT NULL,           -- 数据类型
    blob          BYTEA,                      -- 二进制数据
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- 4. 写操作记录表（事务日志）
CREATE TABLE checkpoint_writes (
    thread_id     TEXT    NOT NULL,
    checkpoint_ns TEXT    NOT NULL DEFAULT '',
    checkpoint_id TEXT    NOT NULL,
    task_id       TEXT    NOT NULL,           -- 任务 ID
    task_path     TEXT    NOT NULL,           -- 任务路径
    idx           INTEGER NOT NULL,           -- 索引
    channel       TEXT    NOT NULL,           -- 数据通道
    type          TEXT,                       -- 数据类型
    blob          BYTEA   NOT NULL,           -- 操作数据
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

#### 表的作用说明

| 表名 | 主要作用 | 存储内容 |
|------|----------|----------|
| `checkpoint_migrations` | 版本管理 | 数据库模式版本号 |
| `checkpoints` | 状态快照 | 图执行的完整状态（JSON） |
| `checkpoint_blobs` | 大对象存储 | 二进制数据（如文件、模型等） |
| `checkpoint_writes` | 操作日志 | 每个写操作的详细记录 |

---

### Cache 在 PostgreSQL 中的存储实现

#### 缓存存储位置

**重要发现**：Node Caching **不会创建额外的表**，而是利用现有的 checkpointer 基础设施！

```python
# 当你这样配置时：
from langgraph.checkpoint.postgres import PostgresSaver

cache = PostgresSaver.from_conn_string("postgresql://...")
graph = builder.compile(cache=cache)

# cache 和 checkpointer 是同一个对象！
# 缓存数据存储在 checkpoints/checkpoint_blobs 表中
```

#### 缓存键生成机制

1. **默认缓存键**
```python
# 源码级实现（简化版）
def generate_cache_key(node_input, cache_policy):
    if cache_policy.key_func:
        return cache_policy.key_func([node_input])
    else:
        # 默认：使用输入的哈希值
        import hashlib
        return hashlib.sha256(
            str(node_input).encode('utf-8')
        ).hexdigest()
```

2. **缓存数据结构**
```python
# 缓存在 PostgreSQL 中的存储格式
cache_record = {
    "thread_id": f"cache_{cache_key}",  # 使用特殊前缀
    "checkpoint_ns": "node_cache",      # 缓存命名空间
    "checkpoint_id": node_name,        # 节点名称
    "checkpoint": {
        "result": node_output,          # 缓存的执行结果
        "timestamp": created_at,        # 创建时间戳
        "ttl": cache_policy.ttl        # TTL 设置
    },
    "metadata": {
        "cache_key": cache_key,         # 原始缓存键
        "node_name": node_name,        # 节点名称
        "expires_at": expires_timestamp # 过期时间
    }
}
```

#### 缓存 CRUD 操作实现

##### 1. **写入缓存（CREATE/UPDATE）**
```sql
-- 插入或更新缓存记录
INSERT INTO checkpoints (
    thread_id, checkpoint_ns, checkpoint_id, 
    checkpoint, metadata
) VALUES (
    'cache_' || :cache_key,
    'node_cache',
    :node_name,
    :result_json,
    :metadata_json
) ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id)
DO UPDATE SET
    checkpoint = EXCLUDED.checkpoint,
    metadata = EXCLUDED.metadata;
```

##### 2. **读取缓存（READ）**
```sql
-- 查询缓存记录
SELECT checkpoint, metadata
FROM checkpoints
WHERE thread_id = 'cache_' || :cache_key
  AND checkpoint_ns = 'node_cache'
  AND checkpoint_id = :node_name
  -- TTL 检查
  AND (metadata->>'expires_at')::timestamp > NOW();
```

##### 3. **删除过期缓存（DELETE）**
```sql
-- 清理过期缓存
DELETE FROM checkpoints
WHERE checkpoint_ns = 'node_cache'
  AND (metadata->>'expires_at')::timestamp < NOW();
```

##### 4. **缓存统计查询**
```sql
-- 查看缓存使用情况
SELECT 
    COUNT(*) as total_cache_entries,
    COUNT(CASE WHEN (metadata->>'expires_at')::timestamp > NOW() 
          THEN 1 END) as active_entries,
    COUNT(CASE WHEN (metadata->>'expires_at')::timestamp <= NOW() 
          THEN 1 END) as expired_entries
FROM checkpoints
WHERE checkpoint_ns = 'node_cache';
```

---

### 源码级工作流程

#### 缓存命中检查流程

```python
# 简化的源码实现逻辑
class PostgresCachingSaver:
    async def check_cache(self, node_name: str, node_input: dict, 
                         cache_policy: CachePolicy):
        # 1. 生成缓存键
        cache_key = self._generate_cache_key(node_input, cache_policy)
        
        # 2. 构造查询
        thread_id = f"cache_{cache_key}"
        
        # 3. 查询数据库
        query = """
            SELECT checkpoint, metadata 
            FROM checkpoints 
            WHERE thread_id = %s 
              AND checkpoint_ns = 'node_cache'
              AND checkpoint_id = %s
        """
        
        result = await self.conn.fetchrow(query, thread_id, node_name)
        
        if result:
            # 4. TTL 检查
            metadata = result['metadata']
            expires_at = metadata.get('expires_at')
            
            if expires_at and datetime.now() < datetime.fromisoformat(expires_at):
                # 缓存命中！
                return result['checkpoint']['result']
            else:
                # 缓存过期，删除记录
                await self._delete_expired_cache(thread_id, node_name)
        
        # 缓存未命中
        return None
    
    async def store_cache(self, node_name: str, node_input: dict, 
                         node_output: dict, cache_policy: CachePolicy):
        cache_key = self._generate_cache_key(node_input, cache_policy)
        thread_id = f"cache_{cache_key}"
        
        # 计算过期时间
        expires_at = None
        if cache_policy.ttl:
            expires_at = datetime.now() + timedelta(seconds=cache_policy.ttl)
        
        # 存储缓存
        checkpoint_data = {
            "result": node_output,
            "timestamp": datetime.now().isoformat(),
            "ttl": cache_policy.ttl
        }
        
        metadata = {
            "cache_key": cache_key,
            "node_name": node_name,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
        
        await self._upsert_checkpoint(
            thread_id, "node_cache", node_name,
            checkpoint_data, metadata
        )
```

#### 节点执行与缓存集成

```python
# 节点执行时的缓存逻辑
async def execute_node_with_cache(node_func, node_input, cache_policy, saver):
    # 1. 检查缓存
    cached_result = await saver.check_cache(
        node_func.__name__, node_input, cache_policy
    )
    
    if cached_result is not None:
        print(f"✅ 缓存命中: {node_func.__name__}")
        return cached_result
    
    # 2. 执行节点函数
    print(f"⚡ 执行节点: {node_func.__name__}")
    result = await node_func(node_input)
    
    # 3. 存储缓存
    await saver.store_cache(
        node_func.__name__, node_input, result, cache_policy
    )
    
    return result
```

---

### 性能优化与监控

#### 数据库索引优化

```sql
-- 为缓存查询优化的索引
CREATE INDEX idx_cache_lookup 
ON checkpoints(thread_id, checkpoint_ns, checkpoint_id)
WHERE checkpoint_ns = 'node_cache';

-- 为 TTL 清理优化的索引
CREATE INDEX idx_cache_expiry 
ON checkpoints((metadata->>'expires_at'))
WHERE checkpoint_ns = 'node_cache';
```

#### 缓存清理任务

```python
# 定期清理过期缓存
import asyncio
from datetime import datetime

async def cleanup_expired_cache(saver):
    """定期清理过期缓存"""
    query = """
        DELETE FROM checkpoints 
        WHERE checkpoint_ns = 'node_cache'
          AND (metadata->>'expires_at')::timestamp < NOW()
    """
    
    result = await saver.conn.execute(query)
    print(f"清理了 {result} 条过期缓存记录")

# 每小时执行一次清理
async def schedule_cleanup(saver):
    while True:
        await cleanup_expired_cache(saver)
        await asyncio.sleep(3600)  # 1小时
```

#### 缓存监控查询

```sql
-- 缓存命中率分析
WITH cache_stats AS (
    SELECT 
        checkpoint_id as node_name,
        COUNT(*) as cache_entries,
        COUNT(CASE WHEN (metadata->>'expires_at')::timestamp > NOW() 
              THEN 1 END) as active_entries,
        AVG(EXTRACT(EPOCH FROM 
            (metadata->>'expires_at')::timestamp - 
            (checkpoint->>'timestamp')::timestamp
        )) as avg_ttl_seconds
    FROM checkpoints 
    WHERE checkpoint_ns = 'node_cache'
    GROUP BY checkpoint_id
)
SELECT 
    node_name,
    cache_entries,
    active_entries,
    ROUND(active_entries::numeric / cache_entries * 100, 2) as hit_rate_percent,
    ROUND(avg_ttl_seconds) as avg_ttl_seconds
FROM cache_stats
ORDER BY cache_entries DESC;
```

---

### 实际应用建议

#### 1. **数据库连接配置**
```python
# 生产环境连接配置
from langgraph.checkpoint.postgres import PostgresSaver

# 使用连接池
saver = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/db",
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接
)

# 初始化表结构（首次使用）
await saver.setup()
```

#### 2. **缓存策略配置**
```python
# 不同场景的缓存配置
builder.add_node(
    "llm_node",
    llm_function,
    cache_policy=CachePolicy(
        ttl=1800,  # LLM 调用缓存 30 分钟
        key_func=lambda args: f"llm_{hash(args[0]['messages'][-1].content)}"
    )
)

builder.add_node(
    "db_query_node", 
    query_function,
    cache_policy=CachePolicy(
        ttl=600,   # 数据库查询缓存 10 分钟
        key_func=lambda args: f"db_{args[0]['query']}"
    )
)
```

#### 3. **监控与维护**
```python
# 缓存健康检查
async def cache_health_check(saver):
    stats = await saver.conn.fetchrow("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN (metadata->>'expires_at')::timestamp > NOW() 
                  THEN 1 END) as active,
            pg_size_pretty(pg_total_relation_size('checkpoints')) as table_size
        FROM checkpoints 
        WHERE checkpoint_ns = 'node_cache'
    """)
    
    return {
        "total_entries": stats["total"],
        "active_entries": stats["active"], 
        "table_size": stats["table_size"],
        "hit_rate": stats["active"] / stats["total"] if stats["total"] > 0 else 0
    }
```

---

## 参考资源

- [LangGraph 官方文档 - Node Caching](https://langchain-ai.github.io/langgraph/concepts/low_level/#node-caching)
- [LangGraph How-to Guide - Cache Expensive Nodes](https://langchain-ai.github.io/langgraphjs/how-tos/node-caching/)
- [LangChain LLM Caching](https://python.langchain.com/docs/integrations/llm_caching/)
- [PostgresSaver API Reference](https://api.python.langchain.com/en/latest/checkpoint/langchain_postgres.checkpoint.PostgresSaver.html)
- [LangGraph Checkpointing Concepts](https://langchain-ai.github.io/langgraph/concepts/persistence/)

---

**文档版本**: v2.0  
**最后更新**: 2025-10-13  
**作者**: AutoAgents Team
