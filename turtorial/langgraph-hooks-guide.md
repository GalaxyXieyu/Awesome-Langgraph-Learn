# LangGraph Pre/Post Model Hooks 使用指南

## 📋 概述

Pre/Post Model Hooks 是 LangGraph v2 版本引入的高级特性，允许在 LLM 调用前后插入自定义处理逻辑。本指南详细说明如何在 AutoAgents 项目中使用这些特性来优化代码结构和提升可维护性。

---

## 🎯 核心概念

### 执行流程

```
用户输入 
  ↓
pre_model_hook (消息预处理)
  ↓
Agent Node (LLM 调用)
  ↓
post_model_hook (响应后处理)
  ↓
工具调用 / 最终输出
```

### 两种 Hook 对比

| 特性 | Pre-Model Hook | Post-Model Hook |
|------|----------------|-----------------|
| **执行时机** | LLM 调用前 | LLM 调用后 |
| **主要用途** | 消息预处理 | 响应后处理 |
| **典型场景** | 裁剪、摘要、上下文注入 | 审批、验证、日志 |
| **状态更新** | messages / llm_input_messages | 任意状态键 |
| **支持中断** | ❌ | ✅ (HITL) |
| **访问 LLM 响应** | ❌ | ✅ |
| **版本要求** | v2 | v2 |

---

## 1️⃣ Pre-Model Hook (前置钩子)

### 用途

在 **LLM 调用之前** 对消息进行预处理：

1. **消息历史管理** - 裁剪过长的历史消息
2. **消息摘要** - 对历史对话进行总结
3. **上下文注入** - 动态添加系统提示或用户偏好
4. **成本优化** - 减少 Token 消耗

### 函数签名

```python
from typing import Dict, Any
from langchain_core.messages import BaseMessage, RemoveMessage, REMOVE_ALL_MESSAGES

def pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    参数:
        state: 当前 graph 状态
    
    返回:
        必须包含以下至少一个键:
        - messages: 更新状态中的消息列表 (永久修改)
        - llm_input_messages: 仅供 LLM 使用，不更新状态 (临时上下文)
    """
    return {
        "messages": [...],           # 可选: 更新状态
        "llm_input_messages": [...], # 可选: 仅供 LLM 输入
        # 其他需要传播的状态键
    }
```

### 两种返回模式

#### 模式 1: 永久修改状态 (messages)

```python
def trim_messages_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """保留最近 10 条消息，删除其他历史"""
    messages = state.get("messages", [])
    
    if len(messages) <= 10:
        return {}  # 无需处理
    
    recent_messages = messages[-10:]
    
    return {
        # ⚠️ 重要: 必须先清空再添加新消息
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *recent_messages
        ]
    }
```

#### 模式 2: 临时上下文注入 (llm_input_messages)

```python
async def inject_user_context_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """临时注入用户偏好，不修改状态"""
    messages = state.get("messages", [])
    user_id = state.get("user_id")
    
    # 从 Store 读取用户偏好
    user_prefs = await get_user_preferences(user_id)
    
    context_message = SystemMessage(
        content=f"用户偏好: {user_prefs['language']}, {user_prefs['style']}"
    )
    
    return {
        # 仅供本次 LLM 调用使用
        "llm_input_messages": [context_message, *messages]
        # 状态中的 messages 保持不变
    }
```

### 实战案例

#### 案例 1: 智能摘要 + 裁剪

```python
async def smart_summarize_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    超过 20 条消息时，摘要前 10 条，保留后 10 条
    """
    messages = state.get("messages", [])
    
    if len(messages) <= 20:
        return {}
    
    # 摘要前 10 条
    old_messages = messages[:-10]
    summary = await summarize_messages(old_messages)
    
    # 保留后 10 条
    recent_messages = messages[-10:]
    
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            SystemMessage(content=f"历史摘要: {summary}"),
            *recent_messages
        ]
    }
```

#### 案例 2: 项目中的应用 (DeepResearch)

