# LangGraph 人机交互(Human-in-the-Loop)指南

## 🔄 核心概念

LangGraph的中断机制允许在工作流执行过程中暂停并等待外部输入，实现真正的人机协作。

## 📊 三种中断方式对比

| 特性 | `interrupt` (动态) | `interrupt_before` | `interrupt_after` |
|------|-------------------|-------------------|------------------|
| **触发时机** | 代码执行时 | 节点执行前 | 节点执行后 |
| **数据传递** | ✅ 丰富上下文 | ❌ 仅基础状态 | ✅ 执行结果 |
| **生产环境** | 🏆 **推荐** | ❌ 仅调试用 | ❌ 仅调试用 |
| **用户交互** | ✅ 复杂决策 | ⚠️ 简单继续/停止 | ⚠️ 简单继续/停止 |

## 🎯 决策指南

```
需要用户交互？
├─ 是 → 生产环境？
│   ├─ 是 → 🏆 使用动态中断 (interrupt)
│   └─ 否 → 🔧 使用静态中断 (interrupt_before/after)
└─ 否 → 不需要中断机制
```

## 🔧 实现模板

### 🏆 动态中断（推荐）
```python
def approval_node(state):
    # 生成内容
    content = generate_content(state)
    
    # 中断等待用户确认
    user_decision = interrupt({
        "type": "content_approval",
        "message": "请审核生成的内容：",
        "content": content,
        "options": {
            "approve": "批准内容",
            "edit": "编辑内容",
            "regenerate": "重新生成"
        },
        "ui_hints": {
            "show_preview": True,
            "allow_inline_edit": True
        }
    })
    
    # 处理用户决策
    if user_decision.get("action") == "approve":
        state["status"] = "approved"
    elif user_decision.get("action") == "edit":
        state["content"] = user_decision.get("edited_content")
        state["status"] = "edited"
    else:  # regenerate
        state["status"] = "regeneration_needed"
    
    return state

# 恢复执行
result = graph.invoke(Command(resume={"action": "approve"}), config)
```

### 🔧 静态中断（调试用）
```python
# 编译时设置
graph = workflow.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["critical_node"],  # 在关键节点前暂停
    interrupt_after=["validation_node"]   # 在验证节点后暂停
)

# 继续执行
result = graph.invoke(None, config)  # 传入None继续执行
```

## 💡 最佳实践

### ✅ 动态中断最佳实践

1. **提供丰富的上下文信息**
```python
user_decision = interrupt({
    "type": "content_approval",
    "message": "请审核生成的内容",
    "content": content,
    "metadata": {
        "word_count": len(content.split()),
        "estimated_reading_time": f"{len(content) // 1000 + 1} 分钟"
    },
    "options": {
        "approve": "批准内容",
        "edit": "编辑内容", 
        "regenerate": "重新生成"
    },
    "ui_hints": {
        "show_preview": True,
        "allow_inline_edit": True
    }
})
```

2. **完整的决策处理逻辑**
```python
if user_decision.get("action") == "approve":
    state["status"] = "approved"
elif user_decision.get("action") == "edit":
    # 处理编辑逻辑
    state["content"] = user_decision.get("edited_content", state["content"])
    state["status"] = "edited"
else:  # regenerate
    state["status"] = "regeneration_needed"
```

3. **记录用户决策历史**
```python
state["user_decisions"].append({
    "step": "content_review",
    "decision": user_decision,
    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
})
```

### ✅ 静态中断最佳实践

1. **开发阶段使用**
```python
if DEBUG_MODE:
    graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["critical_nodes"],
        interrupt_after=["validation_nodes"]
    )
else:
    graph = workflow.compile(checkpointer=checkpointer)
```

2. **逐步调试**
```python
# 设置多个断点
graph = workflow.compile(
    interrupt_before=["data_processing", "model_inference"],
    interrupt_after=["validation", "output_formatting"]
)
```

### ❌ 避免的做法

1. **信息不足的中断**
```python
# ❌ 错误：缺少上下文
user_input = interrupt("继续吗？")  # 用户不知道要决策什么

# ✅ 正确：提供充分信息
user_input = interrupt({
    "type": "confirmation",
    "message": "数据处理完成，是否继续生成报告？",
    "processed_items": len(processed_data),
    "estimated_time": "2分钟"
})
```

