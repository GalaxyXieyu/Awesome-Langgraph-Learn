# Human-in-the-Loop (HIL) 实现指南

本文档总结了在LangGraph中实现Human-in-the-Loop功能的两种主要方法：

1. **工具包装器（Wrapper）方式** - 适用于Agent工具调用的暂停
2. **通用中断节点方式** - 适用于流程节点间的确认和暂停

---

## 🎯 方法一：工具包装器（Wrapper）实现自动暂停

核心思想是：**通过Graph的状态（State）来动态决定工具的行为模式。** 当模式为 `'interactive'` 时，工具不直接执行，而是抛出一个 `HumanInterrupt` 信号，LangGraph引擎会自动捕捉这个信号并暂停整个流程，等待您的指令。

### **实现步骤**

1.  **创建工具包装器 (`wrapper.py`)**
    *   包装器函数会检查传入的 `state` 字典里是否有一个 `mode` 字段。
    *   如果 `mode == 'copilot'`，工具被包装成可以直接执行的模式。
    *   如果 `mode == 'interactive'`，工具被包装成会抛出 `HumanInterrupt` 中断信号的模式。

2.  **在Graph的State中定义`mode`**
    *   在你的 `IntelligentResearchState` (或任何Graph State) 中，必须有一个 `mode: str` 字段。
    *   在开始运行Graph前，你需要为这个`state`的`mode`字段赋值，例如 `state['mode'] = 'interactive'`。

3.  **在Graph节点中正确获取工具**
    *   在需要调用Agent的节点（例如 `research_node`）中，不能直接导入和使用工具。
    *   必须通过调用工具获取函数（例如 `await get_research_tools(state)`）来创建Agent。
    *   **关键点**：必须把当前节点的 `state` 传递进去。这样，工具包装器才能知道当前的 `mode` 是什么，从而决定是直接运行还是暂停。

4.  **创建支持中断的Agent**
    *   在使用 `create_react_agent` 创建Agent时，除了传入包装好的工具外，还必须设置 `interrupt_before_tools=True`。
    *   这个参数告诉ReAct Agent在**决定**使用工具后、**实际执行**工具前，产生一个中断点。这对于实现Human-in-the-loop至关重要。

---

### ⚠️ **关键注意事项**

1.  **绝对不要在Graph节点中捕获 `Interrupt`**
    *   这是最重要也最容易出错的一点。`HumanInterrupt` **不是一个程序错误（Exception）**，而是LangGraph设计的**正常操作信号**，用于暂停流程。
    *   如果在你的节点函数（如 `research_node`）中用 `try...except` 块把Agent的调用包起来，就会错误地把这个正常的暂停信号当作异常处理掉，导致Graph无法暂停，陷入循环。
    *   **正确做法**：移除包裹Agent调用的 `try...except` 块，让 `Interrupt` 信号自然地从节点中抛出，LangGraph引擎会正确处理它。

2.  **`interrupt_before_tools=True` 参数不可或缺**
    *   对于ReAct Agent，如果忘记在创建时设置这个参数，即使工具被正确包装，Agent也不会在工具执行前暂停。

3.  **确保`state`的正确传递**
    *   从Graph的初始状态，到每一个节点，再到工具获取函数，`state` 必须被正确地一路传递下去。它是连接整个机制的“数据总线”。

---

### **流程总结**

`State` 定义模式 -> `节点` 传递State -> `Wrapper` 根据模式包装工具 -> `Agent` 在调用工具时触发中断 -> `LangGraph引擎` 捕捉中断并暂停。

开发者最需要注意的就是不要用 `try...except` 错误地拦截了这个中断信号。

---

## 🚀 方法二：通用中断节点实现确认暂停

这是一种更直接的方式，适用于在流程的关键节点进行用户确认，比如大纲确认、参数编辑等场景。

### **核心设计**

通过封装的工厂函数创建标准化的中断节点，支持：
- 统一的消息格式
- 自动模式适配（Interactive/Copilot）
- 可自定义的数据获取和响应处理
- 非阻塞的异步中断机制

### **使用方法**

#### **1. 基础确认节点**

