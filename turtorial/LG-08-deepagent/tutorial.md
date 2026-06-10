# LG-08: DeepAgents -- 生产级深度研究智能体

> **阶段**: LG-08 | **难度**: 高级 | **预计时长**: 5-6 小时 | **依赖**: LG-01 ~ LG-07

## 学习目标

- 理解 DeepAgents 四大架构支柱和 10 层默认 Middleware 栈
- 使用 Planning (Todo) 工具让 Agent 自主分解和跟踪任务
- 使用 Filesystem 工具让 Agent 在工作空间持久化成果
- 使用 Sub-agent（同步 + Async）实现串行和并行深度研究
- 使用 Skills 渐进式披露管理大量领域知识
- 使用 `create_deep_agent` 快速搭建生产级 Agent Harness

```python
# 安装依赖（取消注释执行）
!pip install -U langgraph langchain langchain-openai pydantic deepagents
```

---

## 1. DeepAgents 架构概述

DeepAgents 是 LangChain 官方推出的 Agent Harness，基于 LangGraph 构建。

### 四大支柱

| 支柱 | 解决的问题 |
|------|-----------|
| **Planning** | 复杂任务不知道怎么拆 |
| **Filesystem** | 上下文窗口装不下全部信息 |
| **Sub-agent** | 一个人干不完，需要团队协作 |
| **Skills** | 领域知识太多，不能全塞进 prompt |

---

## 2. create_deep_agent：一键创建 Deep Agent

DeepAgents 的核心入口是 `create_deep_agent()`，它会自动组装 10 层 Middleware 栈。

```python
# ==========================================
# create_deep_agent 基本用法
# ==========================================

# 伪代码演示（需要安装 deepagents 才能运行）
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_deep_agent(
    model="openai:gpt-4o",  # 推荐用字符串格式
    checkpointer=InMemorySaver(),
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "研究量子计算最新进展"}]
})

print("create_deep_agent 核心参数:")
print("  model: 模型字符串，如 'openai:gpt-4o'")
print("  tools: 自定义工具列表")
print("  subagents: 子智能体定义")
print("  backend: 文件系统后端")
print("  checkpointer: 检查点（必需）")
print("  skills: Skills 目录路径")
print("  middleware: 自定义中间件")
```

**输出**

