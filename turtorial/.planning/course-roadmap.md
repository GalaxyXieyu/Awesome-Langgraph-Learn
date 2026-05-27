# LangGraph 完整课程体系路线图

**版本**: v1.3  
**更新日期**: 2026-05-25  
**课程总数**: 11 个阶段（含导论）  
**预计总时长**: 38-46 小时（含实战）  

> **v1.3 变更摘要**: 新增 LG-00「为什么选择 LangGraph」导论阶段，对比 Agno/CrewAI/SpringAI/AutoGen/Pydantic AI 等框架。
> **v1.2 变更摘要**: LG-07 案例全面替换为 DeepResearch Agent 架构解析；LG-08 监控全面改用 Langfuse，新增 Prompt 生命周期管理模块。详见文档末尾「变更日志」。
> **v1.1 变更摘要**: 新增 LG-08「高级模式与生产部署」阶段；深化 LG-02/LG-04/LG-06/LG-07 相关内容。

---

## 一、课程概述

### 目标受众
- 已掌握 Python 基础和 LangChain 基础的开发者
- 希望系统学习 AI Agent 工作流编排的工程师
- 需要构建生产级多智能体系统的技术团队

### 前置知识要求
- Python 3.10+ 编程经验
- 了解 LangChain 基础（Models、Prompts、Chains）
- 了解 TypedDict / Pydantic 类型系统
- 具备基本的异步编程概念（async/await）

### 课程设计原则
1. **循序渐进**: 每阶段建立在上一阶段基础上，知识螺旋上升
2. **可视化驱动**: 每个阶段至少包含一个可用 AGUI / Web UI 呈现的案例
3. **实战导向**: 理论讲解与代码实战比例约为 3:7
4. **生产就绪**: 覆盖错误处理、性能优化、监控等生产环境议题

---

## 二、阶段详细设计

---

### 阶段 0：为什么选择 LangGraph？—— AI Agent 框架全景对比

**编号**: LG-00  
**预计时长**: 1.5-2 小时（含 30 分钟实战演示）  
**难度**: 入门引导  
**定位**: 课程导论，建立选型认知

#### 学习目标
- 了解主流 AI Agent 框架（LangGraph、CrewAI、Agno、AutoGen、Pydantic AI、Spring AI、LlamaIndex Workflows）的定位和适用场景
- 理解 LangGraph 的核心优势：状态透明、循环原生、持久化、人机协作、可视化
- 建立框架选型决策能力
- 理解「链」vs「图」的本质区别

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| Chain vs Graph | 线性流水线 vs 有向图编排 | 必须掌握 |
| 状态管理 | 显式 State  vs 隐式状态 | 必须掌握 |
| 循环与条件 | 原生支持 vs 补丁化实现 | 必须掌握 |
| 框架选型 | 根据场景选择最合适的框架 | 推荐掌握 |

#### 建议实战案例
**案例名称**: 智能客服路由对比  
**可视化形式**: 七维度雷达图 + 代码对比面板  
**功能**: 同一需求（智能客服路由）用不同框架实现，直观对比代码量和结构清晰度  
**AGUI 呈现点**: 框架对比雷达图、代码行数统计、架构清晰度评分

#### 对比框架
- **LangGraph**: 图编排，精确控制
- **CrewAI**: 角色协作，适合报告生成
- **Agno**: 轻量快速，适合原型
- **AutoGen**: 对话驱动，适合多 Agent 聊天
- **Pydantic AI**: 类型安全，适合强类型偏好者
- **Spring AI**: Java 生态，Spring 开发者首选
- **LlamaIndex Workflows**: 事件驱动，LlamaIndex 生态内

---

### 阶段 1：LangGraph 基础与图构建

**编号**: LG-01  
**预计时长**: 3-4 小时（含 1 小时实战）  
**难度**: 入门  

#### 学习目标
- 理解 LangGraph 的核心理念：用"图"替代"链"来编排 Agent 工作流
- 掌握 State、Node、Edge 三大基石概念
- 能够独立构建并运行一个简单的 StateGraph
- 理解 Channel 底层机制与状态更新原理

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `StateGraph` | 图构建器，定义工作流结构 | 必须掌握 |
| `State` (TypedDict) | 共享状态字典，节点间数据传递 | 必须掌握 |
| `Node` | 执行单元，接收 state 返回更新 | 必须掌握 |
| `Edge` | 控制流，连接节点定义执行顺序 | 必须掌握 |
| `START / END` | 图的起止标记 | 必须掌握 |
| `compile()` | 编译图，类型检查与边验证 | 必须掌握 |
| `Annotated` + Reducer | 状态字段的合并策略 | 必须掌握 |
| `Channel` | 底层数据传递机制（LastValue/Topic/BinaryOperatorAggregate） | 理解即可 |
| `MessagesState` | 预置的消息状态模板 | 推荐掌握 |

#### 建议实战案例
**案例名称**: 智能天气助手（WeatherBot）  
**可视化形式**: Web UI 展示图执行流程（节点高亮+状态变化）  
**功能**: 用户输入城市名 → 图依次执行"解析意图→查询天气→格式化回复"  
**AGUI 呈现点**: 实时显示当前执行节点高亮、状态面板展示 state 变化

#### 已有教程映射
- `langgraph-channels-guide.md` → Channel 底层机制（进阶阅读）
- 无直接对应，为全新基础阶段

---

### 阶段 2：路由、工具与条件控制

**编号**: LG-02  
**预计时长**: 4-5 小时（含 1.5 小时实战）  
**难度**: 初级  
**依赖**: LG-01  

> **v1.1 修改**: 本阶段新增「预构建 Agent 深度对比」模块（`create_react_agent` / `create_tool_calling_agent` / 自定义 StateGraph 的决策框架），时长由原 3-4h 增至 4-5h。

#### 学习目标
- 掌握条件边（Conditional Edge）实现动态路由
- 理解循环（Cycles）在图中的实现：重试、迭代优化
- 掌握 Tool Node 的集成与工具调用模式
- **深度掌握预构建 Agent 模式**：`create_react_agent` 的 plan-execute 流程、`create_tool_calling_agent` 的适用场景
- **建立决策框架**：能够根据业务复杂度判断「预构建 vs 自定义 StateGraph」的选型

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `add_conditional_edges` | 条件边，基于状态动态路由 | 必须掌握 |
| `ToolNode` | 工具执行节点 | 必须掌握 |
| `tools_condition` | 自动判断是否需要调用工具 | 必须掌握 |
| Cycles / Loops | 图中返回前一节点的循环结构 | 必须掌握 |
| ReAct Pattern | 推理→行动→观察的循环模式 | 必须掌握 |
| `create_react_agent` | 预置的 ReAct Agent（plan→execute→observe 循环） | 必须掌握 |
| `create_tool_calling_agent` | 简化的工具调用 Agent（无显式推理步骤） | 推荐掌握 |
| **预构建 vs 自定义决策框架** | 选型判断：复杂度、可观测性、定制需求 | **v1.1 新增** |
| `Command` | 控制指令（goto / update） | 了解 |

