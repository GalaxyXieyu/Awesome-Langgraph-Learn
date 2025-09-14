import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, User, Settings, CheckCircle, XCircle, Edit3 } from 'lucide-react';
import { StreamMessage as StreamMessageType, InterruptResponse } from '../types';
import { getMessageTypeColor, getMessageTypeIcon, formatDuration } from '../utils/api';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Input } from './ui/Input';

interface StreamMessageProps {
  message: StreamMessageType;
  onInterruptResponse?: (interruptId: string, response: InterruptResponse) => void;
}

export const StreamMessage: React.FC<StreamMessageProps> = ({
  message,
  onInterruptResponse,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedArgs, setEditedArgs] = useState(JSON.stringify(message.args || {}, null, 2));

  const handleApprove = () => {
    if (message.interrupt_id && onInterruptResponse) {
      onInterruptResponse(message.interrupt_id, { approved: 'yes' });
    }
  };

  const handleReject = () => {
    if (message.interrupt_id && onInterruptResponse) {
      onInterruptResponse(message.interrupt_id, { approved: 'no' });
    }
  };

  const handleEdit = () => {
    try {
      const parsedArgs = JSON.parse(editedArgs);
      if (message.interrupt_id && onInterruptResponse) {
        onInterruptResponse(message.interrupt_id, { edit: parsedArgs });
      }
      setIsEditing(false);
    } catch (error) {
      alert('Invalid JSON format');
    }
  };

  const handleRespond = () => {
    if (message.interrupt_id && onInterruptResponse) {
      onInterruptResponse(message.interrupt_id, { response: 'Skip tool call' });
    }
  };

  const renderProgressBar = () => {
    if (message.progress !== undefined && message.message_type === 'step_progress') {
      return (
        <div className="mt-2">
          <div className="w-full bg-apple-gray-200 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${message.progress}%` }}
              transition={{ duration: 0.5 }}
              className="progress-bar h-2 rounded-full"
            />
          </div>
          <span className="text-xs text-apple-secondary mt-1 block">{message.progress}%</span>
        </div>
      );
    }
    return null;
  };

  const renderInterruptActions = () => {
    if (message.message_type !== 'interrupt_request' || !message.config) {
      return null;
    }

    return (
      <Card className="mt-4 p-4 border-apple-orange/30 bg-apple-orange/5">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-apple-orange font-medium">
            <Settings className="w-4 h-4" />
            需要确认工具调用
          </div>
          
          <div className="bg-apple-gray-100 rounded-lg p-3">
            <div className="text-sm font-medium text-apple-text mb-1">工具: {message.action}</div>
            <div className="text-xs text-apple-secondary">
              参数: {JSON.stringify(message.args, null, 2)}
            </div>
          </div>

          {isEditing ? (
            <div className="space-y-3">
              <Input
                value={editedArgs}
                onChange={(e) => setEditedArgs(e.target.value)}
                placeholder="编辑参数 (JSON 格式)"
                className="font-mono text-sm"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleEdit}>
                  确认修改
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setIsEditing(false)}>
                  取消
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {message.config.allow_accept && (
                <Button size="sm" onClick={handleApprove} className="bg-apple-green hover:bg-apple-green/90">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  允许 (yes)
                </Button>
              )}
              
              <Button size="sm" variant="destructive" onClick={handleReject}>
                <XCircle className="w-4 h-4 mr-1" />
                拒绝 (no)
              </Button>
              
              {message.config.allow_edit && (
                <Button size="sm" variant="secondary" onClick={() => setIsEditing(true)}>
                  <Edit3 className="w-4 h-4 mr-1" />
                  编辑 (edit)
                </Button>
              )}
              
              {message.config.allow_respond && (
                <Button size="sm" variant="ghost" onClick={handleRespond}>
                  跳过 (response)
                </Button>
              )}
            </div>
          )}
        </div>
      </Card>
    );
  };

  const renderMessageContent = () => {
    switch (message.message_type) {
      case 'thinking':
        return (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="thinking-container bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="text-sm font-medium text-blue-700">思考中...</span>
            </div>
            <div className="text-blue-800 text-sm leading-relaxed">
              {message.content}
            </div>
          </motion.div>
        );

      case 'reasoning':
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="reasoning-container bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-purple-600">🧠</span>
              <span className="text-sm font-medium text-purple-700">推理分析</span>
            </div>
            <div className="text-purple-800 text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
          </motion.div>
        );

      case 'content_streaming':
      case 'content':
        // 检测是否为JSON内容并进行格式化
        const isJsonContent = message.content.trim().startsWith('{') || 
                              message.content.trim().startsWith('[') ||
                              message.content.includes('```json');
        
        if (isJsonContent) {
          // 尝试解析JSON
          try {
            const jsonStr = message.content.replace(/```json\n?/g, '').replace(/\n?```/g, '').trim();
            if (jsonStr.startsWith('{') || jsonStr.startsWith('[')) {
              const parsedJson = JSON.parse(jsonStr);
              return (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="json-content bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-4"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-emerald-600">📋</span>
                    <span className="text-sm font-medium text-emerald-700">结构化数据</span>
                  </div>
                  <pre className="text-emerald-800 text-sm font-mono bg-white rounded-lg p-3 border border-emerald-100 overflow-x-auto">
                    {JSON.stringify(parsedJson, null, 2)}
                  </pre>
                </motion.div>
              );
            }
          } catch (e) {
            // JSON解析失败，显示为代码块
          }
          
          return (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="json-content bg-gray-50 border border-gray-200 rounded-lg p-3 font-mono text-sm"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-blue-600">💻</span>
                <span className="text-xs font-medium text-blue-700">代码内容</span>
              </div>
              <pre className="text-gray-800 whitespace-pre-wrap overflow-x-auto">
                {message.content}
              </pre>
            </motion.div>
          );
        }

        return (
          <span className="inline text-gray-800 whitespace-pre-wrap">
            {message.content}
          </span>
        );

      case 'tool_call':
        return (
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="tool-call bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-lg p-3"
          >
            <div className="flex items-center gap-2">
              <span className="text-orange-600">🔧</span>
              <span className="text-sm font-medium text-orange-700">工具调用</span>
              {message.tool_name && (
                <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                  {message.tool_name}
                </span>
              )}
            </div>
            <div className="text-orange-800 text-sm mt-1">
              {message.content}
            </div>
          </motion.div>
        );

      case 'tool_result':
        return (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="tool-result bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3"
          >
            <div className="flex items-center gap-2">
              <span className="text-green-600">✅</span>
              <span className="text-sm font-medium text-green-700">工具结果</span>
              {message.tool_name && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                  {message.tool_name}
                </span>
              )}
              {message.length && (
                <span className="text-xs text-green-600">
                  ({message.length} 字符)
                </span>
              )}
            </div>
            <div className="text-green-800 text-sm mt-1 max-h-32 overflow-y-auto">
              {message.content}
            </div>
          </motion.div>
        );

      case 'step_start':
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="step-start bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2">
              <span className="text-blue-600">🚀</span>
              <span className="text-sm font-medium text-blue-700">开始步骤</span>
            </div>
            <div className="text-blue-800 text-sm mt-1 font-medium">
              {message.content}
            </div>
          </motion.div>
        );

      case 'step_complete':
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="step-complete bg-gradient-to-r from-green-50 to-teal-50 border border-green-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2">
              <span className="text-green-600">✅</span>
              <span className="text-sm font-medium text-green-700">步骤完成</span>
              {message.duration && (
                <span className="text-xs text-green-600">
                  ({formatDuration(message.duration)})
                </span>
              )}
            </div>
            <div className="text-green-800 text-sm mt-1 font-medium">
              {message.content}
            </div>
          </motion.div>
        );

      case 'step_progress':
        // 特殊处理大纲生成节点
        if (message.node === 'outline_generation') {
          try {
            // 尝试解析content中的数据，处理Python字典格式
            let contentStr = message.content;
            // 将Python字典格式转换为JSON格式
            contentStr = contentStr.replace(/'/g, '"').replace(/None/g, 'null').replace(/True/g, 'true').replace(/False/g, 'false');
            const outlineData = JSON.parse(contentStr);
            return (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="outline-generation bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-emerald-600">📋</span>
                  <span className="text-sm font-medium text-emerald-700">正在生成大纲</span>
                  {message.progress !== undefined && (
                    <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full">
                      {message.progress}%
                    </span>
                  )}
                </div>

                {outlineData.title && (
                  <div className="mb-2">
                    <h3 className="text-emerald-900 font-semibold">{outlineData.title}</h3>
                  </div>
                )}

                {outlineData.executive_summary && (
                  <div className="mb-2">
                    <p className="text-emerald-800 text-sm">{outlineData.executive_summary}</p>
                  </div>
                )}

                {outlineData.sections && Array.isArray(outlineData.sections) && (
                  <div className="mt-3">
                    <div className="text-xs text-emerald-700 mb-2">章节结构：</div>
                    <div className="space-y-1">
                      {outlineData.sections.slice(0, 3).map((section: any, index: number) => (
                        <div key={section.id || index} className="text-xs text-emerald-800 pl-2 border-l-2 border-emerald-300">
                          {section.title}
                        </div>
                      ))}
                      {outlineData.sections.length > 3 && (
                        <div className="text-xs text-emerald-600 pl-2">
                          ...还有 {outlineData.sections.length - 3} 个章节
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {renderProgressBar()}
              </motion.div>
            );
          } catch (e) {
            // 如果解析失败，显示简单的大纲生成状态
            return (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="outline-generation bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-emerald-600">📋</span>
                  <span className="text-sm font-medium text-emerald-700">正在生成大纲</span>
                  {message.progress !== undefined && (
                    <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full">
                      {message.progress}%
                    </span>
                  )}
                </div>
                <div className="text-emerald-800 text-sm">
                  正在分析主题并构建报告结构...
                </div>
                {renderProgressBar()}
              </motion.div>
            );
          }
        }

        // 默认的进度显示
        return (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="step-progress bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-indigo-600">⏳</span>
              <span className="text-sm font-medium text-indigo-700">进度更新</span>
              {message.progress !== undefined && (
                <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full">
                  {message.progress}%
                </span>
              )}
            </div>
            <div className="text-indigo-800 text-sm leading-relaxed">
              {message.content}
            </div>
            {renderProgressBar()}
          </motion.div>
        );

      case 'search_result':
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="search-results bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-blue-600">🔍</span>
              <span className="text-sm font-medium text-blue-700">搜索结果</span>
              {message.query && (
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {message.query}
                </span>
              )}
            </div>
            
            {message.search_results && message.search_results.length > 0 ? (
              <div className="space-y-3">
                {message.search_results.slice(0, 3).map((result, index) => (
                  <motion.div
                    key={result.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="search-result-card bg-white rounded-lg p-3 border border-blue-100 hover:border-blue-200"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className="text-sm font-medium text-blue-900 line-clamp-2">
                        {result.title}
                      </h4>
                      {result.relevance_score && (
                        <span className="relevance-score text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded-full shrink-0">
                          {Math.round(result.relevance_score * 100)}%
                        </span>
                      )}
                    </div>
                    
                    <p className="text-xs text-blue-800 leading-relaxed line-clamp-3 mb-2">
                      {result.content}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      {result.url && (
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="search-link text-xs text-blue-600 hover:text-blue-800 underline truncate flex-1"
                        >
                          {result.url}
                        </a>
                      )}
                      <span className="text-xs text-blue-500 ml-2">
                        {result.source}
                      </span>
                    </div>
                  </motion.div>
                ))}
                
                {message.search_results.length > 3 && (
                  <div className="text-xs text-blue-600 text-center">
                    ...还有 {message.search_results.length - 3} 个结果
                  </div>
                )}
              </div>
            ) : (
              <div className="text-blue-800 text-sm">
                {message.content || '未找到相关搜索结果'}
              </div>
            )}
          </motion.div>
        );

      case 'chart_generation':
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="chart-generation bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="text-purple-600"
              >
                📊
              </motion.span>
              <span className="text-sm font-medium text-purple-700">正在生成图表</span>
              {message.chart_type && (
                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                  {message.chart_type}
                </span>
              )}
            </div>
            
            <div className="text-purple-800 text-sm leading-relaxed">
              {message.content}
            </div>
            
            {message.chart_config?.title && (
              <div className="mt-2 text-xs text-purple-600">
                标题: {message.chart_config.title}
              </div>
            )}
          </motion.div>
        );

      case 'chart_display':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="chart-display bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="text-emerald-600">📈</span>
              <span className="text-sm font-medium text-emerald-700">图表数据</span>
              {message.chart_config?.type && (
                <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full">
                  {message.chart_config.type}
                </span>
              )}
            </div>
            
            {message.chart_config?.title && (
              <h3 className="text-lg font-semibold text-emerald-900 mb-3 text-center">
                {message.chart_config.title}
              </h3>
            )}
            
            {message.chart_data && (
              <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, duration: 0.4 }}
                className="bg-white rounded-lg p-4 border border-emerald-100"
              >
                <div className="space-y-3">
                  {/* 数据预览 */}
                  {message.chart_data.labels && message.chart_data.values && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-emerald-700 mb-2">标签</div>
                        <div className="space-y-1">
                          {message.chart_data.labels.slice(0, 5).map((label, index) => (
                            <div key={index} className="data-entry text-xs text-emerald-800 bg-emerald-50 px-2 py-1 rounded">
                              {label}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-emerald-700 mb-2">数值</div>
                        <div className="space-y-1">
                          {message.chart_data.values.slice(0, 5).map((value, index) => (
                            <div key={index} className="data-entry text-xs text-emerald-800 bg-emerald-50 px-2 py-1 rounded text-right">
                              {typeof value === 'number' ? value.toLocaleString() : value}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* 图表配置信息 */}
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-emerald-100">
                    {message.chart_config?.x_label && (
                      <span className="config-tag text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                        X轴: {message.chart_config.x_label}
                      </span>
                    )}
                    {message.chart_config?.y_label && (
                      <span className="config-tag text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                        Y轴: {message.chart_config.y_label}
                      </span>
                    )}
                    {message.chart_config?.animation && (
                      <span className="config-tag text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                        动画: {message.chart_config.animation.duration}ms
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
            
            <div className="text-emerald-800 text-sm mt-3">
              {message.content}
            </div>
          </motion.div>
        );

      case 'error':
        return (
          <motion.div
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            className="error-message bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2">
              <span className="text-red-600">❌</span>
              <span className="text-sm font-medium text-red-700">错误</span>
              {message.error_type && (
                <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                  {message.error_type}
                </span>
              )}
            </div>
            <div className="text-red-800 text-sm mt-1">
              {message.content}
            </div>
          </motion.div>
        );

      case 'final_result':
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="final-result bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-300 rounded-lg p-6"
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-emerald-600 text-lg">🎉</span>
              <span className="text-lg font-bold text-emerald-700">最终结果</span>
            </div>
            <div className="text-emerald-800 leading-relaxed">
              {message.content}
            </div>
          </motion.div>
        );

      default:
        // 检测内容类型并进行相应处理
        const content = message.content || '';
        
        // 检测是否是JSON内容
        if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
          try {
            // 尝试解析JSON以验证格式
            const parsedJson = JSON.parse(content.trim());
            return (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="json-content bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-blue-600">📋</span>
                  <span className="text-sm font-medium text-blue-700">结构化数据</span>
                </div>
                <pre className="text-blue-800 text-sm font-mono bg-white rounded-lg p-3 border border-blue-100 overflow-x-auto">
                  {JSON.stringify(parsedJson, null, 2)}
                </pre>
              </motion.div>
            );
          } catch (e) {
            // 如果不是有效JSON，但看起来像JSON，显示为代码
            return (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="code-content bg-gray-50 border border-gray-200 rounded-lg p-3"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-gray-600">💻</span>
                  <span className="text-xs font-medium text-gray-700">代码内容</span>
                </div>
                <pre className="text-gray-800 text-sm font-mono whitespace-pre-wrap overflow-x-auto">
                  {content}
                </pre>
              </motion.div>
            );
          }
        }
        
        // 检测是否是代码块
        if (content.includes('```')) {
          return (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="code-block bg-gray-50 border border-gray-200 rounded-lg p-3"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-gray-600">💻</span>
                <span className="text-xs font-medium text-gray-700">代码块</span>
              </div>
              <pre className="text-gray-800 text-sm font-mono whitespace-pre-wrap overflow-x-auto">
                {content}
              </pre>
            </motion.div>
          );
        }
        
        // 默认文本内容
        return (
          <div className="default-message bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-gray-800 text-sm whitespace-pre-wrap">
              {content}
            </div>
          </div>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-4"
    >
      <Card className={`p-4 ${message.message_type === 'interrupt_request' ? 'border-apple-orange/30' : ''}`}>
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-apple-gray-100 flex items-center justify-center text-sm">
              {getMessageTypeIcon(message.message_type)}
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-sm font-medium ${getMessageTypeColor(message.message_type)}`}>
                {message.message_type ? message.message_type.replace('_', ' ').toUpperCase() : 'UNKNOWN'}
              </span>
              
              {message.agent && (
                <div className="flex items-center gap-1 text-xs text-apple-secondary">
                  <User className="w-3 h-3" />
                  {message.agent}
                </div>
              )}
              
              {message.duration !== undefined && (
                <div className="flex items-center gap-1 text-xs text-apple-secondary">
                  <Clock className="w-3 h-3" />
                  {formatDuration(message.duration)}
                </div>
              )}
            </div>
            
            <div className="message-content">
              {renderMessageContent()}
            </div>
          </div>
        </div>
        
        {renderInterruptActions()}
      </Card>
    </motion.div>
  );
};
