"""
通用工具集合
"""

import time
import uuid
from typing import Dict, Any
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def content_analyzer(text: str) -> Dict[str, Any]:
    """内容分析工具"""
    try:
        if not text or len(text.strip()) < 10:
            return {"error": "文本内容过短"}
        
        word_count = len(text.replace(" ", ""))
        sentence_count = len([s for s in text.split("。") if s.strip()])
        
        # 简单关键词提取
        stop_words = {"的", "是", "在", "有", "和", "与", "或", "但", "而", "了", "着", "过"}
        words = [w for w in text if w not in stop_words and len(w) > 1]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "keywords": [{"word": word, "frequency": freq} for word, freq in top_keywords]
        }
        
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        return {"error": f"分析失败: {str(e)}"}


@tool  
def data_formatter(data: Dict[str, Any], format_type: str = "summary") -> str:
    """数据格式化工具"""
    try:
        if format_type == "summary":
            # 生成摘要格式
            summary_parts = []
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    summary_parts.append(f"{key}: {value}")
                elif isinstance(value, list) and len(value) > 0:
                    summary_parts.append(f"{key}: {len(value)}项")
            return " | ".join(summary_parts)
        
        elif format_type == "detailed":
            # 生成详细格式
            result = []
            for key, value in data.items():
                result.append(f"**{key}**: {value}")
            return "\n".join(result)
        
        else:
            return str(data)
            
    except Exception as e:
        logger.error(f"格式化失败: {str(e)}")
        return f"格式化失败: {str(e)}"


# 导出工具列表
COMMON_TOOLS = [
    content_analyzer,
    data_formatter
]