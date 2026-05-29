# LG-10 课后练习：LangGraph Studio 可视化调试与 Langfuse 可观测性

## 实操题

### 练习 1：编写 langgraph.json 配置文件

为一个新的 Agent 项目编写 `langgraph.json` 配置文件。假设你的项目结构如下：

```
my_agent/
├── langgraph.json
├── pyproject.toml
└── src/
    └── agent/
        ├── __init__.py
        └── graph.py          # 包含 graph = builder.compile()
```

**要求**：
1. 正确配置 `dependencies`，让 Studio 能找到项目依赖
2. 正确配置 `graphs`，指向 `graph.py` 中的 `graph` 变量
3. 说明 `langgraph.json` 中每个字段的作用

<details>
<summary>参考答案</summary>

```json
{
  "dependencies": ["."],
  "graphs": {
    "my_agent": "./src/agent/graph.py:graph"
  }
}
```

**字段说明**：

- `dependencies`: 依赖列表。`"."` 表示当前目录，Studio 会读取 `pyproject.toml` 或 `requirements.txt` 安装依赖。
- `graphs`: 图定义映射。键 `"my_agent"` 是图的名称（在 Studio 界面显示），值 `"./src/agent/graph.py:graph"` 是 `文件路径:变量名`，指向 `graph.py` 中 `graph = builder.compile()` 的那个 `graph` 变量。

**常见错误**：
- 路径写错：`src/agent/graph.py` 漏了 `./` 前缀
- 变量名不匹配：`graph.py` 里实际变量叫 `app` 但配置写了 `graph`
- 依赖未安装：忘记在 `pyproject.toml` 中加入 `langgraph` 等依赖

</details>

---

### 练习 2：在 Studio 中执行时间旅行调试

使用本课提供的 WeatherBot 示例，在 Studio 中完成以下操作：

1. 运行一次完整的天气查询（输入：`{"messages": [{"type": "human", "content": "北京今天天气怎么样？"}]}`）
2. 在时间线中点击 `parse_intent` 节点
3. 在状态面板中将 `intent` 从 `"weather"` 修改为 `"time"`
4. 点击 "Replay from here"
5. 观察图的实际执行路径

**问题**：
- 修改 `intent` 后，图走了哪条分支？为什么？
- `extract_city` 节点被执行了吗？为什么？
- 最终 `response` 的内容是什么？

<details>
<summary>参考答案</summary>

**执行路径**：
```
START → parse_intent → get_time → END
```

**回答**：

1. **修改 `intent` 后，图走了时间分支**。因为 `parse_intent` 节点的输出 `intent` 被修改为 `"time"`，而 `route_by_intent` 路由函数在 `intent == "time"` 时返回 `"get_time"`，所以图走向了 `get_time` 节点。

2. **`extract_city` 节点没有被执行**。因为条件路由 `route_by_intent` 已经指向了 `get_time`，不再走 `extract_city` 分支。这正是条件分支的威力——修改一个状态值，整个执行路径都会改变。

3. **最终 `response` 的内容类似于 `"现在是 14:30"`**（具体时间取决于执行时刻）。`get_time` 节点返回 `datetime.now().strftime('%H:%M')` 格式的时间字符串。

**调试价值**：
这个练习展示了 Studio 最核心的能力——**不需要修改代码、不需要重启服务**，就能验证 "如果某个中间状态不同，后续流程会怎样"。在排查 bug 时，你可以快速确认是某个节点的输出有问题，还是后续节点的处理有问题。

</details>

---

### 练习 3：设置断点并逐步执行

在 Studio 中对 WeatherBot 进行断点调试：

1. 在 `query_weather` 节点上右键设置断点
2. 运行图，输入：`{"messages": [{"type": "human", "content": "上海天气如何？"}]}`
3. 当执行暂停在 `query_weather` 时，检查状态面板
4. 回答以下问题后点击 Continue 继续执行