```python
# src/infrastructure/ai/graph/hooks/pre_hooks.py

from src.infrastructure.ai.graph.memory import initialize_store

async def deepresearch_pre_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    DeepResearch 专用前置处理:
    1. 消息历史裁剪
    2. 用户偏好注入 (从 Store 读取)
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id")
    
    # 1. 裁剪历史 (保留最近 15 条)
    if len(messages) > 20:
        summary = await summarize_messages(messages[:-15])
        messages = [
            SystemMessage(content=f"历史摘要: {summary}"),
            *messages[-15:]
        ]
    
    # 2. 注入用户偏好 (临时上下文)
    context_parts = []
    
    if user_id:
        store = initialize_store()
        prefs = await store.aget(
            namespace=("user_preferences", user_id),
            key="research_preferences"
        )
        
        if prefs and prefs.value:
            context_parts.append(
                f"用户研究偏好: {json.dumps(prefs.value, ensure_ascii=False)}"
            )
    
    # 添加通用提示
    context_parts.append("请遵循系统化、结构化的输出风格")
    
    context_message = SystemMessage(
        content="\n".join(context_parts)
    )
    
    return {
        "llm_input_messages": [context_message, *messages]
    }
```

### ⚠️ 重要注意事项

1. **覆盖消息的正确方式**

```python
# ❌ 错误: 直接覆盖会导致状态不一致
return {
    "messages": new_messages
}

# ✅ 正确: 必须先清空再添加
return {
    "messages": [
        RemoveMessage(id=REMOVE_ALL_MESSAGES),
        *new_messages
    ]
}
```

2. **至少返回一个消息键**

```python
# ❌ 错误: 没有返回 messages 或 llm_input_messages
return {
    "user_id": "123"
}

# ✅ 正确
return {
    "llm_input_messages": messages,
    "user_id": "123"
}
```

---

## 2️⃣ Post-Model Hook (后置钩子)

### 用途

在 **LLM 调用之后、工具调用之前** 进行后处理：

1. **人机协同 (HITL)** - 工具调用前的人工审批
2. **内容审查** - 检测有害/敏感内容
3. **响应验证** - 确保输出符合格式要求
4. **日志记录** - 记录 LLM 决策过程
5. **动态路由** - 根据 LLM 输出调整工作流

### 函数签名

```python
from langgraph.types import interrupt

def post_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    参数:
        state: 当前 graph 状态 (包含 LLM 响应)
    
    返回:
        状态更新字典
    """
    return {
        "messages": [...],  # 可选: 修改消息
        # 其他状态更新
    }
```

### 实战案例

#### 案例 1: 工具调用人工审批 (HITL)

```python
from langgraph import interrupt

def approval_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """工具调用前需要人工批准"""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    # 检查是否有工具调用
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        
        # 触发中断，等待人工决策
        decision = interrupt({
            "action": "approve_tools",
            "tool_calls": [
                {
                    "name": tc["name"],
                    "args": tc["args"]
                }
                for tc in tool_calls
            ],
            "message": "请确认是否执行这些工具"
        })
        
        # 根据决策修改状态
        if decision.get("approved"):
            return {}  # 允许继续
        else:
            # 拒绝工具调用
            return {
                "messages": [
                    AIMessage(content="工具调用被拒绝")
                ]
            }
    
    return {}
```

#### 案例 2: 内容安全审查

```python
async def content_safety_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """检测 LLM 输出是否包含敏感内容"""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    if not last_message:
        return {}
    
    content = getattr(last_message, "content", "")
    
    # 调用内容审查 API
    is_safe, reason = await check_content_safety(content)
    
    if not is_safe:
        # 替换为安全消息
        return {
            "messages": [
                RemoveMessage(id=last_message.id),
                AIMessage(content=f"抱歉，无法处理该请求。原因: {reason}")
            ]
        }
    
    return {}
```

#### 案例 3: 项目中的应用 (统一工具审批)

