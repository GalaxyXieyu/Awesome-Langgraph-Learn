"""
LangGraph Custom Stream增强Writer - 使用指南和最佳实践
"""

## 🎯 核心优势

增强Writer系统解决了LangGraph多模式流输出的复杂性问题：

### ❌ **之前的问题**
```python
# 需要处理多种不同格式的输出
for chunk in app.stream(state, stream_mode=["updates", "messages", "custom"]):
    mode, data = chunk
    if mode == "updates":
        # 处理节点更新...
    elif mode == "messages": 
        # 处理LLM token流...
    elif mode == "custom":
        # 处理自定义数据...
```

### ✅ **现在的解决方案**
```python
# 只需要处理一种统一格式
for chunk in app.stream(state, stream_mode=["custom"]):
    mode, unified_message = chunk
    if mode == "custom":
        # 所有类型消息都是统一格式！
        renderer.format_message(unified_message)
```

## 🚀 **快速开始**

### 1. 在节点中使用增强Writer

```python
from enhanced_writer import create_enhanced_writer

async def your_node(state, config=None):
    # 创建writer
    writer = create_enhanced_writer("your_node", "Your Agent")
    
    # 步骤开始
    writer.step_start("开始执行任务")
    
    # 进度更新
    writer.step_progress("正在处理...", 50)
    
    # AI流式输出
    for i, chunk in enumerate(llm_stream):
        writer.ai_streaming(chunk, i)
    
    # 工具调用
    writer.tool_call("calculator", {"expression": "2+3"})
    writer.tool_result("calculator", "5")
    
    # 步骤完成
    writer.step_complete("任务完成")
    
    return state
```

### 2. 前端统一处理

```python
class UnifiedRenderer:
    """前端统一消息渲染器"""
    
    def render_message(self, msg_dict):
        msg_type = msg_dict["message_type"]
        
        if msg_type == "ai_streaming":
            # 流式内容不换行
            print(msg_dict["content"], end='', flush=True)
        elif msg_type == "step_progress":
            # 显示进度条
            progress = msg_dict["metadata"]["progress"]
            print(f"⏳ {msg_dict['content']} ({progress}%)")
        elif msg_type == "tool_call":
            # 显示工具调用
            tool_name = msg_dict["metadata"]["tool_name"]
            print(f"🔧 调用工具: {tool_name}")
        # ... 其他类型的处理
```

## 📋 **消息类型完整列表**

| 消息类型 | 用途 | 前端处理建议 |
|---------|------|-------------|
| `step_start` | 步骤开始 | 显示加载状态 |
| `step_progress` | 步骤进度 | 更新进度条 |
| `step_complete` | 步骤完成 | 隐藏加载状态 |
| `ai_thinking` | AI思考过程 | 显示思考动画 |
| `ai_streaming` | AI流式输出 | 打字机效果 |
| `ai_complete` | AI回复完成 | 停止流式动画 |
| `tool_call` | 工具调用 | 显示工具图标 |
| `tool_result` | 工具结果 | 显示结果卡片 |
| `agent_switch` | Agent切换 | 显示切换动画 |
| `final_result` | 最终结果 | 高亮显示 |
| `error` | 错误信息 | 错误提示 |
| `debug` | 调试信息 | 开发模式显示 |

## 🎨 **前端UI建议**

### React示例
```jsx
const MessageRenderer = ({ message }) => {
  const { message_type, content, metadata, timestamp } = message;
  
  switch (message_type) {
    case 'step_start':
      return <div className="step-start">🚀 {content}</div>;
    
    case 'step_progress':
      return (
        <div className="progress-bar">
          <span>⏳ {content}</span>
          <div className="bar">
            <div style={{width: `${metadata.progress}%`}} />
          </div>
        </div>
      );
    
    case 'ai_streaming':
      return <span className="streaming-text">{content}</span>;
    
    case 'tool_call':
      return (
        <div className="tool-call">
          🔧 调用工具: {metadata.tool_name}
          <pre>{JSON.stringify(metadata.tool_args, null, 2)}</pre>
        </div>
      );
    
    case 'final_result':
      return (
        <div className="final-result">
          🎯 <strong>{content}</strong>
        </div>
      );
    
    default:
      return <div>{content}</div>;
  }
};
```

## 🔧 **高级用法**

### 1. 自定义消息类型

```python
# 扩展MessageType枚举
class CustomMessageType(Enum):
    DATA_ANALYSIS = "data_analysis"
    CHART_GENERATION = "chart_generation"

# 在writer中使用
writer._create_unified_message(
    CustomMessageType.DATA_ANALYSIS,
    "正在分析数据...",
    data_points=1000,
    analysis_type="statistical"
)
```

### 2. 批量消息处理

```python
class BatchMessageProcessor:
    def __init__(self):
        self.message_buffer = []
        self.batch_size = 10
    
    def add_message(self, message):
        self.message_buffer.append(message)
        
        if len(self.message_buffer) >= self.batch_size:
            self.flush_batch()
    
    def flush_batch(self):
        # 批量处理消息，提高性能
        for msg in self.message_buffer:
            self.process_message(msg)
        self.message_buffer.clear()
```

### 3. 消息过滤和路由

```python
class MessageFilter:
    def __init__(self):
        self.filters = {
            "debug": lambda msg: not self.is_production(),
            "tool_result": lambda msg: len(msg["content"]) < 1000,
            "ai_streaming": lambda msg: self.should_show_streaming()
        }
    
    def should_display(self, message):
        msg_type = message["message_type"]
        filter_func = self.filters.get(msg_type)
        
        if filter_func:
            return filter_func(message)
        
        return True  # 默认显示
```

## 🎯 **最佳实践**

### 1. 性能优化
- 流式消息使用`end=''`避免不必要的换行
- 批量处理非关键消息减少UI更新频率
- 长文本内容进行截断显示

### 2. 用户体验
- 为不同类型消息设置不同的视觉样式
- 使用进度条和动画提供反馈
- 错误消息提供明确的解决建议

### 3. 开发调试
- 保留消息统计功能用于性能分析
- 使用时间戳进行执行时间分析
- 提供详细的metadata用于问题排查

### 4. 扩展性
- 消息类型使用枚举便于扩展
- Writer接口保持简洁易用
- 支持自定义metadata字段

## 🔍 **监控和分析**

```python
class MessageAnalyzer:
    def __init__(self):
        self.stats = defaultdict(int)
        self.timings = defaultdict(list)
    
    def analyze_message(self, message):
        msg_type = message["message_type"]
        timestamp = message["timestamp"]
        
        # 统计消息数量
        self.stats[msg_type] += 1
        
        # 记录时间
        if msg_type == "step_complete":
            duration = message["metadata"].get("duration", 0)
            self.timings[message["node_name"]].append(duration)
    
    def get_performance_report(self):
        return {
            "message_counts": dict(self.stats),
            "average_step_times": {
                node: sum(times) / len(times) 
                for node, times in self.timings.items()
            }
        }
```

这个增强Writer系统让你的前端开发变得极其简单 - 只需要处理一种统一的消息格式，就能完美展示所有类型的agent输出！