```text
[31m---------------------------------------------------------------------------[39m
[31mOpenAIError[39m                               Traceback (most recent call last)
[36mCell[39m[36m [39m[32mIn[3][39m[32m, line 9[39m
[32m      5[39m [38;5;66;03m# 伪代码演示（需要安装 deepagents 才能运行）[39;00m
[32m      6[39m [38;5;28;01mfrom[39;00m deepagents [38;5;28;01mimport[39;00m create_deep_agent
[32m      7[39m [38;5;28;01mfrom[39;00m langgraph.checkpoint.memory [38;5;28;01mimport[39;00m InMemorySaver
[32m      8[39m 
[32m----> [39m[32m9[39m agent = create_deep_agent(
[32m     10[39m     model=[33m"openai:gpt-4o"[39m,  [38;5;66;03m# 推荐用字符串格式[39;00m
[32m     11[39m     checkpointer=InMemorySaver(),
[32m     12[39m )

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/deepagents/graph.py:497[39m, in [36mcreate_deep_agent[39m[34m(model, tools, system_prompt, middleware, subagents, skills, memory, permissions, backend, interrupt_on, response_format, context_schema, checkpointer, store, debug, name, cache)[39m
[32m    495[39m     model = _build_default_model()
[32m    496[39m [38;5;28;01melse[39;00m:
[32m--> [39m[32m497[39m     model = [30;43mresolve_model[39;49m[30;43m([39;49m[30;43mmodel[39;49m[30;43m)[39;49m
[32m    498[39m _profile = _harness_profile_for_model(model, _model_spec)
[32m    499[39m [38;5;66;03m# Validate profile-level invariants (required scaffolding, private names)[39;00m

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/deepagents/_models.py:36[39m, in [36mresolve_model[39m[34m(model)[39m
[32m     33[39m [38;5;28;01mif[39;00m [38;5;28misinstance[39m(model, BaseChatModel):
[32m     34[39m     [38;5;28;01mreturn[39;00m model
[32m---> [39m[32m36[39m [38;5;28;01mreturn[39;00m [30;43minit_chat_model[39;49m[30;43m([39;49m[30;43mmodel[39;49m[30;43m,[39;49m[30;43m [39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43mapply_provider_profile[39;49m[30;43m([39;49m[30;43mmodel[39;49m[30;43m)[39;49m[30;43m)[39;49m

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/langchain/chat_models/base.py:494[39m, in [36minit_chat_model[39m[34m(model, model_provider, configurable_fields, config_prefix, **kwargs)[39m
[32m    486[39m     warnings.warn(
[32m    487[39m         [33mf[39m[33m"[39m[38;5;132;01m{[39;00mconfig_prefix[38;5;132;01m=}[39;00m[33m has been set but no fields are configurable. Set [39m[33m"[39m
[32m    488[39m         [33mf[39m[33m"[39m[33m`configurable_fields=(...)` to specify the model params that are [39m[33m"[39m
[32m    489[39m         [33mf[39m[33m"[39m[33mconfigurable.[39m[33m"[39m,
[32m    490[39m         stacklevel=[32m2[39m,
[32m    491[39m     )
[32m    493[39m [38;5;28;01mif[39;00m [38;5;129;01mnot[39;00m configurable_fields:
[32m--> [39m[32m494[39m     [38;5;28;01mreturn[39;00m [30;43m_init_chat_model_helper[39;49m[30;43m([39;49m
[32m    495[39m [30;43m        [39;49m[30;43mcast[39;49m[30;43m([39;49m[30;43m"[39;49m[30;43mstr[39;49m[30;43m"[39;49m[30;43m,[39;49m[30;43m [39;49m[30;43mmodel[39;49m[30;43m)[39;49m[30;43m,[39;49m
[32m    496[39m [30;43m        [39;49m[30;43mmodel_provider[39;49m[30;43m=[39;49m[30;43mmodel_provider[39;49m[30;43m,[39;49m
[32m    497[39m [30;43m        [39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43mkwargs[39;49m[30;43m,[39;49m
[32m    498[39m [30;43m    [39;49m[30;43m)[39;49m
[32m    499[39m [38;5;28;01mif[39;00m model:
[32m    500[39m     kwargs[[33m"[39m[33mmodel[39m[33m"[39m] = model

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/langchain/chat_models/base.py:518[39m, in [36m_init_chat_model_helper[39m[34m(model, model_provider, **kwargs)[39m
[32m    516[39m model, model_provider = _parse_model(model, model_provider)
[32m    517[39m creator_func = _get_chat_model_creator(model_provider)
[32m--> [39m[32m518[39m [38;5;28;01mreturn[39;00m [30;43mcreator_func[39;49m[30;43m([39;49m[30;43mmodel[39;49m[30;43m=[39;49m[30;43mmodel[39;49m[30;43m,[39;49m[30;43m [39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43mkwargs[39;49m[30;43m)[39;49m

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/langchain/chat_models/base.py:35[39m, in [36m_call[39m[34m(cls, **kwargs)[39m
[32m     33[39m [38;5;28;01mdef[39;00m[38;5;250m [39m[34m_call[39m([38;5;28mcls[39m: [38;5;28mtype[39m[BaseChatModel], **kwargs: Any) -> BaseChatModel:
[32m     34[39m     [38;5;66;03m# TODO: replace with operator.call when lower bounding to Python 3.11[39;00m
[32m---> [39m[32m35[39m     [38;5;28;01mreturn[39;00m [30;43mcls[39;49m[30;43m([39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43mkwargs[39;49m[30;43m)[39;49m

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/langchain_core/load/serializable.py:118[39m, in [36mSerializable.__init__[39m[34m(self, *args, **kwargs)[39m
[32m    116[39m [38;5;28;01mdef[39;00m[38;5;250m [39m[34m__init__[39m([38;5;28mself[39m, *args: Any, **kwargs: Any) -> [38;5;28;01mNone[39;00m:
[32m    117[39m [38;5;250m    [39m[33;03m""""""[39;00m  [38;5;66;03m# noqa: D419  # Intentional blank docstring[39;00m
[32m--> [39m[32m118[39m     [30;43msuper[39;49m[30;43m([39;49m[30;43m)[39;49m[30;43m.[39;49m[30;43m__init__[39;49m[30;43m([39;49m[30;43m*[39;49m[30;43margs[39;49m[30;43m,[39;49m[30;43m [39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43mkwargs[39;49m[30;43m)[39;49m

    [31m[... skipping hidden 1 frame][39m

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/langchain_openai/chat_models/base.py:1265[39m, in [36mBaseChatOpenAI.validate_environment[39m[34m(self)[39m
[32m   1251[39m         [38;5;28mself[39m.http_async_client = _build_proxied_async_httpx_client(
[32m   1252[39m             proxy=[38;5;28mself[39m.openai_proxy,
[32m   1253[39m             verify=global_ssl_context,
[32m   1254[39m             socket_options=resolved_socket_options,
[32m   1255[39m         )
[32m   1256[39m     async_specific = {
[32m   1257[39m         [33m"[39m[33mhttp_client[39m[33m"[39m: [38;5;28mself[39m.http_async_client
[32m   1258[39m         [38;5;129;01mor[39;00m _get_default_async_httpx_client(
[32m   (...)[39m[32m   1263[39m         [33m"[39m[33mapi_key[39m[33m"[39m: async_api_key_value,
[32m   1264[39m     }
[32m-> [39m[32m1265[39m     [38;5;28mself[39m.root_async_client = [30;43mopenai[39;49m[30;43m.[39;49m[30;43mAsyncOpenAI[39;49m[30;43m([39;49m
[32m   1266[39m [30;43m        [39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43mclient_params[39;49m[30;43m,[39;49m
[32m   1267[39m [30;43m        [39;49m[30;43m*[39;49m[30;43m*[39;49m[30;43masync_specific[39;49m[30;43m,[39;49m[30;43m  [39;49m[30;43;03m# type: ignore[arg-type][39;49;00m
[32m   1268[39m [30;43m    [39;49m[30;43m)[39;49m
[32m   1269[39m     [38;5;28mself[39m.async_client = [38;5;28mself[39m.root_async_client.chat.completions
[32m   1270[39m [38;5;28;01mreturn[39;00m [38;5;28mself[39m

[36mFile [39m[32m/Volumes/DATABASE/code/learn/langgraph_learn/.venv/lib/python3.14/site-packages/openai/_client.py:700[39m, in [36mAsyncOpenAI.__init__[39m[34m(self, api_key, admin_api_key, workload_identity, organization, project, webhook_secret, base_url, websocket_base_url, timeout, max_retries, default_headers, default_query, http_client, _strict_response_validation, _enforce_credentials)[39m
[32m    691[39m [38;5;28mself[39m.admin_api_key = admin_api_key
[32m    693[39m [38;5;28;01mif[39;00m (
[32m    694[39m     _enforce_credentials
[32m    695[39m     [38;5;129;01mand[39;00m [38;5;129;01mnot[39;00m [38;5;28mself[39m.api_key
[32m   (...)[39m[32m    698[39m     [38;5;129;01mand[39;00m [38;5;28mself[39m.admin_api_key [38;5;129;01mis[39;00m [38;5;28;01mNone[39;00m
[32m    699[39m ):
[32m--> [39m[32m700[39m     [38;5;28;01mraise[39;00m OpenAIError(
[32m    701[39m         [33m"[39m[33mMissing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.[39m[33m"[39m
[32m    702[39m     )
[32m    704[39m [38;5;28;01mif[39;00m organization [38;5;129;01mis[39;00m [38;5;28;01mNone[39;00m:
[32m    705[39m     organization = os.environ.get([33m"[39m[33mOPENAI_ORG_ID[39m[33m"[39m)

[31mOpenAIError[39m: Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.
```

