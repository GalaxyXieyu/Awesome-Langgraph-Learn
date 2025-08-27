# StreamWriter 输出格式文档

## 📋 概述

这是 Interactive Deep Research 项目的标准化流式输出系统，基于 `backend/writer/core.py` 设计。系统提供统一的流式输出格式，便于前端实时渲染和解析。

## 🏗️ 核心架构

### 主要组件
- **StreamWriter**: 标准化流式输出Writer
- **AgentWorkflowProcessor**: Agent工作流程处理器
- **FlatDataProcessor**: 数据扁平化处理器
- **InterruptHandler**: 中断处理器

### 设计特点
- ✅ 扁平化数据结构，便于前端解析
- ✅ 支持流式和批量模式
- ✅ 智能去重机制
- ✅ 中断处理支持
- ✅ 配置化控制

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

## 🔖 消息类型定义

### 消息类型枚举

```typescript
type MessageType = 
  // 步骤状态类型
  | "step_start"              // 步骤开始
  | "step_progress"           // 步骤进度更新
  | "step_complete"           // 步骤完成
  | "node_complete"           // 节点汇总完成 (非流式节点)
  
  // 工具使用类型
  | "tool_call"               // 工具调用
  | "tool_result"             // 工具执行结果
  
  // 思考过程类型
  | "thinking"                // 思考过程
  | "reasoning"               // 推理分析
  
  // 内容输出类型
  | "content_streaming"       // 流式内容输出
  | "content_complete"        // 内容输出完成
  
  // 中断处理类型
  | "interrupt_request"       // 中断请求 (需要用户确认)
  | "interrupt_response"      // 中断响应 (用户回复)
  | "interrupt_waiting"       // 等待用户响应
  | "interrupt_resolved"      // 中断已解决
  
  // 结果状态类型
  | "final_result"            // 最终结果
  | "error";                  // 错误信息
```

## 📝 详细消息格式

### 1. 步骤状态消息

#### 步骤开始
```typescript
interface StepStartMessage extends BaseMessage {
  message_type: "step_start";
  content: string;  // 步骤描述，如 "开始生成大纲"
}
```

**示例:**
```json
{
  "message_type": "step_start",
  "content": "开始生成研究大纲",
  "node": "outline_generation",
  "timestamp": 1703123456.789,
  "duration": 0
}
```

#### 步骤进度
```typescript
interface StepProgressMessage extends BaseMessage {
  message_type: "step_progress";
  content: string;           // 进度描述
  progress: number;          // 进度百分比 (0-100)
  research_title?: string;   // 研究标题 (可选)
}
```

**示例:**
```json
{
  "message_type": "step_progress",
  "content": "发现研究资料: AI在医疗领域的应用",
  "node": "research",
  "agent": "research",
  "progress": 25,
  "research_title": "AI在医疗领域的应用",
  "timestamp": 1703123456.789,
  "duration": 2.34
}
```

#### 步骤完成
```typescript
interface StepCompleteMessage extends BaseMessage {
  message_type: "step_complete";
  content: string;  // 完成总结
  duration: number; // 执行时长
}
```

**示例:**
```json
{
  "message_type": "step_complete",
  "content": "大纲生成完成，包含5个主要章节",
  "node": "outline_generation",
  "duration": 15.67,
  "timestamp": 1703123456.789
}
```

#### 节点汇总完成 (非流式节点)
```typescript
interface NodeCompleteMessage extends BaseMessage {
  message_type: "node_complete";
  content: string;     // 汇总内容
  duration: number;    // 执行时长
  aggregated: true;    // 标识这是汇总结果
}
```

### 2. 工具使用消息

#### 工具调用
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

#### 工具结果
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

### 3. 内容输出消息

#### 流式内容
```typescript
interface ContentStreamingMessage extends BaseMessage {
  message_type: "content_streaming";
  content: string;      // 内容片段
  length: number;       // 片段长度
  chunk_index: number;  // 片段索引
  agent?: string;       // Agent名称 (子图消息)
}
```

**示例:**
```json
{
  "message_type": "content_streaming",
  "content": "# 第一章 人工智能概述\n\n人工智能(AI)是计算机科学的一个分支...",
  "node": "content_creation",
  "agent": "writing",
  "length": 156,
  "chunk_index": 0,
  "timestamp": 1703123456.789
}
```

#### 内容完成
```typescript
interface ContentCompleteMessage extends BaseMessage {
  message_type: "content_complete";
  content: string;          // 完成描述
  word_count?: number;      // 字数统计
  section_title?: string;   // 章节标题
  tools_used?: string[];    // 使用的工具列表
  total_chunks?: number;    // 总片段数
}
```

**示例:**
```json
{
  "message_type": "content_complete",
  "content": "完成章节: 人工智能概述",
  "node": "content_creation",
  "agent": "writing",
  "word_count": 1245,
  "section_title": "人工智能概述",
  "timestamp": 1703123456.789,
  "duration": 45.23
}
```

