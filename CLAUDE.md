# 项目指导

这个项目的课程目标不是“把 API 讲完”，而是帮助学生建立 Agent / Graph 的正确心智模型。每个 notebook、配图、代码示例都应该服务这个目标。

## 1. 基础思考原则

### 1.1 先讲人类世界，再讲机器世界

写 LangGraph / Agent 课程时，先从人类工作里的自然动作开始，再对比 Agent / Graph 为什么不会自然这么做。

推荐思考顺序：

```text
人类自然会怎么做？
Agent/Graph 为什么不会自然这么做？
学生会在哪里觉得反直觉？
系统缺了什么机制？
这个机制把人类动作拆成了哪些机器动作？
最后再说官方术语/API。
```

不要一开始就抛出 `Human-in-the-loop`、`interrupt()`、`checkpointer`、`Command(resume=...)` 这类术语。API 是最后贴上的名字，不是课程入口。

### 1.2 好教程要改变心智模型

好教程不是解释一个 API，而是让学生能用自己的话解释机制。

例如，在说 `interrupt()` 之前，学生应该先能说出：

> 图运行到高风险动作前，保存当前状态，生成一条待审批任务，等待人的决定，然后从同一个位置继续执行。

如果学生只能背 API 名，不能解释为什么需要这个机制，这节课还没讲透。

### 1.3 课程图是认知脚手架

配图不是装饰，而是用来减少文字、暴露反差、建立直觉。

密集概念优先压缩成 1–2 张图：

1. 直觉图：人类世界的交互方式 vs Agent/Graph 的执行模型。
2. 机制图：把机器动作拆开，API 名只做小号辅助标签。

主标签优先中文。API 名可以保留英文，但不能成为视觉中心。

### 1.4 示例要用真实 LLM 跑通

只要课程讲的是 Agent / LLM 行为，就优先使用真实 LLM。

不要用 fake fallback 或硬编码假模型掩盖机制。假的 fallback 往往会增加阅读负担，因为学生要同时理解假模拟器和真实概念。

如果缺少凭据，就清楚报错并提示如何配置；不要静默切换到 fake model。

### 1.5 可读性大于鲁棒性

教学代码优先让学生第一遍能读懂，不追求生产级鲁棒性。不要为了兼容各种环境写多层 fallback、自动猜模型、复杂解析或隐藏配置逻辑。

模型、base URL、key、temperature 等课程关键配置应该显式写出来或从明确的环境变量读取。缺少配置时可以直接报错并提示配置方式，不要悄悄切换成另一个模型或 fake fallback。

### 1.6 可执行清晰优先于工程封装

Notebook 代码的目标不是展示生产架构，而是让学生第一遍能读懂。

优先：

- 数据流直接，能逐行追踪。
- 一个代码单元只讲一个概念。
- 少量短函数，必要时用中文命名。
- 中文注释解释“为什么要有这一行”。
- 输出只展示教学证据。

避免：

- 深层 helper 把机制藏起来。
- 工厂、抽象基类、复杂配置系统，除非本节课就在讲它们。
- 大型 fake service。
- `handler`、`processor`、`manager`、`demo_result`、`naive` 这类泛名。
- 很长的 setup 单元和无意义打印。

## 2. 课程设计流程

设计一节课时，先按这个流程推演，不要直接写代码。

### 2.1 找到人类场景

先找一个学生熟悉的现实场景。

例如 HITL：

```text
新人看到高风险文案，不会直接发布，而是问主管：这个能发吗？
```

### 2.2 找到模型反差

明确人类世界和 Graph / Agent 世界的差异。

```text
人类工作：连续对话、共享上下文、可随时打断、很多判断是隐式的。
Graph 工作：显式状态流转、固定边、checkpoint 保存现场、resume 值显式恢复。
Agent 工作：模型提出动作，工具调用可能产生副作用，安全边界必须人为插入。
```

学生通常不是不理解业务需求，而是不理解为什么到了 Graph / Agent 里需要显式机制。

### 2.3 设计一句核心冲突

每个核心概念最好有一句能记住的冲突句。

