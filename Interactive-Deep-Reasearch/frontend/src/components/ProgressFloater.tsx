import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { StreamMessage } from '../types';

interface ProgressFloaterProps {
  latestProgress: StreamMessage | null;
}

export const ProgressFloater: React.FC<ProgressFloaterProps> = ({ latestProgress }) => {
  if (!latestProgress || latestProgress.message_type !== 'step_progress') {
    return null;
  }

  // 特殊处理大纲生成
  const isOutlineGeneration = latestProgress.node === 'outline_generation';

  return (
    <motion.div
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -50 }}
      className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-white shadow-lg border rounded-lg px-4 py-3 max-w-md ${
        isOutlineGeneration ? 'border-emerald-200' : 'border-gray-200'
      }`}
    >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className={isOutlineGeneration ? "text-emerald-600" : "text-indigo-600"}>
              {isOutlineGeneration ? "📋" : "⏳"}
            </span>
            <span className={`text-sm font-medium ${
              isOutlineGeneration ? "text-emerald-700" : "text-indigo-700"
            }`}>
              {isOutlineGeneration ? "正在生成大纲" : "进度更新"}
            </span>
            {latestProgress.progress !== undefined && (
              <span className={`text-xs px-2 py-1 rounded-full ${
                isOutlineGeneration
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-indigo-100 text-indigo-800"
              }`}>
                {latestProgress.progress}%
              </span>
            )}
          </div>
          {latestProgress.duration && (
            <span className="text-xs text-gray-500">
              {Math.round(latestProgress.duration)}s
            </span>
          )}
        </div>

        <div className="text-sm text-gray-700 mt-1 line-clamp-2">
          {isOutlineGeneration ? "正在分析主题并构建报告结构..." : latestProgress.content}
        </div>

        {latestProgress.progress !== undefined && (
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${latestProgress.progress}%` }}
                transition={{ duration: 0.5 }}
                className={`h-1.5 rounded-full ${
                  isOutlineGeneration ? "bg-emerald-500" : "bg-indigo-500"
                }`}
              />
            </div>
          </div>
        )}
      </motion.div>
  );
};