**问题**：
- 断点暂停时，Input State 中 `city` 的值是什么？
- 如果此时在状态面板中将 `city` 改为 `"深圳"`，然后 Continue，`query_weather` 节点会使用修改后的值吗？
- 为什么断点调试对排查 "某个节点输入异常" 的问题特别有效？

<details>
<summary>参考答案</summary>

**回答**：

1. **Input State 中 `city` 的值是 `"上海"`**。因为用户输入包含 "上海"，`extract_city` 节点从文本中提取了城市名。

2. **会使用修改后的值**。Studio 的状态面板允许在断点处实时修改 State，修改后的值会作为该节点的 Input State 传入。所以如果将 `city` 改为 `"深圳"`，`query_weather` 节点看到的 `state["city"]` 就是 `"深圳"`。

3. **断点调试的有效性**：
   - 可以精确查看某个节点执行前的完整状态，确认上游节点传递的数据是否正确
   - 如果上游数据正确但输出异常，说明问题在该节点内部
   - 如果上游数据就不对，可以快速定位到出问题的上游节点
   - 不需要在代码里加 `print` 或改逻辑，不破坏原有代码结构

</details>

---

### 练习 4：接入 Langfuse 并分析 Trace

将 WeatherBot 接入 Langfuse，运行三次不同的查询，然后在 Langfuse 界面分析：

```python
queries = [
    "北京今天天气怎么样？",   # 天气分支
    "现在几点了？",           # 时间分支
    "讲个笑话"               # 兜底分支
]
```

**问题**：
1. 在 Langfuse Trace 列表页，三条 Trace 的耗时分别是多少？哪条最长？为什么？
2. 点击天气分支的 Trace，查看瀑布图：`parse_intent` → `extract_city` → `query_weather` → `format_weather_reply`，哪个节点耗时最长？
3. 如果 `query_weather` 调用了外部 LLM，Token 用量信息会出现在哪里？
4. 给这三次运行分别打上不同的标签（如 `branch:weather`、`branch:time`、`branch:fallback`），在 Langfuse 中如何按标签筛选？

<details>
<summary>参考答案</summary>

**回答**：

1. **耗时分析**：
   - 天气分支通常最长（4 个节点：parse_intent → extract_city → query_weather → format_weather_reply）
   - 时间分支次之（2 个节点：parse_intent → get_time）
   - 兜底分支最短（2 个节点：parse_intent → fallback_reply）
   
   具体耗时取决于机器性能，但节点数量越多、每个节点的处理越复杂，总耗时越长。

2. **瀑布图分析**：
   在本示例中，所有节点都是简单的 Python 函数，耗时差异不大。但在真实场景中：
   - `query_weather` 如果调用外部 API，可能耗时最长（网络 IO）
   - `format_weather_reply` 如果调用 LLM 生成回复，可能耗时最长（模型推理）
   
   瀑布图的价值就是**一眼看出瓶颈在哪里**。

3. **Token 用量位置**：
   如果 `query_weather` 内部调用了 LLM，Langfuse 会自动捕获这次 LLM 调用作为一个 **Event**，嵌套在 `query_weather` 这个 **Span** 下面。点击展开后可以看到：
   - 输入 Token 数
   - 输出 Token 数
   - 模型名称
   - 调用耗时
   - 完整 prompt 和 completion

4. **标签筛选**：
   ```python
   # 创建不同标签的 handler
   weather_handler = CallbackHandler(tags=["branch:weather"])
   time_handler = CallbackHandler(tags=["branch:time"])
   fallback_handler = CallbackHandler(tags=["branch:fallback"])
   ```
   
   在 Langfuse 界面左侧筛选栏中，选择 "Tags" 条件，输入 `branch:weather` 即可只显示天气分支的 Trace。

</details>

---

### 练习 5：Studio 与 Langfuse 选型决策

假设你在不同的工作场景中需要选择调试/监控工具，请为每个场景选择 Studio 或 Langfuse，并说明理由。

