# StreamWriter 输出格式文档 (简化版)

## 📋 概述

这是 Interactive Deep Research 项目的**简化版**标准化流式输出系统，基于 `backend/writer/core.py` 设计。系统已大幅简化为**4个核心消息类型**，提供统一的流式输出格式，便于前端实时渲染和解析。

## 🏗️ 核心架构 (简化版)

### 主要组件
- **StreamWriter**: 标准化流式输出Writer (简化为4个核心方法)
- **AgentWorkflowProcessor**: Agent工作流程处理器 (兼容旧格式)
- **FlatDataProcessor**: 数据扁平化处理器
- **InterruptHandler**: 中断处理器

### 🎯 简化设计特点
- ✅ **4个核心消息类型** - 大幅简化API
- ✅ 扁平化数据结构，便于前端解析
- ✅ 支持流式和批量模式
- ✅ 智能去重机制
- ✅ 中断处理支持
- ✅ 配置化控制
- ✅ 向后兼容旧格式

## 🎯 简化架构总览

### 核心简化对比

| 旧API (已删除) | 新API (简化版) | 说明 |
|---------------|---------------|------|
| `step_start()` `step_progress()` `step_complete()` | `processing()` | 统一进度处理，支持自动百分比计算 |
| `content_streaming()` `content_complete()` | `content()` | 统一内容输出，支持流式和完整内容 |
| `reasoning()` `planning()` | `thinking()` | 统一思考过程，包含所有推理类型 |
| `interrupt_request()` `interrupt_waiting()` | `interrupt()` | 统一中断处理，简化用户交互 |

### 保留的特殊方法
- `tool_call()` `tool_result()` - 工具相关
- `final_result()` - 最终结果
- `error()` - 错误处理
- `interrupt_response()` `interrupt_resolved()` - 中断响应处理

## 📦 基础消息结构

所有输出消息都遵循统一的基础结构：

```typescript
interface BaseMessage {
  message_type: string;        // 消息类型
  content: string;            // 消息内容
  node: string;               // 节点名称
  timestamp?: number;         // 时间戳 (Unix时间戳)
  duration?: number;          // 执行时长 (秒)
  agent?: string;             // Agent名称 (子图消息才有)
  agent_hierarchy?: string[]; // Agent层级 (可选)
}
```

## 🔖 简化消息类型定义

### 🎯 核心4个消息类型 (简化版)

```typescript
type CoreMessageType =
  // 1. 进度处理 - 节点执行状态（支持百分比）
  | "processing"              // 进度处理 (替代 step_start/progress/complete)

  // 2. 内容输出 - 实际输出内容
  | "content"                 // 内容输出 (替代 content_streaming/complete)

  // 3. 思考过程 - AI推理过程
  | "thinking"                // 思考过程 (替代 reasoning/planning)

  // 4. 中断处理 - 用户交互
  | "interrupt"               // 中断处理 (替代 interrupt_request/waiting)
```

### 🔧 保留的特殊类型

```typescript
type SpecialMessageType =
  // 工具使用类型
  | "tool_call"               // 工具调用
  | "tool_result"             // 工具执行结果

  // 中断响应类型 (保留用于内部处理)
  | "interrupt_response"      // 中断响应 (用户回复)
  | "interrupt_resolved"      // 中断已解决

  // 结果状态类型
  | "final_result"            // 最终结果
  | "error";                  // 错误信息
```

## 📝 简化消息格式详解

### 🎯 1. 进度处理消息 (processing)

**统一的进度处理** - 替代所有步骤相关消息

```typescript
interface ProcessingMessage extends BaseMessage {
  message_type: "processing";
  content: string;           // 进度描述
  progress?: number;         // 进度百分比 (0-100，自动计算)
  graph_nodes?: string[];    // 图节点列表 (用于进度计算)
  [key: string]: any;        // 其他自定义字段
}
```

**示例:**
```json
{
  "message_type": "processing",
  "content": "开始生成研究大纲",
  "node": "outline_generation",
  "progress": 25,
  "timestamp": 1703123456.789,
  "duration": 2.34
}
```

