# LG-00：为什么选择 LangGraph？

**口播时长**: 约 6 分 30 秒（1560 字 ÷ 4 字/秒）
**语速**: 中文 ~4 字/秒，技术术语处放慢
**语气**: 专业但不枯燥，有观点但不偏激

---

## 第一章：开场钩子（~15s）

2024 到 2025 年，AI Agent 框架井喷。

LangChain、LangGraph、CrewAI、AutoGen、Agno、Pydantic AI、Spring AI......

你可能已经试过其中几个，甚至可能已经用某个框架写了一个能跑的 Agent。

但今天我要问你一个问题：如果明天你的 Agent 需要支持用户中途打断修改需求，或者某个步骤失败后自动重试然后转人工，你现在的框架能优雅地支持吗？

Demo 很美好，生产很残酷。这就是框架选型的核心痛点。

---

## 第二章：框架全景对比（~90s）

我们先快速扫描一下主流框架。

LangGraph，基于有向图的 Agent 工作流编排。如果你想精确控制 Agent 的每一步走向，选它。

CrewAI，角色扮演驱动的多 Agent 协作。给每个 Agent 分配角色，让它们协作写报告。角色抽象自然，但状态管理和循环控制较弱。

Agno，轻量级工具包。5 分钟跑起来一个 Agent。快，但复杂工作流支持不足。

AutoGen，微软出品，对话驱动的多 Agent 框架。多 Agent 聊天解决问题，但对话模型强耦合，非对话场景别扭。

Pydantic AI，类型安全框架。Pydantic 重度用户会喜欢，但生态较新。

Spring AI，Java 生态。如果你在 Spring 体系里，选它。但图编排能力弱于 LangGraph。

LlamaIndex Workflows，事件驱动的工作流。适合 RAG 场景，但与 LlamaIndex 强绑定。

好，七个框架，七个维度。状态管理、循环条件、持久化、人机协作、流式输出、可视化、多 Agent。

注意看这张表。LangGraph 不是每项都最强，但它是唯一一个在这七个维度上都有原生支持的框架。

状态管理用 TypedDict 加 Reducer。循环和条件是图的一等公民。持久化有 Checkpoint。人机协作有 interrupt。流式输出有五种模式。可视化有 Studio 加 Mermaid。多 Agent 有 Subgraph 加 Handoff。

生产就绪度，LangGraph 领先。

---

## 第三章：三大痛点解析（~120s）

我们拿同一个需求，看三种写法。

需求是智能客服路由：用户输入，意图识别，然后路由到订单查询、退款申请、常见问题或人工客服。

第一种，传统脚本写法。if 订单查询，嵌套一个重试。elif 退款，嵌套一个人工审核。elif 常见问题。else 转人工。逻辑一复杂，意大利面条。加一个新分支，改函数，改调用方。重试逻辑散落各处。人工介入没有统一机制。出错了不知道走到哪一步。

第二种，CrewAI 写法。定义四个角色：意图识别员、订单专员、退款专员、客服专员。然后创建团队。角色抽象自然，但路由逻辑是隐式的。谁来决定用哪个 Agent？Agent 之间传递了什么？循环重试怎么做？加新分支要改角色定义加改任务列表。

第三种，LangGraph 写法。定义状态 AgentState。定义节点：classify、order、refund、faq、human。添加边：从 classify 出发，根据 intent 条件路由到四个分支。结构清晰。状态透明，每个节点接收完整状态。扩展简单，加新分支就是 add_node 加 add_conditional_edges 两行代码。还能直接生成 Mermaid 图。

这就是图编排的力量。Chain 是单行道，车只能往前开。LangGraph 是立交桥系统，每辆车可以根据路况选择不同出口。

再看状态透明。传统框架调试，print 满天飞，像在黑箱里摸象。LangGraph 的 stream_mode 等于 values，可以实时看到每一步的完整状态。LangGraph Studio 还能可视化看到状态在每个节点的变化。

循环和重试呢？传统框架写递归或 while 循环，和框架格格不入。LangGraph 里，循环就是 add_edge 从 node_a 连到 node_b，再从 node_b 连回 node_a。重试用条件边加计数器。每个节点有 max_executions 天然防死循环。

---

## 第四章：诚实边界（~45s）

但是，LangGraph 不是银弹。

5 分钟搭个 Demo，用 Agno，最快上手。

纯角色扮演协作写报告，用 CrewAI，角色抽象最自然。

Java 技术栈，用 Spring AI，生态一致。

多 Agent 聊天，用 AutoGen，对话模型成熟。

强类型偏好，用 Pydantic AI，类型安全。

LlamaIndex 做 RAG，用 LlamaIndex Workflows，生态内集成。

LangGraph 最适合的是需要精确控制流程、状态透明、可持久化、可人机协作的场景。简单问答机器人，用它可能是杀鸡用牛刀。

---

## 第五章：收尾（~15s）

记住这个口诀：链太线，图更全；要可控，LangGraph 行；状态明，循环轻；人机能，生产顶。

好了，现在你知道为什么选 LangGraph 了。下一节课，我们就从最基本的图开始。什么是 State、Node、Edge，以及怎么把它们拼成一个能跑的 Agent。

准备好了吗？LG-01 见。
