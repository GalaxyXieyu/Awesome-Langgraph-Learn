# LangGraph 上下文工程实战指南（压缩与持久化，项目版）

本文档面向本项目（LAGP/AutoAgents）在 LangGraph 中的“上下文工程（Context Engineering）”落地方案，聚焦两件事：
- 如何在对话/工作流中进行“上下文压缩”（裁剪、摘要、过滤）以稳定控制 token 预算与提升相关性；
- 如何结合本项目已接入的 Postgres Checkpointer 与 Store 实现“会话存储/断点恢复 + 长期记忆”。
> DeepResearch 更新（重要）：
> - 偏好仅使用 Store 读取一次，并以 SystemMessage 注入到 state.messages 首部；
> - 上下文完全走 state 的结构化拼接，不再做报告分段持久化或基于 artifacts 的统一召回；
> - 统一出口为 followup_suggestions 节点（仅生成 3 条建议问题并结束），不做基于产物的追问问答；
> - 若仍需 artifacts 持久化，请在单独 behind-flag 的实现中启用，默认关闭。
参考阅读：`langgraph-postgres-saver-store-guide.md`（持久化细节）与官方 Context Engineering 资料。

---

## 1. 适用场景与目标

- 多轮对话/多步工具调用经常超出模型上下文窗口，导致报错、延迟和“中间丢失（lost-in-the-middle）”。
- 业务需要“记住”用户偏好/历史信息（跨会话），同时在单次会话内需要稳态的上下文长度控制。
- 目标：以“裁剪 + 摘要 + 过滤”的组合策略，确保每次 LLM 调用的输入可控、相关、低成本；并用 Postgres Saver/Store 提供会话连续性与长期记忆。

---

## 1.1 DeepResearch 专项：会话/追问业务设计

- 会话分层：`thread_id`（对话线程，短期记忆/断点恢复） vs `run_id`（一次完整深研执行）。同一线程内可包含多个 run；follow-up QA 可显式引用 `run_id` 或默认最近 run。
- 产物分桶（Store 命名空间建议）：
  - 元信息：`("deepresearch:runs", user_id)` → `run:{run_id}:meta`
  - 产物：`("deepresearch:artifacts", user_id)` → `run:{run_id}:{stage}`（`plan/search/analysis/code/report/summary` 等）
  - QA facets：`("deepresearch:facets", user_id)` → `run:{run_id}:qa:{ts}`（记录问答摘要与命中段落）
- Follow-up QA：不要重放整段历史。构建“Context Pack”：Exec Summary → Key Findings → 报告命中段落（分段存储）→ 相关图表/代码结果。用向量/过滤检索组装，严格 token 预算。
- 运行期稳态：各节点前用 `pre_model_hook` 进行筛选→裁剪→（必要时增量摘要）；工具/大对象只入 Store，不进消息历史。

---

## 2. 核心概念速览

- 短期记忆（Checkpointer，已集成）
  - 用于“线程/会话级”状态快照，自动保存每步执行后的 `state`，支持恢复、分支、时间旅行。
  - 本项目集中管理于 `src/infrastructure/ai/graph/memory/`（saver/store/cache），通过 `initialize_checkpointer()` 与 `get_global_checkpointer()` 提供。

- 长期记忆（Store，已集成）
  - 面向跨会话/跨场景的结构化 KV（可选向量检索），用来存用户偏好、知识碎片、工具结果等。
  - 通过 `initialize_store()` 与 `get_global_store()` 提供，支持命名空间、TTL、语义检索。

- 上下文工程（Context Engineering）
  - 四类策略：写入（组织提示/上下文）、选择（检索/过滤）、压缩（裁剪/摘要）、隔离（分桶/屏蔽）
  - 本文重点在“压缩”与“选择”的工程化落地。

---

## 3. 上下文压缩：三大常用策略

### 3.1 消息裁剪（token 窗口控制）

在每次 LLM 调用前，根据预算截断历史消息。推荐使用 LangChain `trim_messages` 辅助函数，并通过 LangGraph 的 `pre_model_hook` 注入，不破坏原始 `state["messages"]`。

示例（Python）：

```python
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

def build_pre_model_hook(max_tokens: int = 800, keep_system: bool = True):
    def pre_model_hook(state):
        messages = state.get("messages", [])
        trimmed = trim_messages(
            messages,
            strategy="last",                 # 常用策略：保留最近的消息
            token_counter=count_tokens_approximately,
            max_tokens=max_tokens,
            include_system=keep_system,
        )
        # 返回给 LLM 的输入，不修改原始 state
        return {"llm_input_messages": trimmed}
    return pre_model_hook
```

