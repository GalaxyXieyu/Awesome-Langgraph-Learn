# 通用中断节点使用指南

这个模块提供了统一的中断处理机制，让你可以轻松创建各种类型的中断节点，而不需要重复编写中断处理逻辑。

## 主要功能

### 1. `create_confirmation_node` - 确认节点

用于创建简单的用户确认节点，适用于大部分确认场景。

```python
from common import create_confirmation_node

# 创建大纲确认节点
outline_confirmation_node = create_confirmation_node(
    node_name="outline_confirmation",
    title="大纲确认", 
    message_template="""请确认以下研究大纲：
    
📋 标题：{title}
📝 摘要：{summary}
📚 章节数：{section_count}个

是否确认继续？""",
    get_data_func=lambda state: {
        "title": state.get("outline", {}).get("title", "未知"),
        "summary": state.get("outline", {}).get("summary", "无"),
        "section_count": len(state.get("outline", {}).get("sections", []))
    }
)
```

### 2. `create_interrupt_node` - 中断节点

用于创建更复杂的中断节点，支持自定义响应处理。

```python
from common import create_interrupt_node

def get_research_data(state):
    """获取研究数据"""
    return {
        "topic": state.get("topic", ""),
        "sources": state.get("research_sources", []),
        "estimated_time": "5-10分钟"
    }

def process_research_response(state, response_data):
    """处理研究确认响应"""
    if response_data.get("approved"):
        state["research_approved"] = True
        state["research_start_time"] = time.time()
    else:
        state["research_approved"] = False
    return state

# 创建研究权限确认节点
research_permission_node = create_interrupt_node(
    node_name="research_permission",
    action_name="confirm_research",
    description_template="""准备开始研究：{topic}

📊 数据源：{sources}
⏱️ 预计时间：{estimated_time}

是否允许开始研究？""",
    get_interrupt_data_func=get_research_data,
    process_response_func=process_research_response,
    allow_edit=False,
    auto_approve_in_copilot=True
)
```

### 3. `create_parameter_edit_node` - 参数编辑节点

用于创建允许用户编辑参数的中断节点。

```python
from common import create_parameter_edit_node

def get_generation_params(state):
    """获取生成参数"""
    return {
        "topic": state.get("topic", ""),
        "length": state.get("target_length", 5000),
        "style": state.get("writing_style", "academic"),
        "audience": state.get("target_audience", "general")
    }

def apply_generation_params(state, params):
    """应用生成参数"""
    state["topic"] = params.get("topic", state.get("topic"))
    state["target_length"] = params.get("length", state.get("target_length"))
    state["writing_style"] = params.get("style", state.get("writing_style"))
    state["target_audience"] = params.get("audience", state.get("target_audience"))
    return state

# 创建参数编辑节点
params_edit_node = create_parameter_edit_node(
    node_name="generation_params",
    action_name="edit_generation_params",
    description_template="""当前生成参数：

📝 主题：{topic}
📊 字数：{length}
🎨 风格：{style}
👥 读者：{audience}

是否需要修改这些参数？""",
    get_params_func=get_generation_params,
    apply_params_func=apply_generation_params
)
```

## 在图中使用

```python
from langgraph.graph import StateGraph, END, START
from common import create_confirmation_node

# 创建节点
confirmation_node = create_confirmation_node(...)

# 在图中使用
workflow = StateGraph(YourState)
workflow.add_node("confirmation", confirmation_node)
workflow.add_edge(START, "confirmation")
workflow.add_edge("confirmation", END)

app = workflow.compile()
```

## 中断格式

所有通过这些函数创建的节点都会产生统一格式的中断：

```python
('custom', {
    'message_type': 'interrupt_request',
    'content': '描述信息...',
    'node': '节点名称',
    'action': '动作名称',
    'args': {...},
    'interrupt_id': '唯一ID',
    'config': {
        'allow_accept': True,
        'allow_edit': True/False,
        'allow_respond': True
    }
})
```

## 模式支持

- **Copilot模式**: 自动通过所有确认，无需用户干预
- **Interactive模式**: 触发中断，等待用户确认

## 优势

1. **统一的中断格式** - 前端只需要处理一种中断类型
2. **可复用** - 一次编写，到处使用
3. **灵活配置** - 支持自定义数据获取和响应处理
4. **模式感知** - 自动适配Copilot和Interactive模式
5. **类型安全** - 提供完整的类型提示

## 最佳实践

1. 使用描述性的节点名称
2. 提供清晰的用户提示信息
3. 在Copilot模式下合理设置自动通过行为
4. 为复杂场景使用自定义响应处理函数
5. 保持数据获取函数的简洁性
