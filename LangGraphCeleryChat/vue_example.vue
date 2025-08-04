<template>
  <div class="writing-assistant">
    <div class="container">
      <!-- 头部 -->
      <header class="header">
        <h1>🤖 智能写作助手</h1>
        <p>基于 LangGraph + Celery + FastAPI 的实时写作系统</p>
        <div class="connection-status">
          <span :class="['status-indicator', isConnected ? 'connected' : 'disconnected']"></span>
          {{ isConnected ? '已连接' : '未连接' }}
        </div>
      </header>

      <div class="main-content">
        <!-- 配置面板 -->
        <div class="config-panel">
          <h3>📝 写作配置</h3>
          
          <div class="form-group">
            <label for="topic">文章主题</label>
            <input
              id="topic"
              v-model="config.topic"
              type="text"
              placeholder="例如：Vue.js 3.0 Composition API 详解"
              :disabled="isRunning"
            />
          </div>

          <div class="form-group">
            <label for="maxWords">最大字数</label>
            <input
              id="maxWords"
              v-model.number="config.max_words"
              type="number"
              min="100"
              max="5000"
              :disabled="isRunning"
            />
          </div>

          <div class="form-group">
            <label for="style">写作风格</label>
            <select id="style" v-model="config.style" :disabled="isRunning">
              <option value="technical">技术性</option>
              <option value="formal">正式</option>
              <option value="casual">随意</option>
              <option value="academic">学术</option>
            </select>
          </div>

          <div class="form-group">
            <label for="language">语言</label>
            <select id="language" v-model="config.language" :disabled="isRunning">
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>

          <div class="form-group">
            <label for="mode">运行模式</label>
            <select id="mode" v-model="config.mode" :disabled="isRunning">
              <option value="interactive">交互模式（需要确认）</option>
              <option value="copilot">自动模式（无需确认）</option>
            </select>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="config.enable_search"
                type="checkbox"
                :disabled="isRunning"
              />
              启用联网搜索
            </label>
          </div>

          <button
            class="btn"
            :class="{ 'btn-danger': isRunning, 'btn-primary': !isRunning }"
            :disabled="isRunning && !isConnected"
            @click="isRunning ? stopWriting() : startWriting()"
          >
            {{ isRunning ? '⏹️ 停止任务' : '🚀 开始写作' }}
          </button>
        </div>

        <!-- 结果面板 -->
        <div class="result-panel">
          <h3>📊 实时进度</h3>
          
          <!-- 进度条 -->
          <div class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${progress.progress}%` }"
              ></div>
            </div>
            <div class="status-text">
              {{ progress.progress }}% - {{ progress.status }}
            </div>
          </div>

          <!-- 大纲显示 -->
          <div v-if="progress.outline" class="outline-container">
            <h4>📋 文章大纲</h4>
            <div class="outline-display">
              <h5>{{ progress.outline.title }}</h5>
              <div
                v-for="(section, index) in progress.outline.sections"
                :key="index"
                class="outline-section"
              >
                <h6>{{ index + 1 }}. {{ section.title }}</h6>
                <p>{{ section.description }}</p>
                <ul>
                  <li v-for="(point, i) in section.key_points" :key="i">
                    {{ point }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- 内容预览 -->
          <div v-if="progress.current_content" class="content-container">
            <h4>📄 内容预览</h4>
            <div class="content-preview">
              {{ progress.current_content }}
            </div>
          </div>

          <!-- 最终文章 -->
          <div v-if="progress.article" class="article-container">
            <h4>📝 最终文章</h4>
            <div class="article-content" v-html="formatArticle(progress.article)"></div>
            <button class="btn btn-secondary" @click="copyToClipboard(progress.article)">
              📋 复制文章
            </button>
          </div>

          <!-- 执行日志 -->
          <div class="log-container">
            <h4>📋 执行日志</h4>
            <div class="log-display" ref="logDisplay">
              <div
                v-for="(log, index) in logs"
                :key="index"
                class="log-entry"
                :class="`log-${log.level}`"
              >
                <span class="log-timestamp">[{{ formatTime(log.timestamp) }}]</span>
                <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="showInterrupt" class="modal-overlay" @click="closeInterrupt">
      <div class="modal-content" @click.stop>
        <h3>{{ interruptData.title || '需要确认' }}</h3>
        <p>{{ interruptData.message || '是否继续执行？' }}</p>
        <div class="modal-buttons">
          <button class="btn btn-success" @click="respondToInterrupt('yes')">
            ✅ 确认
          </button>
          <button class="btn btn-danger" @click="respondToInterrupt('no')">
            ❌ 取消
          </button>
        </div>
      </div>
    </div>

    <!-- 通知组件 -->
    <div v-if="notification" class="notification" :class="`notification-${notification.type}`">
      {{ notification.message }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'WritingAssistant',
  data() {
    return {
      // API 配置
      apiBase: 'http://localhost:8000',
      
      // 任务配置
      config: {
        topic: 'Vue.js 3.0 Composition API 详解',
        max_words: 1000,
        style: 'technical',
        language: 'zh',
        mode: 'interactive',
        enable_search: true
      },
      
      // 状态管理
      isRunning: false,
      isConnected: false,
      currentTask: null,
      eventSource: null,
      
      // 进度数据
      progress: {
        progress: 0,
        status: '等待开始...',
        step: 'idle',
        outline: null,
        article: null,
        current_content: null
      },
      
      // 交互数据
      showInterrupt: false,
      interruptData: {},
      currentInterruptId: null,
      
      // 日志数据
      logs: [],
      
      // 通知
      notification: null
    }
  },
  
  mounted() {
    this.addLog('智能写作助手已就绪', 'success');
    this.checkApiConnection();
  },
  
  beforeUnmount() {
    this.disconnect();
  },
  
  methods: {
    // 检查API连接
    async checkApiConnection() {
      try {
        const response = await fetch(`${this.apiBase}/health`);
        const data = await response.json();
        
        if (data.status === 'ok') {
          this.addLog('API 连接正常', 'success');
        } else {
          this.addLog('API 连接异常', 'error');
        }
      } catch (error) {
        this.addLog(`API 连接失败: ${error.message}`, 'error');
      }
    },
    
    // 开始写作
    async startWriting() {
      if (!this.config.topic.trim()) {
        this.showNotification('请输入文章主题', 'error');
        return;
      }
      
      try {
        this.isRunning = true;
        this.addLog('正在创建写作任务...', 'info');
        this.updateProgress(0, '创建任务中...');
        
        // 创建任务
        const response = await fetch(`${this.apiBase}/api/v1/tasks`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: 'vue_user',
            config: this.config
          })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        this.currentTask = await response.json();
        this.addLog(`任务创建成功: ${this.currentTask.task_id}`, 'success');
        
        // 开始监听进度
        this.startEventStream(this.currentTask.session_id);
        
      } catch (error) {
        this.addLog(`创建任务失败: ${error.message}`, 'error');
        this.showNotification('创建任务失败', 'error');
        this.resetState();
      }
    },
    
    // 停止写作
    async stopWriting() {
      if (this.currentTask) {
        try {
          await fetch(`${this.apiBase}/api/v1/tasks/${this.currentTask.task_id}`, {
            method: 'DELETE'
          });
          this.addLog('任务已取消', 'info');
        } catch (error) {
          this.addLog(`取消任务失败: ${error.message}`, 'error');
        }
      }
      
      this.resetState();
    },
    
    // 开始事件流监听
    startEventStream(sessionId) {
      if (this.eventSource) {
        this.eventSource.close();
      }
      
      this.addLog('开始监听实时进度...', 'info');
      
      this.eventSource = new EventSource(`${this.apiBase}/api/v1/events/${sessionId}`);
      
      this.eventSource.onopen = () => {
        this.isConnected = true;
        this.addLog('事件流连接成功', 'success');
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // 过滤心跳消息
          if (data.type === 'heartbeat') return;
          
          this.handleEventData(data);
          
        } catch (error) {
          this.addLog(`解析事件数据失败: ${error.message}`, 'error');
        }
      };
      
      this.eventSource.onerror = (error) => {
        this.isConnected = false;
        this.addLog('EventSource 连接错误', 'error');
        console.error('EventSource error:', error);
      };
    },
    
    // 处理事件数据
    handleEventData(data) {
      this.addLog(`事件: ${data.step || data.event_type} - ${data.status}`, 'info');
      
      // 更新进度
      if (data.progress !== undefined) {
        this.updateProgress(data.progress, data.status);
      }
      
      // 处理数据
      if (data.data) {
        // 显示大纲
        if (data.data.outline) {
          this.progress.outline = data.data.outline;
          this.addLog('大纲生成完成', 'success');
        }
        
        // 显示内容预览
        if (data.data.current_content) {
          this.progress.current_content = data.data.current_content;
        }
        
        // 显示最终文章
        if (data.data.article) {
          this.progress.article = data.data.article;
          this.addLog('文章生成完成', 'success');
        }
        
        // 处理交互请求
        if (data.data.interrupt_type) {
          this.currentInterruptId = data.data.interrupt_id || 'default';
          this.interruptData = {
            title: data.data.title || '需要确认',
            message: data.data.message || '是否继续执行？'
          };
          this.showInterrupt = true;
        }
        
        // 任务完成
        if (data.step === 'completed' || data.status === 'completed') {
          this.addLog('🎉 任务完成！', 'success');
          this.updateProgress(100, '任务完成');
          this.showNotification('任务完成！', 'success');
          this.resetState();
        }
      }
    },
    
    // 响应用户交互
    async respondToInterrupt(response) {
      this.showInterrupt = false;
      
      if (!this.currentTask || !this.currentInterruptId) return;
      
      try {
        this.addLog(`用户响应: ${response}`, 'info');
        
        const res = await fetch(`${this.apiBase}/api/v1/tasks/${this.currentTask.task_id}/resume`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            response: response,
            approved: response === 'yes',
            interrupt_id: this.currentInterruptId
          })
        });
        
        const result = await res.json();
        this.addLog(`任务恢复: ${result.message}`, 'success');
        
      } catch (error) {
        this.addLog(`恢复任务失败: ${error.message}`, 'error');
      }
    },
    
    // 关闭交互对话框
    closeInterrupt() {
      this.showInterrupt = false;
    },
    
    // 断开连接
    disconnect() {
      if (this.eventSource) {
        this.eventSource.close();
        this.eventSource = null;
        this.isConnected = false;
      }
    },
    
    // 重置状态
    resetState() {
      this.isRunning = false;
      this.disconnect();
      this.currentTask = null;
      this.currentInterruptId = null;
      this.showInterrupt = false;
    },
    
    // 更新进度
    updateProgress(progress, status) {
      this.progress.progress = progress;
      this.progress.status = status;
    },
    
    // 添加日志
    addLog(message, level = 'info') {
      this.logs.push({
        message,
        level,
        timestamp: new Date()
      });
      
      // 限制日志数量
      if (this.logs.length > 100) {
        this.logs = this.logs.slice(-50);
      }
      
      // 自动滚动到底部
      this.$nextTick(() => {
        const logDisplay = this.$refs.logDisplay;
        if (logDisplay) {
          logDisplay.scrollTop = logDisplay.scrollHeight;
        }
      });
    },
    
    // 显示通知
    showNotification(message, type = 'info') {
      this.notification = { message, type };
      setTimeout(() => {
        this.notification = null;
      }, 3000);
    },
    
    // 格式化时间
    formatTime(date) {
      return date.toLocaleTimeString();
    },
    
    // 格式化文章（简单的Markdown转HTML）
    formatArticle(article) {
      return article
        .replace(/### (.*)/g, '<h3>$1</h3>')
        .replace(/#### (.*)/g, '<h4>$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    },
    
    // 复制到剪贴板
    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text);
        this.showNotification('文章已复制到剪贴板', 'success');
      } catch (error) {
        this.showNotification('复制失败', 'error');
      }
    }
  }
}
</script>

<style scoped>
/* 这里可以添加组件特定的样式 */
/* 或者使用外部CSS文件 */
</style>