---

## 3. Planning：任务规划系统

`TodoListMiddleware` 自动注入 `write_todos` 和 `read_todos` 工具。

```python
# ==========================================
# 模拟 Todo 工具
# ==========================================

from typing import TypedDict, Literal

class TodoItem(TypedDict):
    id: str
    content: str
    status: Literal["pending", "completed"]

# 模拟 write_todos
def write_todos(todos: list[dict]) -> dict:
    print(f"[write_todos] 创建 {len(todos)} 个任务:")
    for todo in todos:
        print(f"  [{todo['status']}] {todo['id']}: {todo['content']}")
    return {"todos": todos}

# 模拟 read_todos
def read_todos(todos: list[dict]) -> dict:
    print(f"[read_todos] 当前任务:")
    for todo in todos:
        icon = "✓" if todo['status'] == "completed" else "○"
        print(f"  {icon} {todo['content']}")
    return {"todos": todos}

# 示例：创建研究计划
research_plan = [
    {"id": "1", "content": "收集市场规模数据", "status": "pending"},
    {"id": "2", "content": "分析主要厂商份额", "status": "pending"},
    {"id": "3", "content": "梳理技术发展趋势", "status": "pending"},
    {"id": "4", "content": "撰写综合分析报告", "status": "pending"},
]

write_todos(research_plan)
print()

# 模拟完成第一个任务
research_plan[0]["status"] = "completed"
read_todos(research_plan)
```

---

## 4. Filesystem：文件系统工作空间

`FilesystemMiddleware` 自动注入 ls、read_file、write_file、edit_file 等工具。

```python
# ==========================================
# 模拟 Filesystem 工具
# ==========================================

import os
from pathlib import Path

WORKSPACE = Path("./workspace")
WORKSPACE.mkdir(exist_ok=True)

def write_file(path: str, content: str) -> str:
    full_path = WORKSPACE / path.lstrip("/")
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return f"已写入: {path}"

def read_file(path: str) -> str:
    full_path = WORKSPACE / path.lstrip("/")
    if not full_path.exists():
        return f"文件不存在: {path}"
    return full_path.read_text(encoding="utf-8")

def ls(path: str = "") -> list:
    full_path = WORKSPACE / path
    if not full_path.exists():
        return []
    return [str(p.relative_to(WORKSPACE)) for p in full_path.rglob("*") if p.is_file()]

# 示例：Agent 写入研究资料
write_file(
    "/research/market_size.md",
    """# 2024 新能源汽车市场规模

- 全球销量：1,400 万辆
- 同比增长：35%
- 中国市场占比：60%
"""
)

write_file(
    "/research/competitors.md",
    """# 主要厂商份额

| 厂商 | 份额 |
|------|------|
| BYD  | 22%  |
| Tesla| 15%  |
"""
)

print("工作空间文件列表:")
for f in ls():
    print(f"  - {f}")

print("\n读取 market_size.md:")
print(read_file("/research/market_size.md"))
```

---

## 5. Backend 系统

