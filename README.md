# LangGraph 从入门到生产：一条完整的学习路径

> 写 AI Agent 的人都有一个共同的感受：Demo 五分钟，上线五个月。

## 这个仓库解决什么问题

2025 到 2026 年，AI Agent 框架井喷。你可能已经试过几个——快速搭出一个能跑的 Demo 并不难，但一旦涉及到这些需求，事情就变得复杂：

- **用户中途改需求**，图怎么暂停、修改状态、再接着跑？
- **对话需要上下文记忆**，进程重启后历史记录怎么恢复？
- **复杂任务要拆给多个 Agent 并行处理**，结果怎么合并、状态怎么隔离？
- **上线后出 bug**，只知道输入输出，中间每一步发生了什么完全黑盒
- **API 费用暴涨**，却不知道哪一步在烧钱、哪里可以加缓存

**LangGraph 是目前唯一把这些问题统一解决掉的框架**，但官方文档偏向 API 参考，缺少一条从"写出第一个图"到"部署到生产"的完整路径。

这个仓库就是那条路径。

## 学完你能做什么

```
入门 → 能独立写带路由判断的 Bot
进阶 → 能设计多 Agent 并行工作流，处理复杂业务场景
实战 → 能接入 Langfuse 监控全链路，定位瓶颈和费用黑洞
生产 → 能判断预构建 vs 自定义的选型，部署 Docker 容器化服务
```

具体能力：
- 根据业务复杂度选择 StateGraph、预构建 Agent、Supervisor、Swarm 等不同架构
- 用 Human-in-the-Loop 实现安全可控的人机协作系统
- 设计并行子图结构处理复杂工作流，掌握 Send/Map-Reduce 模式
- 用 Langfuse 监控每次请求的完整执行链路、Token 用量、成本分析
- 管理 Prompt 版本，实现开发到生产的无缝同步

## 适合谁

- **有 Python 基础**，想亲手写出第一个 LangGraph Agent 的新手
- **已有 LangChain 经验**，被 Chain 的线性限制卡住，想了解图编排的开发者
- **正在做 AI 项目**，需要持久化、人机协作、多 Agent 等生产级能力的工程师
- **想系统学习**，而不是碎片化看文档、抄 Demo 的自学者

## 内容结构

### 11 节渐进式教程（turtorial/）

每节包含`讲义.md`（知识讲解）+ `tutorial.ipynb`（可运行代码）。

| 课程 | 主题 | 你能带走的能力 |
|------|------|---------------|
| LG-00 | 为什么选 LangGraph | 框架选型决策能力，知道什么场景该用什么 |
| LG-01 | 基础与图构建 | State / Node / Edge / Router 的完整掌握 |
| LG-02 | Tools 深度掌握 | 工具定义、注入、缓存、性能优化 |
| LG-03 | 人机协作 | 中断、审批、Hook，实现安全可控的系统 |
| LG-04 | 记忆与持久化 | Checkpoint / Store / Postgres / Redis 混合架构 |
| LG-05 | 子图与并行 | Subgraph、Fan-out/Fan-in、Send/Map-Reduce |
| LG-06 | 预构建 Agent | create_agent / supervisor / swarm 的选型与实战 |
| LG-07 | 流式输出 | 实时推送进度到前端，掌握 SSE 和多 Agent 嵌套流式 |
| LG-08 | 多智能体系统 | DeepResearch Agent：模式路由、计划路由、任务跟踪 |
| LG-09 | 生产部署 | Docker、RAG、Langfuse 全链路监控、Prompt 生命周期管理 |
| LG-10 | 可视化调试 | Studio 断点调试、状态修改重跑、Langfuse Trace 分析 |

### 6 个独立示例项目（examples/）

每个都是可单独运行的完整应用，不是玩具代码：

- **context-engineering-chat** — 上下文裁剪与窗口控制，解决长对话 token 爆炸
- **redis-memory-chat** — Redis 持久化记忆，进程重启对话不丢失
- **multi-agent-handoff** — 三种多智能体架构（Supervisor / Swarm / Handoff）对比实现
- **celery-async-tasks** — LangGraph + Celery 异步任务队列，处理耗时操作
- **langsmith-prompt-pipeline** — 提示词版本管理 + 自动评测 + 回归测试
- **studio-graph** — LangGraph Studio 可视化调试实战

## 快速开始

如果你只是从 LG-00 / LG-01 开始学习，不需要一上来启动 Docker。前两节的目标是先理解“为什么需要图”和 State / Node / Edge 的基本心智模型，本地 Python 环境就够了。

**方式一：轻量本地学习（推荐先用这个）**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U langgraph langchain langchain-openai jupyter
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
jupyter notebook
```

适合：LG-00、LG-01、LG-02，以及大多数不需要数据库的概念练习。

**方式二：只启动课程需要的基础服务**

从 LG-04 记忆、持久化、pgvector 检索开始，再启动精简版 Docker：

```bash
docker compose -f docker-compose.minimal.yml up -d
```

它只包含 PostgreSQL + pgvector 和 Redis，用来跑 checkpoint、Store、缓存相关例子。

**方式三：完整生产观测环境**

只有当你学到 Langfuse 和生产监控时，才需要完整环境：

```bash
docker compose up -d
open http://localhost:3000   # Langfuse 可观测性界面
```

详细 Docker 配置见 [DOCKER.md](DOCKER.md)。

## 项目结构

```
.
├── docker-compose.yml              # 可选完整环境：PG + pgvector + Redis + Langfuse
├── docker-compose.minimal.yml      # 可选精简环境：PG + pgvector + Redis
├── .env.example                    # 环境变量模板
├── DOCKER.md                       # Docker 详细文档
│
├── turtorial/                      # 11 节教程（讲义 + Notebook）
│   ├── LG-00-why-langgraph/
│   ├── LG-01-basics/
│   └── ...
│
├── examples/                       # 6 个独立示例项目
│   ├── 05-context-engineering-chat/
│   ├── 05-redis-memory-chat/
│   ├── 08-multi-agent-handoff/
│   ├── 09-celery-async-tasks/
│   ├── 09-langsmith-prompt-pipeline/
│   └── 10-studio-graph/
│
└── utils/
    └── pretty_print.py
```

## 学习路径建议

```
第 1 周：LG-00 → LG-01 → LG-02 → 跑通 WeatherBot
第 2 周：LG-03 → LG-04 → 实现带审批和记忆的对话系统
第 3 周：LG-05 → LG-06 → LG-07 → 做流式多 Agent 演示
第 4 周：LG-08 → LG-09 → LG-10 → 部署 + 监控 + 调优
```

## 环境变量

```bash
# LLM（必填）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # 非官方渠道需配
OPENAI_MODEL=deepseek-v4-flash

# 数据库（Docker 默认值即可）
POSTGRES_USER=langgraph
POSTGRES_PASSWORD=langgraph
REDIS_PASSWORD=redis

# Langfuse（首次启动后在界面创建项目获取）
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
```

## License

MIT