| 场景 | 你的选择 | 理由 |
|------|---------|------|
| 本地开发新 Agent，条件分支逻辑总是不对，需要反复验证 | | |
| 线上用户反馈 "有时候回复很慢"，需要定位哪个环节慢 | | |
| 团队需要 review 过去一周所有对话的质量 | | |
| 给客户演示 Agent 的工作原理，需要直观的可视化 | | |
| 需要统计本月 OpenAI API 调用成本和 Token 用量 | | |
| 某个节点偶发报错，需要查看报错时的完整输入状态 | | |

<details>
<summary>参考答案</summary>

| 场景 | 选择 | 理由 |
|------|------|------|
| 本地开发新 Agent，条件分支逻辑总是不对，需要反复验证 | **Studio** | 实时高亮、改状态重跑、打断点，不需要改代码就能验证不同分支 |
| 线上用户反馈 "有时候回复很慢"，需要定位哪个环节慢 | **Langfuse** | 历史 Trace 持久化存储，瀑布图精确展示每个节点耗时，可对比慢请求和快请求的差异 |
| 团队需要 review 过去一周所有对话的质量 | **Langfuse** | 多用户共享项目，支持按时间段批量筛选，可配合 Score 功能打分 |
| 给客户演示 Agent 的工作原理，需要直观的可视化 | **Studio** | 界面直观、节点高亮、互动性强，客户能看到 "图是怎么一步一步跑起来的" |
| 需要统计本月 OpenAI API 调用成本和 Token 用量 | **Langfuse** | 精确统计每次 LLM 调用的 Token 用量，支持按模型、时间段聚合成本 |
| 某个节点偶发报错，需要查看报错时的完整输入状态 | **两者结合** | Studio 用于复现和调试，Langfuse 用于查看历史报错现场的完整链路 |

**补充说明**：
- Studio 是 "开发时的显微镜"，擅长实时、交互、单次的调试
- Langfuse 是 "上线后的仪表盘"，擅长历史、批量、统计性的分析
- 两者互补：开发阶段用 Studio 调通逻辑，上线后用 Langfuse 监控运行质量

</details>

---

### 练习 6：为图添加 Langfuse Score 评分

在 WeatherBot 运行后，根据回复质量手动给 Trace 打分。

**要求**：
1. 运行图获取 `trace_id`
2. 根据回复的准确性和完整性，给这次交互打 0-1 分的 `response_quality` 分数
3. 编写代码实现上述逻辑
4. 说明 Score 功能在生产环境中的价值

<details>
<summary>参考答案</summary>

```python
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

# 创建带 metadata 的 handler，方便后续查找 trace
langfuse_handler = CallbackHandler(
    session_id="weather-bot-scoring-demo",
    tags=["env:development", "feature:scoring"]
)

# 运行图
result = graph.invoke(
    {"messages": [HumanMessage("北京今天天气怎么样？")]},
    config={"callbacks": [langfuse_handler]}
)

# 获取 trace_id（通过 Langfuse 客户端查询最新 trace）
langfuse = Langfuse()

# 方法 1：如果知道 session_id，可以筛选查找
traces = langfuse.fetch_traces(
    session_id="weather-bot-scoring-demo",
    limit=1
)

if traces.data:
    trace_id = traces.data[0].id
    
    # 根据回复质量打分
    response = result["response"]
    
    # 评分逻辑（实际项目中可以更复杂）
    if "北京" in response and "度" in response:
        score = 1.0
        comment = "回答准确：包含城市名和温度"
    elif "度" in response:
        score = 0.7
        comment = "回答基本正确，但可能缺少城市名"
    else:
        score = 0.3
        comment = "回答不完整，缺少关键信息"
    
    # 上报分数
    langfuse.score(
        trace_id=trace_id,
        name="response_quality",
        value=score,
        comment=comment
    )
    
    print(f"✅ Score 上报成功: {score} ({comment})")
else:
    print("⚠️ 未找到 Trace，可能上报有延迟")
```