DeepAgents 提供多种后端来控制数据的持久化方式。

```python
# ==========================================
# Backend 系统概念演示
# ==========================================

print("DeepAgents Backend 类型:")
print()
backends = [
    ("StateBackend", "会话结束消失", "临时工作文件"),
    ("StoreBackend", "持久化", "长期记忆、用户偏好"),
    ("FilesystemBackend", "写入真实磁盘", "外部访问的文件"),
    ("CompositeBackend", "混合", "不同数据不同策略"),
]

for name, lifecycle, use_case in backends:
    print(f"  {name}:")
    print(f"    生命周期: {lifecycle}")
    print(f"    适用: {use_case}")
    print()

print("CompositeBackend 示例配置:")
print("""
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

backend = CompositeBackend(
    default=StateBackend(),  # /workspace/* → 临时
    routes={
        "/memories/": StoreBackend(store=store),  # 持久化
    },
)
""")
```

---

## 6. Sub-agent：子智能体委派

三种子智能体类型：SubAgent（同步）、CompiledSubAgent（复用 LangGraph）、AsyncSubAgent（异步）。

```python
# ==========================================
# 子智能体类型对比
# ==========================================

print("三种子智能体类型:")
print()

subagents = [
    {
        "name": "SubAgent",
        "type": "同步",
        "use_case": "最常见；阻塞式委派",
        "model": "gpt-4o-mini",
    },
    {
        "name": "CompiledSubAgent",
        "type": "同步",
        "use_case": "复用现有 LangGraph",
        "model": "任意",
    },
    {
        "name": "AsyncSubAgent",
        "type": "异步",
        "use_case": "长时间运行任务；并行执行",
        "model": "gpt-4o-mini",
    },
]

for sa in subagents:
    print(f"  {sa['name']}:")
    print(f"    类型: {sa['type']}")
    print(f"    场景: {sa['use_case']}")
    print(f"    推荐模型: {sa['model']}")
    print()

print("AsyncSubAgent 5 个管理工具:")
print("  1. start_async_task  - 启动后台任务")
print("  2. check_async_task  - 轮询状态")
print("  3. update_async_task - 发送后续指令")
print("  4. cancel_async_task - 停止任务")
print("  5. list_async_tasks  - 列出所有任务")
```

---

## 7. Skills：渐进式领域知识披露

Skills 采用三层渐进式架构，避免上下文爆炸。

```python
# ==========================================
# Skills 定义和加载
# ==========================================

from typing import TypedDict

class Skill(TypedDict):
    name: str
    description: str
    content: str

SKILLS = [
    {
        "name": "market_research",
        "description": "市场研究技能。包含行业分析方法、数据来源。",
        "content": """
# 市场研究方法论

## 分析框架
1. TAM/SAM/SOM 市场规模分析
2. 波特五力模型
3. SWOT 分析

## 数据来源
- 行业报告：McKinsey、Gartner
- 政府数据：统计局、工信部
""",
    },
    {
        "name": "financial_analysis",
        "description": "财务分析技能。包含比率分析、估值方法。",
        "content": """
# 财务分析

## 核心比率
- ROE = 净利润 / 股东权益
- ROA = 净利润 / 总资产
- 毛利率 = (收入 - 成本) / 收入
""",
    },
]

def load_skill(skill_name: str) -> str:
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"已加载技能: {skill_name}\n\n{skill['content']}"
    return f"技能 '{skill_name}' 未找到"

print("=== Layer 1: Skills 列表（常驻 System Prompt）===")
for skill in SKILLS:
    print(f"  - {skill['name']}: {skill['description']}")

print("\n=== Layer 2: 按需加载 Skill 内容 ===")
print(load_skill("market_research"))
```

---

## 8. Middleware 默认栈

`create_deep_agent()` 自动按顺序组装 10 层 Middleware。

```python
# ==========================================
# 默认 Middleware 栈
# ==========================================

middleware_stack = [
    ("1", "TodoListMiddleware", "任务规划", True),
    ("2", "SkillsMiddleware", "Skills 加载", "条件"),
    ("3", "FilesystemMiddleware", "文件操作", True),
    ("4", "SubAgentMiddleware", "子智能体委派", True),
    ("5", "SummarizationMiddleware", "自动摘要", True),
    ("6", "PatchToolCallsMiddleware", "修复不完整工具调用", True),
    ("-", "用户 Middleware", "自定义扩展", "手动"),
    ("-", "AnthropicPromptCachingMiddleware", "提示词缓存", True),
    ("-", "MemoryMiddleware", "长期记忆注入", "条件"),
    ("-", "HumanInTheLoopMiddleware", "人工审批", "条件"),
]

print("create_deep_agent 默认 Middleware 栈:")
print()
print(f"{'位置':<6} {'Middleware':<35} {'功能':<25} {'自动':<8}")
print("-" * 80)
for pos, name, func, auto in middleware_stack:
    print(f"{pos:<6} {name:<35} {func:<25} {auto:<8}")
```

---

## 9. 完整 Deep Research Agent

