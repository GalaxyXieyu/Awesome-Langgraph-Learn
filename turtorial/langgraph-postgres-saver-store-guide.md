# LangGraph Postgres Saver/Store 学习指南（项目集成版）

本文档用中文系统讲解：
- 本项目如何集成与使用 LangGraph 的短期内存（Checkpointer）与长期内存（Store）
- 如何在 Graph 节点中优雅地读写 Store
- 最小化测试脚本与最佳实践

并附官方参考链接，便于进一步深入。

---

## 1. 核心概念（必须理解）

- AsyncPostgresSaver（官方 Checkpointer）
  - 作用：短期内存（会话级状态）持久化，用于多轮对话/多步工作流的状态保存与恢复。
  - 表结构：`checkpoints`、`checkpoint_writes`、`checkpoint_blobs`。
  - 颗粒度：按 `thread_id`（或 `session_id`）分组；每次 `ainvoke/astream` 都会产生/更新 checkpoint。
  - 使用方式：编译 Graph 时传 `checkpointer=...`，运行时无需手动读写。

- AsyncPostgresStore（官方 Store）
  - 作用：长期内存（Key/Value + 可选向量检索）。适合跨会话的用户画像、偏好、知识缓存等。
  - 命名空间：一般推荐 `(bucket, user_id)` 二元组，便于按业务域与用户隔离。
  - 常用方法：`aput(namespace, key, value)`、`asearch(namespace, filter=None, limit=N)`。
  - 使用方式：编译 Graph 时传 `store=...`，在节点函数签名中声明 `store` 参数即可自动注入。

> 两者区别：Saver 管“短期、线程态”的状态快照（自动），Store 管“长期、业务态”的 KV/向量数据（手动）。

---

## 2. 本项目如何集成

- 资源工厂（统一创建与缓存）
- 位置：`backend/src/infrastructure/ai/graph/memory/`（saver.py / store.py / cache.py）
  - 方法：
    - `await initialize_checkpointer('MAIN_DB')` → 创建并缓存 `AsyncPostgresSaver`
    - `await initialize_store('MAIN_DB')` → 创建并缓存 `AsyncPostgresStore`
    - `get_global_checkpointer()` / `get_global_store()` → 取回当前事件循环的实例
    - `close_checkpointer()` → 关闭池与相关资源
  - 实现要点：使用 `psycopg_pool.AsyncConnectionPool`；在 DSN 中注入 `options=-c search_path=ai_ns,public`；首次调用 `setup()` 自动建表（幂等）。

- Graph 注册与编译
  - 文件：`backend/src/infrastructure/ai/graph/registry.py`
  - 注册时获取资源并编译：
    ```python
    compiled_app = workflow.compile(checkpointer=self.checkpointer, store=store)
    ```
  - 好处：所有 Graph 共享连接池与资源，低延迟、低耦合。

- 自定义 Saver（Legacy，已归档）
  - 旧文件已移至 `backend/backup/custom_pg_saver/custom_pg_saver.py`
  - 主代码不再引用；请使用官方 AsyncPostgresSaver/Store。

---

## 3. 环境变量与连接串

- 必需：
  - `MAIN_DB_TYPE=postgresql`
  - `MAIN_DB_URL`、`MAIN_DB_USERNAME`、`MAIN_DB_PASSWORD`
  - DSN 推荐：
    ```text
    postgresql://user:pass@host:5432/db?options=-c%20search_path%3Dai_ns%2Cpublic
    ```
    注意 `options=-c search_path=ai_ns,public` 需要 URL 编码。

- 可选（Store 向量索引）：
  - `STORE_VECTOR_INDEX_ENABLED=true|false`
  - `VECTOR_DIMENSION=1024`（与 embedding provider 维度一致）

---

## 4. 在 Graph 中如何使用（从 0 到 1）

1) 应用启动（一次性）
```python
await initialize_checkpointer('MAIN_DB')
await initialize_store('MAIN_DB')
```

2) 编译注入
```python
app = workflow.compile(
    checkpointer=get_global_checkpointer(),
    store=get_global_store(),
)
```