#### 建议实战案例
**案例名称**: 智能客服路由系统（SmartRouter）  
**可视化形式**: Web UI 展示决策树路由过程 + Agent 架构对比面板  
**功能**: 用户输入 → 意图识别节点 → 条件路由到"订单查询/退款申请/人工客服/常见问题"不同分支 → **各分支分别用「预构建 Agent」和「自定义 StateGraph」实现，实时对比执行路径差异** → 汇总回复  
**AGUI 呈现点**: 动态路由动画（高亮当前分支）、意图置信度仪表盘、工具调用详情面板、**预构建/自定义执行路径对比视图（v1.1 新增）**

#### 已有教程映射
- `langchain-prompt-templates-guide.md` → Prompt 模板与工具描述优化

---

### 阶段 3：流式输出与实时监控

**编号**: LG-03  
**预计时长**: 3-4 小时（含 1.5 小时实战）  
**难度**: 初级-中级  
**依赖**: LG-01, LG-02  

#### 学习目标
- 掌握 5 种 stream_mode 的区别与适用场景
- 实现 token 级实时流式输出到前端
- 能够组合多种 stream mode 构建丰富的实时 UI
- 理解 Node 元数据与事件过滤

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `stream_mode="values"` | 流式输出完整 state | 必须掌握 |
| `stream_mode="updates"` | 流式输出 state 增量 | 必须掌握 |
| `stream_mode="messages"` | 流式输出 LLM token | 必须掌握 |
| `stream_mode="custom"` | 自定义事件流 | 必须掌握 |
| `stream_mode="tasks"` | 任务级生命周期事件 | 推荐掌握 |
| `astream_events` (v2) | 最细粒度的事件流 API | 推荐掌握 |
| Node Metadata / Tags | 节点标记用于事件过滤 | 了解 |

#### 建议实战案例
**案例名称**: 实时写作助手（LiveWriter）  
**可视化形式**: Web 编辑器 + 实时状态面板  
**功能**: 用户输入写作主题 → AI 并行执行"大纲规划+资料检索" → 逐段生成内容（token 级流式）→ 实时显示生成进度和来源引用  
**AGUI 呈现点**: 逐字打字机效果、段落进度条、来源卡片实时弹出、节点执行时间线

#### 已有教程映射
- `langgraph-stream-mode-guide.md` → 核心参考（全部内容复用重组）

---

### 阶段 4：持久化与记忆系统

**编号**: LG-04  
**预计时长**: 5-6 小时（含 2.5 小时实战）  
**难度**: 中级  
**依赖**: LG-01, LG-02  

> **v1.1 修改**: 本阶段新增「Redis + Postgres 混合架构」模块（初步介绍分工与选型，为 LG-08 深化做铺垫），时长由原 4-5h 增至 5-6h。

#### 学习目标
- 理解 Checkpoint 机制：超级步边界、状态快照、恢复
- 掌握短期记忆（Short-term Memory）：线程级状态持久化
- 掌握长期记忆（Long-term Memory）：Store 的 KV 存储与语义检索
- 能够配置 Postgres / Redis / Memory 三种 Saver
- **理解混合持久化架构**：何时用 Redis（高速缓存/会话）、何时用 Postgres（持久化/审计）
- 理解 Context Engineering：上下文裁剪、摘要、过滤策略

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `checkpointer` | 检查点保存器（Saver） | 必须掌握 |
| `MemorySaver` | 内存检查点（开发测试） | 必须掌握 |
| `PostgresSaver` | PostgreSQL 持久化 | 必须掌握 |
| `RedisSaver` | Redis 高速持久化 | 推荐掌握 |
| `Store` / `BaseStore` | 长期记忆存储 | 必须掌握 |
| `thread_id` | 会话/线程标识 | 必须掌握 |
| `user_id` | 用户标识（Store 命名空间） | 必须掌握 |
| `aput / aget / asearch` | Store 读写检索 API | 必须掌握 |
| **Redis + Postgres 混合架构** | 双后端分工：Redis 缓存热数据，Postgres 持久化冷数据 | **v1.1 新增** |
| 上下文裁剪 (`trim_messages`) | 消息历史长度控制 | 推荐掌握 |
| 增量摘要 | 超长对话的摘要压缩 | 推荐掌握 |

#### 建议实战案例
**案例名称**: 有记忆的私人助手（MemoryPal）  
**可视化形式**: 聊天界面 + 记忆管理面板 + **持久化后端状态监控（v1.1 新增）**  
**功能**: 多轮对话自动保存到 Postgres → 跨会话记住用户偏好（语言、风格、兴趣）→ **高频访问的偏好数据自动缓存到 Redis** → 支持"忘记某事"和"回忆某事"指令 → 显示当前记忆的 token 占用和压缩状态 → **展示 Redis/Postgres 各自的命中率与延迟（v1.1 新增）**  
**AGUI 呈现点**: 记忆时间线可视化、token 用量仪表盘、偏好标签云、会话恢复选择器、**后端存储状态仪表盘（Redis 命中率、Postgres 查询延迟）（v1.1 新增）**

#### 已有教程映射
- `langgraph-postgres-saver-store-guide.md` → 核心参考（Saver/Store 详细用法）
- `langgraph-context-engineering-guide.md` → 上下文工程（裁剪/摘要/过滤）
- `langgraph-cache-guide.md` → 节点级缓存策略（性能优化补充）
- `RedisMemory-Graph/` → 示例项目参考

---

### 阶段 5：人机协作与 Hooks

**编号**: LG-05  
**预计时长**: 4-5 小时（含 2 小时实战）  
**难度**: 中级  
**依赖**: LG-01, LG-02, LG-04  

#### 学习目标
- 掌握 `interrupt()` 原语实现人工审批/干预
- 理解 `interrupt_before` / `interrupt_after` 的配置方式
- 掌握 `Command(resume=...)` 恢复中断的执行
- 掌握 Pre/Post Model Hooks 实现消息预处理和后处理
- 能够构建安全可控的 HITL（Human-in-the-Loop）工作流

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `interrupt()` | 中断执行等待人工输入 | 必须掌握 |
| `Command(resume=...)` | 从中断点恢复 | 必须掌握 |
| `interrupt_before` | 节点执行前中断 | 必须掌握 |
| `interrupt_after` | 节点执行后中断 | 必须掌握 |
| `pre_model_hook` | LLM 调用前预处理 | 推荐掌握 |
| `post_model_hook` | LLM 调用后处理/HITL | 推荐掌握 |
| `llm_input_messages` | 临时注入上下文（不修改 state） | 推荐掌握 |
| `RemoveMessage` | 消息删除/替换 | 了解 |
| Guardrails | 输出安全审查 | 了解 |