```python
# src/infrastructure/ai/graph/hooks/post_hooks.py

def unified_tool_approval_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一的工具调用审批逻辑
    根据 auto 决定是否需要人工确认（auto=False 才需要）
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    auto = state.get("auto")
    tool_mode = "copilot" if (auto is None or auto) else "interactive"
    
    # 检查工具调用
    if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        return {}
    
    tool_calls = last_message.tool_calls
    
    # Interactive 模式需要审批
    if tool_mode == "interactive":
        # 危险工具列表
        dangerous_tools = ["delete_file", "execute_code", "coding_tool"]
        
        needs_approval = any(
            tc["name"] in dangerous_tools 
            for tc in tool_calls
        )
        
        if needs_approval:
            decision = interrupt({
                "action": "approve_tools",
                "tool_calls": tool_calls,
                "config": {
                    "allow_accept": True,
                    "allow_reject": True,
                    "allow_edit": True
                }
            })
            
            if decision.get("type") == "reject":
                return {
                    "messages": [
                        AIMessage(content="工具调用已被用户拒绝")
                    ]
                }
            elif decision.get("type") == "edit":
                # 修改工具参数 (需要更新 tool_calls)
                edited_args = decision.get("args", {})
                # 实现参数修改逻辑...
                pass
    
    return {}
```

#### 案例 4: 结合 Writer 输出日志

```python
from src.infrastructure.ai.graph.writer import create_stream_writer

def logging_post_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """记录 LLM 决策并流式输出"""
    writer = create_stream_writer("agent", "myagent")
    
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    if not last_message:
        return {}
    
    # 记录 LLM 响应
    content = getattr(last_message, "content", "")
    writer.thinking(content)
    
    # 检查工具调用
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tc in last_message.tool_calls:
            writer.tool_call(
                tool_name=tc["name"],
                tool_args=tc["args"]
            )
    
    return {}  # 不修改状态
```

---

## 🔄 组合使用 Pre + Post Hooks

### 完整示例

```python
# src/infrastructure/ai/graph/hooks/__init__.py

from typing import Dict, Any
from langchain_core.messages import SystemMessage, AIMessage, RemoveMessage, REMOVE_ALL_MESSAGES
from langgraph.types import interrupt, Command
import json

async def unified_pre_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """统一前置处理: 消息裁剪 + 用户偏好注入"""
    messages = state.get("messages", [])
    user_id = state.get("user_id")
    
    # 1. 消息裁剪
    if len(messages) > 20:
        summary = await summarize_messages(messages[:-15])
        messages = [
            SystemMessage(content=f"历史摘要: {summary}"),
            *messages[-15:]
        ]
    
    # 2. 用户偏好注入
    user_prefs = await get_user_preferences(user_id)
    context = SystemMessage(
        content=f"用户偏好: {json.dumps(user_prefs, ensure_ascii=False)}"
    )
    
    return {
        "llm_input_messages": [context, *messages]
    }


def unified_post_hook(state: Dict[str, Any]) -> Dict[str, Any]:
    """统一后置处理: 工具审批 + 内容安全"""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    if not last_message:
        return {}
    
    # 1. 内容安全检查
    content = getattr(last_message, "content", "")
    is_safe, reason = check_content_safety(content)
    
    if not is_safe:
        return {
            "messages": [
                AIMessage(content=f"抱歉，无法处理该请求。原因: {reason}")
            ]
        }
    
    # 2. 工具调用审批
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        auto = state.get("auto")
        tool_mode = "copilot" if (auto is None or auto) else "interactive"
        
        if tool_mode == "interactive":
            decision = interrupt({
                "action": "approve_tools",
                "tool_calls": last_message.tool_calls
            })
            
            if decision.get("type") == "reject":
                return {
                    "messages": [
                        AIMessage(content="工具调用被拒绝")
                    ]
                }
    
    return {}


# 导出
__all__ = ["unified_pre_hook", "unified_post_hook"]
```

### 在节点中使用

```python
# src/application/services/graph/deepresearch/nodes.py

from langgraph.prebuilt import create_react_agent
from src.infrastructure.ai.graph.hooks import unified_pre_hook, unified_post_hook
from src.infrastructure.ai.graph.tools.wrapper import wrap_tools

async def react_agent_node(state: DeepResearchState) -> Dict[str, Any]:
    """优化后的 React Agent 节点 - 使用 Hooks"""
    writer = create_stream_writer("react_agent", "deepresearch")
    
    # 准备工具
    tools = await wrap_tools([web_search_tool], mode="copilot")
    
    # 创建带 hooks 的 agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        pre_model_hook=unified_pre_hook,   # 自动消息预处理
        post_model_hook=unified_post_hook,  # 自动工具审批
        version="v2"  # 必须使用 v2
    )
    
    # 简化的执行逻辑
    messages = state.get("messages", [])
    final = await writer.agent(agent, {"messages": messages})
    
    return {"answer": final}
```