3) 运行配置（关键）
```python
config = {
  "configurable": {
    "thread_id": "<线程/会话标识>",
    "user_id": "<用户标识>",
  }
}
```

4) 节点内访问 Store（直连写法）
```python
async def save_pref(state, *, config, store):
    user = config.get("configurable", {}).get("user_id", "anon")
    ns = ("user_prefs", user)
    await store.aput(ns, key="theme", value={"dark": True})
    return {"messages": state["messages"] + ["saved:theme"]}
```

---

## 5. 更优雅的写法：封装小工具（推荐）

为了避免在每个节点反复处理 `user_id/namespace`、返回结构等，建议提供一些小工具函数。示例代码：

```python
# src/application/memory/helpers.py
from typing import Any, Optional, Tuple
from langchain_core.runnables import RunnableConfig

def user_ns(config: RunnableConfig, bucket: str) -> Tuple[str, str]:
    user = config.get("configurable", {}).get("user_id", "anon")
    return (bucket, user)

async def put_user_kv(store, config: RunnableConfig, bucket: str, key: str, value: Any) -> None:
    await store.aput(user_ns(config, bucket), key=key, value=value)

async def get_user_kv(store, config: RunnableConfig, bucket: str, key: str, default: Any=None) -> Any:
    items = await store.asearch(user_ns(config, bucket), filter=None, limit=50)
    for it in items:
        k = getattr(it, "key", None)
        if k is None and isinstance(it, dict):
            k = it.get("key")
        if k != key:
            continue
        v = getattr(it, "value", None)
        if v is None and isinstance(it, dict):
            v = it.get("value")
        return v
    return default
```

节点中就能这样写：

```python
from src.application.memory.helpers import put_user_kv, get_user_kv

async def save_pref(state, *, config, store):
    await put_user_kv(store, config, "user_prefs", "theme", {"dark": True})
    return {"messages": state["messages"] + ["saved:theme"]}

async def load_pref(state, *, config, store):
    theme = await get_user_kv(store, config, "user_prefs", "theme")
    return {"messages": state["messages"] + [f"theme:{bool(theme)}"]}
```

同理，也可以按领域封装（例如 deepresearch）：

```python
# src/application/memory/deepresearch.py
async def remember_query(store, config, text: str):
    await put_user_kv(store, config, "deepresearch:queries", "last_query", {"text": text})

async def recall_last_query(store, config) -> Optional[str]:
    v = await get_user_kv(store, config, "deepresearch:queries", "last_query")
    return v.get("text") if isinstance(v, dict) else v
```

---

## 6. 示例脚本（可运行）

- 文件：`backend/scripts/test.py`
- 功能：
  - 写入并读取用户偏好（Store）
  - 写入用户 query、调用 LLM 总结并再次从 Store 读回（Store）
  - 两次运行同一 `thread_id` 以查看检查点历史（Saver）
- 运行：
  ```bash
  # 在 backend 目录下
  python -m scripts.test
  # 或使用 uv
  uv run backend/scripts/test.py
  ```
- 注意：
  - LLM 可选。若未配置，将使用占位总结，不会阻塞。
  - `saver.alist(...)` 在某些版本中返回异步生成器，需 `async for` 迭代。

---

## 7. 何时用 Store、何时用 Saver？

- 用 Store：
  - 需要跨会话/跨节点长期共享的信息（用户偏好、资料、缓存、工具结果）。
  - 需要向量检索的语义记忆（开启索引后）。

- 用 Saver（自动）：
  - 需要让对话/流程在“同一线程”内连续可恢复。
  - 需要查看执行历史、回滚/分支（writes/pending_writes）。

---

## 8. 常见问题与排查

- 表未创建/权限不足：确保 `ai_ns` schema 存在、角色具备 `USAGE/CREATE`；首次会 `setup()` 建表。
- 找不到资源：确保在同一事件循环中，先 `initialize_*` 再 `get_global_*`。
- DSN/search_path：推荐通过 DSN 携带 `options=-c search_path=ai_ns,public`；或在角色层面设置默认 schema。
- `alist` 使用：根据安装版本，可能返回异步生成器，需 `async for`。
- 向量索引：未配置 embedding provider 时请关闭 `STORE_VECTOR_INDEX_ENABLED`。