#### 建议实战案例
**案例名称**: 内容审核工作流（ContentGuard）  
**可视化形式**: 审批仪表盘 + 内容编辑界面  
**功能**: AI 生成营销文案 → 自动安全检查 → **高风险内容触发人工审批** → 审核员可"通过/拒绝/编辑" → 通过后自动发布到多渠道 → 全程审计日志  
**AGUI 呈现点**: 审批队列看板、风险评分仪表盘、并排对比（原始/修改）、操作时间线

#### 已有教程映射
- `langgraph-hooks-guide.md` → 核心参考（Pre/Post Hooks 完整指南）
- `Multi-Agent-Handoff/` → 可作为 Handoff 模式参考

---

### 阶段 6：并行执行与子图

**编号**: LG-06  
**预计时长**: 5-6 小时（含 2.5 小时实战）  
**难度**: 中高级  
**依赖**: LG-01, LG-02, LG-03  

> **v1.1 修改**: 本阶段新增「多 Subgraph 状态组合高级模式」模块（state 传递、共享、隔离策略），时长由原 4-5h 增至 5-6h。

#### 学习目标
- 掌握 Fan-out / Fan-in 模式实现并行节点执行
- 理解 Reducer 机制处理并发状态更新冲突
- 掌握 `Send` 实现动态 Map-Reduce 模式
- 掌握 Subgraph 的构建与集成：模块化、复用、隔离状态
- **掌握多 Subgraph 之间的状态传递与组合策略：父图与子图的 state 映射、共享 state 字段、跨图通信**
- 理解 Deferred Nodes 与跨运行时协作（概念性了解）

#### 核心概念清单
| 概念 | 说明 | 重要性 |
|------|------|--------|
| Fan-out / Fan-in | 并行分支与汇聚 | 必须掌握 |
| `Annotated[type, reducer]` | 并发更新合并策略 | 必须掌握 |
| `operator.add` | 内置列表/数值累加 Reducer | 必须掌握 |
| 自定义 Reducer | 排序、去重、保留最近 N 个 | 推荐掌握 |
| `Send` | 动态分发到子任务 | 推荐掌握 |
| `StateGraph` as Node | 子图作为节点嵌入 | 必须掌握 |
| 子图状态隔离 | 子图拥有独立 state schema | 必须掌握 |
| **父图↔子图 state 映射** | `input`/`output` 字段映射配置 | **v1.1 新增** |
| **跨 Subgraph 共享 state** | 通过公共字段或 Store 实现子图间通信 | **v1.1 新增** |
| **复杂 state 组合策略** | 嵌套子图的状态扁平化与聚合模式 | **v1.1 新增** |
| `max_concurrency` | 并发数控制 | 了解 |
| `recursion_limit` | 超级步上限 | 了解 |

#### 建议实战案例
**案例名称**: 多源研报生成器（ResearchForge）  
**可视化形式**: 报告编辑器 + 并行任务监控面板 + **子图协作拓扑图（v1.1 新增）**  
**功能**: 输入研究主题 → **并行**执行"财经数据抓取/新闻 sentiment 分析/竞品对比/专家观点收集" → **各分支均为独立 Subgraph，拥有各自的状态隔离** → 各子图结果通过 state 映射汇聚到父图"综合分析师"节点 → 生成结构化研究报告 → 流式输出到编辑器  
**AGUI 呈现点**: 并行任务甘特图、各数据源进度条、汇聚节点数据融合动画、报告大纲实时构建、**子图层级拓扑图（点击展开子图内部结构）（v1.1 新增）**

#### 已有教程映射
- `langgraph-parallel-execution-guide.md` → 核心参考（Fan-out/Fan-in/Reducer 详解）
- `langgraph-runtime-guide.md` → Runtime 上下文在复杂图中的传递

---

### 阶段 8：多智能体系统与复杂工作流

**编号**: LG-09  
**预计时长**: 5-6 小时（含 2.5 小时实战）  
**难度**: 高级  
**依赖**: LG-01 ~ LG-08  

> **v1.2 重大修改**: 本阶段案例全面替换为 **DeepResearch Agent**（原 DevSquad AI 移至附录备选）。DeepResearch 作为 Hierarchical Multi-Agent 架构的终极综合案例，完整覆盖模式路由、计划路由循环、节点级缓存、任务跟踪、执行次数控制等生产级设计。

#### 学习目标
- 掌握 Multi-Agent 架构模式：Hierarchical、Network、Supervisor
- 掌握 Agent Handoff 机制与状态传递
- 能够将复杂系统拆分为多个协作子图
- **深度解析 DeepResearch Agent 架构：模式路由、计划路由循环、节点级缓存、任务跟踪系统、执行次数控制**
- 了解 LangGraph Studio 可视化调试

#### 核心概念清单

**8.1 Multi-Agent 理论基础**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| Multi-Agent Patterns | 多智能体架构模式 | 必须掌握 |
| Hierarchical Teams | 层级团队：主管分配任务 | 必须掌握 |
| Network / Peer-to-Peer | 对等协作网络 | 了解 |
| Supervisor Pattern | 监督者协调多个 Worker | 推荐掌握 |
| Agent Handoff | 智能体间任务交接 | 必须掌握 |
| LangGraph Studio | 可视化调试工具 | 了解 |

**8.2 DeepResearch Agent 架构（v1.2 新增）**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| **模式路由（Mode Router）** | 根据查询复杂度自动选择「快速问答(react)」或「深度研究(deep)」 | 必须掌握 |
| **计划路由（Plan Router）** | 循环结构：根据任务完成状态决定下一步（搜索/分析/代码/报告/总结） | 必须掌握 |
| **节点级缓存** | `CachePolicy(ttl=3600, key_func=...)` 为不同节点配置差异化缓存 | 必须掌握 |
| **任务跟踪系统** | `@track_execute` 装饰器自动管理任务状态（pending→running→completed/failed） | 必须掌握 |
| **执行次数控制** | `max_executions` 防止无限循环的安全阀 | 必须掌握 |
| **Annotated + add Reducer** | 累加历史消息和错误信息的状态管理 | 推荐掌握 |
| **进度推送** | 任务状态实时推送到前端（与 LG-03 stream 结合） | 推荐掌握 |