例如：

- `人会问，图不会`
- `风险识别不等于风险拦截`
- `待办不是聊天，是恢复事件`
- `工具调用前，要先过人这一关`
- `人处理的是待办，图接收的是恢复值`

这句话应该影响标题、配图和开场解释。

### 2.4 先画机制，再写解释

大段解释优先压缩成图。

推荐结构：

```text
A. 人类世界：学生熟悉的自然动作
B. Agent/Graph 世界：为什么它不会自然发生
C. 机制桥梁：系统需要拆成哪些机器动作
```

### 2.5 设计证据链

代码不是为了“跑一下”，而是为了证明课程目标。

最终 demo 应该串成一条证据链，例如 HITL：

```text
没有审批会误发布
高风险会生成待办
人修改后恢复会发布修改稿
人拒绝后流程改走拒绝分支
低风险不会生成待办
执行前/执行后挂起的差异能被观察到
```

## 3. Notebook 写作方式

每个 `tutorial.ipynb` 应该像一节有引导的课程，而不是代码堆砌。

推荐结构：

```text
1. 人类场景 / 学生问题
2. 为什么 Agent/Graph 模型和人类做法不一样
3. 一张直觉图或紧凑机制图
4. 最小数据准备，不打印无意义 setup 信息
5. 如果有助于说明问题，可以先写一个故意有缺陷的 baseline
6. 核心实现拆成几个短小、可读的代码单元
7. 每个代码单元只观察一个行为
8. 最后用证据链 demo 串起来
9. 练习要延展本节机制，而不是做无关杂活
```

推荐单元节奏：

```text
Markdown：这个单元要回答什么问题
Code：最小实现或最小实验
Output：只展示学生需要看到的证据
Markdown：刚才发生了什么，为什么重要
```

避免长篇 markdown 后面接一个巨大代码块。

## 4. 教学代码规范

### 4.1 命名贴近学生直觉

中文课程里，学习者可见的演示代码可以使用中文命名。

适合用中文：

- 演示函数名：`查找发布请求`、`生成文案`、`审查风险`、`直接发布`
- 提示词变量：`生成文案提示词`、`风险审查提示词`、`工具调用审批提示词`
- 打印标签和注释

保留英文：

- LangGraph / LangChain API 名
- 外部库要求的数据结构字段
- 模型和工具协议字段，例如 `messages`、`tool_calls`、`content`、`role`

### 4.2 提示词是教学材料

提示词不要藏在内联字符串里。它应该是学生能读到、能理解、能修改的课程内容。

推荐：

```python
MODEL_NAME = os.getenv("LG03_MODEL", "openai:gpt-4o-mini")
chat_model = init_chat_model(MODEL_NAME)

生成文案提示词 = """
你是内容运营助手。请根据发布请求生成文案，并返回 JSON。
"""
```

要求：

- 模型选择放在一个清晰变量里。
- 提示词放在命名变量里。
- 提示词要短到学生愿意读。
- 如果后续流程依赖模型输出，优先要求结构化 JSON。
- 必要时，先展示一条模型回复样例，再接入 graph。

### 4.3 输出必须是证据

好的输出：

```text
是否生成待办: 是
图停在: 等待人工审批
恢复后发布状态: 修改后发布
```

避免：

```text
setup complete
graph compiled
requests: 4
policy_rules: 4
```

setup 信息如果有用，写进注释或 markdown。不要让学生被无意义输出刷屏。

当原始值是英文状态码时，打印前映射成中文：

```python
状态显示 = {"published": "已发布", "reject": "拒绝"}
print("发布状态:", 状态显示[result["publish_status"]])
```

## 5. 课程图生成规范

### 5.1 统一视觉风格

生成课程图时使用这个风格：

- NeurIPS / Nature 风格的学术教学图
- 暖白色背景
- 柔和的论文图配色：灰绿、雾蓝、鼠尾草绿、暖沙色、柔和珊瑚色、石板灰
- 细线条、向量感箭头
- 精致圆角卡片
- 留白充足
- 阴影克制
- 对齐精确
- 中文字体大且清晰
- 不要卡通风、不要 3D、不要玻璃拟态 UI、不要深色背景、不要假 logo、不要水印、不要乱码