**使用方法:**
```python
# 基本用法
processor.writer.processing("开始处理")

# 带进度计算
processor.writer.processing("处理中", graph_nodes=["node1", "node2", "node3"])

# 带自定义字段
processor.writer.processing("完成", sections_count=5, total_words=1000)
```

### 🎯 2. 内容输出消息 (content)

**统一的内容输出** - 替代所有内容相关消息

```typescript
interface ContentMessage extends BaseMessage {
  message_type: "content";
  content: string;           // 输出内容
  chunk_index?: number;      // 流式片段索引 (可选)
  length?: number;           // 内容长度
  [key: string]: any;        // 其他自定义字段
}
```

**示例:**
```json
{
  "message_type": "content",
  "content": "第一章：人工智能概述\n\n人工智能是...",
  "node": "writing",
  "agent": "writing",
  "length": 1500,
  "word_count": 500,
  "timestamp": 1703123456.789
}
```

**使用方法:**
```python
# 基本内容输出
processor.writer.content("生成的内容")

# 带自定义字段
processor.writer.content("章节内容", word_count=500, section_title="概述")
```

### 🎯 3. 思考过程消息 (thinking)

**统一的思考过程** - 替代推理、规划等消息

```typescript
interface ThinkingMessage extends BaseMessage {
  message_type: "thinking";
  content: string;           // 思考内容
  [key: string]: any;        // 其他自定义字段
}
```

**示例:**
```json
{
  "message_type": "thinking",
  "content": "正在分析用户需求，准备生成大纲结构...",
  "node": "outline_generation",
  "timestamp": 1703123456.789
}
```

**使用方法:**
```python
# 基本思考过程
processor.writer.thinking("正在分析...")

# 带自定义字段
processor.writer.thinking("推理完成", reasoning_type="logical")
```

### 🎯 4. 中断处理消息 (interrupt)

**统一的中断处理** - 替代所有中断相关消息

```typescript
interface InterruptMessage extends BaseMessage {
  message_type: "interrupt";
  content: string;           // 中断描述
  action?: string;           // 中断动作
  args?: any;               // 中断参数
  interrupt_id?: string;     // 中断ID
  [key: string]: any;        // 其他自定义字段
}
```

**示例:**
```json
{
  "message_type": "interrupt",
  "content": "等待用户确认大纲",
  "node": "outline_confirmation",
  "action": "confirm_outline",
  "args": {"outline": "..."},
  "interrupt_id": "confirm_123456",
  "timestamp": 1703123456.789
}
```

**使用方法:**
```python
# 基本中断
processor.writer.interrupt("等待用户确认")

# 带中断参数
processor.writer.interrupt("确认操作", action="confirm", args={"data": "..."})
```

### 🔧 5. 保留的特殊消息类型

#### 工具调用 (tool_call)
```typescript
interface ToolCallMessage extends BaseMessage {
  message_type: "tool_call";
  content: string;                    // 简化描述，如 "调用了 web_search 工具"
  tool_name: string;                  // 工具名称
  args: Record<string, any>;          // 工具参数
}
```

**示例:**
```json
{
  "message_type": "tool_call",
  "content": "调用了 web_search 工具",
  "node": "research",
  "agent": "research",
  "tool_name": "web_search",
  "args": {
    "query": "人工智能医疗应用",
    "num_results": 10
  },
  "timestamp": 1703123456.789
}
```

#### 工具结果 (tool_result)
```typescript
interface ToolResultMessage extends BaseMessage {
  message_type: "tool_result";
  content: string;      // 清理后的工具结果
  tool_name: string;    // 工具名称
  length: number;       // 结果内容长度
}
```

**示例:**
```json
{
  "message_type": "tool_result",
  "content": "找到了15篇关于AI医疗应用的相关文献...",
  "node": "research",
  "agent": "research",
  "tool_name": "web_search",
  "length": 2847,
  "timestamp": 1703123456.789,
  "duration": 3.45
}
```

### 🔧 6. 最终结果消息 (final_result)

```typescript
interface FinalResultMessage extends BaseMessage {
  message_type: "final_result";
  content: string;                          // 最终结果内容
  execution_summary: Record<string, any>;   // 执行摘要
  is_final: true;                          // 标识最终结果
}
```

