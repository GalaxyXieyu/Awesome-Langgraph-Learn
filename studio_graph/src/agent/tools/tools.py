"""
工具系统模块
为多智能体系统提供真实、强大的工具集合
"""

import os
import re
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@tool
def calculator(expression: str) -> str:
    """
    计算器工具
    支持基本的数学运算

    Args:
        expression: 数学表达式，如 "2+3*4"

    Returns:
        计算结果字符串
    """
    try:
        # 安全的数学表达式计算
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression)
        return f"🔢 计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"


@tool
def web_search(query: str, max_results: int = 5, search_depth: str = "basic") -> str:
    """
    网络搜索工具，使用Tavily API进行真实搜索

    Args:
        query: 搜索查询词
        max_results: 最大结果数量 (1-10)
        search_depth: 搜索深度 ("basic" 或 "advanced")

    Returns:
        格式化的搜索结果字符串
    """
    try:
        # 检查API密钥
        # 使用真实的Tavily搜索
        # 设置环境变量或直接传递API密钥
        import os
        os.environ["TAVILY_API_KEY"] = "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"

        search_tool = TavilySearch(
            max_results=min(max_results, 10),
            search_depth=search_depth
        )

        search_response = search_tool.invoke(query)

        # 提取实际的搜索结果
        if not search_response or "results" not in search_response:
            return f"未找到关于'{query}'的相关信息"

        results = search_response["results"]
        if not results:
            return f"未找到关于'{query}'的相关信息"

        # 格式化结果
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            content = result.get("content", "无内容")
            url = result.get("url", "")

            formatted_result = f"""
{i}. **{title}**
   内容：{content[:200]}{'...' if len(content) > 200 else ''}
   来源：{url}
"""
            formatted_results.append(formatted_result)

        return f"🔍 搜索结果 (关键词: {query}):\n" + "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return f"搜索失败：{str(e)}"


@tool
def content_writer(topic: str, style: str = "formal", length: str = "medium") -> str:
    """
    内容写作工具
    根据主题和要求生成内容

    Args:
        topic: 写作主题
        style: 写作风格 ("formal", "casual", "academic", "creative")
        length: 内容长度 ("short", "medium", "long")

    Returns:
        生成的内容
    """
    try:
        # 长度映射
        length_map = {
            "short": 100,
            "medium": 300,
            "long": 500
        }

        target_length = length_map.get(length, 300)

        # 风格模板
        style_templates = {
            "formal": {
                "intro": f"关于{topic}，我们需要从专业角度进行深入分析。",
                "body": f"{topic}在当前环境下具有重要意义。通过系统性的研究和分析，我们可以得出以下结论：",
                "conclusion": f"综上所述，{topic}的重要性不言而喻，值得我们持续关注和深入研究。"
            },
            "casual": {
                "intro": f"说到{topic}，这真是个有趣的话题！",
                "body": f"让我们来聊聊{topic}吧。从我的观察来看，这个领域有很多值得探讨的地方。",
                "conclusion": f"总的来说，{topic}确实很有意思，希望大家也能从中获得启发。"
            },
            "academic": {
                "intro": f"本文旨在对{topic}进行系统性的学术研究和分析。",
                "body": f"通过文献综述和实证分析，本研究发现{topic}具有以下特征和规律：",
                "conclusion": f"本研究对{topic}的分析为相关领域的理论发展和实践应用提供了重要参考。"
            },
            "creative": {
                "intro": f"想象一下，如果{topic}是一个故事的开始...",
                "body": f"在{topic}的世界里，充满了无限的可能性和创意。",
                "conclusion": f"这就是{topic}的魅力所在——它激发我们的想象力，让我们看到更广阔的世界。"
            }
        }

        template = style_templates.get(style, style_templates["formal"])

        # 构建内容
        content_parts = [template["intro"]]

        if length in ["medium", "long"]:
            content_parts.append(template["body"])

            # 添加具体内容点
            if "技术" in topic or "科技" in topic:
                content_parts.append("从技术发展的角度来看，创新是推动进步的核心动力。")
            elif "教育" in topic:
                content_parts.append("教育的本质在于培养人的全面发展，这需要我们不断探索新的教学方法。")
            elif "经济" in topic or "商业" in topic:
                content_parts.append("市场环境的变化要求我们具备敏锐的商业洞察力和适应能力。")
            else:
                content_parts.append(f"深入了解{topic}的各个方面，有助于我们形成更全面的认识。")

        if length == "long":
            content_parts.append(f"进一步分析{topic}的发展趋势，我们可以预见其未来的重要作用。")
            content_parts.append("这种发展不仅影响当前的实践，也为未来的创新奠定了基础。")

        content_parts.append(template["conclusion"])

        final_content = "\n\n".join(content_parts)

        return f"📝 内容生成结果：\n\n{final_content}"

    except Exception as e:
        logger.error(f"内容生成失败: {str(e)}")
        return f"内容生成失败：{str(e)}"


