# LG-01: LangGraph 基础与图构建

> **阶段**: LG-01 | **难度**: 入门 | **预计时长**: 3-4 小时

## 学习目标
- 理解 LangGraph 的核心理念
- 掌握 State、Node、Edge 三大基石概念
- 能够独立构建并运行一个简单的 StateGraph
- 理解 Reducer 机制与状态更新原理
- 了解 Channel 底层机制与 Runtime Context

```python
# 安装依赖（如未安装请取消注释）
# !pip install -U langgraph langchain langchain-openai
```

## 1. 案例背景：旅行计划助手

本节实现一个能体现 `State` 和 `Reducer` 作用的案例：`TravelPlannerBot`。

假设用户会连续提出这些请求：

- `帮我规划一个北京 3 天亲子游`
- `再帮我规划一个上海 2 天美食游`
- `看看我之前做过哪些计划`

先看两个设计问题：

1. 多轮生成的旅行计划存在哪里？
2. 新计划怎么自动追加到总列表，而不是覆盖旧结果？

我们这节课会把它组织成一张图：

```text
START
  → parse_request
    ├─ create_plan → extract_trip_info → build_plan → save_plan → reply_plan → END
    ├─ show_history → format_history → END
    └─ clarify → ask_clarification → END
```

> 先看案例整体流程，再拆它在图里的状态、节点、边和合并规则。

## 1.1 迁移图：同一机制换到胰腺癌辅助问诊

同一套机制换到更严肃的医疗辅助场景，也不是先背 API，而是先看“人怎么自然处理”。例如胰腺癌辅助问诊里，医生会把症状、危险因素、检查线索和缺失信息放在脑中一起判断；Graph 不能这样隐式协作，所以必须把共享病例、处理步骤、分支规则和证据累积显式拆开。

![胰腺癌辅助问诊中的 LangGraph 基础角色](images/pancreatic-cancer-graph-basics.svg)

这张图不是让 `TravelPlannerBot` 变成医疗系统，而是帮助你迁移本节的四个基础概念：

- `State`：从“旅行计划列表”迁移成“病例共享工作台”。
- `Node`：从“提取目的地、生成计划”迁移成“提取症状、整理检查线索”。
- `Edge / Router`：从“创建计划 / 查询历史 / 澄清”迁移成“信息完整 / 信息不足 / 高风险提示”。
- `Reducer`：从“累计旅行计划”迁移成“累计证据列表”，防止新证据覆盖旧证据。

## 2. 核心概念：图和链的区别

传统的 Chain 更像线性执行：`A → B → C`。

LangGraph 是图结构：可以分支、循环、并行，还能把共享状态保留下来。

**五个核心概念**：State、Node、Edge、Reducer、compile/invoke/stream

> **State 是共享数据，Node 是处理步骤，Edge 是流转规则，Reducer 是合并规则，compile/invoke/stream 是运行方式。**

## 3. State —— 图里的共享数据

这次要把 State 理解成：**这张图的共享记忆**。

旅行计划案例里，最关键的不是 `destination` 这种临时字段，而是 `travel_plans` 这种会跨轮次累计的数据。

```python
from typing import TypedDict, Annotated
from operator import add
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    intent: str
    destination: str
    days: int
    style: str
    current_plan: dict
    travel_plans: Annotated[list[dict], add]
    response: str


print("TravelState 定义完成!")
```

### 3.1 这个 State 里的关键字段

- `current_plan` 表示这一轮刚生成的计划
- `travel_plans` 表示所有轮次累计出来的总计划列表
- `messages` 表示完整对话历史

这三个字段能直接体现：State 不是临时变量，而是给后续节点和后续轮次复用的共享记忆。

```python
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class TravelStateModel(BaseModel):
    destination: str = ""
    intent: str = ""
    response: str = ""
    travel_plans: Annotated[list[dict], add] = Field(default_factory=list)


@dataclass
class TravelStateData:
    destination: str = ""
    intent: str = ""
    response: str = ""
    travel_plans: list[dict] = field(default_factory=list)


print("TypedDict / Pydantic / dataclass 示例已准备")
```

## 4. Reducer —— `travel_plans` 的累加规则

Reducer 回答的是：**旧值和新值碰到一起时，怎么合并？**

这个案例里会用到两类 reducer：

- `travel_plans: Annotated[list[dict], add]`：新计划追加进总列表
- `messages: Annotated[list[AnyMessage], add_messages]`：消息历史追加并去重