使用 LangGraph StateGraph 模拟 DeepAgents 的核心工作流程。

```python
# ==========================================
# DeepResearch StateGraph
# ==========================================

from pathlib import Path
import json
from copy import deepcopy
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

deep_data_path = Path("deep_research_data.json")
if not deep_data_path.exists():
    deep_data_path = Path("turtorial/LG-08-deepagent/deep_research_data.json")

deep_research_data = json.loads(deep_data_path.read_text(encoding="utf-8"))

class DeepState(TypedDict):
    query: str
    todos: list[dict]
    current_step: int
    workspace_files: list[str]
    subagent_results: list[str]
    loaded_skill: str | None
    final_report: str

def plan_node(state: DeepState) -> dict:
    print("\n[plan] 创建研究计划...")
    todos = deepcopy(deep_research_data["todos"])
    return {"todos": todos, "current_step": 0}

def skill_check(state: DeepState) -> dict:
    print("\n[skill_check] 检查所需技能...")
    if "市场" in state["query"] or "行业" in state["query"]:
        print("  -> 需要 market_research 技能")
        return {"loaded_skill": "market_research"}
    return {"loaded_skill": None}

def execute(state: DeepState) -> dict:
    step = state["current_step"]
    todos = state["todos"]
    if step >= len(todos):
        return {}
    todo = todos[step]
    print(f"\n[execute] 任务 {step+1}/{len(todos)}: {todo['content']}")
    filename = f"/research/step_{step+1}.md"
    step_output = deep_research_data["step_outputs"].get(str(step + 1), "本步骤结果已记录。")
    write_file(filename, f"# {todo['content']}\n\n{step_output}")
    todos[step]["status"] = "completed"
    return {"todos": todos, "current_step": step + 1, "workspace_files": ls()}

def parallel(state: DeepState) -> dict:
    print("\n[parallel] 启动并行子任务...")
    return {"subagent_results": deep_research_data["subagent_results"]}

def summarize(state: DeepState) -> dict:
    print("\n[summarize] 汇总研究成果...")
    completed = sum(1 for t in state['todos'] if t['status'] == 'completed')
    report = f"""
# DeepResearch 报告: {state['query']}

## 完成情况
- 已完成: {completed}/{len(state['todos'])}
- 技能: {state.get('loaded_skill', '无')}
- 子任务: {len(state.get('subagent_results', []))} 条
- 文件: {len(state.get('workspace_files', []))} 个
""".strip()
    return {"final_report": report}

def should_continue(state: DeepState) -> Literal["execute", "parallel", "summarize"]:
    step = state["current_step"]
    total = len(state["todos"])
    if step >= total:
        return "summarize"
    elif step == 2:
        return "parallel"
    return "execute"

print("DeepResearch 节点函数定义完成！")
```

```python
# ==========================================
# 编译 StateGraph
# ==========================================

builder = StateGraph(DeepState)

builder.add_node("plan", plan_node)
builder.add_node("skill_check", skill_check)
builder.add_node("execute", execute)
builder.add_node("parallel", parallel)
builder.add_node("summarize", summarize)

builder.add_edge(START, "plan")
builder.add_edge("plan", "skill_check")
builder.add_edge("skill_check", "execute")
builder.add_conditional_edges(
    "execute",
    should_continue,
    {"execute": "execute", "parallel": "parallel", "summarize": "summarize"}
)
builder.add_edge("parallel", "execute")
builder.add_edge("summarize", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

print("DeepResearch Agent 编译成功！")
print("流程: START → plan → skill_check → execute → [循环] → summarize → END")
```

```python
# ==========================================
# 执行 DeepResearch Agent
# ==========================================

print("=" * 60)
print("执行 DeepResearch Agent")
print("=" * 60)

result = graph.invoke(
    {
        "query": "分析2024年新能源汽车行业格局",
        "todos": [],
        "current_step": 0,
        "workspace_files": [],
        "subagent_results": [],
        "loaded_skill": None,
        "final_report": "",
    },
    config={"configurable": {"thread_id": "research_001"}}
)

print("\n" + "=" * 60)
print("最终报告:")
print("=" * 60)
print(result["final_report"])
```

---

## 10. 与简单 Agent 的对比

| 维度 | 简单 ReAct Agent | Deep Agent |
|------|-----------------|------------|
| 任务规划 | 无，随机调用工具 | Todo 列表，有序执行 |
| 工作空间 | 无，全靠上下文 | 文件系统持久化 |
| 并行处理 | 无，单线程 | AsyncSubAgent 并行 |
| 领域知识 | 全部塞进 prompt | Skills 渐进加载 |
| 上下文管理 | 手动清理 | SummarizationMiddleware 自动摘要 |
| 人工审批 | 无 | HumanInTheLoopMiddleware |
| 任务复杂度 | 简单问答 | 深度研究、报告撰写 |

---

## 11. 速查表 / Cheat Sheet