#### 建议实战案例
**案例名称**: DeepResearch Agent（深度研究助手）  
**可视化形式**: 研究工作台（Research Workbench）—— 多面板协作界面  

**架构解析**:
```
记忆助手 → 模式路由 → [快速问答(react模式) → 追问建议 → END]
                    → [任务规划 → 信息搜索 → 计划路由]
                                          ↑________↓
                              [数据分析 / 代码执行 / 报告撰写]
                                          ↓
                                    结果总结 → 追问建议 → END
```

**功能**:  
1. 用户输入研究问题 → **记忆助手**加载用户历史偏好和上下文  
2. **模式路由**评估复杂度：简单问题走「快速问答」分支（`create_react_agent` 预构建模式），复杂问题走「深度研究」分支  
3. **深度研究分支**：任务规划 → 信息搜索（并行多源）→ **计划路由循环**（根据当前状态决定下一步是继续搜索、数据分析、代码执行、报告撰写还是结果总结）→ 每个节点有 **max_executions** 限制防止死循环  
4. **节点级缓存**：搜索结果缓存 1 小时、分析结果缓存 30 分钟、报告生成缓存 24 小时（不同 TTL 策略）  
5. **任务跟踪**：`@track_execute` 装饰器自动追踪每个节点的执行状态，实时推送进度到前端  
6. **追问建议**：研究完成后自动生成 3 条 follow-up 问题引导用户深入  

**AGUI 呈现点**:  
- 🧭 **架构拓扑图**：实时高亮当前执行路径，模式路由决策动画（react vs deep 分支展开）  
- 🔄 **计划路由循环可视化**：循环计数器、当前迭代次数 vs max_executions、计划状态看板  
- 💾 **节点级缓存面板**：每个节点的缓存命中状态（绿色=命中/红色=未命中）、TTL 倒计时、节省的 API 调用次数  
- 📊 **任务跟踪时间线**：`@track_execute` 追踪的所有任务甘特图（pending→running→completed/failed）  
- 📈 **进度推送流**：实时消息流展示当前节点名称、执行状态、预计剩余时间  
- ❓ **追问建议卡片**：研究完成后弹出的 3 条智能 follow-up 问题  

#### 已有教程映射
- `langgraph-hooks-guide.md` → Pre/Post Hooks 在 DeepResearch 中的应用
- `langgraph-cache-guide.md` → 节点级缓存策略（CachePolicy 配置）
- `langgraph-parallel-execution-guide.md` → 信息搜索的并行执行
- `langgraph-context-engineering-guide.md` → 上下文裁剪与记忆管理
- `langgraph-stream-mode-guide.md` → 任务进度实时推送
- `Multi-Agent-Handoff/` → Handoff 模式参考（模式路由的变体）
- `Multi-Agent-report/` → 报告生成参考
- `studio_graph/` → LangGraph Studio 可视化调试
- `Context-Mange-Chat/` → 上下文管理参考

---

### 阶段 9：生产部署、可观测性与 Prompt 工程

**编号**: LG-08  
**预计时长**: 7-8 小时（含 3.5 小时实战）  
**难度**: 高级-专家  
**依赖**: LG-01 ~ LG-07  

> **v1.1 新增**: 本阶段为全新阶段，整合预构建 Agent 深度模式、缓存策略实战、Redis+Postgres 混合架构、知识库向量检索/RAG、生产化部署等高级主题。  
> **v1.2 重大修改**: 监控部分全面改用 **Langfuse**（替代 Prometheus/Grafana）；新增 **Prompt 生命周期管理**模块；时长由 6-7h 增至 7-8h。

#### 学习目标
- **深度掌握预构建 Agent 的 plan-execute 流程**：拆解 `create_react_agent` 内部机制，理解何时用预构建、何时必须自定义
- **精通缓存策略**：节点级缓存（`CachePolicy`）、结果缓存、TTL 策略、缓存失效与穿透防护，并能可视化展示缓存命中/未命中
- **掌握 Redis + Postgres 混合架构**：双后端数据流设计、一致性策略、容灾方案
- **掌握知识库向量检索与 RAG**：Chroma/Pinecone 集成、LangGraph 中的 RAG 节点设计、检索效果评估与可视化
- **掌握 Langfuse 全链路可观测性**：Trace、CallbackHandler、Tags、Score、Dataset，替代传统 Prometheus/Grafana 方案
- **掌握 Prompt 生命周期管理**：YAML 本地存储、Langfuse Prompt Hub 同步、版本管理、自动标签
- **掌握生产化部署全流程**：Docker 容器化、LangGraph Cloud、性能调优

#### 核心概念清单

**8.1 预构建 Agent 深度模式**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `create_react_agent` plan-execute 流程 | 内部拆解：plan→tool_call→observe→(loop) | 必须掌握 |
| `create_tool_calling_agent` | 轻量级工具调用，无显式 plan 步骤 | 推荐掌握 |
| 预构建 Agent 的局限性 | 状态不可观测、循环控制受限、定制困难 | 必须掌握 |
| 自定义 StateGraph 的适用场景 | 复杂路由、精细状态控制、多模态交互 | 必须掌握 |
| 选型决策矩阵 | 根据「复杂度×可观测性×定制需求」快速决策 | 推荐掌握 |

**8.2 多 Subgraph 状态组合（深化）**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `input` / `output` 映射 | 子图与父图之间的字段映射配置 | 必须掌握 |
| 共享 state 字段模式 | 多个子图读写同一 state 键的并发控制 | 推荐掌握 |
| 状态扁平化 vs 嵌套 | 复杂嵌套子图的状态结构设计权衡 | 了解 |
| 跨子图通信（Store） | 通过长期记忆存储实现子图间解耦通信 | 推荐掌握 |

**8.3 缓存策略实战**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `CachePolicy` | 节点级缓存策略配置（TTL、key_func） | 必须掌握 |
| `MemorySaver` as Cache | 内存缓存后端 | 必须掌握 |
| `PostgresSaver` as Cache | 数据库缓存后端 | 推荐掌握 |
| 缓存失效策略 | TTL、主动失效、版本号失效 | 必须掌握 |
| 缓存穿透/雪崩防护 | 空值缓存、随机 TTL 偏移、互斥锁 | 推荐掌握 |
| 缓存命中率监控 | 命中/未命中统计、性能对比 | 推荐掌握 |

**8.4 Redis + Postgres 混合架构**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| Redis 定位 | 高速缓存、会话热数据、分布式锁 | 必须掌握 |
| Postgres 定位 | 持久化审计、长期记忆、复杂查询 | 必须掌握 |
| 双写一致性 | Cache-Aside、Write-Through、Write-Behind | 推荐掌握 |
| 连接池管理 | 多后端连接池的统一生命周期管理 | 了解 |
| 容灾与降级 | Redis 故障时的 Postgres 兜底策略 | 了解 |