2. **在有副作用的操作前中断**
```python
# ❌ 错误：危险操作已执行
database.delete_all()  # 危险操作
user_confirm = interrupt("确认删除？")  # 为时已晚

# ✅ 正确：先中断再执行
user_confirm = interrupt("确认删除所有数据？")
if user_confirm == "yes":
    database.delete_all()
```

3. **生产环境使用静态中断**
```python
# ❌ 错误：影响用户体验
graph = workflow.compile(
    interrupt_before=["every_node"]  # 生产环境用户体验差
)
```

## 🎯 应用场景

### 1. 内容审核
```python
def content_review_node(state):
    generated_content = state["content"]
    
    user_review = interrupt({
        "type": "content_review",
        "message": "请审核生成的内容：",
        "content": generated_content,
        "content_stats": {
            "word_count": len(generated_content.split()),
            "sentiment": analyze_sentiment(generated_content)
        },
        "options": {
            "approve": "批准发布",
            "edit": "需要编辑",
            "reject": "拒绝内容"
        }
    })
    
    return handle_review_decision(state, user_review)
```

### 2. 参数确认
```python
def parameter_confirmation_node(state):
    suggested_params = generate_parameters(state["requirements"])
    
    user_params = interrupt({
        "type": "parameter_confirmation",
        "message": "请确认或调整参数设置：",
        "suggested_params": suggested_params,
        "param_descriptions": get_param_descriptions(),
        "options": {
            "use_suggested": "使用建议参数",
            "customize": "自定义参数",
            "regenerate": "重新生成建议"
        }
    })
    
    return apply_parameters(state, user_params)
```

### 3. 数据筛选
```python
def data_filtering_node(state):
    search_results = state["search_results"]
    
    user_selection = interrupt({
        "type": "data_selection",
        "message": "请选择要使用的数据源：",
        "available_data": search_results,
        "selection_criteria": {
            "relevance_threshold": 0.8,
            "max_selections": 5
        },
        "options": {
            "select_all": "选择所有",
            "select_top": "选择最相关的",
            "custom_select": "自定义选择"
        }
    })
    
    return filter_data(state, user_selection)
```

### 4. 输入验证
```python
def input_validation_node(state):
    while True:
        user_input = interrupt({
            "type": "input_validation",
            "message": "请输入有效的邮箱地址：",
            "validation_rules": [
                "必须包含@符号",
                "必须有有效的域名",
                "长度不超过100字符"
            ]
        })
        
        if validate_email(user_input):
            state["email"] = user_input
            break
        else:
            # 继续循环，再次中断
            continue
    
    return state
```

## 🧪 测试和调试

### 中断测试
```python
def test_interrupt_flow():
    graph = create_graph_with_interrupts()
    config = {"configurable": {"thread_id": "test"}}
    
    # 第一次执行到中断点
    result1 = graph.invoke(initial_state, config)
    assert "__interrupt__" in result1
    
    # 模拟用户决策
    result2 = graph.invoke(Command(resume="approve"), config)
    assert result2["status"] == "approved"
```

### 调试中断
```python
def debug_interrupt_node(state):
    # 添加调试信息
    debug_info = {
        "node": "debug_interrupt_node",
        "state_keys": list(state.keys()),
        "timestamp": time.time()
    }
    
    user_decision = interrupt({
        "type": "debug_review",
        "message": "调试检查点",
        "debug_info": debug_info,
        "state_snapshot": state
    })
    
    return state
```

## 📋 状态管理

### 完整的状态跟踪
```python
class InterruptState(TypedDict):
    # 业务数据
    content: str
    status: str
    
    # 中断管理
    interrupt_count: int
    user_decisions: List[Dict[str, Any]]
    execution_log: List[str]

def track_interrupt(state, decision):
    state["interrupt_count"] += 1
    state["user_decisions"].append({
        "decision": decision,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })
    state["execution_log"].append(f"用户决策: {decision}")
```

### 错误恢复
```python
def safe_interrupt_node(state):
    try:
        user_decision = interrupt({
            "type": "safe_operation",
            "message": "请确认操作",
            "options": ["confirm", "cancel"]
        })
        
        if user_decision == "confirm":
            return perform_operation(state)
        else:
            return cancel_operation(state)
            
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        return state
```

## 🎉 总结

中断机制是实现人机协作的强大工具。动态中断适合生产环境的复杂交互，静态中断适合开发调试。关键是提供丰富的上下文信息，完善的决策处理逻辑，以及可靠的状态管理。