```python
from langchain_core.messages import HumanMessage

plan_a = {"destination": "北京", "days": 3, "style": "亲子"}
plan_b = {"destination": "上海", "days": 2, "style": "美食"}

travel_plans = add([plan_a], [plan_b])
print("travel_plans 合并结果:", travel_plans)

messages = add_messages([HumanMessage(content="北京 3 天亲子游")], [HumanMessage(content="上海 2 天美食游")])
print("messages 条数:", len(messages))
```

```python
def unique_append(old: list[str], new: list[str]) -> list[str]:
    merged = old.copy()
    for item in new:
        if item not in merged:
            merged.append(item)
    return merged


def merge_dicts(old: dict, new: dict) -> dict:
    return {**old, **new}


class ReducerShowcaseState(TypedDict):
    intent: str
    tags: Annotated[list[str], unique_append]
    metadata: Annotated[dict, merge_dicts]


print("更多 reducer 示例已定义")
```

## 5. Node —— 图里的处理单元

Node 就是一个函数：接收 `state`，返回一个 `dict`。

这个案例里最关键的拆法是：

- `build_plan` 只负责生成当前计划
- `save_plan` 只负责把当前计划追加进 `travel_plans`

```python
def parse_request(state: TravelState) -> dict:
    text = state["messages"][-1].content
    if "看看" in text or "历史" in text or "之前" in text:
        return {"intent": "show_history"}
    if "规划" in text or "旅行" in text or "旅游" in text:
        return {"intent": "create_plan"}
    return {"intent": "clarify"}


def extract_trip_info(state: TravelState) -> dict:
    text = state["messages"][-1].content
    destination = "北京" if "北京" in text else "上海" if "上海" in text else ""
    days = 3 if "3天" in text else 2 if "2天" in text else 0
    style = "亲子" if "亲子" in text else "美食" if "美食" in text else "轻松"
    return {
        "destination": destination,
        "days": days,
        "style": style,
    }


def build_plan(state: TravelState) -> dict:
    plan = {
        "destination": state["destination"],
        "days": state["days"],
        "style": state["style"],
        "summary": f"{state['destination']}{state['days']}天{state['style']}旅行计划",
    }
    return {"current_plan": plan}


def save_plan(state: TravelState) -> dict:
    return {"travel_plans": [state["current_plan"]]}


def reply_plan(state: TravelState) -> dict:
    return {"response": f"已为你生成：{state['current_plan']['summary']}"}


def format_history(state: TravelState) -> dict:
    plans = state.get("travel_plans", [])
    if not plans:
        return {"response": "你目前还没有保存过旅行计划。"}

    lines = [f"{idx + 1}. {plan['summary']}" for idx, plan in enumerate(plans)]
    return {"response": "你保存过的旅行计划有：\n" + "\n".join(lines)}


def ask_clarification(state: TravelState) -> dict:
    return {"response": "请告诉我目的地、天数和旅行偏好，例如：北京3天亲子游。"}


print("所有节点函数已定义")
```

## 6. Edge —— 普通边与条件边

同一个案例里会同时出现两种边。

- **普通边**：固定流水线，例如 `build_plan → save_plan → reply_plan`
- **条件边**：根据 State 决定下一步去哪，例如 `parse_request` 后分成建计划 / 查历史 / 澄清

```python
from langgraph.graph import StateGraph, START, END


def route_by_intent(state: TravelState) -> str:
    if state["intent"] == "create_plan":
        return "extract_trip_info"
    if state["intent"] == "show_history":
        return "format_history"
    return "ask_clarification"


def route_after_extract(state: TravelState) -> str:
    if state["destination"] and state["days"] > 0:
        return "build_plan"
    return "ask_clarification"


builder = StateGraph(TravelState)
builder.add_node("parse_request", parse_request)
builder.add_node("extract_trip_info", extract_trip_info)
builder.add_node("build_plan", build_plan)
builder.add_node("save_plan", save_plan)
builder.add_node("reply_plan", reply_plan)
builder.add_node("format_history", format_history)
builder.add_node("ask_clarification", ask_clarification)

builder.add_edge(START, "parse_request")
builder.add_edge("build_plan", "save_plan")
builder.add_edge("save_plan", "reply_plan")
builder.add_edge("reply_plan", END)
builder.add_edge("format_history", END)
builder.add_edge("ask_clarification", END)

builder.add_conditional_edges(
    "parse_request",
    route_by_intent,
    {
        "extract_trip_info": "extract_trip_info",
        "format_history": "format_history",
        "ask_clarification": "ask_clarification",
    },
)

builder.add_conditional_edges(
    "extract_trip_info",
    route_after_extract,
    {
        "build_plan": "build_plan",
        "ask_clarification": "ask_clarification",
    },
)

print("普通边和条件边已添加")
```