**8.5 知识库向量检索与 RAG**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| 向量存储集成 | Chroma、Pinecone、Weaviate 等接入 LangGraph | 必须掌握 |
| RAG 节点设计 | retrieve→rerank→inject 的图节点实现 | 必须掌握 |
| 检索效果评估 | 命中率、相关性评分、Bad Case 分析 | 推荐掌握 |
| Hybrid Search | 向量相似度 + 关键词过滤的组合检索 | 推荐掌握 |
| 检索结果可视化 | 相似度热力图、命中片段高亮、来源追溯 | 推荐掌握 |

**8.6 可观测性与监控：Langfuse 全面方案（v1.2 重大更新）**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| `init_langfuse_observability()` | 从环境变量初始化 Langfuse | 必须掌握 |
| `CallbackHandler` | 自动追踪图执行：trace_name、user_id、session_id、tags | 必须掌握 |
| `create_callback_handler()` | 为每次图执行创建追踪实例 | 必须掌握 |
| `get_langfuse_config()` | 一键获取包含 callbacks 和 metadata 的 config 字典 | 推荐掌握 |
| **Tags 标签系统** | `build_default_tags()` 自动构建 env:dev/proc:api 等标签 | 推荐掌握 |
| **Score 评分系统** | `report_cache_hit_rate()` 上报缓存命中率；自定义评分（输出质量、响应时间） | **v1.2 新增** |
| **Dataset 管理** | QA Capture 自动保存运行数据到 Langfuse Dataset 用于后续评估 | **v1.2 新增** |
| Langfuse Trace 链路 | 全链路可视化：请求→节点→LLM 调用→工具调用→响应 | 必须掌握 |
| Prometheus/Grafana（可选） | 传统方案，作为 Langfuse 的补充了解 | 了解 |

**8.7 Prompt 生命周期管理（v1.2 新增）**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| **YAML 本地存储** | Prompt 以 YAML 文件存储，支持 Jinja2 和 f-string 格式 | 必须掌握 |
| **Prompt 元数据配置** | 配置文件管理 prompt 版本、标签、适用场景 | 推荐掌握 |
| **Langfuse Prompt Hub** | 云端 Prompt 托管与版本管理 | 必须掌握 |
| **自动拉取** | 本地不存在时从 Langfuse Hub 自动拉取 prompt | 必须掌握 |
| **推送发布** | 将本地 prompt 推送到 Langfuse Hub，自动打 `labels: ["production"]` | 必须掌握 |
| **智能标签** | 自动从目录名推断 agent，从 prompt 名推断功能标签 | 推荐掌握 |
| **PromptManager API** | `get_prompt()` / `build_langchain_prompt()` / `save_prompt()` / `push_to_hub()` / `_auto_pull_if_needed()` | 必须掌握 |
| **版本对比** | 本地版本 vs Hub 版本的差异对比与冲突解决 | 推荐掌握 |

**8.8 生产化部署深化**
| 概念 | 说明 | 重要性 |
|------|------|--------|
| Docker 容器化 | Dockerfile、多阶段构建、健康检查 | 必须掌握 |
| LangGraph Cloud | 托管部署、自动扩缩容、版本管理 | 了解 |
| 性能调优 | 并发控制、递归限制、状态大小优化、连接池 | 必须掌握 |
| 安全加固 | API 认证、输入校验、速率限制、敏感信息过滤 | 了解 |

#### 建议实战案例
**案例名称**: 智能企业运维助手（OpsMate）  
**可视化形式**: 生产级运维监控仪表盘（Operations Dashboard）  

**功能**:  
1. **预构建 vs 自定义 Agent 对比区**：同一运维查询分别用 `create_react_agent` 和自定义 StateGraph 处理，实时展示执行路径差异和延迟对比  
2. **缓存监控面板**：展示各节点的缓存命中率（绿色=命中/红色=未命中）、TTL 倒计时、缓存节省的 API 调用次数  
3. **Redis + Postgres 健康看板**：双后端 QPS、延迟、连接数实时监控，模拟 Redis 故障时的自动降级  
4. **知识库 RAG 检索区**：用户输入运维问题 → 向量检索知识库 → 展示检索结果的相似度热力图、命中文档片段高亮、来源引用 → LLM 生成解决方案  
5. **Langfuse 可观测性大屏（v1.2 核心）**：
   - Trace 列表：每次图执行的完整链路，点击展开查看每个节点的输入/输出/延迟
   - Score 看板：缓存命中率评分、输出质量评分、响应时间评分的时序图
   - Dataset 管理界面：QA Capture 自动采集的数据集，支持一键重新运行评估
   - Tags 筛选器：按 env:dev/proc:api、agent 类型、功能标签筛选 Trace
6. **Prompt 同步看板（v1.2 新增）**：
   - Prompt 版本对比：本地 YAML 版本 vs Langfuse Hub 版本的并排差异展示
   - 同步状态指示灯：绿色=已同步、黄色=本地有更新待推送、红色=Hub 有新版本待拉取
   - 一键推送/拉取按钮 + 智能标签自动补全提示  

**AGUI 呈现点**:  
- 🔵 **架构对比视图**：预构建 Agent 与自定义 StateGraph 的执行路径并排动画对比  
- 🟢🔴 **缓存仪表盘**：节点级缓存命中/未命中的实时色块矩阵 + 节省成本计算器  
- 📊 **双后端监控**：Redis/Postgres 状态卡片（延迟、连接数、命中率）  
- 🌡️ **向量检索热力图**：检索结果与查询的相似度可视化矩阵  
- 🔭 **Langfuse Trace 大屏（v1.2 新增）**：Trace 链路瀑布图、Score 时序趋势、Dataset 表格  
- 📝 **Prompt 同步看板（v1.2 新增）**：版本差异高亮（增删改）、同步状态指示灯、操作日志  

#### 已有教程映射
- `langgraph-cache-guide.md` → **核心教材**（缓存策略详解，v1.1 升级为核心）
- `langgraph-postgres-saver-store-guide.md` → 参考（Postgres 部分，深化混合架构）
- `RedisMemory-Graph/` → 参考实现（Redis 集成方案）
- `LangGraphCeleryChat/` → 参考架构（异步任务队列集成）
- `Langsmith-prompt-pipeline/` → 参考实践（Prompt CI/CD 与监控）
- `Interative-Report-Workflow/` → 改造为案例（交互式报告工作流）

---

## 三、阶段依赖关系图