---

## 9. 官方参考（强烈推荐）

- 持久化（Postgres Saver）：
  - https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/
- 记忆/Store 概念与使用：
  - https://langchain-ai.github.io/langgraph/how-tos/memory/add-memory/
- Postgres 实现包（了解即可）：
  - https://pypi.org/project/langgraph-checkpoint-postgres/

---

## 10. 实战 Tips

- 统一命名空间：`("<bucket>", user_id)`，按业务域划分 bucket，例如 `user_prefs`、`deepresearch:queries`。
- 封装最小工具：降低节点内样板代码；提高可读性与可测试性。
- Graph 编译一次：生产中建议启动时编译并缓存，运行时直接调用（你已按此模式落地）。
- 控制 LLM 超时：节点中调用 LLM 建议加超时与降级兜底，避免阻塞整个图。

---

如需，我可以：
- 提交一份 `src/application/memory/helpers.py` 的实际文件并改造 `scripts/test.py` 采用该封装；
- 为 deepresearch 提供 `remember_query/recall_last_query/save_summary` 等专用的记忆 API；
- 在 docs 目录添加“Store 设计规范”小文档（命名、分区、有效期、容量治理）。

---

## 11. 数据库存储结构与向量说明（pgvector）

- 表结构（默认 schema: `ai_ns`）
  - `store`（KV 主表，JSONB 值）
    - `prefix text`：命名空间（把 `("bucket", "user")` 拼成 `bucket.user`）
    - `key text`：键
    - `value jsonb`：任意 JSON 值
    - `created_at timestamptz`、`updated_at timestamptz`
    - `expires_at timestamptz`、`ttl_minutes int`（可选 TTL）
    - PK: `(prefix, key)`；索引：`store_prefix_idx`
  - `store_vectors`（开启向量索引时创建）
    - `prefix text`、`key text`、`field_name text`
    - `embedding vector|halfvec(dims)`：pgvector 向量类型
    - `created_at/updated_at`；PK: `(prefix, key, field_name)`；FK 引用 `store(prefix, key)`
  - 迁移表：`store_migrations`、`vector_migrations`

- 向量类型与距离
  - `vector_type`：`vector`（默认）或 `halfvec`（半精度占用更少内存）
  - `distance_type`：`cosine`（默认）、`l2`、`inner_product`
  - ANN 索引：`hnsw`（默认）、`ivfflat` 或 `flat`（直扫）

> 注意：只有启用了 `index` 配置，`setup()` 才会创建 `store_vectors` 与向量索引。

---

## 12. `index` 配置详解（如何“开启语义检索”）

当在初始化 Store 时传入 `index=...` 即表示开启语义检索能力。关键字段：

- `dims`（int，必填）：向量维度。需与嵌入模型输出一致（如 1536/1024）。
- `embed`（必填）：提供一个具备 `aembed_documents(texts) -> List[List[float]]` 的对象/函数。
  - 本项目通过 `_EmbeddingAdapter` 包装了 `create_embedding_provider()`，自动对齐维度、做异常兜底。
- `fields`（可选）：要索引的字段路径列表。如 `['text']` 表示只对 `value['text']` 做嵌入；默认是整份 JSON（`'$'`）。
- `ann_index_config`（可选）：ANN 索引配置，例如：
  ```python
  {
    "kind": "hnsw",  # 或 "ivfflat"、"flat"
    "vector_type": "vector",  # 或 "halfvec"
    # hnsw 其他参数：m、ef_construction
    # ivfflat 其他参数：nlist
  }
  ```
- `distance_type`（可选）：`"cosine" | "l2" | "inner_product"`

示例（只索引 `value['text']` 字段）：
```python
index = {
  "dims": 1536,
  "embed": adapter,      # 实现 aembed_documents
  "fields": ["text"],   # 强烈推荐用于“文本偏好/文档”场景
  "ann_index_config": {"kind": "hnsw", "vector_type": "vector"},
  "distance_type": "cosine",
}
```