**示例:**
```json
{
  "message_type": "final_result",
  "content": "研究报告已完成，总计15000字，包含5个主要章节",
  "node": "report_generation",
  "execution_summary": {
    "total_words": 15000,
    "sections": 5,
    "research_sources": 25,
    "generation_time": 180.5
  },
  "is_final": true,
  "timestamp": 1703123456.789,
  "duration": 180.5
}
```

### 🔧 7. 错误消息 (error)

```typescript
interface ErrorMessage extends BaseMessage {
  message_type: "error";
  content: string;      // 错误描述
  error_type: string;   // 错误类型
}
```

**示例:**
```json
{
  "message_type": "error",
  "content": "网络搜索超时，请稍后重试",
  "node": "research",
  "agent": "research",
  "error_type": "NetworkTimeout",
  "timestamp": 1703123456.789
}
```

## 🎯 前端解析建议 (简化版)

### 1. 简化消息处理器示例

```typescript
class SimplifiedStreamMessageProcessor {
  private contentBuffer = new Map<string, string>();

  processMessage(message: BaseMessage) {
    switch (message.message_type) {
      // 核心4个消息类型
      case 'processing':
        this.showProcessing(message as ProcessingMessage);
        break;

      case 'content':
        this.handleContent(message as ContentMessage);
        break;

      case 'thinking':
        this.showThinking(message as ThinkingMessage);
        break;

      case 'interrupt':
        this.handleInterrupt(message as InterruptMessage);
        break;

      // 保留的特殊类型
      case 'tool_call':
        this.showToolCall(message as ToolCallMessage);
        break;

      case 'tool_result':
        this.showToolResult(message as ToolResultMessage);
        break;

      case 'final_result':
        this.showFinalResult(message as FinalResultMessage);
        break;

      case 'error':
        this.showError(message as ErrorMessage);
        break;

      default:
        console.log('未处理的消息类型:', message.message_type);
    }
  }

  private handleContent(message: ContentMessage) {
    const key = `${message.node}_${message.agent || 'main'}`;
    const current = this.contentBuffer.get(key) || '';
    this.contentBuffer.set(key, current + message.content);

    // 实时更新UI
    this.updateContentDisplay(key, this.contentBuffer.get(key)!);
  }

  private handleInterrupt(message: InterruptMessage) {
    // 显示确认对话框
    const confirmed = confirm(message.content);

    // 发送用户响应 (需要通过WebSocket或API发送)
    this.sendInterruptResponse(message.interrupt_id, confirmed);
  }
}
```

### 2. 简化状态管理建议

```typescript
interface SimplifiedAppState {
  currentStep: string;
  progress: number;
  activeAgents: Set<string>;
  contentSections: Map<string, string>;
  toolCalls: ToolCallMessage[];
  pendingInterrupts: Map<string, InterruptMessage>;
  errors: ErrorMessage[];
  isComplete: boolean;
}

class SimplifiedStateManager {
  private state: SimplifiedAppState = {
    currentStep: '',
    progress: 0,
    activeAgents: new Set(),
    contentSections: new Map(),
    toolCalls: [],
    pendingInterrupts: new Map(),
    errors: [],
    isComplete: false
  };

  updateFromMessage(message: BaseMessage) {
    switch (message.message_type) {
      // 简化的消息类型处理
      case 'processing':
        const processingMsg = message as ProcessingMessage;
        this.state.currentStep = processingMsg.content;
        if (processingMsg.progress !== undefined) {
          this.state.progress = processingMsg.progress;
        }
        break;

      case 'content':
        const contentMsg = message as ContentMessage;
        if (contentMsg.agent) {
          this.state.activeAgents.add(contentMsg.agent);
        }
        break;

      case 'interrupt':
        const interruptMsg = message as InterruptMessage;
        if (interruptMsg.interrupt_id) {
          this.state.pendingInterrupts.set(interruptMsg.interrupt_id, interruptMsg);
        }
        break;

      case 'final_result':
        this.state.isComplete = true;
        break;

      case 'error':
        this.state.errors.push(message as ErrorMessage);
        break;
    }
  }
}
```

### 3. UI组件建议