要点：
- 在 ReAct/Agent 预构建器或自定义节点调用前注入 `pre_model_hook`；
- `include_system=True` 常用于保留系统指令，减轻“丢失中间指令”的风险；
- 若需要严格窗口化，可配合“固定保留最近 N 条”的窗口策略（见 4.2）。

### 3.2 消息摘要（信息聚合）

当累计 token 超阈值，将“较早的多轮历史”压缩为一段摘要，并仅保留最近 K 轮原文。

常见两种落地：
- 增量摘要：每次交互后更新摘要，低开销、延迟小；
- 检索时摘要：保留完整历史，只有在“即将调用 LLM”时对历史做摘要，适合不确定是否会继续长对话的场景。

伪代码（增量摘要节点）：

```python
async def summarize_if_needed(state, *, config, llm):
    messages = state.get("messages", [])
    budget = config.get("configurable", {}).get("summary_budget", 400)
    if too_long(messages, budget):
        # 仅对早期消息做摘要，保留最近若干轮
        early, recent = split_history(messages, keep_last=6)
        summary = await llm.ainvoke(
            "请将以下对话内容浓缩为要点摘要，用于后续上下文：\n" + format_msgs(early)
        )
        new_messages = [
            {"type": "system", "content": f"历史摘要：{summary}"},
            *recent,
        ]
        return {"messages": new_messages}
    return {}
```

注意：摘要应短小可控，并尽量保留实体/数字等关键信息；建议在系统消息里标注“这是摘要，遇到冲突以最新用户输入为准”。

### 3.3 压缩式检索（RAG 阶段过滤/压缩）

对长文档/知识库，先“检索→压缩→入模”，而非将整段原文塞给模型。可使用 LangChain 的“Contextual Compression Retriever”。

要点：
- `base_retriever` 先取初选文档，`DocumentCompressor` 再做过滤/截断；
- 尽量让压缩发生在“每轮调用前”的节点里，避免无关文本进入对话历史；
- 压缩后的片段可附加来源标注，便于溯源与后续引用。

---

## 4. 对话历史管理实践

### 4.1 统一入口：pre_model_hook

不破坏原始 `state` 的前提下，为每次 LLM 调用提供“可控输入”。推荐组合：
- 先按重要性过滤（系统/工具结果/最近用户输入），
- 再用 `trim_messages` 控预算，
- 超阈值时用“增量摘要”回收历史。

在预构建代理中使用（示意）：

```python
from langgraph.prebuilt import create_react_agent

pre_hook = build_pre_model_hook(max_tokens=900)
agent = create_react_agent(model, tools, pre_model_hook=pre_hook)
```

在自定义 Graph 中，可以在“LLM 节点”前增加一个“prepare_input”节点来执行上述逻辑。

### 4.2 窗口化与删除（强约束）

当需要“硬控长度”时，可采用“固定保留最近 N 条”。示例（仅示意）：

```python
def window_messages(state, keep_last: int = 12):
    msgs = state.get("messages", [])
    if len(msgs) <= keep_last:
        return {}
    # 可选：总是保留首条系统消息
    head = msgs[:1] if msgs and getattr(msgs[0], "type", "") == "system" else []
    tail = msgs[-keep_last:]
    return {"messages": head + tail}
```

注意：聊天历史的有效结构通常要求“以系统/人类开始、以人类/工具结束”。裁剪/删除后应确保序列合法，避免模型/工具调用异常。

---

## 5. 与本项目持久化集成（Postgres Saver/Store）

项目已提供企业级资源工厂：`backend/src/infrastructure/ai/graph/memory/`（saver/store/cache）

初始化与编译（示例）：

```python
from src.infrastructure.ai.graph.memory import (
    initialize_checkpointer,
    initialize_store,
    get_global_checkpointer,
    get_global_store,
)

# 应用启动时（一次性）
await initialize_checkpointer("MAIN_DB")
await initialize_store("MAIN_DB")

# 编译 Graph
app = workflow.compile(
    checkpointer=get_global_checkpointer(),
    store=get_global_store(),
)

# 运行时配置：用 thread_id 绑定会话，用 user_id 绑定用户
config = {
  "configurable": {
    "thread_id": "session-123",
    "user_id": "u_42",
    "summary_budget": 400,  # 自定义预算示例
  }
}
```

在节点中读写 Store（结构化长期记忆）：

