import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  StreamMessage, 
  TaskStatus, 
  ReportOutline, 
  CreateTaskRequest, 
  InterruptResponse,
  AppState 
} from '../types';
import { ApiClient, parseStreamData, isInterruptMessage } from '../utils/api';

export const useReportGenerator = () => {
  const [state, setState] = useState<AppState>({
    currentTask: null,
    messages: [],
    outline: null,
    isConnected: false,
    isGenerating: false,
    pendingInterrupts: new Map(),
    latestProgress: null,
    settings: {
      mode: 'interactive',
      auto_approve: false,
      show_thinking: true,
      show_tool_calls: true,
    },
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到最新消息
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 添加消息
  const addMessage = useCallback((message: StreamMessage) => {
    setState(prev => {
      // 处理 content_streaming 和 content 消息的累积拼接
      if (message.message_type === 'content_streaming' || message.message_type === 'content') {
        const messages = [...prev.messages];

        // 查找最后一个流式内容消息（不限制node匹配，因为JSON片段可能来自不同节点）
        let lastStreamingIndex = -1;
        for (let i = messages.length - 1; i >= 0; i--) {
          const msg = messages[i];
          if ((msg.message_type === 'content_streaming' || msg.message_type === 'content') &&
              !msg.is_final && // 只与未完成的消息合并
              msg.node === message.node) { // 同一节点的消息才合并
            lastStreamingIndex = i;
            break;
          }
        }

        if (lastStreamingIndex !== -1) {
          // 如果找到了未完成的流式消息，就累积内容
          const existingMessage = messages[lastStreamingIndex];
          const combinedContent = existingMessage.content + message.content;
          
          // 检测是否是完整的JSON或其他完整内容
          let isCompleteContent = false;
          let finalMessageType: 'content_streaming' | 'content' = 'content_streaming';
          
          // JSON 检测
          if (combinedContent.trim().startsWith('{') || combinedContent.trim().startsWith('[')) {
            try {
              JSON.parse(combinedContent.trim());
              isCompleteContent = true;
              finalMessageType = 'content'; // 完整JSON使用content类型
            } catch (e) {
              // 仍在构建中的JSON，继续累积
            }
          }
          
          // 检测其他完整内容标志
          if (message.is_final || isCompleteContent) {
            finalMessageType = 'content';
            isCompleteContent = true;
          }

          messages[lastStreamingIndex] = {
            ...existingMessage,
            content: combinedContent,
            message_type: finalMessageType,
            timestamp: message.timestamp, // 更新时间戳
            length: combinedContent.length,
            is_final: isCompleteContent
          };
        } else {
          // 如果没找到可合并的消息，创建新的流式消息
          messages.push({
            ...message,
            message_type: message.is_final ? 'content' : 'content_streaming',
            is_final: message.is_final || false
          });
        }

        return {
          ...prev,
          messages,
          lastActivity: Date.now(),
        };
      }

      // 过滤重复消息
      const isDuplicate = prev.messages.some(m =>
        m.timestamp === message.timestamp &&
        m.content === message.content &&
        m.message_type === message.message_type
      );

      if (isDuplicate) return prev;

      // 更新最新进度消息
      let newLatestProgress = prev.latestProgress;
      if (message.message_type === 'step_progress') {
        newLatestProgress = message;

        // 如果是大纲生成的进度消息，不添加到主消息列表中
        if (message.node === 'outline_generation') {
          return {
            ...prev,
            latestProgress: newLatestProgress,
          };
        }
      }

      // 处理中断消息
      if (isInterruptMessage(message) && message.interrupt_id) {
        const newPendingInterrupts = new Map(prev.pendingInterrupts);
        newPendingInterrupts.set(message.interrupt_id, message);
        
        return {
          ...prev,
          messages: [...prev.messages, message],
          pendingInterrupts: newPendingInterrupts,
          latestProgress: newLatestProgress,
        };
      }

      // 处理大纲数据
      if (message.message_type === 'step_complete' && 
          message.node === 'outline_generation' && 
          message.content.includes('大纲')) {
        // 这里可以解析outline数据，暂时用模拟数据
        const mockOutline: ReportOutline = {
          title: `${message.content} - 研究报告`,
          executive_summary: '这是一个由AI生成的深度研究报告的执行摘要...',
          sections: [
            {
              id: '1',
              title: '研究背景与意义',
              description: '分析研究主题的背景和重要性',
              key_points: ['背景分析', '研究意义', '发展趋势'],
              research_queries: ['背景研究', '意义分析'],
              priority: 5,
              status: 'pending',
              word_count: 0,
            },
            {
              id: '2',
              title: '现状分析',
              description: '当前发展现状的深入分析',
              key_points: ['技术现状', '市场分析', '竞争格局'],
              research_queries: ['现状调研', '竞争分析'],
              priority: 4,
              status: 'pending',
              word_count: 0,
            },
            {
              id: '3',
              title: '发展趋势与展望',
              description: '未来发展趋势和前景展望',
              key_points: ['发展趋势', '技术展望', '应用前景'],
              research_queries: ['趋势分析', '前景预测'],
              priority: 3,
              status: 'pending',
              word_count: 0,
            },
          ],
          methodology: '采用文献调研、数据分析、专家访谈等方法',
          target_audience: '专业人士',
          estimated_length: 3000,
          creation_time: Date.now() / 1000,
        };

        return {
          ...prev,
          messages: [...prev.messages, message],
          outline: mockOutline,
          latestProgress: newLatestProgress,
        };
      }

      return {
        ...prev,
        messages: [...prev.messages, message],
        latestProgress: newLatestProgress,
      };
    });
  }, []);

  // 开始流式监听
  const startStreaming = useCallback((taskId: string) => {
    // 关闭现有连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = ApiClient.createEventSource(taskId);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setState(prev => ({ ...prev, isConnected: true }));
    };

    eventSource.onmessage = (event) => {
      const data = parseStreamData(event.data);
      if (data) {
        // 检查数据结构，如果有data字段，则提取其中的消息数据
        if (data.data && typeof data.data === 'object') {
          addMessage(data.data);
        } else if (data.type === 'connected') {
          // 连接确认消息，不需要添加到消息列表
          console.log('EventSource connected:', data);
        } else if (data.type === 'heartbeat') {
          // 心跳消息，不需要添加到消息列表
          console.log('EventSource heartbeat:', data);
        } else if (data.type === 'error') {
          // 错误消息
          console.error('EventSource error:', data.message);
        } else {
          // 其他格式的消息，直接添加
          addMessage(data);
        }
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource 错误:', error);
      setState(prev => ({ 
        ...prev, 
        isConnected: false,
        isGenerating: false 
      }));
    };

    // 清理函数
    return () => {
      eventSource.close();
    };
  }, [addMessage]);

  // 创建任务
  const createTask = useCallback(async (topic: string, config: CreateTaskRequest) => {
    try {
      setState(prev => ({ 
        ...prev, 
        isGenerating: true, 
        messages: [],
        outline: null,
        pendingInterrupts: new Map(),
      }));

      const response = await ApiClient.createTask(config);
      const taskStatus: TaskStatus = {
        task_id: response.task_id,
        status: 'pending',
        topic,
        user_id: config.user_id || 'user',
      };

      setState(prev => ({ 
        ...prev, 
        currentTask: taskStatus,
        settings: { ...prev.settings, mode: config.mode || 'interactive' }
      }));

      // 开始监听流式数据
      startStreaming(response.task_id);

    } catch (error) {
      console.error('创建任务失败:', error);
      setState(prev => ({ ...prev, isGenerating: false }));
    }
  }, [startStreaming]);

  // 处理中断响应
  const handleInterruptResponse = useCallback(async (
    interruptId: string, 
    response: InterruptResponse
  ) => {
    if (!state.currentTask) return;

    try {
      // 发送响应到后端
      await ApiClient.sendInterruptResponse(
        state.currentTask.task_id,
        interruptId,
        response
      );

      // 从待处理中断中移除
      setState(prev => {
        const newPendingInterrupts = new Map(prev.pendingInterrupts);
        newPendingInterrupts.delete(interruptId);
        return {
          ...prev,
          pendingInterrupts: newPendingInterrupts,
        };
      });

      // 添加响应消息
      const responseMessage: StreamMessage = {
        message_type: 'interrupt_response',
        content: `用户响应: ${response.approved ? '批准' : response.edit ? '编辑参数' : '拒绝'}`,
        node: 'user_response',
        timestamp: Date.now(),
        interrupt_id: interruptId,
      };
      
      addMessage(responseMessage);

    } catch (error) {
      console.error('发送中断响应失败:', error);
    }
  }, [state.currentTask, addMessage]);

  // 取消任务
  const cancelTask = useCallback(async () => {
    if (!state.currentTask) return;

    try {
      await ApiClient.cancelTask(state.currentTask.task_id);
      
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setState(prev => ({
        ...prev,
        currentTask: null,
        isConnected: false,
        isGenerating: false,
        pendingInterrupts: new Map(),
      }));

    } catch (error) {
      console.error('取消任务失败:', error);
    }
  }, [state.currentTask]);

  // 更新设置
  const updateSettings = useCallback((newSettings: Partial<AppState['settings']>) => {
    setState(prev => ({
      ...prev,
      settings: { ...prev.settings, ...newSettings }
    }));
  }, []);

  // 清理资源
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [state.messages, scrollToBottom]);

  return {
    state,
    actions: {
      createTask,
      cancelTask,
      handleInterruptResponse,
      updateSettings,
    },
    refs: {
      messagesEndRef,
    },
  };
};