---

## 📊 最佳实践

### 1. 关注点分离

```python
# ✅ 好: 每个 hook 专注一件事
pre_hook = trim_messages_hook
post_hook = safety_check_hook

# ❌ 差: 一个 hook 做太多事
def mega_hook(state):
    # 裁剪 + 摘要 + 审查 + 日志 + ...
    pass
```

### 2. 性能优化

```python
# ✅ 好: 仅在必要时处理
def smart_pre_hook(state):
    messages = state.get("messages", [])
    if len(messages) < 10:
        return {}  # 无需处理
    # ...

# ❌ 差: 每次都执行复杂逻辑
def heavy_hook(state):
    await expensive_operation()  # 每次都调用
```

### 3. 错误处理

```python
async def safe_hook(state):
    try:
        # Hook 逻辑
        return await process(state)
    except Exception as e:
        logger.error(f"Hook failed: {e}")
        return {}  # 返回空更新，避免中断流程
```

### 4. 可测试性

```python
# hooks/tests/test_pre_hooks.py

async def test_pre_hook_message_trim():
    """测试消息裁剪"""
    state = {
        "messages": [HumanMessage(content=f"msg{i}") for i in range(30)]
    }
    
    result = await unified_pre_hook(state)
    
    # 验证消息数量
    assert "llm_input_messages" in result
    assert len(result["llm_input_messages"]) <= 16  # 摘要 + 15 条
```

---

## 🎓 迁移指南

### 从手动处理迁移到 Hooks

#### Before (手动处理)

```python
async def my_node(state):
    messages = state.get("messages", [])
    
    # 手动裁剪
    if len(messages) > 20:
        messages = messages[-10:]
    
    # 手动注入上下文
    user_prefs = await get_user_preferences(state.get("user_id"))
    context = SystemMessage(content=f"偏好: {user_prefs}")
    messages = [context, *messages]
    
    # 调用 LLM
    result = await llm.ainvoke(messages)
    
    # 手动安全检查
    if not is_safe(result.content):
        return {"error": "内容不安全"}
    
    return {"answer": result.content}
```

#### After (使用 Hooks)

```python
async def my_node(state):
    agent = create_react_agent(
        model=llm,
        tools=tools,
        pre_model_hook=unified_pre_hook,   # 自动裁剪 + 注入
        post_model_hook=unified_post_hook,  # 自动安全检查
        version="v2"
    )
    
    final = await writer.agent(agent, {"messages": state.get("messages")})
    return {"answer": final}
```

### 收益对比

| 指标 | Before | After | 改进 |
|------|--------|-------|------|
| 代码行数 | ~50 行 | ~15 行 | ⬇️ 70% |
| 重复代码 | 每个节点重复 | 集中复用 | ⬆️ 100% |
| 可测试性 | 困难 | 简单 | ⬆️ 80% |
| 可维护性 | 低 | 高 | ⬆️ 90% |

---

## 📚 相关文档

- [LangGraph Agents 开发指南](./langgraph-agents-development-guide.md)
- [LangGraph Human-in-the-Loop 指南](./langgraph-human-in-the-loop-guide.md)
- [优化记录](./optimized.md)

---

## 🚀 快速开始

1. **创建 hooks 模块**
   ```bash
   mkdir -p backend/src/infrastructure/ai/graph/hooks
   touch backend/src/infrastructure/ai/graph/hooks/__init__.py
   ```

2. **实现基础 hooks** (参考上面的示例)

3. **在节点中使用**
   ```python
   from src.infrastructure.ai.graph.hooks import unified_pre_hook, unified_post_hook
   ```

4. **编写测试**
   ```bash
   mkdir -p backend/tests/unit/infrastructure/ai/graph/hooks
   ```

5. **更新文档**
   - 在项目 README 中添加 hooks 使用说明
   - 为新 Graph 提供带 hooks 的模板代码

---

**更新记录**
- 2025-10-13: 创建文档，详细说明 Pre/Post Model Hooks 的使用方法和最佳实践
