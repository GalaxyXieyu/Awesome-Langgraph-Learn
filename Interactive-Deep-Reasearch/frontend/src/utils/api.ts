import { CreateTaskRequest, TaskStatus, InterruptResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export class ApiClient {
  // 创建研究任务
  static async createTask(request: CreateTaskRequest): Promise<{ task_id: string }> {
    const response = await fetch(`${API_BASE_URL}/research/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`创建任务失败: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 获取任务状态
  static async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await fetch(`${API_BASE_URL}/research/tasks/${taskId}`);
    
    if (!response.ok) {
      throw new Error(`获取任务状态失败: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 取消任务
  static async cancelTask(taskId: string): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/research/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`取消任务失败: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 创建流式连接
  static createEventSource(taskId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/research/tasks/${taskId}/stream`);
  }

  // 发送中断响应 (通过resume接口)
  static async sendInterruptResponse(
    taskId: string, 
    interruptId: string, 
    response: InterruptResponse
  ): Promise<void> {
    // 根据你的示例代码，这里需要调用resume接口
    // 具体实现可能需要根据后端的resume接口来调整
    const resumeData = {
      interrupt_id: interruptId,
      ...response
    };
    
    // 这里可能需要通过WebSocket或其他方式发送resume指令
    // 暂时使用console.log来模拟
    console.log('Sending resume command:', resumeData);
  }
}

// 解析流式数据
export function parseStreamData(data: string): any {
  try {
    return JSON.parse(data);
  } catch (error) {
    console.error('解析流式数据失败:', error);
    return null;
  }
}

// 格式化时间
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const remainingMinutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${remainingMinutes}m`;
  }
}

// 生成唯一ID
export function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

// 检查是否为中断消息
export function isInterruptMessage(message: any): boolean {
  return message.message_type === 'interrupt_request';
}

// 获取消息显示颜色
export function getMessageTypeColor(messageType: string): string {
  const colorMap: Record<string, string> = {
    'step_start': 'text-apple-blue',
    'step_progress': 'text-apple-orange',
    'step_complete': 'text-apple-green',
    'tool_call': 'text-apple-purple',
    'tool_result': 'text-apple-secondary',
    'thinking': 'text-apple-gray-600',
    'reasoning': 'text-apple-text',
    'content_streaming': 'text-apple-text',
    'interrupt_request': 'text-apple-red',
    'error': 'text-apple-red',
    'final_result': 'text-apple-green',
  };
  
  return colorMap[messageType] || 'text-apple-text';
}

// 获取消息图标
export function getMessageTypeIcon(messageType: string): string {
  const iconMap: Record<string, string> = {
    'step_start': '🚀',
    'step_progress': '⏳',
    'step_complete': '✅',
    'tool_call': '🔧',
    'tool_result': '📊',
    'thinking': '💭',
    'reasoning': '🤔',
    'content_streaming': '✍️',
    'interrupt_request': '⚠️',
    'error': '❌',
    'final_result': '🎉',
  };
  
  return iconMap[messageType] || '📝';
}