```python
from common import create_confirmation_node

# 创建大纲确认节点
def get_outline_data(state):
    """获取大纲数据用于确认"""
    outline = state.get("outline", {})
    return {
        "title": outline.get("title", ""),
        "executive_summary": outline.get("executive_summary", ""),
        "sections_text": format_sections(outline.get("sections", [])),
        "methodology": outline.get("methodology", ""),
        "estimated_length": outline.get("estimated_length", 0),
        "target_audience": outline.get("target_audience", "")
    }

def process_outline_response(state, response_data):
    """处理大纲确认响应"""
    if response_data.get("approved"):
        state["approval_status"]["outline_confirmation"] = True
        # 可以添加其他自定义处理逻辑
    return state

# 创建节点
outline_confirmation = create_confirmation_node(
    node_name="outline_confirmation",
    title="大纲确认",
    message_template="""请确认以下深度研究报告大纲：

    标题：{title}
    摘要：{executive_summary}
    章节结构：
    {sections_text}

    研究方法：{methodology}
    预估字数：{estimated_length:,}字
    目标读者：{target_audience}""",
    get_data_func=get_outline_data,
    process_response_func=process_outline_response
)
```

#### **2. 参数编辑节点**

```python
from common import create_parameter_edit_node

# 创建参数编辑节点
parameter_edit = create_parameter_edit_node(
    node_name="parameter_edit",
    title="参数编辑",
    message_template="请编辑以下参数：\n{parameters}",
    get_data_func=get_parameters_data,
    allow_edit=True  # 允许编辑
)
```

#### **3. 通用中断节点**

```python
from common import create_interrupt_node

# 创建自定义中断节点
custom_interrupt = create_interrupt_node(
    node_name="custom_check",
    action_name="confirm_custom_action",
    description_template="请确认：{action_description}",
    get_interrupt_data_func=get_custom_data,
    process_response_func=process_custom_response,
    allow_edit=False,
    auto_approve_in_copilot=True
)
```

### **在Graph中使用**

```python
from langgraph.graph import StateGraph, END, START

def create_research_graph():
    workflow = StateGraph(DeepResearchState)

    # 添加节点
    workflow.add_node("outline_generation", outline_generation)
    workflow.add_node("outline_confirmation", outline_confirmation)  # 使用封装的中断节点
    workflow.add_node("report_generation", report_generation)

    # 设置流程
    workflow.add_edge(START, "outline_generation")
    workflow.add_edge("outline_generation", "outline_confirmation")

    # 添加条件路由
    workflow.add_conditional_edges(
        "outline_confirmation",
        route_after_outline_confirmation,  # 根据确认结果路由
        {
            "outline_generation": "outline_generation",  # 拒绝时重新生成
            "report_generation": "report_generation"     # 通过时继续
        }
    )

    workflow.add_edge("report_generation", END)
    return workflow
```

### **路由函数适配**

```python
def route_after_outline_confirmation(state: DeepResearchState) -> str:
    """大纲确认后的路由 - 适配通用中断节点"""
    # 检查通用中断节点的确认状态
    confirmations = state.get("confirmations", {})
    outline_confirmation = confirmations.get("outline_confirmation", {})

    # 如果用户拒绝或没有确认，重新生成大纲
    if not outline_confirmation.get("approved", True):
        return "outline_generation"

    # 确认通过，进入报告生成
    return "report_generation"
```

### **状态定义要求**

确保你的状态类型包含必要的字段：

```python
class DeepResearchState(TypedDict):
    # ... 其他字段 ...

    # 通用中断节点需要的字段
    confirmations: Dict[str, Dict[str, Any]]     # 中断确认记录
    mode: str                                    # 运行模式：interactive/copilot
```

### **前端集成**

在前端使用时，需要指定正确的stream_mode：

```python
# 后端流式处理
async for chunk in app.astream(
    initial_state,
    stream_mode=["custom", "updates", "messages"]  # 必须包含custom
):
    if isinstance(chunk, tuple) and chunk[0] == "custom":
        message_data = chunk[1]

        # 检查是否是中断消息
        if "interrupt_content" in message_data:
            # 处理中断请求
            handle_interrupt_request(message_data)
```

### **消息格式**

中断节点会发送统一格式的消息：