@tool
def text_analyzer(text: str, analysis_type: str = "comprehensive") -> str:
    """
    文本分析工具
    支持情感分析、关键词提取、可读性评估等

    Args:
        text: 要分析的文本
        analysis_type: 分析类型 ("basic", "sentiment", "keywords", "comprehensive")

    Returns:
        详细的文本分析结果
    """
    if not text or not text.strip():
        return "错误：文本不能为空"

    try:
        # 基础统计
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len([s for s in re.split(r'[.!?。！？]', text) if s.strip()])
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])

        # 平均词长和句长
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # 情感分析（基于关键词）
        positive_words = [
            "好", "棒", "优秀", "成功", "喜欢", "满意", "高兴", "快乐", "美好", "完美",
            "excellent", "good", "great", "amazing", "wonderful", "perfect", "love", "like"
        ]
        negative_words = [
            "坏", "差", "失败", "讨厌", "不满", "糟糕", "痛苦", "难过", "愤怒", "失望",
            "bad", "terrible", "awful", "hate", "dislike", "angry", "sad", "disappointed"
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        # 情感倾向计算
        if positive_count > negative_count:
            sentiment = "积极"
            sentiment_score = min((positive_count - negative_count) / word_count * 100, 100)
        elif negative_count > positive_count:
            sentiment = "消极"
            sentiment_score = min((negative_count - positive_count) / word_count * 100, 100)
        else:
            sentiment = "中性"
            sentiment_score = 0

        # 关键词提取
        stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"
        }

        words_clean = [word.lower().strip('.,!?;:"()[]{}') for word in words
                      if word.lower().strip('.,!?;:"()[]{}') not in stop_words and len(word) > 2]

        word_freq = {}
        for word in words_clean:
            word_freq[word] = word_freq.get(word, 0) + 1

        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

        # 根据分析类型返回结果
        if analysis_type == "basic":
            return f"""
📊 基础文本分析：
- 字符数：{char_count}
- 词数：{word_count}
- 句子数：{sentence_count}
- 段落数：{paragraph_count}
"""

        elif analysis_type == "sentiment":
            return f"""
😊 情感分析：
- 情感倾向：{sentiment}
- 情感强度：{sentiment_score:.1f}%
- 积极词汇：{positive_count}个
- 消极词汇：{negative_count}个
"""

        elif analysis_type == "keywords":
            keywords_str = ", ".join([f"{word}({count})" for word, count in keywords])
            return f"""
🔑 关键词分析：
- 高频关键词：{keywords_str}
- 词汇丰富度：{len(set(words_clean))/len(words_clean)*100:.1f}%
"""

        else:  # comprehensive
            keywords_str = ", ".join([f"{word}({count})" for word, count in keywords])

            result = f"""
📈 综合文本分析报告：

📊 基础统计：
- 字符数：{char_count}
- 词数：{word_count}
- 句子数：{sentence_count}
- 段落数：{paragraph_count}
- 平均词长：{avg_word_length:.1f}字符
- 平均句长：{avg_sentence_length:.1f}词

😊 情感分析：
- 情感倾向：{sentiment}
- 情感强度：{sentiment_score:.1f}%
- 积极词汇：{positive_count}个
- 消极词汇：{negative_count}个

🔑 关键词分析：
- 高频关键词：{keywords_str}
- 词汇丰富度：{len(set(words_clean))/len(words_clean)*100:.1f}%

💡 分析建议：
"""

            # 添加改进建议
            suggestions = []
            if avg_sentence_length > 20:
                suggestions.append("- 句子较长，建议适当分割以提高可读性")
            if sentiment_score < 10 and sentiment == "中性":
                suggestions.append("- 文本情感较为平淡，可考虑增加情感色彩")
            if len(set(words_clean))/len(words_clean) < 0.5:
                suggestions.append("- 词汇重复度较高，建议增加词汇多样性")

            if suggestions:
                result += "\n".join(suggestions)
            else:
                result += "- 文本质量良好，无明显改进建议"

            return result.strip()

    except Exception as e:
        logger.error(f"文本分析失败: {str(e)}")
        return f"文本分析失败：{str(e)}"


# ============================================================================
# 工具集合函数
# ============================================================================

def get_search_tools() -> List:
    """获取搜索相关工具"""
    return [web_search]


def get_analysis_tools() -> List:
    """获取分析相关工具"""
    return [text_analyzer, calculator]


def get_writing_tools() -> List:
    """获取写作相关工具"""
    return [content_writer]


def get_all_tools() -> List:
    """获取所有工具"""
    return [
        web_search,
        text_analyzer,
        content_writer,
        calculator
    ]


if __name__ == "__main__":
    # 测试工具
    print("=== 工具测试 ===")
    print(web_search.invoke({"query": "Python"}))
    print(text_analyzer.invoke({"text": "这是一个很好的产品，我很满意！"}))
    print(content_writer.invoke({"topic": "人工智能", "style": "formal", "length": "medium"}))
    print(calculator.invoke({"expression": "2+3*4"}))