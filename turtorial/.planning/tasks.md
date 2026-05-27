# LangGraph 教程开发任务列表

## 任务概览

- [x] 1. 梳理LangGraph官方文档并拆分课程体系
- [x] 2. 编写带AGUI可视化的.ipynb教程代码
- [x] 3. 编写讲解大纲逻辑文档

---

## 任务 1：梳理LangGraph官方文档并拆分课程体系

**状态**: completed

**产出**:
- `/turtorial/.planning/course-roadmap.md` — 完整的8阶段课程设计文档

---

## 任务 2：编写带AGUI可视化的.ipynb教程代码

**状态**: completed

**产出**: `/turtorial/notebooks/` 目录下的8个完整Jupyter Notebook

| 文件 | 阶段 | 案例名称 | 核心内容 |
|------|------|----------|----------|
| `01_stategraph_basics.ipynb` | LG-01 | WeatherBot | StateGraph基础、State/Node/Edge、Reducer、MessagesState |
| `02_routing_tools.ipynb` | LG-02 | SmartRouter | 条件边、循环重试、ToolNode、预构建Agent对比 |
| `03_streaming.ipynb` | LG-03 | LiveWriter | 5种stream_mode、custom事件、astream_events |
| `04_persistence_memory.ipynb` | LG-04 | MemoryPal | MemorySaver、thread_id、Store概念、Postgres/Redis混合架构 |
| `05_human_in_the_loop.ipynb` | LG-05 | ContentGuard | interrupt()、Command.resume、interrupt_before/after、Hooks |
| `06_parallel_subgraphs.ipynb` | LG-06 | ResearchForge | Fan-out/Fan-in、Reducer并发、Subgraph嵌入、Send Map-Reduce |
| `07_deepresearch_agent.ipynb` | LG-07 | DeepResearch Agent | 模式路由、计划路由循环、任务跟踪、节点级缓存、执行次数控制 |
| `08_production_langfuse.ipynb` | LG-08 | OpsMate | Langfuse可观测性、PromptManager、缓存策略、生产部署清单 |

**代码规范**:
- 使用 LangGraph >=1.0.0 API
- 每个notebook顶部有依赖安装命令
- 中文注释和输出
- API key使用占位符 `YOUR_API_KEY`
- AGUI可视化使用 `draw_mermaid_png()` 展示图结构
- 外部服务部分提供模拟方案或详细说明

---

## 任务 3：编写讲解大纲逻辑文档

**状态**: completed

**产出**: `/turtorial/LG-*/` 目录下的 outline.md 讲解大纲

---

## LG-03 预构建 Agent 教程文件

**状态**: completed

**产出**:
- `/turtorial/LG-03-prebuilt-agents/tutorial.ipynb` — Jupyter Notebook 教程（10个章节）
- `/turtorial/LG-03-prebuilt-agents/exercises.md` — 课后练习题（6道编程题 + 1道设计题）
- `/turtorial/LG-03-prebuilt-agents/outline.md` — 讲解大纲（已存在）

**tutorial.ipynb 内容结构**:
1. 为什么需要预构建 Agent
2. create_react_agent 快速上手（工具定义 + 3行代码搭建 + 运行）
3. 内部机制白盒化（should_continue 路由 + 步数限制 + 图结构可视化）
4. 自定义 System Prompt 和配置（字符串/SystemMessage/函数）
5. 添加记忆（InMemorySaver + thread_id）
6. 消息历史管理（Trimming/Summarization/Tool精简）
7. 观察内部过程（stream 代替 invoke）
8. 预构建 vs 自定义 StateGraph（对比矩阵 + 决策树 + 实战对比）
9. 常见误区与注意事项
10. 阶段小结

**exercises.md 内容结构**:
- 练习1：用 create_react_agent 搭建数学助手
- 练习2：为 Agent 添加记忆能力
- 练习3：实现消息裁剪防止上下文爆炸
- 练习4：预构建 vs 自定义 StateGraph 对比实现
- 练习5：动态 System Prompt 根据对话轮数切换模式
- 练习6：用 stream 监控 Agent 的 tool_calls 消耗
- 设计题：预构建 Agent 的适用边界分析

---