```python
# Planning: Todo 工具
write_todos(todos=["1. ...", "2. ..."])
read_todos()

# Filesystem: 文件操作
write_file(path="/workspace/result.md", content="...")
read_file(path="/workspace/result.md")
ls(path="/workspace")

# Sub-agent: 委派任务
task(description="分析竞品", subagent_type="research-agent")

# AsyncSubAgent
start_async_task("deep-researcher", "Research topic X")
check_async_task("task_id")

# Skills: 渐进加载
load_skill("market_research")

# Middleware: 组合能力
agent = create_deep_agent(
    model="openai:gpt-4o",
    middleware=[
        TodoListMiddleware(),
        FilesystemMiddleware(),
        SubAgentMiddleware(),
        SkillMiddleware(skills=SKILLS),
    ],
)
```

**记忆口诀**：

> **Planning 列大纲，Filesystem 存文件，Sub-agent 派任务，Skills 按需加载。Middleware 像乐高，组装出 Deep Agent。**

---

## 12. 课后练习

1. **Todo 练习**：为『写周报』任务创建 5 个子任务
2. **Filesystem 练习**：在 /workspace 下创建研究笔记文件
3. **Sub-agent 练习**：定义 2 个子智能体，用 task 委派任务
4. **AsyncSubAgent 练习**：模拟 start_async_task + check_async_task
5. **Skills 练习**：创建 2 个 Skill 并模拟 load_skill 加载
6. **综合实战**：组合所有能力，构建 Deep Research Agent

## 13. 源码架构深度解析

本节从源码角度深入理解 DeepAgents 的内部实现。

### 13.1 create_deep_agent 的组装流程

`create_deep_agent()` 的核心逻辑分为 7 步：
1. 模型解析（resolve_model）
2. 验证不可排除的中间件
3. 处理子代理规格
4. 自动添加通用子代理
5. 组装主代理中间件栈
6. 组装系统提示
7. 创建最终 Agent

让我们通过打印中间件栈来观察组装结果：

```python
# 演示中间件栈的组装
from deepagents import create_deep_agent
from deepagents.backends import StateBackend

# 创建 agent 并观察中间件栈
agent = create_deep_agent(
    model='openai:gpt-4o-mini',  # 使用便宜模型演示
    backend=StateBackend(),
)

print('=== DeepAgent 组装完成 ===')
print(f'Agent 名称: {agent.name}')
print('递归限制: 9999')
print('\n提示：中间件栈在内部通过 create_agent 的 middleware 参数传入')
```

### 13.2 系统提示组装顺序

DeepAgents 的系统提示按以下顺序组装：

`USER` -> (`BASE` 或 `CUSTOM`) -> `SUFFIX`

- **USER**：用户传入的 `system_prompt` 参数，优先级最高
- **BASE**：SDK 默认的 `BASE_AGENT_PROMPT`，定义 Deep Agent 行为指南
- **CUSTOM**：`HarnessProfile.base_system_prompt`，覆盖 BASE（用于模型调优）
- **SUFFIX**：`HarnessProfile.system_prompt_suffix`，放在最靠近历史的位置

为什么 SUFFIX 在最后？因为模型对系统提示末尾的关注度最高（attention 机制）。

```python
# 演示系统提示组装
from deepagents import create_deep_agent
from deepagents.backends import StateBackend

# 用户自定义系统提示
user_prompt = '你是一位专注于数据分析的研究员。请使用中文回复。'

agent = create_deep_agent(
    model='openai:gpt-4o-mini',
    system_prompt=user_prompt,
    backend=StateBackend(),
)

print('=== 系统提示组装演示 ===')
print('最终系统提示 = 用户提示 + 默认 BASE_AGENT_PROMPT')
print('\n用户提示（USER）在最前面，确保用户指令优先于 SDK 默认行为')
```

### 13.3 子代理的继承规则

子代理可以继承或覆盖父代理的多个属性：

```python
from deepagents import create_deep_agent, SubAgent
from deepagents.middleware.filesystem import FilesystemPermission
from deepagents.backends import StateBackend

# 定义子代理，演示继承行为
researcher = {
    'name': 'financial_analyst',
    'description': '专业的财务分析师，擅长分析财报数据',
    'system_prompt': '你是一位资深财务分析师。请基于提供的财务数据进行分析。',
    # tools 未声明 -> 继承父代理工具
    # permissions 未声明 -> 继承父代理权限
    # interrupt_on 未声明 -> 继承父代理 HITL 配置
    # model 未声明 -> 继承父代理模型
}

# 定义带有独立权限的子代理
code_reviewer = {
    'name': 'code_reviewer',
    'description': '代码审查专家',
    'system_prompt': '你是一位代码审查专家。请检查代码质量。',
    'permissions': [
        FilesystemPermission(
            operations=['read'],
            paths=['/workspace/src/*'],
            mode='allow'
        ),
        FilesystemPermission(
            operations=['write'],
            paths=['/workspace/reviews/*'],
            mode='allow'
        ),
    ],
    # 独立权限规则，不继承父代理
}

print('=== 子代理继承规则 ===')
print('financial_analyst:')
print('  - tools: 继承父代理')
print('  - permissions: 继承父代理')
print('  - model: 继承父代理')
print('\ncode_reviewer:')
print('  - tools: 继承父代理')
print('  - permissions: 独立配置（只读 /workspace/src/）')
print('  - model: 继承父代理')
```