### 6.1 回到案例总图：现在再看一遍会更清楚

```text
START
  → parse_request
    ├─ create_plan → extract_trip_info -(条件判断)-> build_plan → save_plan → reply_plan → END
    ├─ show_history → format_history → END
    └─ clarify → ask_clarification → END
```

这张图里有三件事需要看清楚：

1. 所有请求先进入 `parse_request`
2. 先靠条件边按意图分流
3. 进入建计划分支后，再靠普通边跑固定流水线

## 7. compile / invoke / stream

五步走还是一样：定义 State → 添加 Node → 连接普通边 → 连接条件边 → `compile()`。

```python
graph = builder.compile()
print("图编译成功！")
print("create_plan 分支: START -> parse_request -> extract_trip_info -> build_plan -> save_plan -> reply_plan -> END")
print("show_history 分支: START -> parse_request -> format_history -> END")
print("clarify 分支: START -> parse_request -> ask_clarification -> END")
```

```python
from IPython.display import Image, display

png_bytes = graph.get_graph().draw_mermaid_png()
display(Image(data=png_bytes))
print("上图展示了 TravelPlannerBot 的图结构")
```

## 8. 完整案例验证

下面用三轮输入直接验证：先新增两条计划，再查询历史。

```python
state = {
    "messages": [],
    "travel_plans": [],
}

state = graph.invoke({
    **state,
    "messages": [HumanMessage(content="帮我规划一个北京3天亲子游")],
})
print("第 1 轮回复:", state["response"])
print("累计计划数:", len(state["travel_plans"]))
```

```python
state = graph.invoke({
    **state,
    "messages": [HumanMessage(content="再帮我规划一个上海2天美食游")],
})
print("第 2 轮回复:", state["response"])
print("累计计划数:", len(state["travel_plans"]))
```

```python
state = graph.invoke({
    **state,
    "messages": [HumanMessage(content="看看我之前做过哪些计划")],
})
print("第 3 轮回复:")
print(state["response"])
print("最终 travel_plans:", state["travel_plans"])
```

```python
print("=" * 60)
print("使用 stream 观察中间状态")
print("=" * 60)
for chunk in graph.stream({
    "messages": [HumanMessage(content="帮我规划一个北京3天亲子游")],
    "travel_plans": [],
}):
    for node_name, node_state in chunk.items():
        print(f"节点: {node_name}")
        print(node_state)
```

## 9. MessagesState —— 聊天场景的预制模板

如果只是为了做聊天机器人，LangGraph 已经预制了一个最常用的 State 模板：

```python
from langgraph.graph import MessagesState


class TravelChatState(MessagesState):
    intent: str
    travel_plans: Annotated[list[dict], add]


print("MessagesState 预置字段: messages: list[Message]")
```

## 10. Runtime Context

除了 State 里的业务数据，节点还可以通过 `config` 读取运行时上下文，例如用户 ID、租户 ID、权限等。

```python
from dataclasses import dataclass
from typing import Optional
from langchain_core.runnables import RunnableConfig


@dataclass
class GraphContext:
    user_id: str
    tenant_id: Optional[str] = None
    user_permissions: list[str] | None = None
    api_keys: dict | None = None

    def __post_init__(self):
        if self.user_permissions is None:
            self.user_permissions = []
        if self.api_keys is None:
            self.api_keys = {}


def node_with_context(state: TravelState, config: RunnableConfig):
    user_id = config.get("configurable", {}).get("user_id", "anonymous")
    return {"response": f"用户 {user_id} 的旅行请求已处理"}


print("Runtime Context 示例完成")
```

## 11. 课后练习

1. 扩展 `TravelPlannerBot`：增加一个节点，在保存前校验目的地和天数是否为空
2. 修改图结构：让生成计划失败后重试一次
3. 尝试使用 `MessagesState` 重写本案例
4. 自定义 Reducer：实现一个去重的 `travel_plans` 合并器
5. 增加一个新分支：`删除某条旅行计划`
6. 增加一个新分支：`只查看最近一次生成的计划`

---
**下一节**: LG-02 Tools 深度掌握
