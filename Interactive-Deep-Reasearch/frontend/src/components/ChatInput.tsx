import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Settings, Zap, Users, Brain } from 'lucide-react';
import { CreateTaskRequest, ChatInputProps } from '../types';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  disabled = false,
  mode,
  onModeChange,
}) => {
  const [topic, setTopic] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<Partial<CreateTaskRequest>>({
    user_id: 'user',
    report_type: 'research',
    target_audience: '专业人士',
    depth_level: 'medium',
    max_sections: 3,
    target_length: 2000,
    language: 'zh',
    style: 'professional',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    const request: CreateTaskRequest = {
      topic: topic.trim(),
      mode,
      ...settings,
    };

    onSubmit(topic.trim(), request);
    setTopic('');
  };

  const modeConfig = {
    interactive: {
      icon: Users,
      label: '交互模式',
      description: '需要用户确认每个步骤',
      color: 'text-apple-blue',
      bgColor: 'bg-apple-blue/10',
    },
    copilot: {
      icon: Zap,
      label: '副驾驶模式',
      description: '自动执行所有步骤',
      color: 'text-apple-green',
      bgColor: 'bg-apple-green/10',
    },
    guided: {
      icon: Brain,
      label: '引导模式',
      description: '提供建议并需要确认',
      color: 'text-apple-orange',
      bgColor: 'bg-apple-orange/10',
    },
  };

  const currentModeConfig = modeConfig[mode];
  const CurrentModeIcon = currentModeConfig.icon;

  return (
    <Card className="p-6 border-t-0 rounded-t-none bg-white/95 backdrop-blur-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 模式选择器 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${currentModeConfig.bgColor}`}>
              <CurrentModeIcon className={`w-4 h-4 ${currentModeConfig.color}`} />
            </div>
            <div>
              <div className="text-sm font-medium text-apple-text">
                {currentModeConfig.label}
              </div>
              <div className="text-xs text-apple-secondary">
                {currentModeConfig.description}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* 模式切换按钮 */}
            <div className="flex rounded-lg bg-apple-gray-100 p-1">
              {(Object.keys(modeConfig) as Array<keyof typeof modeConfig>).map((modeKey) => {
                const config = modeConfig[modeKey];
                const Icon = config.icon;
                const isActive = mode === modeKey;
                
                return (
                  <motion.button
                    key={modeKey}
                    type="button"
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onModeChange(modeKey)}
                    className={`p-2 rounded-md transition-all duration-200 ${
                      isActive 
                        ? 'bg-white shadow-sm text-apple-text' 
                        : 'text-apple-secondary hover:text-apple-text'
                    }`}
                    title={config.label}
                  >
                    <Icon className="w-4 h-4" />
                  </motion.button>
                );
              })}
            </div>
            
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
              className="p-2"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* 高级设置 */}
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-2 gap-4 p-4 bg-apple-gray-50 rounded-lg"
          >
            <Input
              label="报告类型"
              value={settings.report_type}
              onChange={(e) => setSettings({...settings, report_type: e.target.value})}
              placeholder="research, analysis, market, technical"
            />
            <Input
              label="目标读者"
              value={settings.target_audience}
              onChange={(e) => setSettings({...settings, target_audience: e.target.value})}
              placeholder="专业人士, 普通大众, 技术专家"
            />
            <Input
              label="最大章节数"
              type="number"
              value={settings.max_sections}
              onChange={(e) => setSettings({...settings, max_sections: parseInt(e.target.value)})}
              min="1"
              max="10"
            />
            <Input
              label="目标字数"
              type="number"
              value={settings.target_length}
              onChange={(e) => setSettings({...settings, target_length: parseInt(e.target.value)})}
              min="500"
              max="10000"
              step="500"
            />
          </motion.div>
        )}

        {/* 主输入区域 */}
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="输入研究主题，例如：人工智能发展趋势"
              disabled={disabled}
              className="text-base"
            />
          </div>
          <Button
            type="submit"
            disabled={disabled || !topic.trim()}
            isLoading={disabled}
            className="px-6"
          >
            <Send className="w-4 h-4 mr-2" />
            生成报告
          </Button>
        </div>

        {/* 示例提示 */}
        <div className="flex flex-wrap gap-2">
          {[
            '区块链技术发展现状',
            '可持续能源解决方案',
            '远程工作趋势分析',
            '数字化转型策略',
          ].map((example) => (
            <motion.button
              key={example}
              type="button"
              whileTap={{ scale: 0.95 }}
              onClick={() => setTopic(example)}
              className="px-3 py-1 text-xs text-apple-secondary hover:text-apple-text bg-apple-gray-100 hover:bg-apple-gray-200 rounded-full transition-colors"
              disabled={disabled}
            >
              {example}
            </motion.button>
          ))}
        </div>
      </form>
    </Card>
  );
};