### 4. 思考过程消息

#### 思考过程
```typescript
interface ThinkingMessage extends BaseMessage {
  message_type: "thinking";
  content: string;  // 思考内容
}
```

**示例:**
```json
{
  "message_type": "thinking",
  "content": "需要搜索更多关于AI医疗诊断的资料",
  "node": "research",
  "agent": "research",
  "timestamp": 1703123456.789
}
```

#### 推理分析
```typescript
interface ReasoningMessage extends BaseMessage {
  message_type: "reasoning";
  content: string;  // 推理内容
}
```

**示例:**
```json
{
  "message_type": "reasoning",
  "content": "基于收集到的资料，AI在医疗领域主要应用于诊断、治疗和药物研发三个方面",
  "node": "research",
  "agent": "research",
  "timestamp": 1703123456.789,
  "duration": 1.23
}
```

### 5. 中断处理消息

#### 中断请求
```typescript
interface InterruptRequestMessage extends BaseMessage {
  message_type: "interrupt_request";
  content: string;                    // 中断描述
  action: string;                     // 请求的操作
  args: Record<string, any>;          // 操作参数
  interrupt_id: string;               // 中断ID
  requires_approval: true;            // 需要用户确认
  config?: Record<string, any>;       // 配置信息
}
```

**示例:**
```json
{
  "message_type": "interrupt_request",
  "content": "需要进行网络搜索以获取最新信息，是否继续？",
  "node": "research",
  "agent": "research",
  "action": "web_search",
  "args": {
    "query": "2024年AI医疗最新发展",
    "num_results": 5
  },
  "interrupt_id": "search_20241201_001",
  "requires_approval": true,
  "timestamp": 1703123456.789
}
```

#### 中断响应
```typescript
interface InterruptResponseMessage extends BaseMessage {
  message_type: "interrupt_response";
  content: string;        // 用户响应内容
  approved: boolean;      // 是否批准
  interrupt_id: string;   // 中断ID
}
```

#### 中断等待
```typescript
interface InterruptWaitingMessage extends BaseMessage {
  message_type: "interrupt_waiting";
  content: string;        // 等待描述
  interrupt_id: string;   // 中断ID
  status: "waiting";      // 状态
}
```

#### 中断解决
```typescript
interface InterruptResolvedMessage extends BaseMessage {
  message_type: "interrupt_resolved";
  content: string;        // 解决结果
  interrupt_id: string;   // 中断ID
  status: "resolved";     // 状态
}
```

### 6. 结果状态消息

#### 最终结果
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

#### 错误消息
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

## 🎯 前端解析建议

### 1. 消息处理器示例

```typescript
class StreamMessageProcessor {
  private contentBuffer = new Map<string, string>();
  
  processMessage(message: BaseMessage) {
    switch (message.message_type) {
      case 'step_start':
        this.showStepStart(message as StepStartMessage);
        break;
        
      case 'step_progress':
        this.updateProgress(message as StepProgressMessage);
        break;
        
      case 'content_streaming':
        this.handleContentStream(message as ContentStreamingMessage);
        break;
        
      case 'tool_call':
        this.showToolCall(message as ToolCallMessage);
        break;
        
      case 'tool_result':
        this.showToolResult(message as ToolResultMessage);
        break;
        
      case 'interrupt_request':
        this.handleInterrupt(message as InterruptRequestMessage);
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
  
  private handleContentStream(message: ContentStreamingMessage) {
    const key = `${message.node}_${message.agent || 'main'}`;
    const current = this.contentBuffer.get(key) || '';
    this.contentBuffer.set(key, current + message.content);
    
    // 实时更新UI
    this.updateContentDisplay(key, this.contentBuffer.get(key)!);
  }
  
  private handleInterrupt(message: InterruptRequestMessage) {
    // 显示确认对话框
    const confirmed = confirm(message.content);
    
    // 发送用户响应 (需要通过WebSocket或API发送)
    this.sendInterruptResponse(message.interrupt_id, confirmed);
  }
}
```

### 2. 状态管理建议

```typescript
interface AppState {
  currentStep: string;
  progress: number;
  activeAgents: Set<string>;
  contentSections: Map<string, string>;
  toolCalls: ToolCallMessage[];
  pendingInterrupts: Map<string, InterruptRequestMessage>;
  errors: ErrorMessage[];
  isComplete: boolean;
}

class StateManager {
  private state: AppState = {
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
      case 'step_start':
        this.state.currentStep = message.content;
        break;
        
      case 'step_progress':
        const progressMsg = message as StepProgressMessage;
        this.state.progress = progressMsg.progress;
        break;
        
      case 'content_streaming':
        const contentMsg = message as ContentStreamingMessage;
        if (contentMsg.agent) {
          this.state.activeAgents.add(contentMsg.agent);
        }
        break;
        
      case 'final_result':
        this.state.isComplete = true;
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