可复用风格文件：

- `turtorial/LG-03-human-in-the-loop/images/FIGURE_STYLE.md`

参考资料：

- Skill：`gpt-image`
- 图库索引：`.claude/skills/gpt-image/references/gallery.md`
- 论文图模板：`.claude/skills/gpt-image/references/gallery-research-paper-figures.md`
- 提示词规则：`.claude/skills/gpt-image/references/craft.md`

### 5.2 SVG 和生成图怎么选

用 SVG / Mermaid：

- 标签必须精确。
- 图在解释 API、状态流转、执行位置。
- 后续需要频繁改字。

用生成图：

- 章节引入图。
- 概念封面图。
- 需要高级视觉风格和记忆点。

最佳流程：

```text
先用文字或 SVG 定结构 → 再生成 GPT 精修图 → notebook 引用本地图片
```

### 5.3 通过 `image-this-remote` MCP 生成图

生成精致课程图时，优先使用 `image-this-remote` MCP，而不是直接写本地 API 脚本。

推荐参数：

```text
工具：generate_image
provider: openai
model: gpt-image-2
aspect_ratio: 16:9
resolution: high
output_dir: 当前章节的 images/ 目录
```

生成时 prompt 要明确：

```text
所有可见标签使用简体中文。
API 名可以保留英文，但必须是较小的辅助标签。
风格是 NeurIPS / Nature 风格的学术教学图。
不要卡通、不要 3D、不要深色背景、不要假 logo、不要水印、不要乱码。
```

MCP 返回的本地路径可能是服务端路径，不一定是当前项目机器上的真实文件。要以返回的远端 artifact URL 为准，下载到本地章节目录。

下载方式：

```bash
curl -L --fail "<artifact-url>" \
  -o "turtorial/<chapter>/images/<figure-name>.png"
```

Notebook 中使用相对路径引用：

```markdown
![图说明](images/<figure-name>.png)
```

如果当前 Claude Code 会话看不到新配置的 MCP 工具，重启会话或重新加载 MCP 配置后再试。

## 6. 通常需要额外解释的概念

这些概念很容易让学生困惑，应该配场景、配图和小型可运行例子：

- `state`：不是随便一个字典，而是图的共享工作台。
- `node`：不是人类步骤，而是一个接收 state、返回更新的执行单元。
- `edge` / router：不是随口判断，而是显式控制流。
- `interrupt()`：不是聊天，而是创建一个待处理的外部决策，并挂起当前运行。
- `Command(resume=...)`：不是新请求，而是人的决定回到原来挂起的位置。
- `checkpointer`：不是个性化记忆，而是保存可恢复现场，让流程可以断开后再继续。
- Agent `tool_call`：不只是消息，它可能触发副作用，所以需要安全边界。
- Wrapper 级审批：不是重复代码，而是让危险能力无论被哪个 Agent / Graph 调用都不会漏审。

## 7. 练习设计

练习应该延展本节机制，不要问无关的编码杂活。

好的练习：

- 把人工决定从 `edit_and_approve` 改成 `reject`，观察分支变化。
- 给医疗效果文案增加法务审批路径。
- 人修改文案后，重新自动审核并比较风险分数。
- 把 `MemorySaver()` 换成持久化 checkpointer，验证进程重启后能恢复。
- 包装一个危险工具，让任何 Agent 调用前都必须经过人工审批。

避免只让学生改变量名或加装饰性日志。

## 8. 可参考案例

当前已有的课程图案例：

- `turtorial/LG-03-human-in-the-loop/images/human-vs-graph-approval-cn-premium.png`
- `turtorial/LG-03-human-in-the-loop/images/human-vs-graph-approval.svg`
- `turtorial/LG-03-human-in-the-loop/images/three-interrupt-positions.svg`

当前已有的风格说明：

- `turtorial/LG-03-human-in-the-loop/images/FIGURE_STYLE.md`
