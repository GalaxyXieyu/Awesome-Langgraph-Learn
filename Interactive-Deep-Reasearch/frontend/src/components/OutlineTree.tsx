import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ChevronDown, 
  ChevronRight, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Loader,
  Star
} from 'lucide-react';
import { ReportOutline, ReportSection, OutlineTreeProps } from '../types';
import { Card } from './ui/Card';
import { formatDuration } from '../utils/api';

export const OutlineTree: React.FC<OutlineTreeProps> = ({
  outline,
  currentSection,
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-apple-green" />;
      case 'in_progress':
        return <Loader className="w-4 h-4 text-apple-blue animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-apple-red" />;
      default:
        return <Clock className="w-4 h-4 text-apple-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'border-l-apple-green bg-apple-green/5';
      case 'in_progress':
        return 'border-l-apple-blue bg-apple-blue/5';
      case 'failed':
        return 'border-l-apple-red bg-apple-red/5';
      default:
        return 'border-l-apple-gray-300 bg-apple-gray-50/50';
    }
  };

  const renderSection = (section: ReportSection, index: number) => {
    const isExpanded = expandedSections.has(section.id);
    const isCurrentSection = currentSection === section.id;

    return (
      <motion.div
        key={section.id}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1 }}
        className="mb-3"
      >
        <Card 
          className={`p-4 border-l-4 ${getStatusColor(section.status)} ${
            isCurrentSection ? 'ring-2 ring-apple-blue/20' : ''
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <button
                onClick={() => toggleSection(section.id)}
                className="flex items-center gap-2 text-left w-full group"
              >
                <div className="flex-shrink-0">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-apple-secondary group-hover:text-apple-text transition-colors" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-apple-secondary group-hover:text-apple-text transition-colors" />
                  )}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-apple-text group-hover:text-apple-blue transition-colors">
                      {section.title}
                    </span>
                    {section.priority >= 4 && (
                      <Star className="w-3 h-3 text-apple-orange fill-current" />
                    )}
                  </div>
                  <p className="text-sm text-apple-secondary mt-1 line-clamp-2">
                    {section.description}
                  </p>
                </div>
              </button>
            </div>
            
            <div className="flex items-center gap-2 ml-4">
              {getStatusIcon(section.status)}
              {section.word_count > 0 && (
                <span className="text-xs text-apple-secondary bg-apple-gray-100 px-2 py-1 rounded-full">
                  {section.word_count} 字
                </span>
              )}
            </div>
          </div>

          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-4 space-y-3"
            >
                {/* 关键要点 */}
                {section.key_points.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-apple-text mb-2">关键要点:</h4>
                    <ul className="space-y-1">
                      {section.key_points.map((point, idx) => (
                        <li key={idx} className="text-sm text-apple-secondary flex items-start gap-2">
                          <span className="w-1 h-1 bg-apple-blue rounded-full mt-2 flex-shrink-0" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 研究查询 */}
                {section.research_queries.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-apple-text mb-2">研究方向:</h4>
                    <div className="flex flex-wrap gap-2">
                      {section.research_queries.map((query, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-apple-blue/10 text-apple-blue px-2 py-1 rounded-full"
                        >
                          {query}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 章节内容预览 */}
                {section.content && (
                  <div>
                    <h4 className="text-sm font-medium text-apple-text mb-2">内容预览:</h4>
                    <div className="text-sm text-apple-secondary bg-apple-gray-50 p-3 rounded-lg max-h-32 overflow-y-auto">
                      {section.content.length > 200 
                        ? `${section.content.substring(0, 200)}...` 
                        : section.content
                      }
                    </div>
                  </div>
                )}
              </motion.div>
            )}
        </Card>
      </motion.div>
    );
  };

  if (!outline) {
    return (
      <Card className="p-6 text-center">
        <FileText className="w-12 h-12 text-apple-gray-400 mx-auto mb-4" />
        <p className="text-apple-secondary">等待生成报告大纲...</p>
      </Card>
    );
  }

  const completedSections = outline.sections.filter(s => s.status === 'completed').length;
  const totalSections = outline.sections.length;
  const progress = totalSections > 0 ? (completedSections / totalSections) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* 大纲头部信息 */}
      <Card className="p-6">
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-apple-text mb-2">
              {outline.title}
            </h2>
            <p className="text-sm text-apple-secondary">
              {outline.executive_summary}
            </p>
          </div>

          {/* 进度指示器 */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-apple-secondary">完成进度</span>
              <span className="text-apple-text font-medium">
                {completedSections}/{totalSections} 章节
              </span>
            </div>
            <div className="w-full bg-apple-gray-200 rounded-full h-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="bg-gradient-to-r from-apple-blue to-apple-green h-2 rounded-full"
              />
            </div>
          </div>

          {/* 元信息 */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-apple-secondary">目标读者:</span>
              <span className="text-apple-text ml-2">{outline.target_audience}</span>
            </div>
            <div>
              <span className="text-apple-secondary">预估字数:</span>
              <span className="text-apple-text ml-2">{outline.estimated_length.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-apple-secondary">研究方法:</span>
              <span className="text-apple-text ml-2">{outline.methodology}</span>
            </div>
            <div>
              <span className="text-apple-secondary">创建时间:</span>
              <span className="text-apple-text ml-2">
                {new Date(outline.creation_time * 1000).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* 章节列表 */}
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-apple-text px-2">报告章节</h3>
        {outline.sections.map((section, index) => renderSection(section, index))}
      </div>
    </div>
  );
};
