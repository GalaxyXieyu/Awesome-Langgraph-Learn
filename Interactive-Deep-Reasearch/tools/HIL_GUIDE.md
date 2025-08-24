# 使用工具包装器（Wrapper）实现自动暂停（Human-in-the-Loop）指南

本文档总结了如何通过工具包装器（Wrapper）实现LangGraph流程的自动暂停功能，以及关键的注意事项。

核心思想是：**通过Graph的状态（State）来动态决定工具的行为模式。** 当模式为 `'interactive'` 时，工具不直接执行，而是抛出一个 `HumanInterrupt` 信号，LangGraph引擎会自动捕捉这个信号并暂停整个流程，等待您的指令。

---

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
