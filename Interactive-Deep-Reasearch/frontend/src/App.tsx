import React from 'react';
import { motion } from 'framer-motion';
import { 
  Brain, 
  Wifi, 
  WifiOff, 
  X, 
  RotateCcw,
  Eye,
  EyeOff,
  Settings
} from 'lucide-react';
import { useReportGenerator } from './hooks/useReportGenerator';
import { StreamMessage } from './components/StreamMessage';
import { ChatInput } from './components/ChatInput';
import { OutlineTree } from './components/OutlineTree';
import { ProgressFloater } from './components/ProgressFloater';
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';

function App() {
  const { state, actions, refs } = useReportGenerator();

  const {
    currentTask,
    messages,
    outline,
    isConnected,
    isGenerating,
    pendingInterrupts,
    latestProgress,
    settings,
  } = state;

  const {
    createTask,
    cancelTask,
    handleInterruptResponse,
    updateSettings,
  } = actions;

  const { messagesEndRef } = refs;

  // 过滤消息
  const filteredMessages = messages.filter(message => {
    if (!settings.show_thinking && message.message_type === 'thinking') return false;
    if (!settings.show_tool_calls && 
        ['tool_call', 'tool_result'].includes(message.message_type)) return false;
    return true;
  });

  const currentSection = messages
    .filter(m => m.message_type === 'step_progress' && m.content.includes('章节'))
    .pop()?.content;

  return (
    <div className="min-h-screen bg-gradient-to-br from-apple-bg via-white to-apple-gray-50">
      {/* 悬浮进度显示 */}
      <ProgressFloater latestProgress={latestProgress} />

      <div className="flex h-screen">
        {/* 左侧边栏 - 大纲和设置 */}
        <motion.div
          initial={{ x: -300 }}
          animate={{ x: 0 }}
          className="w-80 border-r border-apple-gray-200 bg-white/80 backdrop-blur-sm"
        >
          <div className="p-6 border-b border-apple-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-apple-blue to-apple-purple rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-apple-text">
                  智能报告生成器
                </h1>
                <div className="flex items-center gap-2 text-sm">
                  {isConnected ? (
                    <div className="flex items-center gap-1 text-apple-green">
                      <Wifi className="w-3 h-3" />
                      已连接
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-apple-gray-400">
                      <WifiOff className="w-3 h-3" />
                      未连接
                    </div>
                  )}
                  {currentTask && (
                    <span className="text-apple-secondary">
                      · {currentTask.task_id.slice(-8)}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* 控制按钮 */}
            {currentTask && (
              <div className="flex gap-2 mt-4">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={cancelTask}
                  disabled={!isGenerating}
                >
                  <X className="w-3 h-3 mr-1" />
                  取消
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.location.reload()}
                >
                  <RotateCcw className="w-3 h-3 mr-1" />
                  重置
                </Button>
              </div>
            )}
          </div>

          {/* 显示设置 */}
          <div className="p-4 border-b border-apple-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <Settings className="w-4 h-4 text-apple-secondary" />
              <span className="text-sm font-medium text-apple-text">显示设置</span>
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={settings.show_thinking}
                  onChange={(e) => updateSettings({ show_thinking: e.target.checked })}
                  className="rounded border-apple-gray-300"
                />
                <span className="text-apple-text">显示思考过程</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={settings.show_tool_calls}
                  onChange={(e) => updateSettings({ show_tool_calls: e.target.checked })}
                  className="rounded border-apple-gray-300"
                />
                <span className="text-apple-text">显示工具调用</span>
              </label>
            </div>
          </div>

          {/* 大纲树 */}
          <div className="flex-1 overflow-y-auto p-4">
            <OutlineTree 
              outline={outline} 
              currentSection={currentSection}
            />
          </div>
        </motion.div>

        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col">
          {/* 消息流区域 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {filteredMessages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-center h-full"
              >
                <Card className="p-8 text-center max-w-md">
                  <div className="w-16 h-16 bg-gradient-to-br from-apple-blue to-apple-purple rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Brain className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="text-xl font-semibold text-apple-text mb-2">
                    欢迎使用智能报告生成器
                  </h2>
                  <p className="text-apple-secondary mb-6">
                    输入研究主题，AI 将为您生成专业的深度研究报告
                  </p>
                  <div className="grid grid-cols-1 gap-2 text-sm text-apple-secondary">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-apple-blue rounded-full" />
                      支持交互式确认工具调用
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-apple-green rounded-full" />
                      实时显示生成进度
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-apple-orange rounded-full" />
                      层级化报告大纲展示
                    </div>
                  </div>
                </Card>
              </motion.div>
            ) : (
              <>
                {filteredMessages.map((message, index) => (
                  <StreamMessage
                    key={`${message.timestamp}-${index}`}
                    message={message}
                    onInterruptResponse={handleInterruptResponse}
                  />
                ))}
                <div ref={messagesEndRef} />
              </>
            )}

            {/* 待处理中断提示 */}
            {pendingInterrupts.size > 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="fixed top-4 right-4 z-50"
              >
                <Card className="p-4 border-apple-orange/30 bg-apple-orange/10">
                  <div className="flex items-center gap-2 text-apple-orange">
                    <Settings className="w-4 h-4" />
                    <span className="font-medium">
                      有 {pendingInterrupts.size} 个待处理的确认请求
                    </span>
                  </div>
                </Card>
              </motion.div>
            )}
          </div>

          {/* 输入区域 */}
          <ChatInput
            onSubmit={createTask}
            disabled={isGenerating}
            mode={settings.mode}
            onModeChange={(mode) => updateSettings({ mode })}
          />
        </div>
      </div>
    </div>
  );
}

export default App;