```typescript
// 进度显示组件
function ProgressDisplay({ currentStep, progress }: { currentStep: string, progress: number }) {
  return (
    <div className="progress-container">
      <div className="step-name">{currentStep}</div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
      <span className="progress-text">{progress}%</span>
    </div>
  );
}

// 工具调用显示组件
function ToolCallDisplay({ toolCall }: { toolCall: ToolCallMessage }) {
  return (
    <div className="tool-call">
      <span className="tool-icon">🔧</span>
      <span className="tool-name">{toolCall.tool_name}</span>
      <span className="tool-description">{toolCall.content}</span>
    </div>
  );
}

// 中断处理组件
function InterruptDialog({ interrupt, onResponse }: { 
  interrupt: InterruptRequestMessage, 
  onResponse: (approved: boolean) => void 
}) {
  return (
    <div className="interrupt-dialog">
      <h3>需要确认</h3>
      <p>{interrupt.content}</p>
      <div className="buttons">
        <button onClick={() => onResponse(true)}>确认</button>
        <button onClick={() => onResponse(false)}>取消</button>
      </div>
    </div>
  );
}
```

## 🚀 简化API使用指南

### 基本使用模式

```python
from writer import create_workflow_processor

# 创建处理器
processor = create_workflow_processor("my_node", "my_agent")

# 使用4个核心方法
processor.writer.processing("开始处理")        # 进度处理
processor.writer.content("生成的内容")          # 内容输出
processor.writer.thinking("正在思考...")       # 思考过程
processor.writer.interrupt("等待确认")         # 中断处理
```

### 进度计算示例

```python
# 自动进度计算
graph_nodes = ["outline", "research", "writing", "integration"]
processor.writer.processing("当前步骤", graph_nodes=graph_nodes)

# 手动进度 (如果不传graph_nodes，默认50%)
processor.writer.processing("处理中")  # 自动返回50%进度
```

### 兼容性说明

```python
# ✅ 新的简化API (推荐)
processor.writer.processing("消息")
processor.writer.content("内容")
processor.writer.thinking("思考")
processor.writer.interrupt("中断")

# ❌ 旧API (已删除，不再支持)
# processor.writer.step_start("开始")
# processor.writer.step_progress("进度", 50)
# processor.writer.step_complete("完成")
# processor.writer.content_streaming("流式内容")
# processor.writer.content_complete("内容完成")
# processor.writer.reasoning("推理")
# processor.writer.planning("规划")
# processor.writer.interrupt_request("请求")
# processor.writer.interrupt_waiting("等待")
```

## ⚙️ 配置控制

系统支持通过配置文件控制输出行为：

### 配置选项
- **消息类型过滤**: 可以选择显示/隐藏特定类型的消息
- **Agent过滤**: 可以控制显示特定Agent的消息
- **节点过滤**: 可以控制显示特定节点的消息
- **流式控制**: 可以切换流式/批量模式
- **详细程度**: 控制是否显示时间戳、Agent层级等元数据

### 配置示例
```yaml
# 只显示核心消息
messages:
  include: ["step_start", "step_complete", "content_streaming", "final_result"]
  exclude: ["thinking", "reasoning"]

# 只显示特定Agent
agents:
  include: ["research", "writing"]
  exclude: ["supervisor"]

# 节点流式控制
streaming:
  nodes:
    outline_generation: true      # 大纲生成：流式
    content_creation: false       # 内容创建：汇总输出
```

## 🔍 注意事项

1. **去重机制**: 系统自动去重相同的reasoning消息和中断消息
2. **时间字段**: `timestamp`是Unix时间戳，`duration`是秒数(浮点数)
3. **Agent信息**: 只有子图消息才包含`agent`字段
4. **中断处理**: 中断消息需要前端响应，否则流程会暂停
5. **内容聚合**: 流式内容需要前端按`node`和`agent`聚合
6. **错误处理**: 错误消息不会停止流程，需要前端适当处理

## 📚 相关文件

- `backend/writer/core.py` - 核心实现
- `backend/writer/config.py` - 配置管理
- `backend/writer/config.yaml` - 配置文件
- `backend/writer/guide.md` - 使用指南

---

*最后更新: 2024年12月*