```python
async def save_user_pref(state, *, config, store):
    user = config.get("configurable", {}).get("user_id", "anon")
    ns = ("user_prefs", user)
    await store.aput(ns, key="theme", value={"dark": True})
    return {}

async def load_user_pref(state, *, config, store):
    user = config.get("configurable", {}).get("user_id", "anon")
    ns = ("user_prefs", user)
    item = await store.aget(ns, "theme")
    theme = (item.value if item else {}).get("dark", False)
    return {"messages": state["messages"] + [f"theme:{theme}"]}
```

更多 Store 用法（向量检索 / 过滤 / TTL）与索引配置，见 `langgraph-postgres-saver-store-guide.md` 的第 11–13 章。

---

## 5.1 DeepResearch：Run 持久化与 Follow-up QA

落库建议（在 `summarizing_node` 或收口处统一写入）：

```python
async def persist_run_artifacts(store, user_id: str, run_id: str, artifacts: dict):
    ns = ("deepresearch:artifacts", user_id)
    # 关键产物（仅示例字段）
    await store.aput(ns, key=f"{run_id}:plan", value={"text": artifacts.get("plan_text",""), "run_id": run_id, "type": "plan"})
    await store.aput(ns, key=f"{run_id}:analysis", value={"text": artifacts.get("analysis_summary",""), "citations": artifacts.get("citations",[]), "run_id": run_id, "type": "analysis"})
    await store.aput(ns, key=f"{run_id}:report", value={"text": artifacts.get("final_report",""), "sections": artifacts.get("sections",[]), "run_id": run_id, "type": "report"})
    await store.aput(ns, key=f"{run_id}:exec_summary", value={"text": artifacts.get("exec_summary",""), "run_id": run_id, "type": "summary"})

    # 元数据
    meta_ns = ("deepresearch:runs", user_id)
    await store.aput(meta_ns, key=f"run:{run_id}:meta", value={
        "run_id": run_id,
        "topic": artifacts.get("topic",""),
        "ts": artifacts.get("ts"),
        "stages": artifacts.get("stages",[]),
    })
```

Follow-up QA 入口（独立轻量子图/节点）：

```python
async def followup_qa(state, *, config, store, llm):
    user = config["configurable"].get("user_id")
    run_id = state.get("run_id") or state.get("session_id")
    q = (state.get("question") or "").strip()

    ns = ("deepresearch:artifacts", user)
    # 语义检索：从 exec_summary/analysis/report 中召回
    items = await store.asearch(ns, query=q, filter={"run_id": {"$eq": run_id}}, limit=6)

    # 组装 Context Pack（优先 summary/analysis，再命中 report 段）
    pack = []
    for it in items:
        v = it.value or {}
        pack.append({"type": v.get("type"), "text": v.get("text",""), "citations": v.get("citations",[])})

    prompt = make_followup_prompt(q, pack)  # 约束基于本次 run 产物回答，并附引用
    resp = await llm.ainvoke([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1000)

    # 保存本次 QA 摘要，支持下次检索
    facets_ns = ("deepresearch:facets", user)
    await store.aput(facets_ns, key=f"{run_id}:qa:{int(time.time())}", value={"text": q + "\n" + resp.content, "run_id": run_id, "type": "qa"})
    return {"answer": resp.content}
```

---

## 6. 端到端示例（压缩 + 持久化）

```python
from langgraph.prebuilt import create_react_agent
from my_llm import model, tools

pre_hook = build_pre_model_hook(max_tokens=900)
agent = create_react_agent(model, tools, pre_model_hook=pre_hook)

# 编译时注入 saver/store（参考上节）
app = agent.compile(
    checkpointer=get_global_checkpointer(),
    store=get_global_store(),
)

config = {"configurable": {"thread_id": "s1", "user_id": "u_42"}}

# 轮 1：保存偏好
await app.ainvoke({"messages": [("user", "以后请用中文、简洁分段。")], "ops": "save_pref"}, config=config)

# 轮 2：提问（触发 pre_model_hook 裁剪，并读取偏好拼入提示）
await app.ainvoke({"messages": [("user", "生成一段周报摘要")], "ops": "answer_with_prefs"}, config=config)
```

实现要点：
- `save_pref` 节点写入 Store；`answer_with_prefs` 节点在调用 LLM 前读取 Store（可配合语义检索过滤），在 `pre_model_hook` 执行后将“偏好提示 + 裁剪后的历史”共同传给模型。

---

