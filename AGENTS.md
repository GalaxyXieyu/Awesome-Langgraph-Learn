# 项目指导

本项目的课程目标不是“把 API 讲完”，而是帮助学生建立 Agent / Graph 的正确心智模型。所有 notebook、代码、配图和练习都要服务这个目标。

## 1. 课程最高原则

### 1.1 API 不是入口，人的直觉才是入口

每个概念都先从人类世界里的自然动作讲起，再说明 Agent / Graph 为什么不会自然这样做，最后才贴上 API 名。

固定推理顺序：

```text
人类自然动作 → Agent/Graph 的限制 → 学生的反直觉点 → 机制需求 → 白话模型 → API 名 → 可运行证据
```

不要用 `Human-in-the-loop`、`interrupt()`、`checkpointer`、`Command(resume=...)` 这类术语开场。术语只能在学生已经理解动作之后出现。

### 1.2 好教程要改变心智模型

一节课讲完后，学生应该能不用 API 名解释机制。

例如，在说 `interrupt()` 之前，学生应该能先说出：

> 图运行到高风险动作前，保存当前状态，生成一条待审批任务，等待人的决定，然后从同一个位置继续执行。

如果学生只能背 API 名，不能说出“为什么需要它”，这节课还没讲透。

### 1.3 人类协作和 Graph/Agent 执行模型必须对齐讲

课程要持续解释这组差异：

```text
人类工作：连续对话、共享上下文、可随时打断、很多判断是隐式的。
Graph 工作：显式状态流转、固定边、checkpoint 保存现场、resume 值显式恢复。
Agent 工作：模型提出动作，工具调用可能产生副作用，安全边界必须人为插入。
```

学生常常不是不理解业务需求，而是不理解为什么到了 Graph / Agent 里要显式设计状态、边、工具审批、挂起和恢复。

### 1.4 可读性大于鲁棒性

这是教学，不是 SDK。教学代码优先让学生第一遍读懂，不追求生产级鲁棒性。

不要为了兼容各种环境写多层 fallback、自动猜模型、复杂配置系统或隐藏 helper。模型、base URL、key、temperature 等关键配置要显式写出来或从明确环境变量读取。缺配置时可以直接报错并提示配置方式，不要悄悄切换到 fake model。

### 1.5 真实 LLM 优先

只要课程讲的是 Agent / LLM 行为，示例就应该用真实 LLM 跑通。fake fallback 和硬编码假模型会让学生同时理解“假模拟器”和“真实机制”，反而增加难度。

fake model 只适合明确讲 graph 机制、且 fake 部分极小的时候。

### 1.6 课程要训练判断力，不只是给答案

学生不只需要知道“该用哪个 API”，还要知道“为什么这里选它、还有哪些合理选择、换场景后怎么迁移”。

讲到后端、模型、存储、图形表达、审批边界这类工程选择时，不能只给结论。要用最小必要篇幅交代：

```text
可选方案 → 本课选择 → 选择理由 → 适用边界 → 换场景时怎么判断
```

但不要机械堆表格、堆链接、堆枚举。只补学生形成判断所缺的那部分。如果一个选择已经能从上下文自然推出，就融合进叙事；如果学生会疑惑“为什么不用另一个方案”，就显式解释。

好的课程补充不是“信息更多”，而是让学生多一个可迁移的判断框架。

## 2. 一节课的设计流程

写 notebook 前，先按这个流程推演：

```text
1. 找人类场景：学生熟悉的真实动作是什么？
2. 找模型反差：Graph/Agent 为什么不会自然这么做？
3. 写核心冲突句：一句话让学生记住问题。
4. 画认知图：先用图建立直觉，再讲术语。
5. 设计证据链：代码要证明什么，而不是只是跑一下。
6. 补选型判断：这里有没有学生会追问“为什么不用 X”？
7. 设计练习：练习要延展本节机制。
```

好的核心冲突句示例：

- `人会问，图不会`
- `风险识别不等于风险拦截`
- `待办不是聊天，是恢复事件`
- `工具调用前，要先过人这一关`
- `人处理的是待办，图接收的是恢复值`

好的选型疑问句示例：

- `为什么这里用 Postgres，而不是继续用内存？`
- `为什么这张图用 SVG，而不是生成图？`
- `为什么把长期偏好放 Store，而不是塞进 checkpoint？`
- `为什么审批放工具 wrapper，而不是只放某个 Agent 节点？`

标题也要围绕问题，而不是围绕 API：

- 推荐：`从一条不能直接发布的文案开始`
- 推荐：`把“问一下主管”拆成几个动作`
- 避免：`先别急着看 interrupt()`

## 3. Notebook 输出契约

每个 `tutorial.ipynb` 都应该像一节有引导的课程，而不是代码堆砌。

推荐结构：