### 13.4 DeltaChannel：O(N) Checkpoint 优化

DeepAgents 使用 `_DeepAgentState` 自定义状态模式，通过 `DeltaChannel` 将 checkpoint 增长从 O(N^2) 降到 O(N)。

```python
# DeltaChannel 优化演示

# 普通 Channel：每次 checkpoint 保存完整消息列表
# N 轮对话的总存储 = 1 + 2 + 3 + ... + N = O(N^2)

# DeltaChannel：只保存增量变化
# N 轮对话的总存储 = N = O(N)

print('=== DeltaChannel 优化 ===')
print('普通 Channel 总存储（100轮）: ~5,050 条消息当量')
print('DeltaChannel 总存储（100轮）: ~100 条消息当量')
print('压缩比: ~50x')
print('\nsnapshot_frequency=50: 每50步强制完整快照，防止增量链过长')
```

## 14. 沙箱系统与代码执行

DeepAgents 支持多种沙箱后端，用于在隔离环境中执行代码。

### 14.1 Backend 协议层次

```
+-----------------------------------------------+
|        SandboxBackendProtocol                 |
|  (BackendProtocol + execute() + id 属性)      |
+-----------------------------------------------+
|        BackendProtocol                        |
|  ls() / read() / write() / edit()             |
|  grep() / glob() / upload_files()             |
+-----------------------------------------------+
```

- `BackendProtocol`：基础文件操作协议
- `SandboxBackendProtocol`：扩展了代码执行能力

### 14.2 LocalShellBackend：本地开发调试

`LocalShellBackend` 直接在主机上执行命令，**不提供沙箱隔离**，仅用于本地开发。

```python
from deepagents.backends import LocalShellBackend

# 创建本地 shell 后端（仅限开发环境！）
backend = LocalShellBackend(
    root_dir='/tmp',
    virtual_mode=True,       # 文件路径映射模式
    timeout=60,              # 默认超时 60 秒
    max_output_bytes=50_000,
    inherit_env=True,        # 继承环境变量
)

# 执行命令
result = backend.execute("echo 'Hello from LocalShell' && pwd")
print(f'退出码: {result.exit_code}')
print(f'输出: {result.output}')
print(f'截断: {result.truncated}')

# 文件操作（继承自 FilesystemBackend）
write_result = backend.write('/test.txt', 'Hello World')
print(f'\n写入结果: {write_result.path or write_result.error}')

read_result = backend.read('/test.txt')
content = read_result.file_data['content'] if read_result.file_data else read_result.error
print(f'读取结果: {content}')
```

### 14.3 沙箱后端对比

| 特性 | StateBackend | FilesystemBackend | LocalShellBackend | ModalSandbox | DaytonaSandbox | RunloopSandbox |
|------|-------------|-------------------|-------------------|--------------|----------------|----------------|
| **持久化** | 会话内 | 真实磁盘 | 真实磁盘 | 容器内 | 沙箱内 | Devbox 内 |
| **execute()** | 不支持 | 不支持 | 支持 | 支持 | 支持 | 支持 |
| **隔离性** | 完全隔离 | 无隔离 | 无隔离 | 容器隔离 | 沙箱隔离 | Devbox 隔离 |
| **GPU 支持** | 无 | 主机 GPU | 主机 GPU | 支持 | 不支持 | 不支持 |
| **成本** | 免费 | 免费 | 免费 | 按秒计费 | 按秒计费 | 按秒计费 |

### 14.4 自定义沙箱后端

通过继承 `BaseSandbox` 创建自定义沙箱（以 Docker 为例）：

```python
# 自定义 Docker 沙箱后端示例
from deepagents.backends.sandbox import BaseSandbox
from deepagents.backends.protocol import ExecuteResponse, FileUploadResponse, FileDownloadResponse

class DockerSandbox(BaseSandbox):
    """基于 Docker 容器的沙箱后端"""
    
    def __init__(self, container_name: str):
        self._container = container_name
        self._default_timeout = 300
        
    @property
    def id(self):
        return self._container
    
    def execute(self, command, *, timeout=None):
        import subprocess
        effective = timeout or self._default_timeout
        result = subprocess.run(
            ['docker', 'exec', self._container, 'sh', '-c', command],
            capture_output=True, text=True, timeout=effective
        )
        return ExecuteResponse(
            output=result.stdout + ('\n' + result.stderr if result.stderr else ''),
            exit_code=result.returncode,
        )
    
    def upload_files(self, files):
        import tempfile, subprocess, os
        responses = []
        for path, content in files:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(content)
                tmp.flush()
                subprocess.run(
                    ['docker', 'cp', tmp.name, f'{self._container}:{path}'],
                    check=True
                )
                os.unlink(tmp.name)
            responses.append(FileUploadResponse(path=path, error=None))
        return responses
    
    def download_files(self, paths):
        import tempfile, subprocess, os
        responses = []
        for path in paths:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                result = subprocess.run(
                    ['docker', 'cp', f'{self._container}:{path}', tmp.name],
                    capture_output=True
                )
                if result.returncode == 0:
                    with open(tmp.name, 'rb') as f:
                        content = f.read()
                    responses.append(FileDownloadResponse(path=path, content=content, error=None))
                else:
                    responses.append(FileDownloadResponse(path=path, content=None, error='file_not_found'))
                os.unlink(tmp.name)
        return responses

print('=== DockerSandbox 示例 ===')
print('使用方式:')
print("  backend = DockerSandbox(container_name='my-sandbox')")
print("  agent = create_deep_agent(model='...', backend=backend)")
print('\n关键点:')
print('  1. 继承 BaseSandbox 自动获得 ls/read/edit/grep/glob')
print('  2. 只需实现 execute/upload_files/download_files/id')
print('  3. 文件操作通过服务器端脚本完成')
```