```json
{
  "message_type": "step_complete",
  "content": "等待用户确认",
  "interrupt_content": "请确认以下内容：...",
  "action": "confirm_outline_confirmation",
  "args": {...},
  "interrupt_id": "confirm_outline_confirmation_1756292256924",
  "interrupt_config": {
    "allow_accept": true,
    "allow_edit": false,
    "allow_respond": true
  }
}
```

### **响应格式**

用户响应的标准格式：

```python
# 接受
{"type": "accept"}

# 拒绝
{"type": "reject"}

# 编辑（如果允许）
{"type": "edit", "args": {"args": {...}}}

# 自定义反馈
{"type": "response", "args": "用户反馈内容"}
```

---

## 📊 两种方法对比

| 特性 | 工具包装器方式 | 通用中断节点方式 |
|------|---------------|-----------------|
| **适用场景** | Agent工具调用暂停 | 流程节点间确认 |
| **实现复杂度** | 中等 | 简单 |
| **消息格式** | 工具相关 | 统一标准化 |
| **自定义程度** | 高 | 高 |
| **维护成本** | 中等 | 低 |
| **代码复用** | 中等 | 高 |

---

## ⚠️ **通用注意事项**

### **对于工具包装器方式：**

1. **绝对不要在Graph节点中捕获 `Interrupt`**
   - 这是最重要也最容易出错的一点。`HumanInterrupt` **不是一个程序错误（Exception）**，而是LangGraph设计的**正常操作信号**，用于暂停流程。
   - 如果在你的节点函数（如 `research_node`）中用 `try...except` 块把Agent的调用包起来，就会错误地把这个正常的暂停信号当作异常处理掉，导致Graph无法暂停，陷入循环。
   - **正确做法**：移除包裹Agent调用的 `try...except` 块，让 `Interrupt` 信号自然地从节点中抛出，LangGraph引擎会正确处理它。

2. **`interrupt_before_tools=True` 参数不可或缺**
   - 对于ReAct Agent，如果忘记在创建时设置这个参数，即使工具被正确包装，Agent也不会在工具执行前暂停。

3. **确保`state`的正确传递**
   - 从Graph的初始状态，到每一个节点，再到工具获取函数，`state` 必须被正确地一路传递下去。它是连接整个机制的"数据总线"。

### **对于通用中断节点方式：**

1. **必须指定正确的stream_mode**
   ```python
   # ❌ 错误：缺少stream_mode
   app.astream(state)

   # ✅ 正确：包含custom模式
   app.astream(state, stream_mode=["custom", "updates", "messages"])
   ```

2. **状态字段完整性**
   - 确保状态定义包含 `confirmations` 字段
   - 确保状态定义包含 `mode` 字段

3. **路由函数适配**
   - 使用 `confirmations` 而不是 `approval_status` 检查确认状态
   - 正确处理默认值和异常情况

4. **不要阻塞中断**
   - 中断节点使用 `types.interrupt()` 实现异步中断
   - 不要在中断节点中使用同步阻塞操作

---

## 🎯 **最佳实践**

1. **选择合适的方法**：
   - 工具调用暂停 → 使用工具包装器
   - 流程确认暂停 → 使用通用中断节点

2. **统一消息格式**：
   - 使用封装的中断节点确保消息格式一致
   - 便于前端统一处理

3. **模式适配**：
   - Interactive模式：触发中断等待用户
   - Copilot模式：自动通过，不中断流程

4. **错误处理**：
   - 不要捕获 `Interrupt` 异常
   - 正确处理用户响应的各种情况

5. **代码复用**：
   - 使用工厂函数创建中断节点
   - 自定义数据获取和响应处理函数

---

## 📝 **流程总结**

### 工具包装器方式：
`State` 定义模式 → `节点` 传递State → `Wrapper` 根据模式包装工具 → `Agent` 在调用工具时触发中断 → `LangGraph引擎` 捕捉中断并暂停

### 通用中断节点方式：
`State` 定义模式 → `中断节点` 检查模式 → `发送中断消息` → `types.interrupt()` 触发中断 → `LangGraph引擎` 捕捉中断并暂停 → `用户响应` → `恢复执行`

两种方式都能有效实现Human-in-the-Loop功能，选择哪种取决于具体的使用场景和需求。