## 6.1 DeepResearch：意图识别 + 人工确认路由

为长流程加“意图识别/确认”入口，复杂问题建议 deep，简单走 react；当建议 deep 且用户未显式指定时，通过 HumanInterrupt 确认：

```python
from langgraph import types
from langgraph.prebuilt.interrupt import HumanInterrupt

async def intent_detection_node(state, *, config=None):
    q = (state.get("question") or "").strip()
    complex = len(q) >= 120 or any(kw in q.lower() for kw in ["research","综述","调研","benchmark","代码","实验"])
    suggested = "deep" if complex else "react"
    if suggested == "deep" and state.get("deepresearch") not in {"deep","react"}:
        req: HumanInterrupt = {
            "action_request": {"action": "confirm_deep", "args": {"question": q, "suggested_mode": "deep"}},
            "config": {"allow_accept": True, "allow_reject": True, "allow_edit": False},
            "description": "检测到问题较复杂，建议进入【深度研究】。accept 继续，reject 使用快速问答。",
        }
        resp = types.interrupt(req)
        if isinstance(resp, (list, tuple)) and resp: resp = resp[-1]
        if isinstance(resp, str): resp = {"type": resp}
        mode = "deep" if resp.get("type") == "accept" else "react"
        return {"deepresearch": mode}
    return {"deepresearch": suggested}
```

在图中作为入口点，并据此路由到 `planning`（deep）或 `react_agent`（react）。

---

## 7. 生产化建议

- Token 预算：为“模型输入 + 期望输出”留足余量；常见做法是按输入窗口 60–80% 设裁剪阈值。
- 系统消息保留：在裁剪/摘要时坚持保留关键系统指令，降低“指令漂移”。
- 增量摘要：对超长对话建议启用增量摘要，摘要中明确“冲突以最新用户输入为准”。
- 角色与顺序：裁剪/删除后检查消息序列合法性（以 System/Human 开始、以 Human/Tool 结束）。
- 会话标识：`thread_id` 仅影响 Saver（短期记忆）；跨会话共享信息应写入 Store（长期记忆）。
- 向量索引：若仅需索引 `value["text"]`，建议在初始化 Store 时指定 `fields=["text"]`，减少噪声嵌入。

DeepResearch 额外建议：
- run 分段：报告入库按章节/段落切分并存段 ID，便于精准检索与 UI 原文定位；
- QA 约束：提示中显式要求“仅基于 run 产物回答；若不足需标注不确定并建议追加研究”；
- 保留策略：`runs` 30–90 天；`artifacts` 更久（视容量）；`facets:qa` 支持 TTL；
- 中断体验：确认提示明确时间/成本权衡，支持一键 accept/reject。

---

## 8. 常见问题排查

- “裁剪后调用报错”：优先检查消息开头/结尾角色是否符合模型要求；必要时保留首条 System 与最后一条 Human。
- “摘要丢信息”：调大 `keep_last`、为关键字段设定“不可摘要”规则（如工具结构化结果）。
- “会话不连续”：调用时未带 `thread_id`；或运行在不同事件循环中未复用同一 checkpointer。
- “向量检索无结果”：确认 `VECTOR_DIMENSION` 与嵌入模型一致；或先用 `filter` 精确筛选回退。
- “Schema 不存在/权限不足”：确保 `ai_ns` 已创建且角色具备 `USAGE/CREATE`，详见持久化指南。

---

## 9. 参考资料

- Context Engineering（官方博客）：https://blog.langchain.com/context-engineering-for-agents
- 上下文裁剪（trim_messages，Python/JS）：
  - Python API 参考：https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.html
  - JS How-to：https://js.langchain.com/docs/how_to/trim_messages/
- 管理对话历史（LangGraph How-to）：https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/
- 持久化与记忆（LangGraph）：
  - 概念： https://langchain-ai.github.io/langgraph/concepts/persistence/
  - Postgres Saver： https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/
  - 添加记忆： https://langchain-ai.github.io/langgraph/how-tos/memory/add-memory/
- RAG 压缩检索（LangChain）：https://python.langchain.com/docs/how_to/contextual_compression/

---

如需，我可以：
- 提供一个可直接运行的 demo（包含增量摘要节点 + pre_model_hook + Store 读写 + PostgresSaver 恢复）；
- 将“消息裁剪/摘要/过滤”封装为复用的 `utils`，并在现有 Graph 注册处统一挂载；
- 按你的具体业务场景（如 deepresearch）补充专用的记忆命名空间与读写工具函数。