```text
1. 人类场景 / 学生问题
2. Agent/Graph 为什么和人类做法不一样
3. 一张直觉图或机制图
4. 最小数据准备，不打印无意义 setup 信息
5. 必要时先展示一个会出错的 baseline
6. 核心实现拆成短小代码单元
7. 每个代码单元只观察一个行为
8. 最后用证据链 demo 串起来
9. 练习延展本节机制
```

推荐单元节奏：

```text
Markdown：这个单元回答什么问题
Code：最小实现或最小实验
Output：只展示学生需要看到的证据
Markdown：刚才发生了什么，为什么重要
```

避免长篇 markdown 后面接巨大代码块。

章节收束不要只是重复代码输出。最后一屏应该帮助学生把本节机制带走：

```text
本节解决了什么反直觉问题 → 机制分层 / 全景图 → 一句话判断规则 → 可迁移练习
```

如果收束内容包含多列对比、生命周期、隔离方式、选型理由，优先做成可维护的 SVG 或表格化 markdown；代码 `print()` 只能作为证据，不要替代认知总结。

## 4. 教学代码契约

### 4.1 命名要服务理解

中文课程里，**讲解文本、输出标签、图中标签、注释可以使用中文**，但 Notebook 里的 Python 代码标识符默认使用英文，保持专业、贴近真实项目。

适合中文：

- Markdown 讲解、章节标题、图中主标签
- `print()` 里给学生看的临时输出标签
- 简短教学注释，放在相关代码上方说明教学意图
- 业务示例数据里的中文内容

代码标识符默认用英文：

- 类名、函数名、变量名：`AssistantState`、`generate_reply`、`chat_history`、`risk_review_prompt`
- Graph 节点名建议英文，必要时输出时再映射成中文标签
- prompt 变量也用英文命名，但内容可以是中文：`copy_generation_prompt_template`
- 如果某个变量需要中文解释，用上一行 `#` 注释说明，不要把变量名、函数名、类名翻译成中文

推荐写法：

```python
# 生成文案时使用的系统提示词，内容会给学生直接阅读和修改。
copy_generation_system_prompt = """
你是内容运营助手。请根据发布请求生成文案，并返回 JSON。
"""
```

避免写法：

```python
生成文案提示词 = """
你是内容运营助手。请根据发布请求生成文案，并返回 JSON。
"""
```

保留英文：

- LangGraph / LangChain API 名
- 外部库要求的字段
- 模型和工具协议字段：`messages`、`tool_calls`、`content`、`role`

避免泛名：`naive`、`foo`、`bar`、`handler`、`processor`、`manager`、`demo_result`。

### 4.2 Prompt 是教学材料

提示词不要藏在内联字符串里。它要作为课程内容被学生看见、理解和修改。

推荐：

```python
OPENAI_MODEL = os.environ["OPENAI_MODEL"]
OPENAI_BASE_URL = os.environ["OPENAI_BASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

chat_model = init_chat_model(
    f"openai:{OPENAI_MODEL}",
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
    temperature=0,
)

# 生成文案时使用的系统提示词，内容会给学生直接阅读和修改。
copy_generation_system_prompt = """
你是内容运营助手。请根据发布请求生成文案，并返回 JSON。
"""
```

要求：

- 模型配置显式可见。
- prompt 放在有意义的变量里。
- prompt 短到学生愿意读。
- 如果后续流程依赖模型输出，优先要求结构化 JSON。
- 必要时先展示一条模型回复样例，再接入 graph。

Prompt 要优先使用 `ChatPromptTemplate` 或清晰的模板变量，不要把大段 f-string 塞进业务函数里。推荐命名：`copy_generation_system_prompt`、`copy_generation_user_prompt_template`、`risk_review_user_prompt_template`。

长 prompt 不要直接嵌在 `ChatPromptTemplate.from_messages([...])` 里面，否则缩进和换行会很丑。先把 system prompt、human prompt template 单独定义成变量，再组装 `ChatPromptTemplate`。

业务函数里只保留：准备变量 → invoke 模板 → 调模型 → 解析结果 → 写回 state。

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

英文状态码打印前要映射成中文：

```python
状态显示 = {"published": "已发布", "reject": "拒绝"}
print("发布状态:", 状态显示[result["publish_status"]])
```

### 4.4 不要过度封装

优先让学生能逐行追踪数据流。不要用深层 helper、工厂、抽象基类、复杂配置系统把机制藏起来，除非本节课就在讲这些东西。

### 4.5 `interrupt()` 所在节点要薄

LangGraph 恢复中断时，会从当前节点开头重新执行，而不是从 `interrupt()` 那一行继续执行。因此不要把“生成文案、调用外部 API、写数据库、审计日志、interrupt、发布”塞进一个复合节点里。

推荐拆法：

```text
生成文案节点 → 风险审查节点 → 人工审批节点 → 发布节点
```

`interrupt()` 所在节点最好只负责：准备给人看的 payload、接收 `Command(resume=...)` 的值、把人工决定写回 state。这样恢复时即使节点重跑，也不会重复生成、重复调用外部服务或重复写数据库。

## 5. 配图契约

### 5.1 图是认知脚手架