**Score 功能在生产环境中的价值**：

1. **质量监控**：通过 Score 时序图观察 Agent 回复质量的变化趋势，及时发现质量下降
2. **A/B 测试**：不同版本的 Agent 分别打标签，对比 Score 分布，量化版本改进效果
3. **问题定位**：筛选低分 Trace，分析共同特征（如特定意图、特定节点总是得低分）
4. **数据集构建**：将高分 Trace 收集为训练数据，用于后续微调或回归测试
5. **自动化评分**：结合 LLM-as-a-Judge 自动打分，减少人工 review 成本

</details>

---

## 思考题

### 思考题：Studio 的 "时间旅行" 调试 vs 传统代码调试

Studio 允许你在任意节点修改 State 后 "Replay from here"，这与传统代码调试中的 "修改变量后继续执行" 有什么本质区别？请从以下角度分析：

1. **状态可见性**：Studio 中你能看到什么？传统调试中你能看到什么？
2. **修改范围**：Studio 中修改 State 会影响什么？传统调试中修改变量会影响什么？
3. **可重复性**：Studio 的 Replay 可以重复执行吗？传统调试的断点执行可以重复吗？
4. **团队协作**：Studio 的调试过程可以分享给同事吗？传统调试呢？

最后，举一个 Studio 时间旅行调试特别适合解决的具体问题场景。

<details>
<summary>参考答案</summary>

#### 1. 状态可见性
- **Studio**：可以看到每个节点执行前后的 **完整 State**（Input State、Output Update、Merged State），以及图的结构和当前执行位置。状态是 "全局可见" 的。
- **传统调试**：可以看到当前作用域的变量，但需要在不同函数间切换才能看到完整状态。状态是 "局部可见" 的，需要手动追踪。

#### 2. 修改范围
- **Studio**：修改 State 后，**后续所有节点的执行都会基于新 State**。因为 LangGraph 的 State 是共享的，一个节点的输出就是下一个节点的输入。修改 State 相当于 "修改了历史"，后续流程会按新历史发展。
- **传统调试**：修改变量通常只影响当前函数的后续执行，除非该变量是全局状态或被指针/引用传递。

#### 3. 可重复性
- **Studio**：Replay 可以 **无限次重复**。每次点击 "Replay from here" 都会从修改后的状态重新开始执行，结果一致（假设节点函数是确定性的）。
- **传统调试**：断点执行也可以重复，但需要重新启动程序、重新设置断点、重新执行到目标位置。Studio 把时间线可视化后，重复执行的成本更低。

#### 4. 团队协作
- **Studio**：可以 **截图或录屏** 分享调试过程，同事能看到完整的图结构、节点高亮、状态变化。但无法直接 "分享断点" 让同事在自己的机器上复现。
- **传统调试**：通常只能分享日志或口头描述问题，难以直观展示执行流程。

#### 特别适合的场景

> **场景**：条件分支逻辑 bug
> 
> 用户反馈 "查询天气时偶尔会返回时间"。通过 Langfuse 发现出问题的那次 Trace 中 `intent` 被识别为 `"time"`。但你检查代码，`parse_intent` 函数中 `"天气" in text` 的判断看起来没问题。
> 
> 在 Studio 中：
> 1. 运行相同的输入，确认正常情况走的是天气分支
> 2. 在 `parse_intent` 节点后把 `intent` 改为 `"time"`，Replay 观察
> 3. 确认当 `intent="time"` 时，图确实会走向 `get_time` 分支
> 4. 回到代码检查：发现用户输入中同时包含 "天气" 和 "几点"（如 "北京今天天气怎么样？现在几点了？"），而 `parse_intent` 中 `"时间" in text` 的判断在 `"天气" in text` 之后，导致被覆盖
> 
> Studio 的价值：快速验证 "如果某个中间值不同，后续会怎样"，帮助定位是路由逻辑的问题还是上游节点输出的问题。

</details>