> 本项目当前工厂默认不指定 `fields`，等同于索引整个 JSON。若你主要存 `{"text": "..."}`，可以把工厂改为默认 `fields=["text"]`，索引更干净、效果更稳。

---

## 13. Store API 速查（异步）

以下为常用方法与关键参数（来自 `AsyncPostgresStore`）：

- `await store.aput(namespace, key, value, *, index=None|False|List[str], ttl=None)`
  - `namespace`: 元组，如 `("report_prefs", user_id)`；内部存为 `prefix='report_prefs.user_id'`
  - `key`: 文档键（字符串）。重复 `key` 会 upsert。
  - `value`: 任意 JSON 可序列化对象。若开启向量索引：
    - `index=None` → 使用 `index.fields`（或整份 JSON）来抽取文本生成嵌入
    - `index=False` → 本次写入不参与向量索引
    - `index=["text", "title"]` → 仅对这些字段做嵌入
  - `ttl`：秒数；设置后会写入 `expires_at/ttl_minutes`，需手动启动 TTL 清理（一般业务无需）。

- `item = await store.aget(namespace, key, refresh_ttl: bool=False)`
  - 返回 `Item(key, value, namespace, created_at, updated_at)` 或 None
  - `refresh_ttl=True` 会在命中时刷新 TTL 过期时间（如果设置过）

- `items = await store.asearch(namespace, *, query=None, filter=None, limit=10, offset=0, refresh_ttl=False)`
  - 语义检索：`query="..."` 需要已启用 `index`
  - 精确过滤（JSONB）：`filter={"type": {"$eq": "format"}}` 等；支持 `$eq/$gt/$gte/$lt/$lte/$ne`
  - 返回 `SearchItem(value, key, namespace, created_at, updated_at, score)` 列表；`score` 越大越相似
  - 不传 `query` → 按 `updated_at DESC` 的时间序获取

- `namespaces = await store.alist_namespaces(...)`（若版本提供）
  - 用于浏览可用的命名空间（不常用）

实用示例：
```python
# 写入偏好（默认参与索引）
await store.aput(("report_prefs", user), f"format:{ts}", {"text": pref, "type": "format"})

# 精确读取
item = await store.aget(("report_prefs", user), "format:2024-10-01")

# 语义检索 + 过滤
items = await store.asearch(
    ("report_prefs", user),
    query="报告的格式和风格要求",
    filter={"type": {"$eq": "format"}},
    limit=5,
)
texts = [it.value.get("text", "") for it in items]
```

---

## 14. 报告生成场景：偏好存取策略（推荐）

- 命名空间：`("report_prefs", user_id)`
- 键设计：按类型+时间，如 `format:<ts>`、`tone:<ts>`、`length:<ts>`
- 值结构：
  ```json
  { "text": "中文、简洁、分段清晰、表格", "type": "format", "source": "user", "weight": 0.8 }
  ```
- 写入节点：用户提出偏好时写入；写报告前检索：
  ```python
  prefs = await store.asearch(("report_prefs", user),
      query="报告格式与个人风格偏好",
      filter={"type": {"$eq": "format"}},
      limit=5)
  hint = "\n".join(it.value.get("text", "") for it in prefs)
  prompt = f"请按以下偏好撰写报告:\n{hint}\n---\n{用户问题/大纲}"
  ```

---

## 15. 常见坑与排查（向量）

- 维度不匹配：`VECTOR_DIMENSION` 必须与嵌入模型一致；本项目会在不一致时做截断/填充，但建议配置正确。
- 权限/扩展：`setup()` 需要执行 `CREATE EXTENSION vector;`，DB 角色需有权限。
- 过滤与索引：复杂 WHERE 条件可能让查询走顺序扫描；一般规模下仍可接受，必要时再调索引策略（如 IVF 参数）。
- `fields`：若只关心 `value['text']`，建议在 `index` 里设置 `fields=["text"]`，避免索引杂质。
