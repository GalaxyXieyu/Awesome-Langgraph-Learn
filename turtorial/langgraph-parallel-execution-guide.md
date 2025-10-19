# LangGraph 并行任务处理技巧完全指南

## 📋 目录

- [1. 核心概念](#1-核心概念)
- [2. 执行模式对比](#2-执行模式对比)
- [3. Reducer 机制详解](#3-reducer-机制详解)
- [4. 实战案例](#4-实战案例)
- [5. 最佳实践](#5-最佳实践)
- [6. 进阶技巧](#6-进阶技巧)
- [7. 常见问题与解决方案](#7-常见问题与解决方案)

---

## 1. 核心概念

### 1.1 什么是并行执行?

在 LangGraph 中,**并行执行**指让多个节点在**同一时间步(step)**内同时运行,而非顺序执行。这种模式通过 **Fan-out/Fan-in** 模式实现:

- **Fan-out (扇出)**: 一个节点的输出分发到多个并行节点
- **Fan-in (扇入)**: 多个并行节点的输出汇聚到一个节点

```
     节点A (Fan-out)
      /    \
     /      \
  节点B    节点C  (并行执行)
     \      /
      \    /
     节点D (Fan-in)
```

### 1.2 为什么需要并行执行?

**性能优势:**
- 多个独立任务同时执行,显著减少总执行时间
- 充分利用系统资源(CPU、I/O、网络)
- 对于 I/O 密集型任务(API 调用、数据库查询)尤其有效

**业务场景:**
- 同时从多个数据源检索信息
- 并行调用多个 AI 模型
- 多智能体协作系统
- 批量处理任务

### 1.3 关键术语

| 术语 | 说明 |
|------|------|
| **Step (步骤)** | 图执行的一个时间单位,并行节点在同一 step 内执行 |
| **Reducer** | 用于合并多个并行更新的函数 |
| **State** | 图的共享状态字典 |
| **Annotated** | Python 类型提示,用于指定 reducer |

---

## 2. 执行模式对比

### 2.1 线性执行模式 (Sequential)

**代码示例:**

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    state: str

class ReturnNodeValue:
    def __init__(self, node_secret: str):
        self._value = node_secret
    
    def __call__(self, state: State):
        print(f"Adding {self._value} to {state['state']}")
        return {"state": [self._value]}

# 构建线性图
builder = StateGraph(State)
builder.add_node("a", ReturnNodeValue("I'm A"))
builder.add_node("b", ReturnNodeValue("I'm B"))
builder.add_node("c", ReturnNodeValue("I'm C"))

# 线性连接: START → a → b → c → END
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("b", "c")
builder.add_edge("c", END)

graph = builder.compile()
```

**执行结果:**
```
Adding I'm A to []
Adding I'm B to ["I'm A"]
Adding I'm C to ["I'm B"]

{'state': ["I'm C"]}
```

**时间线:**
```
时间 →  [Step 1: A] → [Step 2: B] → [Step 3: C]
总耗时: T(A) + T(B) + T(C)
```

### 2.2 并行执行模式 (Parallel)

**修复版本 (使用 Reducer):**

```python
import operator
from typing import Annotated

class State(TypedDict):
    # ✅ 使用 operator.add 作为 reducer
    state: Annotated[list, operator.add]

builder = StateGraph(State)
builder.add_node("a", ReturnNodeValue("I'm A"))
builder.add_node("b", ReturnNodeValue("I'm B"))
builder.add_node("c", ReturnNodeValue("I'm C"))
builder.add_node("d", ReturnNodeValue("I'm D"))

builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "d")
builder.add_edge("c", "d")
builder.add_edge("d", END)

graph = builder.compile()
```

**执行结果:**
```
Adding I'm A to []
Adding I'm B to ["I'm A"]
Adding I'm C to ["I'm A"]
Adding I'm D to ["I'm A", "I'm B", "I'm C"]

{'state': ["I'm A", "I'm B", "I'm C", "I'm D"]}
```

**常见错误:**
```
InvalidUpdateError: At key 'state': Can receive only one value per step.
Use an Annotated key to handle multiple values.
```

**原因:** 多个节点在同一 step 内更新同一键,但没有指定 reducer。

### 2.3 模式对比总结

| 维度 | 线性执行 | 并行执行 |
|------|---------|---------|
| **执行顺序** | 严格顺序 | 同一 step 内无序 |
| **总耗时** | ∑ T(所有节点) | ∑ T(关键路径) |
| **状态更新** | 单一更新 | 需要 Reducer 合并 |
| **适用场景** | 有依赖关系 | 独立任务 |
| **性能提升** | 无 | 可显著提升 |

---

## 3. Reducer 机制详解

### 3.1 什么是 Reducer?

**Reducer** 是一个函数,定义如何合并多个并行更新。

```python
def reducer(left: T, right: T) -> T:
    """
    Args:
        left: 当前状态的值
        right: 新节点返回的值
    Returns:
        合并后的值
    """
    pass
```

### 3.2 使用 Annotated 指定 Reducer

```python
from typing import Annotated
import operator

# 语法: Annotated[类型, reducer函数]
field: Annotated[list, operator.add]
```

### 3.3 内置 Reducer: operator.add

```python
import operator

# 对列表: 执行拼接
operator.add([1, 2], [3, 4])  # [1, 2, 3, 4]

# 对数字: 执行加法
operator.add(10, 20)  # 30
```

### 3.4 自定义 Reducer 示例

#### 排序 Reducer

```python
def sorting_reducer(left, right):
    """合并并排序"""
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return sorted(left + right)

class State(TypedDict):
    state: Annotated[list, sorting_reducer]
```

#### 去重 Reducer

```python
def unique_reducer(left, right):
    """合并并去重"""
    combined = (left if isinstance(left, list) else [left]) + \
               (right if isinstance(right, list) else [right])
    return list(dict.fromkeys(combined))
```

#### 保留最近 N 个

```python
def keep_last_n(n=5):
    def reducer(left, right):
        combined = (left if isinstance(left, list) else [left]) + \
                   (right if isinstance(right, list) else [right])
        return combined[-n:]
    return reducer

class State(TypedDict):
    recent: Annotated[list, keep_last_n(10)]
```

### 3.5 Reducer 选择指南

| 需求 | Reducer | 使用场景 |
|------|---------|---------|
| 收集所有结果 | `operator.add` | 搜索结果聚合 |
| 需要排序 | `sorting_reducer` | 按优先级排序 |
| 去重 | `unique_reducer` | 实体提取 |
| 只保留最新 | `lambda l, r: r` | 状态更新 |
| 保留最近 N 个 | `keep_last_n(N)` | 消息历史 |

---

## 4. 实战案例

### 4.1 多源并行检索问答系统

**场景:** 同时从 Wikipedia 和 Web 搜索获取信息生成答案。

#### State 定义

```python
import operator
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    question: str
    answer: str
    context: Annotated[list, operator.add]  # 支持并行追加
```

#### 节点实现

```python
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WikipediaLoader
from langchain_openai import ChatOpenAI

def search_web(state):
    """Web 搜索"""
    tavily_search = TavilySearchResults(max_results=3)
    docs = tavily_search.invoke(state['question'])
    formatted = "\n\n---\n\n".join([
        f'<Document href="{d["url"]}">\n{d["content"]}\n</Document>'
        for d in docs
    ])
    return {"context": [formatted]}

def search_wikipedia(state):
    """Wikipedia 搜索"""
    docs = WikipediaLoader(query=state['question'], load_max_docs=2).load()
    formatted = "\n\n---\n\n".join([
        f'<Document source="{d.metadata["source"]}">\n{d.page_content}\n</Document>'
        for d in docs
    ])
    return {"context": [formatted]}

def generate_answer(state):
    """生成答案"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"Answer: {state['question']}\nContext: {state['context']}"
    answer = llm.invoke([{"role": "user", "content": prompt}])
    return {"answer": answer}
```

#### 构建图

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node("search_web", search_web)
builder.add_node("search_wikipedia", search_wikipedia)
builder.add_node("generate_answer", generate_answer)

# 并行流程
builder.add_edge(START, "search_web")
builder.add_edge(START, "search_wikipedia")
builder.add_edge("search_web", "generate_answer")
builder.add_edge("search_wikipedia", "generate_answer")
builder.add_edge("generate_answer", END)

graph = builder.compile()
```

**流程可视化:**
```
        START
       /     \
  search_web  search_wikipedia  (并行)
       \     /
   generate_answer  (汇聚)
         |
        END
```

**性能对比:**
- 串行: T(web) + T(wiki) + T(gen) ≈ 5s
- 并行: max(T(web), T(wiki)) + T(gen) ≈ 3s
- **提升约 40%**

### 4.2 不同长度的并行路径

```python
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "b2")  # 更长路径
builder.add_edge(["b2", "c"], "d")  # 等待所有路径
```

**关键点:**
- b、c、b2 都在同一 step 内执行
- 节点 d 等待所有并行路径完成
- 这是 LangGraph 的自动同步机制

---

## 5. 最佳实践

### 5.1 何时使用并行执行?

#### ✅ 适用场景

- 多数据源检索 (2-5x 提速)
- 多模型推理
- 批量独立任务
- 多智能体协作
- 多维度分析

#### ❌ 不适用场景

- 任务有依赖关系
- 共享资源冲突
- API 限流
- 内存受限
- 严格顺序要求

### 5.2 State 设计最佳实践

```python
class State(TypedDict):
    # 输入字段 (只读)
    question: str
    user_id: str
    
    # 并行收集的数据 (使用 reducer)
    search_results: Annotated[list, operator.add]
    
    # 最终输出 (单一节点更新)
    answer: str
```

### 5.3 错误处理

```python
def safe_wrapper(func):
    def wrapper(state):
        try:
            return func(state)
        except Exception as e:
            return {"context": [f"<Error>{str(e)}</Error>"]}
    return wrapper

builder.add_node("search", safe_wrapper(search_web))
```

---

## 6. 进阶技巧

### 6.1 稳定排序: 临时字段模式

```python
class State(TypedDict):
    temp_results: dict  # 临时存储
    final_results: list  # 排序后

def collect_and_sort(state):
    results = state['temp_results']
    ordered = [results['s1'], results['s2'], results['s3']]
    return {"final_results": ordered, "temp_results": {}}
```

### 6.2 控制并发数

```python
import asyncio

semaphore = asyncio.Semaphore(3)  # 最多3个并发

async def limited_search(state):
    async with semaphore:
        return await search(state)
```

### 6.3 超时控制

```python
async def search_with_timeout(state, timeout=5.0):
    try:
        return await asyncio.wait_for(search(state), timeout)
    except asyncio.TimeoutError:
        return {"context": ["<Timeout>"]}
```

### 6.4 调试技巧

```python
import time
from functools import wraps

def trace_execution(func):
    @wraps(func)
    def wrapper(state):
        start = time.time()
        print(f"🚀 开始: {func.__name__}")
        result = func(state)
        print(f"✅ 完成: {func.__name__} ({time.time()-start:.2f}s)")
        return result
    return wrapper
```

---

## 7. 常见问题与解决方案

### 7.1 InvalidUpdateError 错误

**问题:**
```
InvalidUpdateError: At key 'state': Can receive only one value per step.
```

**原因:** 多个并行节点更新同一键,但未指定 reducer。

**解决:**
```python
from typing import Annotated
import operator

class State(TypedDict):
    state: Annotated[list, operator.add]  # 添加 reducer
```

### 7.2 更新顺序不可控

**问题:** 并行节点的更新顺序无法预测。

**解决方案 1: 自定义排序 reducer**
```python
def sorting_reducer(left, right):
    combined = (left if isinstance(left, list) else [left]) + \
               (right if isinstance(right, list) else [right])
    return sorted(combined)
```

**解决方案 2: 临时字段 + 汇聚节点**
```python
class State(TypedDict):
    temp: dict
    final: list

def collect(state):
    return {"final": [state['temp']['a'], state['temp']['b']]}
```

### 7.3 并行节点没有真正并发

**问题:** 节点仍然串行执行。

**原因:** 使用了同步函数,Python GIL 限制。

**解决:** 使用异步函数
```python
async def search_web(state):
    # 异步实现
    pass
```

### 7.4 性能提升不明显

**可能原因:**
1. 任务是 CPU 密集型(受 GIL 限制)
2. 并发数太少
3. 网络/API 本身很快,并行收益小

**优化建议:**
- CPU 密集型: 使用多进程
- I/O 密集型: 增加并发数
- 测量实际耗时,确认瓶颈

---

## 8. 核心知识点总结

### 8.1 LangGraph 特有概念

1. **并行执行模式**: Fan-out/Fan-in
2. **Reducer 机制**: 处理并行更新冲突
3. **执行步骤 (Step)**: 并行节点在同一 step 执行
4. **自动同步**: 等待所有并行路径完成

### 8.2 Python 特有知识点

1. **TypedDict**: 定义字典类型结构
2. **Annotated**: 为类型添加元数据
3. **operator.add**: 内置运算符函数
4. **可调用类**: 实现 `__call__` 方法

### 8.3 性能优化原则

```
串行耗时: T1 + T2 + T3 + ... + Tn
并行耗时: max(T1, T2, ..., Tk) + T(k+1) + ...
```

理想提升: **N 倍** (N 个完全独立的任务)

实际提升: **2-5 倍** (考虑开销和同步)

---

## 9. 参考资源

- [LangGraph 并行执行官方文档](https://langchain-ai.github.io/langgraph/how-tos/branching/)
- [LangGraph State 和 Reducer 详解](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [Python typing 模块文档](https://docs.python.org/3/library/typing.html)
- [Python operator 模块文档](https://docs.python.org/3/library/operator.html)

---

## 10. 快速参考

### 常用 Reducer

```python
import operator

# 列表拼接
Annotated[list, operator.add]

# 数值求和
Annotated[int, operator.add]

# 只保留最新
Annotated[str, lambda l, r: r]

# 自定义排序
Annotated[list, lambda l, r: sorted((l if isinstance(l, list) else [l]) + (r if isinstance(r, list) else [r]))]
```

### 典型图结构

```python
# 简单并行
builder.add_edge(START, "task1")
builder.add_edge(START, "task2")
builder.add_edge(["task1", "task2"], "merge")

# 不同长度路径
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "b2")
builder.add_edge(["b2", "c"], "d")
```

---

**总结:** 并行执行是 LangGraph 的核心功能,通过合理使用 Reducer 和图结构设计,可以构建高效的多任务、多智能体系统。掌握这个概念是进入高级 LangGraph 开发的关键!