### 14.5 BaseSandbox 的服务器端脚本机制

BaseSandbox 的核心设计：**子类只需实现 `execute()`，文件操作通过服务器端 Python 脚本完成**。

以 `read()` 为例：
1. 生成包含 path/offset/limit 的 Python 脚本
2. 通过 `execute()` 在沙箱中执行该脚本
3. 解析脚本输出的 JSON 结果
4. 返回 `ReadResult`

这种设计的优点：
- 沙箱提供者只需实现命令执行和文件传输
- 所有文件操作逻辑统一在 BaseSandbox 中
- 分页、编码检测、错误处理等行为一致

以 `edit()` 为例：
- 小 payload（< 50KB）：内联编辑，单次 execute 调用
- 大 payload（>= 50KB）：上传临时文件，服务器端替换，自动清理

## 15. 完整实验：带沙箱的 Deep Research Agent

组合所有能力，构建一个能在沙箱中执行代码的深度研究 Agent。

```python
# 完整实验：带 LocalShellBackend 的 Deep Research Agent
# 注意：此示例使用 LocalShellBackend，仅在本地开发环境运行！

from deepagents import create_deep_agent, SubAgent
from deepagents.middleware.filesystem import FilesystemPermission
from deepagents.backends import LocalShellBackend

# 创建本地 shell 后端
backend = LocalShellBackend(
    root_dir='/tmp/deep_research',
    virtual_mode=True,
    timeout=120,
    inherit_env=True,
)

# 定义研究子代理
researcher = {
    'name': 'data_researcher',
    'description': '数据研究员，擅长收集和整理数据',
    'system_prompt': '你是一位数据研究员。请使用 available tools 收集数据并保存到文件。',
    'permissions': [
        FilesystemPermission(
            operations=['read', 'write'],
            paths=['/workspace/data/*'],
            mode='allow'
        ),
    ],
}

# 定义分析子代理
analyst = {
    'name': 'data_analyst',
    'description': '数据分析师，擅长数据分析和可视化',
    'system_prompt': '你是一位数据分析师。请读取数据文件，进行分析并生成报告。',
    'permissions': [
        FilesystemPermission(
            operations=['read'],
            paths=['/workspace/data/*'],
            mode='allow'
        ),
        FilesystemPermission(
            operations=['write'],
            paths=['/workspace/reports/*'],
            mode='allow'
        ),
    ],
}

# 创建主 agent（使用便宜模型演示）
agent = create_deep_agent(
    model='openai:gpt-4o-mini',
    backend=backend,
    subagents=[researcher, analyst],
    permissions=[
        FilesystemPermission(
            operations=['read', 'write', 'edit'],
            paths=['/workspace/*'],
            mode='allow'
        ),
    ],
)

print('=== Deep Research Agent 创建成功 ===')
print('能力:')
print('  - Planning: write_todos / read_todos')
print('  - Filesystem: ls / read_file / write_file / edit_file / glob / grep')
print('  - Execution: execute（在 /tmp/deep_research 中运行命令）')
print('  - Sub-agents: data_researcher + data_analyst')
print('  - 权限: /workspace/ 目录读写')
print('\n使用方式:')
print("  result = agent.invoke({'messages': ['请研究 Python 性能优化并写报告']})")
```

## 课程总结

### 核心知识点

1. **Planning**：write_todos / read_todos 自主任务分解
2. **Filesystem**：多种 Backend（State/Store/Filesystem/Composite）
3. **Sub-agent**：同步 SubAgent + 异步 AsyncSubAgent（5 个管理工具）
4. **Skills**：SKILL.md + YAML frontmatter，三层渐进式披露
5. **Middleware**：10 层默认栈，洋葱模型执行
6. **源码**：create_deep_agent() 7 步组装，DeltaChannel O(N) checkpoint
7. **沙箱**：BaseSandbox 协议，Modal/Daytona/Runloop/LocalShell 四种实现

### 架构口诀

> "Planning 列大纲，Filesystem 存文件，Sub-agent 派任务，Skills 按需加载。Middleware 像洋葱，BaseSandbox 做隔离。"
