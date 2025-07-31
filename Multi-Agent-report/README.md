# 🤖 Multi-Agent 流式输出系统完整指南

一个基于 LangGraph 的多智能体系统，实现了完整的流式输出和智能协作功能。

## 📋 目录

- [核心特性](#核心特性)
- [多 Agent 流式输出实现](#多-agent-流式输出实现)
- [多 Agent 系统构建优化](#多-agent-系统构建优化)
- [系统架构](#系统架构)
- [安装和使用](#安装和使用)
- [最佳实践](#最佳实践)

## 🎯 核心特性

- 🤖 **多智能体协作**：监督器 + 专业化 Agent 的分层架构
- 🖨️ **真正的打字机效果**：Token 级别的实时流式输出
- 🔄 **智能路由**：根据用户输入自动选择最合适的 Agent
- 🛠️ **工具集成**：计算器、搜索引擎等多种工具支持
- 📊 **实时进度反馈**：完整的执行状态和进度显示
- 🎯 **任务完成检测**：自动判断任务完成状态

---

## 🖨️ 多 Agent 流式输出实现

### 核心挑战

多 Agent 系统的流式输出面临以下主要挑战：

1. **Agent 输出结构复杂**：包含工具调用、工具结果、最终回复等多个阶段
2. **配置冲突**：LangGraph 的 config 与 Agent 的流式配置不兼容
3. **消息类型多样**：AIMessageChunk、ToolMessage、HumanMessage 等需要分别处理
4. **状态同步**：需要将流式输出与整体工作流状态同步

### 🔧 解决方案

#### 1. Agent 输出结构分析

Agent 的流式输出包含三个关键阶段：

```python
async for chunk in agent.astream(input, stream_mode="messages"):
    if isinstance(chunk, tuple) and len(chunk) == 2:
        message, metadata = chunk
        
        # 阶段1: 工具调用准备
        if type(message).__name__ == "AIMessageChunk" and hasattr(message, 'tool_calls'):
            # 处理工具调用信息
            
        # 阶段2: 工具执行结果  
        elif type(message).__name__ == "ToolMessage":
            # 处理工具返回结果
            
        # 阶段3: 最终回复流式输出
        elif type(message).__name__ == "AIMessageChunk" and message.content:
            # 处理 token 级流式回复
```

#### 2. 配置隔离策略

**关键发现**：LangGraph 的 config 对象不能直接传递给 Agent 的 astream()

```python
# ❌ 错误：会导致流式输出失败
async for chunk in agent.astream(input, config=langgraph_config, stream_mode="messages"):

# ✅ 正确：移除 config 参数
async for chunk in agent.astream(input, stream_mode="messages"):
```

#### 3. 完善的流式处理器

```python
async def process_agent_stream(agent, input_dict, writer, agent_type):
    """完善的 Agent 流式处理器"""
    
    full_response = ""
    chunk_count = 0
    tool_calls_count = 0
    content_chunks = 0
    current_tool = None
    
    try:
        async for chunk in agent.astream(input_dict, stream_mode="messages"):
            chunk_count += 1
            
            if isinstance(chunk, tuple) and len(chunk) == 2:
                message, metadata = chunk
                msg_type = type(message).__name__
                
                # 处理不同类型的消息
                if msg_type == "AIMessageChunk":
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        # 工具调用阶段
                        tool_calls_count += 1
                        current_tool = message.tool_calls[0].get('name', 'unknown_tool')
                        
                        writer({
                            "type": "tool_call",
                            "agent": agent_type,
                            "tool": current_tool,
                            "status": f"正在调用工具: {current_tool}",
                            "progress": 40
                        })
                    
                    elif hasattr(message, 'content') and message.content:
                        # AI 最终回复的流式输出
                        content = str(message.content)
                        full_response += content
                        content_chunks += 1
                        
                        writer({
                            "type": "streaming_content",
                            "agent": agent_type,
                            "content": content,
                            "status": f"Agent生成回复中...",
                            "progress": 70
                        })
                
                elif msg_type == "ToolMessage":
                    # 工具执行结果
                    if hasattr(message, 'content') and message.content:
                        tool_result = str(message.content)
                        full_response += tool_result
                        
                        writer({
                            "type": "tool_result",
                            "agent": agent_type,
                            "tool": current_tool,
                            "result": tool_result,
                            "status": f"工具执行完成: {current_tool}",
                            "progress": 60
                        })
        
        return {
            "success": True,
            "content": full_response,
            "stats": {
                "total_chunks": chunk_count,
                "tool_calls": tool_calls_count,
                "content_chunks": content_chunks
            }
        }
        
    except Exception as e:
        logger.error(f"Agent流式执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": ""
        }
```

#### 4. 打字机效果实现

```python
# 在流式处理中实现真正的打字机效果
elif mode == "messages":
    token, metadata = data
    if hasattr(token, 'content') and token.content:
        node_name = metadata.get('langgraph_node', '') if metadata else ''
        if node_name in ['agent_execution', 'result_integration', 'supervisor']:
            # 直接输出token内容，不换行，实现打字机效果
            print(token.content, end='', flush=True)
```

### 📊 流式输出统计示例

成功的流式统计示例：
- **计算任务**：`总chunk=27, 工具调用=1, 内容chunk=15, 响应长度=34`
- **搜索任务**：`总chunk=297, 工具调用=1, 内容chunk=268, 响应长度=1883`
- **分析任务**：`总chunk=81, 工具调用=1, 内容chunk=57, 响应长度=157`

---

## 🏗️ 多 Agent 系统构建优化

### 设计原则

#### 1. 分层架构设计

```python
# 监督器层：负责智能路由和任务协调
class SupervisorAgent:
    def analyze_input(self, user_input):
        # 分析用户意图
        # 选择合适的专业 Agent
        # 返回路由决策
        
# 专业 Agent 层：负责具体任务执行
class SpecializedAgent:
    def __init__(self, tools, expertise):
        self.tools = tools
        self.expertise = expertise
    
    def execute_task(self, task):
        # 使用专业工具执行任务
        # 返回专业结果
```

#### 2. 工具集成策略

```python
# 工具定义标准化
@tool
def calculator(expression: str) -> str:
    """执行数学计算"""
    try:
        result = eval(expression)
        return f"🔢 计算结果：{expression} = {result}"
    except Exception as e:
        return f"❌ 计算错误：{e}"

@tool  
def tavily_search(query: str) -> str:
    """搜索最新信息"""
    search = TavilySearchResults(max_results=3)
    results = search.invoke(query)
    # 格式化搜索结果
    return formatted_results
```

#### 3. 状态管理优化

```python
class MultiAgentState(TypedDict):
    """多智能体状态定义"""
    messages: Annotated[list, add_messages]
    user_input: str
    current_agent: str
    execution_path: list
    agent_results: dict
    final_result: str
    iteration_count: int
    max_iterations: int
    context: dict
    error_log: list
    supervisor_reasoning: str
    next_action: str
    task_completed: bool
```

### 性能优化策略

#### 1. 并发处理

```python
# 对于独立的任务，可以并发执行多个 Agent
async def parallel_agent_execution(tasks):
    results = await asyncio.gather(*[
        agent.execute(task) for agent, task in tasks
    ])
    return results
```

#### 2. 缓存机制

```python
# 缓存常用的计算结果和搜索结果
class AgentCache:
    def __init__(self):
        self.cache = {}
    
    def get_cached_result(self, key):
        return self.cache.get(key)
    
    def cache_result(self, key, result):
        self.cache[key] = result
```

#### 3. 错误处理和重试

```python
class ErrorHandler:
    @staticmethod
    async def handle_agent_error(agent, input_dict, error, max_retries=3):
        """Agent 错误处理和重试机制"""
        for attempt in range(max_retries):
            try:
                result = await agent.ainvoke(input_dict)
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"Agent 执行失败: {e}"
                await asyncio.sleep(2 ** attempt)  # 指数退避
```

### 可扩展性设计

#### 1. 插件化 Agent

```python
class AgentRegistry:
    """Agent 注册表，支持动态添加新的 Agent"""
    
    def __init__(self):
        self.agents = {}
    
    def register_agent(self, name, agent_class, tools):
        self.agents[name] = {
            "class": agent_class,
            "tools": tools,
            "capabilities": agent_class.get_capabilities()
        }
    
    def get_agent(self, name):
        return self.agents.get(name)
```

#### 2. 动态工具加载

```python
class ToolManager:
    """工具管理器，支持动态加载和配置工具"""
    
    def __init__(self):
        self.tools = {}
    
    def load_tool(self, tool_name, tool_config):
        # 动态加载工具
        tool = self.create_tool(tool_name, tool_config)
        self.tools[tool_name] = tool
    
    def get_tools_for_agent(self, agent_type):
        # 根据 Agent 类型返回相应的工具集
        return [tool for tool in self.tools.values() 
                if agent_type in tool.supported_agents]
```

### 监控和调试

#### 1. 执行追踪

```python
class ExecutionTracker:
    """执行追踪器，记录 Agent 执行过程"""
    
    def __init__(self):
        self.execution_log = []
    
    def log_agent_start(self, agent_name, input_data):
        self.execution_log.append({
            "timestamp": time.time(),
            "event": "agent_start",
            "agent": agent_name,
            "input": input_data
        })
    
    def log_agent_complete(self, agent_name, result, duration):
        self.execution_log.append({
            "timestamp": time.time(),
            "event": "agent_complete", 
            "agent": agent_name,
            "result": result,
            "duration": duration
        })
```

#### 2. 性能监控

```python
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_execution_time(self, agent_name, duration):
        if agent_name not in self.metrics:
            self.metrics[agent_name] = []
        self.metrics[agent_name].append(duration)
    
    def get_average_execution_time(self, agent_name):
        times = self.metrics.get(agent_name, [])
        return sum(times) / len(times) if times else 0
```

---

## 🏛️ 系统架构

### 核心组件

```python
# 1. 多智能体状态管理
class MultiAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_input: str
    current_agent: str
    execution_path: list
    agent_results: dict
    final_result: str
    iteration_count: int
    max_iterations: int
    context: dict
    error_log: list
    supervisor_reasoning: str
    next_action: str
    task_completed: bool

# 2. Agent 创建工厂
def create_agents():
    """创建所有专业化 Agent"""
    return {
        "analysis": create_react_agent(
            llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
            tools=[calculator],
            state_modifier="You are an analysis expert..."
        ),
        "search": create_react_agent(
            llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
            tools=[tavily_search],
            state_modifier="You are a search expert..."
        )
    }

# 3. 工作流图构建
def create_multi_agent_graph():
    """创建多智能体工作流图"""
    workflow = StateGraph(MultiAgentState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("agent_execution", agent_execution_node)
    workflow.add_node("result_integration", result_integration_node)

    # 添加边和条件路由
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "analysis": "agent_execution",
            "search": "agent_execution",
            "finish": "result_integration"
        }
    )
    workflow.add_edge("agent_execution", "supervisor")
    workflow.add_edge("result_integration", END)

    # 编译图
    return workflow.compile(checkpointer=MemorySaver())
```

### Agent 节点实现

```python
async def supervisor_node(state: MultiAgentState) -> MultiAgentState:
    """监督器节点：智能路由和任务协调"""

    # 构建监督器提示
    system_message = """你是一个智能任务调度器。分析用户输入，决定下一步行动：

    可选行动：
    - analysis: 数据分析、计算、逻辑推理
    - search: 信息搜索、最新资讯查询
    - finish: 任务完成，准备输出结果

    返回格式：只返回行动名称，如 'analysis' 或 'search' 或 'finish'
    """

    # LLM 决策
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [SystemMessage(content=system_message)] + state["messages"]
    response = await llm.ainvoke(messages)

    # 解析决策
    decision = response.content.strip().lower()

    return {
        **state,
        "next_action": decision,
        "supervisor_reasoning": f"检测到{decision}需求"
    }

async def agent_execution_node(state: MultiAgentState) -> MultiAgentState:
    """Agent 执行节点：执行具体任务"""

    next_action = state.get("next_action")
    agents = create_agents()
    agent = agents.get(next_action)

    if not agent:
        return {**state, "error_log": [f"未找到Agent: {next_action}"]}

    # 准备 Agent 输入
    agent_input = {"messages": [HumanMessage(content=state["user_input"])]}

    # 执行 Agent（带流式输出）
    full_response = ""
    try:
        async for chunk in agent.astream(agent_input, stream_mode="messages"):
            if isinstance(chunk, tuple) and len(chunk) == 2:
                message, metadata = chunk
                msg_type = type(message).__name__

                if msg_type == "AIMessageChunk" and hasattr(message, 'content') and message.content:
                    full_response += str(message.content)
                elif msg_type == "ToolMessage" and hasattr(message, 'content') and message.content:
                    full_response += str(message.content)

    except Exception as e:
        logger.error(f"Agent执行失败: {e}")
        full_response = "Agent执行完成"

    # 更新状态
    result_text = full_response.strip() if full_response.strip() else "Agent执行完成"

    return {
        **state,
        "current_agent": next_action,
        "execution_path": state["execution_path"] + [next_action],
        "agent_results": {**state["agent_results"], next_action: result_text},
        "iteration_count": state["iteration_count"] + 1
    }

async def result_integration_node(state: MultiAgentState) -> MultiAgentState:
    """结果整合节点：整合所有 Agent 结果"""

    # 构建整合提示
    agent_results = state.get("agent_results", {})
    results_summary = "\n".join([
        f"- {agent}: {result}"
        for agent, result in agent_results.items()
    ])

    system_message = f"""基于以下Agent执行结果，生成最终整合答案：

{results_summary}

要求：
1. 整合所有相关信息
2. 提供清晰、准确的最终答案
3. 保持专业和友好的语调
"""

    # LLM 整合
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=state["user_input"])
    ]

    response = await llm.ainvoke(messages)

    return {
        **state,
        "final_result": response.content,
        "task_completed": True
    }
```

---

## 🚀 安装和使用

### 环境要求

- Python 3.8+
- LangChain >= 0.1.0
- LangGraph >= 0.1.0
- OpenAI API Key
- Tavily API Key

### 安装依赖

```bash
pip install langchain langgraph openai tavily-python
```

### 配置

```python
import os

# 设置 API Keys
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"

# 或使用配置文件
from config import OPENAI_API_KEY, TAVILY_API_KEY
```

### 基本使用

```python
import asyncio
from graph import create_multi_agent_graph

async def main():
    # 创建应用
    app = create_multi_agent_graph()

    # 准备输入
    initial_state = {
        "messages": [],
        "user_input": "搜索Python最新特性并分析其优势",
        "current_agent": "",
        "execution_path": [],
        "agent_results": {},
        "final_result": "",
        "iteration_count": 0,
        "max_iterations": 3,
        "context": {},
        "error_log": [],
        "supervisor_reasoning": "",
        "next_action": "",
        "task_completed": False
    }

    # 配置
    config = {"configurable": {"thread_id": "example_session"}}

    # 执行
    result = await app.ainvoke(initial_state, config=config)

    print(f"✅ 最终结果: {result['final_result']}")
    print(f"📊 执行路径: {' → '.join(result['execution_path'])}")
    print(f"🔄 迭代次数: {result['iteration_count']}")

# 运行
asyncio.run(main())
```

### 流式输出使用

```python
import asyncio
from graph import create_multi_agent_graph

async def stream_example():
    app = create_multi_agent_graph()

    initial_state = {
        "messages": [],
        "user_input": "计算 25 * 4 的结果",
        "current_agent": "",
        "execution_path": [],
        "agent_results": {},
        "final_result": "",
        "iteration_count": 0,
        "max_iterations": 3,
        "context": {},
        "error_log": [],
        "supervisor_reasoning": "",
        "next_action": "",
        "task_completed": False
    }

    config = {"configurable": {"thread_id": "stream_session"}}

    print("🖨️ 流式输出开始:")

    async for chunk in app.astream(initial_state, config=config, stream_mode=["messages"]):
        if isinstance(chunk, tuple) and len(chunk) == 2:
            mode, data = chunk

            if mode == "messages":
                token, metadata = data
                if hasattr(token, 'content') and token.content:
                    node_name = metadata.get('langgraph_node', '') if metadata else ''
                    if node_name in ['agent_execution', 'result_integration', 'supervisor']:
                        # 打字机效果：直接输出，不换行
                        print(token.content, end='', flush=True)

    print("\n\n✅ 流式输出完成")

# 运行
asyncio.run(stream_example())
```

---

## 🎯 最佳实践

### 1. 设计原则

- **分离关注点**：流式处理与业务逻辑分离
- **错误容错**：始终提供回退机制
- **性能优化**：合理缓冲和批量处理
- **用户体验**：提供清晰的进度反馈

### 2. 实施步骤

1. **分析 Agent 输出结构** → 理解所有可能的消息类型
2. **设计流式处理器** → 针对不同消息类型设计处理逻辑
3. **实现配置隔离** → 避免 LangGraph config 冲突
4. **添加错误处理** → 实现优雅的回退机制
5. **优化性能** → 批量处理和缓冲策略
6. **全面测试** → 覆盖正常和异常情况

### 3. 关键要点

- ✅ **移除 config 参数**：Agent.astream() 不要传递 LangGraph 的 config
- ✅ **分类处理消息**：AIMessageChunk、ToolMessage 需要不同处理逻辑
- ✅ **标准化消息格式**：统一的流式消息结构
- ✅ **性能优化**：合理的缓冲和批量发送策略
- ✅ **打字机效果**：使用 `print(content, end='', flush=True)` 实现

### 4. 常见问题解决

#### 问题1：流式输出为空
```python
# 原因：config 参数冲突
# 解决：移除 config 参数
async for chunk in agent.astream(input_dict, stream_mode="messages"):  # ✅ 正确
```

#### 问题2：打字机效果不连续
```python
# 原因：额外的换行
# 解决：只在非 messages 模式时换行
if not (isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "messages"):
    print()  # 只在必要时换行
```

#### 问题3：节点名称过滤错误
```python
# 原因：节点名称不匹配
# 解决：检查实际的节点名称
node_name = metadata.get('langgraph_node', '') if metadata else ''
if node_name in ['agent_execution', 'result_integration', 'supervisor']:  # ✅ 正确
```

---

## 📁 项目结构

```
Multi-Agent-report/
├── README.md              # 项目文档
├── README_COMPLETE.md     # 完整技术指南
├── graph.py              # 多智能体图定义
├── tools.py              # 工具定义
├── config.py             # 配置文件
└── test.py              # 测试脚本（含打字机效果）
```

---

## 🎉 总结

这套多 Agent 流式输出系统实现了：

1. **完整的流式体验**：从工具调用到最终回复的全程流式输出
2. **真正的打字机效果**：Token 级别的实时显示
3. **智能协作**：多个专业化 Agent 的无缝协作
4. **高性能架构**：异步处理、错误容错、状态管理
5. **易于扩展**：插件化设计，支持动态添加新的 Agent 和工具

通过这套方案，您可以构建出既智能又具有出色用户体验的多 Agent 系统！🚀
