# LangGraph Multi-Agent Handoff 设计指南

## 概述

本项目展示了如何使用LangGraph实现多智能体(Multi-Agent)之间的交互和handoff机制。基于2024-2025年最新的LangGraph功能，包含了多种agent交互模式的实现。

## 核心概念

### 什么是Agent Handoff?

Agent handoff是指一个智能体将控制权转移给另一个智能体的机制。在LangGraph中，handoff通过以下方式实现：

1. **LLM调用专用的handoff工具**
2. **返回Command对象指定目标agent**
3. **传递状态和上下文信息**

### 关键组件

- **Command**: 特殊类型，指定下一个要去的节点和要传递的数据
- **Handoff Tools**: 专门用于agent间交互的工具函数
- **Shared State**: 所有agent共享的状态通道

## Multi-Agent交互网络设计方法汇总

### 1. 监督者模式 (Supervisor Pattern)

**特点**: 中央监督agent协调所有worker agents

**优势**:
- 清晰的控制流
- 易于管理和调试
- 适合任务明确划分的场景

**实现要点**:
```python
# 监督者决定将任务分配给哪个worker
supervisor_agent = create_react_agent(
    model,
    tools=[assign_to_research_agent, assign_to_math_agent],
    prompt="你是一个监督者，负责将任务分配给合适的专业agent"
)
```

### 2. 对等交互模式 (Peer-to-Peer)

**特点**: agents之间可以直接相互调用

**优势**:
- 更灵活的交互
- 减少中心化瓶颈
- 适合复杂协作场景

**实现要点**:
```python
# 每个agent都可以调用其他agents
agent_tools = [
    transfer_to_agent_b,
    transfer_to_agent_c,
    # ... 其他工具
]
```

### 3. 分层模式 (Hierarchical)

**特点**: 多层级的agent结构

**优势**:
- 支持复杂的组织结构
- 清晰的权责划分
- 易于扩展

### 4. Swarm模式 (2025年新增)

**特点**: 轻量级的swarm-style多agent系统

**优势**:
- 专门的agent协作能力
- 内置的context传递
- 可定制的handoff工具

## 核心实现模式

### 1. Command原语 (2024年新增)

```python
from langgraph.types import Command

@tool
def transfer_to_bob():
    """Transfer to bob."""
    return Command(
        goto="bob",  # 目标agent节点
        update={"my_state_key": "my_state_value"},  # 传递的数据
        graph=Command.PARENT,  # 在父图中导航
    )
```

### 2. 共享状态通信

```python
from langgraph.graph import MessagesState

class MultiAgentState(MessagesState):
    last_active_agent: str
    shared_context: dict
    # 其他共享状态字段
```

### 3. 动态handoff工具创建

```python
def create_handoff_tool(*, agent_name: str, description: str = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"向{agent_name}求助"
    
    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        return Command(
            goto=agent_name,
            update={"messages": [...]},
            graph=Command.PARENT,
        )
    
    return handoff_tool
```

## 设计最佳实践

### 1. 状态管理

- 使用共享的MessagesState作为基础
- 为每个agent定义清晰的输入输出格式
- 合理设计状态字段避免冲突

### 2. Context传递

- 使用Send()原语直接向worker agents发送数据
- 在handoff时传递必要的上下文信息
- 避免传递过多无关信息

### 3. 错误处理

- 为每个handoff点添加错误处理逻辑
- 设计fallback机制
- 记录handoff的执行轨迹

### 4. 性能优化

- 合理设计agent的职责划分
- 避免过度的handoff循环
- 使用异步处理提升性能

## 项目结构

```
Multi-Agent-Handoff/
├── README.md                 # 本文档
├── graph.py                  # 主要的multi-agent图实现
├── agents.py                 # agent定义和配置
├── tools.py                  # handoff工具和其他工具
├── state.py                  # 状态定义
├── test.py                   # 测试脚本
└── examples/                 # 示例代码
    ├── supervisor_pattern.py
    ├── peer_to_peer.py
    └── hierarchical.py
```

## 使用场景

1. **客服系统**: 不同专业的客服agent处理不同类型的问题
2. **研究助手**: 研究agent、分析agent、写作agent协作完成研究任务
3. **代码助手**: 代码生成agent、测试agent、优化agent协作开发
4. **内容创作**: 创意agent、写作agent、编辑agent协作创作

## 技术要求

- Python 3.11+
- LangGraph 0.2+
- LangChain
- 支持的LLM模型 (OpenAI, Anthropic, etc.)

## 下一步

查看 `test.py` 文件了解如何运行和测试这些实现。