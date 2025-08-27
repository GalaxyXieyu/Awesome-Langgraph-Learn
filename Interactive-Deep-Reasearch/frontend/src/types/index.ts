// 流式消息类型
export interface StreamMessage {
  message_type: 
    | 'step_start'
    | 'step_progress' 
    | 'step_complete'
    | 'tool_call'
    | 'tool_result'
    | 'thinking'
    | 'reasoning'
    | 'content_streaming'
    | 'content_complete'
    | 'interrupt_request'
    | 'interrupt_response'
    | 'interrupt_waiting'
    | 'interrupt_resolved'
    | 'final_result'
    | 'error'
    | 'node_complete';
  
  content: string;
  node: string;
  timestamp: number;
  duration?: number;
  progress?: number;
  agent?: string;
  agent_hierarchy?: string[];
  
  // 工具相关字段
  tool_name?: string;
  args?: Record<string, any>;
  length?: number;
  
  // 中断相关字段
  action?: string;
  interrupt_id?: string;
  config?: {
    allow_accept?: boolean;
    allow_edit?: boolean;
    allow_respond?: boolean;
  };
  
  // 其他字段
  chunk_index?: number;
  aggregated?: boolean;
  is_final?: boolean;
  error_type?: string;
  [key: string]: any;
}

// 报告章节
export interface ReportSection {
  id: string;
  title: string;
  description: string;
  key_points: string[];
  research_queries: string[];
  priority: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  content?: string;
  word_count: number;
}

// 报告大纲
export interface ReportOutline {
  title: string;
  executive_summary: string;
  sections: ReportSection[];
  methodology: string;
  target_audience: string;
  estimated_length: number;
  creation_time: number;
}

// 任务状态
export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'canceled';
  topic: string;
  user_id: string;
  celery_id?: string;
}

// 创建任务请求
export interface CreateTaskRequest {
  topic: string;
  user_id?: string;
  mode?: 'interactive' | 'copilot' | 'guided';
  report_type?: string;
  target_audience?: string;
  depth_level?: string;
  max_sections?: number;
  target_length?: number;
  language?: string;
  style?: string;
}

// 中断响应
export interface InterruptResponse {
  approved?: 'yes' | 'no';
  edit?: Record<string, any>;
  response?: string;
}

// 应用状态
export interface AppState {
  currentTask: TaskStatus | null;
  messages: StreamMessage[];
  outline: ReportOutline | null;
  isConnected: boolean;
  isGenerating: boolean;
  pendingInterrupts: Map<string, StreamMessage>;
  latestProgress: StreamMessage | null;
  settings: {
    mode: 'interactive' | 'copilot' | 'guided';
    auto_approve: boolean;
    show_thinking: boolean;
    show_tool_calls: boolean;
  };
}

// 组件Props类型
export interface StreamMessageProps {
  message: StreamMessage;
  onInterruptResponse?: (interruptId: string, response: InterruptResponse) => void;
}

export interface OutlineTreeProps {
  outline: ReportOutline | null;
  currentSection?: string;
}

export interface ChatInputProps {
  onSubmit: (topic: string, config: CreateTaskRequest) => void;
  disabled?: boolean;
  mode: 'interactive' | 'copilot' | 'guided';
  onModeChange: (mode: 'interactive' | 'copilot' | 'guided') => void;
}