大段概念解释优先压缩成图。常用结构：

```text
A. 人类世界：学生熟悉的自然动作
B. Agent/Graph 世界：为什么它不会自然发生
C. 机制桥梁：系统需要拆成哪些机器动作
```

主标签用中文。API 名可以保留英文，但只能做较小的辅助标签。

### 5.2 统一视觉风格

生成课程图使用这个风格：

- NeurIPS / Nature 风格的学术教学图
- 暖白色背景
- 柔和论文图配色：灰绿、雾蓝、鼠尾草绿、暖沙色、柔和珊瑚色、石板灰
- 细线条、向量感箭头、精致圆角卡片
- 留白充足、阴影克制、对齐精确
- 中文字体大且清晰
- 不要卡通风、不要 3D、不要玻璃拟态 UI、不要深色背景、不要假 logo、不要水印、不要乱码

参考文件：

- `turtorial/LG-03-human-in-the-loop/images/FIGURE_STYLE.md`
- `.claude/skills/gpt-image/references/gallery.md`
- `.claude/skills/gpt-image/references/gallery-research-paper-figures.md`
- `.claude/skills/gpt-image/references/craft.md`

### 5.3 SVG、Mermaid 和生成图的分工

选图形载体时，先问这张图承担什么教学任务，不要为了“看起来高级”默认用生成图，也不要为了省事只用代码打印。

用 SVG / Mermaid：

- 标签、术语、箭头和表格列名必须精确。
- 图在解释 API、状态流转、执行位置、生命周期或隔离方式。
- 后续需要频繁改字、增删节点、放进 git diff 里维护。
- 章节总结图、机制全景图、对比表格图优先用 SVG。

用生成图：

- 章节引入图、概念封面图、隐喻图。
- 需要高级视觉风格、情绪氛围和记忆点。
- 中文标签较少，或标签已经先由 SVG / 文字结构定稿。

用代码打印表格：

- 只作为运行证据，不作为核心认知图。
- 适合证明“刚才程序真的产生了这个结果”。
- 不适合承担章节全景总结，因为学生很难从输出框形成稳定心智模型。

最佳流程：

```text
先用文字或 SVG 定结构 → 再生成 GPT 精修图 → notebook 引用本地图片
```

### 5.4 通过 `image-this-remote` MCP 生成图

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

prompt 必须明确：

```text
所有可见标签使用简体中文。
API 名可以保留英文，但必须是较小的辅助标签。
风格是 NeurIPS / Nature 风格的学术教学图。
不要卡通、不要 3D、不要深色背景、不要假 logo、不要水印、不要乱码。
```

MCP 返回的本地路径可能是服务端路径，不一定是当前项目机器上的真实文件。以返回的远端 artifact URL 为准，下载到本地章节目录：

```bash
curl -L --fail "<artifact-url>" \
  -o "turtorial/<chapter>/images/<figure-name>.png"
```

Notebook 中使用相对路径引用：

```markdown
![图说明](images/<figure-name>.png)
```

如果当前 Claude Code 会话看不到新配置的 MCP 工具，重启会话或重新加载 MCP 配置后再试。

## 6. 重点概念的讲法

这些概念必须配场景、配图和小型可运行例子：

- `state`：不是随便一个字典，而是图的共享工作台。
- `node`：不是人类步骤，而是接收 state、返回更新的执行单元。
- `edge` / router：不是随口判断，而是显式控制流。
- `interrupt()`：不是聊天，而是创建待处理的外部决策，并挂起当前运行。恢复时会从所在节点开头重跑，所以不要放进大而杂的复合节点。
- `Command(resume=...)`：不是新请求，而是人的决定回到原来挂起的位置。
- `checkpointer`：不是个性化记忆，而是保存可恢复现场，让流程可以断开后再继续。
- Agent `tool_call`：不只是消息，它可能触发副作用，所以需要安全边界。
- Wrapper 级审批：不是重复代码，而是让危险能力无论被哪个 Agent / Graph 调用都不会漏审。

## 7. 练习契约

练习要延展本节机制，不要做无关杂活。

好的练习：

- 把人工决定从 `edit_and_approve` 改成 `reject`，观察分支变化。
- 给医疗效果文案增加法务审批路径。
- 人修改文案后，重新自动审核并比较风险分数。
- 把 `MemorySaver()` 换成持久化 checkpointer，验证进程重启后能恢复。
- 包装一个危险工具，让任何 Agent 调用前都必须经过人工审批。

避免只让学生改变量名或加装饰性日志。

## 8. 可参考案例

当前已有课程图案例：

- `turtorial/LG-03-human-in-the-loop/images/human-vs-graph-approval-cn-premium.png`
- `turtorial/LG-03-human-in-the-loop/images/human-vs-graph-approval.svg`
- `turtorial/LG-03-human-in-the-loop/images/three-interrupt-positions.svg`

当前已有风格说明：

- `turtorial/LG-03-human-in-the-loop/images/FIGURE_STYLE.md`