```
                    ┌─────────────────────────────────────┐
                    │      阶段 0: 为什么选择 LangGraph     │
                    │          (LG-00: 1.5-2h)            │
                    │            [课程导论]                │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │         阶段 1: 基础与图构建          │
                    │          (LG-01: 3-4h)              │
                    └──────────────┬──────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   阶段 2: 路由与工具  │  │   阶段 3: 流式输出   │  │   阶段 4: 持久化记忆  │
│    (LG-02: 4-5h)    │  │    (LG-03: 3-4h)    │  │    (LG-04: 5-6h)    │
└──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
           │                       │                       │
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │      阶段 5: 人机协作与 Hooks        │
                    │          (LG-05: 4-5h)              │
                    │     (依赖 LG-01 + LG-02 + LG-04)    │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │      阶段 6: 并行执行与子图          │
                    │          (LG-06: 5-6h)              │
                    │     (依赖 LG-01 + LG-02 + LG-03)    │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │   阶段 7: 多智能体与复杂工作流       │
                    │          (LG-07: 5-6h)              │
                    │      (依赖 LG-01 ~ LG-06)           │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │   阶段 8: 生产部署、可观测性与       │
                    │           Prompt 工程                 │
                    │          (LG-08: 7-8h)              │
                    │      (依赖 LG-01 ~ LG-07)           │
                    └─────────────────────────────────────┘
```

**依赖说明**:
- **LG-00 为课程导论**，无前置依赖，建议所有学员先学习
- **LG-01 是所有技术阶段的基石**，必须在最前面
- **LG-02（路由）和 LG-03（流式）相对独立**，可并行学习
- **LG-04（持久化）和 LG-05（HITL）关联紧密**，建议顺序学习
- **LG-06（并行/子图）需要 LG-02 和 LG-03 的基础**
- **LG-07 为 Multi-Agent + 复杂工作流综合阶段**，需要完成 LG-01 ~ LG-06
- **LG-08 为「从开发到生产」的终极闭环**，需要全部前置阶段基础

---

## 四、与现有教程和示例项目的映射关系

### 4.1 教程文档映射

| 现有教程 | 所属阶段 | 使用方式 | 备注 |
|----------|----------|----------|------|
| `langgraph-channels-guide.md` | LG-01 | 进阶阅读/选学 | Channel 底层机制，初学者可跳过 |
| `langchain-prompt-templates-guide.md` | LG-02 | 部分内容复用 | Prompt 模板与工具描述 |
| `langgraph-stream-mode-guide.md` | **LG-03** | **核心教材** | 5 种 stream mode 完整讲解 |
| `langgraph-postgres-saver-store-guide.md` | **LG-04 / LG-08** | **核心教材** | Saver/Store 详细用法 + 混合架构深化 |
| `langgraph-context-engineering-guide.md` | **LG-04 / LG-07** | **核心教材** | 上下文裁剪/摘要/过滤（DeepResearch 记忆助手） |
| `langgraph-cache-guide.md` | **LG-07 / LG-08** | **核心教材** | 节点级缓存策略 + 命中率可视化（DeepResearch + OpsMate） |
| `langgraph-hooks-guide.md` | **LG-05 / LG-07** | **核心教材** | Pre/Post Hooks 完整指南（DeepResearch 上下文注入） |
| `langgraph-parallel-execution-guide.md` | **LG-06 / LG-07** | **核心教材** | 并行执行/Reducer/Map-Reduce（DeepResearch 信息搜索） |
| `langgraph-runtime-guide.md` | LG-06 / LG-08 | 参考材料 | Runtime 上下文在复杂图中的传递 |

### 4.2 示例项目映射

| 示例项目 | 所属阶段 | 使用方式 | 案例定位 |
|----------|----------|----------|----------|
| `Multi-Agent-Handoff/` | LG-05 / **LG-07** | 改造为案例 | HITL + Handoff 模式（DeepResearch 模式路由） |
| `Multi-Agent-report/` | **LG-07** | 改造为案例 | 报告生成节点（DeepResearch 报告撰写） |
| `RedisMemory-Graph/` | LG-04 / **LG-08** | 参考实现 | Redis 持久化 + 混合架构 |
| `LangGraphCeleryChat/` | **LG-08** | 参考架构 | 异步任务队列 + 生产部署 |
| `Context-Mange-Chat/` | LG-04 / **LG-07** | 参考实现 | 上下文管理 + 记忆助手 |
| `Langsmith-prompt-pipeline/` | **LG-08** | 参考实践 | Prompt CI/CD + 监控追踪 |
| `studio_graph/` | LG-07 | 演示工具 | LangGraph Studio 可视化调试 |
| `Interative-Report-Workflow/` | LG-03 / LG-06 / **LG-07** | 改造为案例 | 交互式报告工作流（DeepResearch 结果总结） |

---

## 五、每个阶段的 AGUI 可视化案例总览

| 阶段 | 案例名称 | 可视化界面类型 | 核心交互 |
|------|----------|---------------|----------|
| **LG-00** | **框架对比分析** | **七维度雷达图 + 代码对比面板** | **框架雷达对比、代码行数统计、架构清晰度评分** |
| LG-01 | WeatherBot | 状态流转图 + 对话面板 | 节点高亮、状态实时展示 |
| LG-02 | SmartRouter | 决策树可视化 + 分支面板 + 架构对比区 | 路由动画、意图置信度、预构建/自定义路径对比 |
| LG-03 | LiveWriter | 编辑器 + 进度监控面板 | 打字机效果、来源卡片 |
| LG-04 | MemoryPal | 聊天界面 + 记忆管理面板 + 存储监控 | 记忆时间线、token 仪表盘、Redis/Postgres 状态 |
| LG-05 | ContentGuard | 审批仪表盘 + 编辑界面 | 审批队列、风险评分 |
| LG-06 | ResearchForge | 报告编辑器 + 任务甘特图 + 子图拓扑 | 并行进度、数据融合动画、子图层级展开 |
| **LG-07** | **DeepResearch Agent（v1.2 替换）** | **研究工作台（Research Workbench）** | **架构拓扑高亮、计划路由循环计数器、节点级缓存面板、任务跟踪甘特图、进度推送流、追问建议卡片** |
| **LG-08** | **OpsMate（v1.2 增强）** | **生产级运维监控仪表盘** | **缓存命中矩阵、双后端监控、向量检索热力图、Langfuse Trace 瀑布图、Score 时序趋势、Prompt 同步看板** |

---

## 六、课程交付物规划

### 每阶段标准交付物
1. **理论讲义**（Markdown）：概念讲解 + 图示 + 代码片段
2. **完整代码仓库**（Python）：可独立运行的示例项目
3. **AGUI 可视化界面**：基于 Streamlit / Gradio / React 的交互界面
4. **课后练习**：3-5 道编程题 + 1 道设计题
5. **阶段测验**：15-20 道选择题 + 1 道综合编程题

### 特别交付物
- **LG-07 大作业**: "基于 DeepResearch 架构，改造一个你熟悉的业务场景（如法律研究、医疗诊断、金融分析）"
- **LG-08 终极项目**: "从零到一部署一个生产级 LangGraph 应用到云环境，集成 Langfuse 可观测性和 Prompt Hub"
- **附录**: LangGraph 2.0 迁移指南、常见问题排查手册、性能优化 cheat sheet、预构建/自定义选型决策树、Langfuse 集成速查表

---

## 七、技术栈建议

### 核心框架
| 组件 | 推荐选择 | 版本 |
|------|----------|------|
| LangGraph | 官方 Python SDK | >= 1.0.0 |
| LangChain | 官方 Python SDK | >= 1.0.0 |
| Python | | >= 3.10 |

### 可视化/UI 框架（AGUI）
| 场景 | 推荐选择 | 理由 |
|------|----------|------|
| 快速原型 | Streamlit | Python 原生、开发快、适合演示 |
| 中等复杂度 | Gradio | 组件丰富、支持实时流式 |
| 生产级 | React + FastAPI | 完全自定义、最佳用户体验 |
| 图可视化 | LangGraph Studio / React Flow | 节点-边图渲染 |
| 监控仪表盘 | **Langfuse UI / Streamlit** | **LG-08 首选 Langfuse 原生 UI** |

### 持久化后端
| 环境 | 推荐选择 |
|------|----------|
| 开发/测试 | `MemorySaver` |
| 生产（关系型+审计） | `PostgresSaver` + `AsyncPostgresStore` |
| 生产（高速缓存+会话） | `RedisSaver` + `RedisStore` |
| 生产（混合架构） | `Redis`（热数据缓存）+ `Postgres`（冷数据持久化） |

### 向量存储与 RAG（LG-08）
| 场景 | 推荐选择 | 理由 |
|------|----------|------|
| 本地开发/轻量 | Chroma | 零配置、内存/文件存储 |
| 生产级云原生 | Pinecone | 托管服务、自动扩缩容 |
| 自托管生产 | Weaviate / Qdrant | 开源、高性能、混合检索 |

### 可观测性与监控（LG-08，v1.2 更新）
| 组件 | 推荐选择 | 用途 | 备注 |
|------|----------|------|------|
| **全链路追踪** | **Langfuse** | **Trace、Score、Dataset、Prompt Hub** | **v1.2 首选方案** |
| 指标采集（可选） | Prometheus | 延迟、吞吐量、错误率 | 与 Langfuse 互补 |
| 可视化（可选） | Grafana | 监控仪表盘 | 与 Langfuse 互补 |
| 链路追踪（可选） | OpenTelemetry | 标准化链路追踪 | Langfuse 已支持 OTLP |
| 日志聚合 | ELK / Loki | 集中化日志分析 | 生产环境建议 |
| 告警通知 | Alertmanager / PagerDuty | 异常告警 | 与 Prometheus 搭配 |

### Prompt 管理（LG-08，v1.2 新增）
| 组件 | 推荐选择 | 用途 |
|------|----------|------|
| 本地存储 | YAML + Jinja2/f-string | 开发阶段版本管理 |
| 云端托管 | **Langfuse Prompt Hub** | **生产环境同步、版本控制、团队协作** |
| 管理工具 | PromptManager（自定义） | 封装 get/build/save/push/pull API |

---

## 八、质量与学习效果保障

### 每个阶段的验证标准
- [ ] 能够不看讲义独立画出本阶段核心概念的脑图
- [ ] 能够独立修改/扩展本阶段的实战案例代码
- [ ] 能够向他人清晰解释本阶段至少 3 个核心概念的区别
- [ ] 实战案例的 AGUI 界面能够正常运行并展示预期效果

### 课程整体成功指标
- 学习者能够独立完成从需求分析到生产部署的完整 LangGraph 项目
- 学习者能够根据业务场景选择合适的多智能体架构模式
- **学习者能够独立设计并实现一个 DeepResearch 级别的复杂 Agent 工作流（含模式路由、计划循环、任务跟踪、节点缓存）**
- 学习者能够基于「复杂度×可观测性×定制需求」矩阵，快速判断预构建 Agent 与自定义 StateGraph 的选型
- **学习者能够集成 Langfuse 实现全链路可观测性（Trace、Score、Dataset）**
- **学习者能够管理 Prompt 生命周期（本地 YAML + Langfuse Prompt Hub 同步）**
- 学习者能够设计并部署 Redis + Postgres 混合持久化架构
- 学习者能够诊断和优化 LangGraph 应用的性能瓶颈（缓存、并发、状态大小）

---

## 九、演进计划

### v1.0
- 7 个阶段完整课程体系设计
- 每阶段理论 + 1 个可视化案例

### v1.1
- **新增 LG-08「高级模式与生产部署」阶段**
- **深化 LG-02**：新增预构建 Agent 深度对比与选型框架
- **深化 LG-04**：新增 Redis + Postgres 混合架构初步
- **深化 LG-06**：新增多 Subgraph 状态组合高级模式
- **调整 LG-07**：聚焦 Multi-Agent，生产部署内容移至 LG-08
- **技术栈扩展**：新增向量存储、Prometheus/Grafana、Docker 等生产组件

### v1.2（当前）
- **LG-07 案例全面替换为 DeepResearch Agent**：模式路由、计划路由循环、节点级缓存、任务跟踪、执行次数控制
- **LG-08 监控全面改用 Langfuse**：CallbackHandler、Trace、Tags、Score、Dataset 全链路可观测性
- **LG-08 新增 Prompt 生命周期管理模块**：YAML 本地存储、Langfuse Prompt Hub 同步、版本对比
- **LG-08 案例 OpsMate 增强**：Langfuse Trace 瀑布图、Score 时序趋势、Prompt 同步看板
- **技术栈更新**：监控首选 Langfuse，Prompt 管理加入 Langfuse Prompt Hub
- **成功指标更新**：增加 DeepResearch 设计能力、Langfuse 集成能力、Prompt 管理能力

### v1.3（当前）
- **新增 LG-00「为什么选择 LangGraph」导论阶段**：框架全景对比（LangGraph vs CrewAI vs Agno vs AutoGen vs Pydantic AI vs Spring AI vs LlamaIndex Workflows）
- 七维度雷达图对比、核心痛点深度解析、选型决策树

### v1.4（规划）
- 增加 LangGraph Cloud 深度部署专题
- 增加与 Temporal / Celery 的集成案例
- 补充 MCP（Model Context Protocol）集成内容

### v1.5（规划）
- 增加 JS/TS 版本平行课程
- 增加语音/多模态 Agent 案例
- 增加评估与测试最佳实践（LangSmith / Langfuse 深度集成）

---

## 十、变更日志

### v1.2 → v1.3 变更详情

#### 新增内容

| 变更项 | 位置 | 说明 |
|--------|------|------|
| **LG-00 导论阶段** | **新增阶段 0** | **「为什么选择 LangGraph」**：对比 CrewAI/Agno/AutoGen/Pydantic AI/Spring AI/LlamaIndex Workflows，七维度雷达图，选型决策树 |
| **框架对比分析 AGUI** | LG-00 | 七维度雷达图可视化、代码行数统计对比、架构清晰度评分 |

#### 修改内容

| 变更项 | 位置 | 变更说明 |
|--------|------|----------|
| **课程总数更新** | 全局 | 8 阶段 → **9 阶段（含导论）** |
| **总时长更新** | 全局 | 32-40h → **34-42h** |
| **依赖关系图更新** | 全局 | 新增 LG-00 作为导论入口 |
| **AGUI 案例总览更新** | 全局 | 新增 LG-00 框架对比案例 |

---

### v1.1 → v1.2 变更详情

#### 新增内容

| 变更项 | 位置 | 说明 |
|--------|------|------|
| **DeepResearch Agent 架构解析** | **LG-07** | **全新核心案例**，覆盖模式路由、计划路由循环、节点级缓存、任务跟踪系统、执行次数控制、追问建议 |
| **任务跟踪系统概念** | LG-07 | `@track_execute` 装饰器、任务状态机（pending→running→completed/failed）、进度推送 |
| **Langfuse 全链路可观测性** | **LG-08** | **全面替代 Prometheus/Grafana**：`init_langfuse_observability()`、`CallbackHandler`、`create_callback_handler()`、`get_langfuse_config()`、Tags 标签系统 |
| **Langfuse Score 评分** | LG-08 | `report_cache_hit_rate()`、自定义评分（输出质量、响应时间） |
| **Langfuse Dataset 管理** | LG-08 | QA Capture 自动保存运行数据到 Dataset 用于后续评估 |
| **Prompt 生命周期管理** | **LG-08（8.7 新增模块）** | YAML 本地存储、Langfuse Prompt Hub 集成（自动拉取/推送/标签）、PromptManager API、版本对比 |
| **Prompt 同步看板 AGUI** | LG-08 OpsMate | 版本差异高亮、同步状态指示灯、一键推送/拉取 |
| **Langfuse Trace 瀑布图 AGUI** | LG-08 OpsMate | Trace 链路可视化、节点输入/输出/延迟详情 |

#### 修改内容

| 变更项 | 位置 | 变更说明 |
|--------|------|----------|
| **LG-07 案例替换** | **阶段 7** | **DevSquad AI → DeepResearch Agent**。原 DevSquad AI 移至附录备选。LG-07 标题调整为「多智能体系统与复杂工作流」 |
| **LG-07 时长增加** | 阶段 7 | 4-5h → **5-6h**，增加 DeepResearch 架构解析内容 |
| **LG-08 监控方案替换** | **阶段 8（8.6）** | **Prometheus/Grafana → Langfuse 作为首选方案**。原 Prometheus/Grafana 降级为「可选/了解」 |
| **LG-08 标题扩展** | 阶段 8 | 原「高级模式与生产部署」→ **「生产部署、可观测性与 Prompt 工程」** |
| **LG-08 时长增加** | 阶段 8 | 6-7h → **7-8h**，新增 Prompt 管理模块和 Langfuse 深化内容 |
| **LG-08 OpsMate 增强** | LG-08 | AGUI 新增 Langfuse Trace 瀑布图、Score 时序趋势看板、Dataset 管理界面、Prompt 同步看板 |
| **技术栈更新** | 全局 | 监控首选 **Langfuse**（替代 Prometheus/Grafana）；新增 **Langfuse Prompt Hub** 作为 Prompt 管理首选 |
| **成功指标更新** | 全局 | 新增 3 项成功指标：DeepResearch 设计能力、Langfuse 集成能力、Prompt 生命周期管理能力 |
| **教程映射更新** | 全局 | `langgraph-cache-guide.md`、`langgraph-hooks-guide.md`、`langgraph-parallel-execution-guide.md`、`langgraph-context-engineering-guide.md` 均新增 LG-07 映射 |

#### 数据更新

| 指标 | v1.1 | v1.2 |
|------|------|------|
| 阶段总数 | 8 | **8**（未变，内容深化） |
| 预计总时长 | 30-38 小时 | **32-40 小时** |
| AGUI 可视化案例 | 8 | **8**（LG-07/LG-08 案例全面增强） |
| 核心教材教程 | 5 | **5**（使用场景扩展） |
| LG-08 模块数 | 6 | **8**（+ Prompt 管理 + Langfuse Dataset） |

---

### v1.0 → v1.1 变更详情（历史记录）

#### v1.1 新增内容

| 变更项 | 位置 | 说明 |
|--------|------|------|
| **LG-08 全新阶段** | 阶段 8 | 新增「高级模式与生产部署」阶段，6-7 小时，覆盖预构建 Agent 深度模式、缓存策略实战、Redis+Postgres 混合架构、知识库向量检索/RAG、生产化部署深化 |
| **OpsMate 案例** | LG-08 | 全新 AGUI 案例：生产级运维监控仪表盘，包含缓存命中矩阵、双后端监控、向量检索热力图、性能大屏 |

#### v1.1 修改内容

| 变更项 | 位置 | 变更说明 |
|--------|------|----------|
| **LG-02 时长增加** | 阶段 2 | 3-4h → 4-5h，新增「预构建 Agent 深度对比」模块 |
| **LG-04 时长增加** | 阶段 4 | 4-5h → 5-6h，新增「Redis + Postgres 混合架构」初步 |
| **MemoryPal 增强** | LG-04 | AGUI 新增 Redis/Postgres 后端存储状态仪表盘 |
| **LG-06 时长增加** | 阶段 6 | 4-5h → 5-6h，新增「多 Subgraph 状态组合高级模式」 |
| **ResearchForge 增强** | LG-06 | AGUI 新增子图层级拓扑图 |
| **LG-07 聚焦调整** | 阶段 7 | 原「多智能体与生产部署」→「多智能体系统」，生产部署内容移至 LG-08，时长 5-6h → 4-5h |
| **SmartRouter 增强** | LG-02 | AGUI 新增预构建/自定义 Agent 执行路径对比视图 |

---

*本文档为 LangGraph 课程体系的设计蓝图，具体实现时每阶段的讲义和代码应根据 LangGraph 最新版本（当前 v1.x）进行适配更新。*
