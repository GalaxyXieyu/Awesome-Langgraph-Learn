"""
LangGraph智能写作助手 - 工具模块
包含Tavily搜索工具和其他写作相关工具
"""

import os
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
# 移除向量数据库依赖，使用简单的关键词匹配
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --#DEBUG#--
# 调试模式标记，用于开发阶段的临时代码
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
# --#DEBUG#--


@tool
def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    使用Tavily进行联网搜索

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数量

    Returns:
        搜索结果列表，包含标题、URL、摘要等信息
    """
    try:
        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 搜索查询: {query}")
        # --#DEBUG#--
        
        # 创建Tavily搜索工具
        search_tool = TavilySearchResults(
            tavily_api_key="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",
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )

        # 执行搜索
        results = search_tool.invoke({"query": query})

        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 搜索结果数量: {len(results) if isinstance(results, list) else 1}")
        # --#DEBUG#--

        # 格式化结果
        if isinstance(results, list):
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                    "score": result.get("score", 0)
                })
            return formatted_results
        else:
            return [{"title": "搜索结果", "content": str(results)}]

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return [{"error": f"搜索失败: {str(e)}"}]


@tool
def validate_outline(outline: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证文章大纲的完整性和合理性

    Args:
        outline: 文章大纲字典

    Returns:
        验证结果，包含是否有效和建议
    """
    try:
        validation_result = {
            "is_valid": True,
            "suggestions": [],
            "score": 0
        }

        # 检查必要字段
        required_fields = ["title", "sections"]
        for field in required_fields:
            if field not in outline:
                validation_result["is_valid"] = False
                validation_result["suggestions"].append(f"缺少必要字段: {field}")

        # 检查章节数量
        if "sections" in outline:
            sections = outline["sections"]
            if len(sections) < 2:
                validation_result["suggestions"].append("建议至少包含2个章节")
                validation_result["score"] -= 10
            elif len(sections) > 8:
                validation_result["suggestions"].append("章节数量过多，建议控制在8个以内")
                validation_result["score"] -= 5
            else:
                validation_result["score"] += 20

        # 检查标题长度
        if "title" in outline:
            title_length = len(outline["title"])
            if title_length < 5:
                validation_result["suggestions"].append("标题过短，建议至少5个字符")
                validation_result["score"] -= 5
            elif title_length > 50:
                validation_result["suggestions"].append("标题过长，建议控制在50个字符以内")
                validation_result["score"] -= 5
            else:
                validation_result["score"] += 10

        # 计算最终分数
        validation_result["score"] = max(0, min(100, validation_result["score"] + 70))

        return validation_result

    except Exception as e:
        logger.error(f"大纲验证失败: {str(e)}")
        return {
            "is_valid": False,
            "suggestions": [f"验证过程出错: {str(e)}"],
            "score": 0
        }


@tool
def format_article(content: str, style: str = "formal") -> Dict[str, Any]:
    """
    格式化文章内容

    Args:
        content: 原始文章内容
        style: 格式化风格 (formal/casual/academic)

    Returns:
        格式化后的文章信息
    """
    try:
        # 基本统计
        word_count = len(content.replace(" ", ""))
        paragraph_count = len([p for p in content.split("\n\n") if p.strip()])

        # 根据风格调整格式
        if style == "academic":
            # 学术风格：添加更多的段落分隔
            formatted_content = content.replace("\n", "\n\n")
        elif style == "casual":
            # 随意风格：保持原有格式
            formatted_content = content
        else:
            # 正式风格：标准格式化
            formatted_content = content.replace("\n\n\n", "\n\n")

        return {
            "formatted_content": formatted_content,
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "style": style,
            "reading_time": max(1, word_count // 200)  # 估算阅读时间（分钟）
        }

    except Exception as e:
        logger.error(f"文章格式化失败: {str(e)}")
        return {
            "formatted_content": content,
            "word_count": 0,
            "paragraph_count": 0,
            "style": style,
            "reading_time": 0,
            "error": str(e)
        }


# 全局变量存储多个知识库
_knowledge_bases = {}
_available_knowledge_bases = []

def load_knowledge_bases():
    """
    加载多个知识库文件
    从JSON文件中加载不同领域的知识库
    """
    global _knowledge_bases, _available_knowledge_bases

    if _knowledge_bases:
        return _knowledge_bases

    try:
        import json
        import os

        # 知识库文件列表
        kb_files = [
            "knowledge_bases/python_advanced.json",
            "knowledge_bases/web_development.json",
            "knowledge_bases/data_science.json",
            "knowledge_bases/system_design.json"
        ]

        for kb_file in kb_files:
            if os.path.exists(kb_file):
                try:
                    with open(kb_file, 'r', encoding='utf-8') as f:
                        kb_data = json.load(f)
                        kb_id = kb_data["id"]
                        _knowledge_bases[kb_id] = kb_data
                        _available_knowledge_bases.append({
                            "id": kb_id,
                            "name": kb_data["name"],
                            "description": kb_data["description"],
                            "category": kb_data["category"],
                            "document_count": len(kb_data["documents"])
                        })
                except Exception as e:
                    logger.warning(f"加载知识库文件 {kb_file} 失败: {e}")
            else:
                logger.warning(f"知识库文件不存在: {kb_file}")

        # 如果没有加载到任何知识库，创建默认的简单知识库
        if not _knowledge_bases:
            _knowledge_bases["default"] = {
                "id": "default",
                "name": "默认Python知识库",
                "description": "基础Python编程知识",
                "category": "编程语言",
                "documents": [
                    {
                        "id": "python_basics",
                        "title": "Python基础知识",
                        "content": "Python是一种高级编程语言，具有简洁的语法和强大的功能。",
                        "keywords": ["Python", "编程", "语法"],
                        "difficulty": "beginner"
                    }
                ]
            }
            _available_knowledge_bases.append({
                "id": "default",
                "name": "默认Python知识库",
                "description": "基础Python编程知识",
                "category": "编程语言",
                "document_count": 1
            })

        logger.info(f"成功加载 {len(_knowledge_bases)} 个知识库")
        return _knowledge_bases

    except Exception as e:
        logger.error(f"加载知识库失败: {str(e)}")
        return {}


@tool
def get_available_knowledge_bases() -> List[Dict[str, Any]]:
    """
    获取可用的知识库列表
    返回所有可用知识库的基本信息

    Returns:
        知识库列表
    """
    try:
        load_knowledge_bases()  # 确保知识库已加载
        return _available_knowledge_bases
    except Exception as e:
        logger.error(f"获取知识库列表失败: {str(e)}")
        return [{"error": f"获取知识库列表失败: {str(e)}"}]


@tool
def search_knowledge_base(query: str, knowledge_base_ids: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    在指定的知识库中搜索内容
    支持多知识库选择性搜索

    Args:
        query: 搜索查询
        knowledge_base_ids: 要搜索的知识库ID列表
        top_k: 每个知识库返回的最大结果数

    Returns:
        搜索结果列表
    """
    try:
        load_knowledge_bases()  # 确保知识库已加载

        if not knowledge_base_ids:
            return [{"error": "未指定要搜索的知识库"}]

        all_results = []
        query_lower = query.lower()
        query_words = query_lower.split()

        for kb_id in knowledge_base_ids:
            if kb_id not in _knowledge_bases:
                all_results.append({
                    "error": f"知识库 '{kb_id}' 不存在",
                    "knowledge_base_id": kb_id
                })
                continue

            kb_data = _knowledge_bases[kb_id]
            kb_results = []

            # 搜索该知识库中的文档
            for doc in kb_data.get("documents", []):
                score = 0
                title = doc.get("title", "")
                content = doc.get("content", "")
                keywords = doc.get("keywords", [])

                # 标题匹配（权重最高）
                if any(word in title.lower() for word in query_words):
                    score += 10

                # 关键词匹配
                for keyword in keywords:
                    if any(word in keyword.lower() for word in query_words):
                        score += 5
                    if keyword.lower() in query_lower:
                        score += 3

                # 内容匹配
                for word in query_words:
                    if word in content.lower():
                        score += 2

                if score > 0:
                    kb_results.append({
                        "document_id": doc.get("id", ""),
                        "title": title,
                        "content": content,
                        "keywords": keywords,
                        "knowledge_base_id": kb_id,
                        "knowledge_base_name": kb_data.get("name", ""),
                        "relevance_score": score,
                        "summary": content[:100] + "..." if len(content) > 100 else content,
                        "difficulty": doc.get("difficulty", "unknown")
                    })

            # 按分数排序并取前top_k个
            kb_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            all_results.extend(kb_results[:top_k])

        # 按总分数排序
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # --#DEBUG#--
        if DEBUG_MODE:
            print(f"[DEBUG] 多知识库搜索: {query}, 知识库: {knowledge_base_ids}, 返回 {len(all_results)} 个结果")
        # --#DEBUG#--

        return all_results

    except Exception as e:
        logger.error(f"知识库搜索失败: {str(e)}")
        return [{"error": f"知识库搜索失败: {str(e)}"}]


# 为了兼容性，保留原有的函数
def initialize_keyword_knowledge_base():
    """兼容性函数"""
    load_knowledge_bases()
    return _knowledge_bases


@tool
def keyword_knowledge_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    基于关键词的知识库检索工具 (兼容性函数)
    默认搜索所有知识库

    Args:
        query: 检索查询
        top_k: 返回的最相关文档数量

    Returns:
        检索结果列表
    """
    try:
        load_knowledge_bases()
        all_kb_ids = list(_knowledge_bases.keys())
        return search_knowledge_base.invoke({
            "query": query,
            "knowledge_base_ids": all_kb_ids,
            "top_k": top_k
        })
    except Exception as e:
        logger.error(f"关键词检索失败: {str(e)}")
        return [{"error": f"关键词检索失败: {str(e)}"}]


# 为了兼容性，创建一个别名
rag_knowledge_search = keyword_knowledge_search


@tool
def hybrid_search(query: str, use_rag: bool = True, use_web: bool = True) -> Dict[str, Any]:
    """
    混合搜索工具
    结合RAG知识库检索和网络搜索

    Args:
        query: 搜索查询
        use_rag: 是否使用RAG检索
        use_web: 是否使用网络搜索

    Returns:
        混合搜索结果
    """
    try:
        results = {
            "query": query,
            "rag_results": [],
            "web_results": [],
            "combined_summary": ""
        }

        # RAG检索
        if use_rag:
            rag_results = rag_knowledge_search.invoke({"query": query, "top_k": 3})
            results["rag_results"] = rag_results

        # 网络搜索
        if use_web:
            web_results = tavily_search.invoke({"query": query, "max_results": 3})
            results["web_results"] = web_results

        # 生成综合摘要
        rag_content = " ".join([r.get("content", "") for r in results["rag_results"] if "content" in r])
        web_content = " ".join([r.get("snippet", "") for r in results["web_results"] if "snippet" in r])

        if rag_content or web_content:
            results["combined_summary"] = f"知识库内容: {rag_content[:200]}... 网络内容: {web_content[:200]}..."

        return results

    except Exception as e:
        logger.error(f"混合搜索失败: {str(e)}")
        return {"error": f"混合搜索失败: {str(e)}"}


@tool
def content_analyzer(text: str) -> Dict[str, Any]:
    """
    内容分析工具
    分析文本的各种特征和质量指标

    Args:
        text: 要分析的文本

    Returns:
        分析结果字典
    """
    try:
        if not text or not isinstance(text, str):
            return {"error": "无效的文本输入"}

        # 基本统计
        word_count = len(text.replace(" ", ""))  # 中文字符数
        sentence_count = len([s for s in text.split("。") if s.strip()])
        paragraph_count = len([p for p in text.split("\n\n") if p.strip()])

        # 关键词提取（简单版本）
        common_words = ["的", "是", "在", "有", "和", "与", "或", "但", "而", "了", "着", "过"]
        words = [w for w in text if w not in common_words and len(w) > 1]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 获取前5个高频词
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

        # 可读性评估（简单版本）
        avg_sentence_length = word_count / max(sentence_count, 1)
        readability_score = 100 - (avg_sentence_length * 2)  # 简化的可读性分数
        readability_score = max(0, min(100, readability_score))

        # 内容质量评估
        quality_indicators = {
            "has_structure": paragraph_count > 1,
            "appropriate_length": 100 <= word_count <= 2000,
            "good_readability": readability_score > 60,
            "keyword_diversity": len(top_keywords) >= 3
        }

        quality_score = sum(quality_indicators.values()) / len(quality_indicators) * 100

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "top_keywords": [{"word": word, "frequency": freq} for word, freq in top_keywords],
            "readability_score": round(readability_score, 1),
            "quality_score": round(quality_score, 1),
            "quality_indicators": quality_indicators,
            "suggestions": generate_content_suggestions(quality_indicators, word_count)
        }

    except Exception as e:
        logger.error(f"内容分析失败: {str(e)}")
        return {"error": f"内容分析失败: {str(e)}"}


def generate_content_suggestions(quality_indicators: Dict[str, bool], word_count: int) -> List[str]:
    """生成内容改进建议"""
    suggestions = []

    if not quality_indicators["has_structure"]:
        suggestions.append("建议增加段落分隔，提高文章结构性")

    if not quality_indicators["appropriate_length"]:
        if word_count < 100:
            suggestions.append("文章内容较短，建议增加更多细节和例子")
        elif word_count > 2000:
            suggestions.append("文章内容较长，建议精简或分段处理")

    if not quality_indicators["good_readability"]:
        suggestions.append("句子较长，建议使用更简洁的表达方式")

    if not quality_indicators["keyword_diversity"]:
        suggestions.append("关键词多样性不足，建议丰富词汇使用")

    if not suggestions:
        suggestions.append("内容质量良好，继续保持！")

    return suggestions


@tool
def topic_expander(topic: str, expansion_type: str = "related") -> Dict[str, Any]:
    """
    主题扩展工具
    根据给定主题生成相关的扩展内容和建议

    Args:
        topic: 原始主题
        expansion_type: 扩展类型 (related/deeper/broader)

    Returns:
        扩展建议字典
    """
    try:
        # 预定义的主题扩展规则
        expansion_rules = {
            "Python": {
                "related": ["Python框架", "Python库", "Python工具", "Python最佳实践"],
                "deeper": ["Python内存管理", "Python GIL", "Python字节码", "Python C扩展"],
                "broader": ["编程语言对比", "软件开发", "数据科学", "Web开发"]
            },
            "异步编程": {
                "related": ["协程", "事件循环", "并发编程", "多线程"],
                "deeper": ["异步I/O原理", "事件驱动架构", "回调地狱", "Promise模式"],
                "broader": ["系统架构", "性能优化", "分布式系统", "微服务"]
            },
            "装饰器": {
                "related": ["高阶函数", "闭包", "元编程", "设计模式"],
                "deeper": ["装饰器实现原理", "functools.wraps", "类装饰器", "装饰器工厂"],
                "broader": ["Python高级特性", "代码复用", "AOP编程", "框架设计"]
            }
        }

        # 查找匹配的主题
        matched_expansions = []
        topic_lower = topic.lower()

        for key, expansions in expansion_rules.items():
            if key.lower() in topic_lower or topic_lower in key.lower():
                matched_expansions.extend(expansions.get(expansion_type, []))

        # 如果没有找到匹配的，生成通用建议
        if not matched_expansions:
            if expansion_type == "related":
                matched_expansions = [f"{topic}应用", f"{topic}工具", f"{topic}案例"]
            elif expansion_type == "deeper":
                matched_expansions = [f"{topic}原理", f"{topic}实现", f"{topic}优化"]
            else:  # broader
                matched_expansions = [f"{topic}与其他技术", f"{topic}在行业中的应用", f"{topic}发展趋势"]

        # 生成扩展建议
        suggestions = []
        for expansion in matched_expansions[:5]:  # 限制数量
            suggestions.append({
                "subtopic": expansion,
                "description": f"探讨{expansion}的相关内容，包括概念、应用和实践",
                "potential_sections": [f"{expansion}概述", f"{expansion}实践", f"{expansion}案例"]
            })

        return {
            "original_topic": topic,
            "expansion_type": expansion_type,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }

    except Exception as e:
        logger.error(f"主题扩展失败: {str(e)}")
        return {"error": f"主题扩展失败: {str(e)}"}


@tool
def writing_style_advisor(content: str, target_style: str = "formal") -> Dict[str, Any]:
    """
    写作风格顾问工具
    分析内容并提供风格改进建议

    Args:
        content: 要分析的内容
        target_style: 目标风格 (formal/casual/academic/creative)

    Returns:
        风格分析和建议
    """
    try:
        if not content:
            return {"error": "内容不能为空"}

        # 风格特征分析
        style_features = {
            "formal": {
                "indicators": ["因此", "然而", "此外", "综上所述", "根据", "表明"],
                "avoid": ["很", "非常", "超级", "特别"],
                "sentence_style": "复合句较多，逻辑连接词丰富"
            },
            "casual": {
                "indicators": ["其实", "感觉", "觉得", "挺", "还是", "比较"],
                "avoid": ["综上所述", "鉴于", "基于", "据此"],
                "sentence_style": "句子简短，口语化表达"
            },
            "academic": {
                "indicators": ["研究表明", "数据显示", "分析结果", "实验证明", "理论框架"],
                "avoid": ["我觉得", "可能", "大概", "应该"],
                "sentence_style": "严谨的表述，引用和数据支撑"
            },
            "creative": {
                "indicators": ["想象", "如同", "仿佛", "生动", "形象", "比喻"],
                "avoid": ["数据显示", "研究表明", "根据统计"],
                "sentence_style": "富有想象力，修辞手法丰富"
            }
        }

        current_style_scores = {}
        target_features = style_features.get(target_style, style_features["formal"])

        # 分析当前风格
        for style_name, features in style_features.items():
            score = 0
            for indicator in features["indicators"]:
                score += content.count(indicator) * 2
            for avoid_word in features["avoid"]:
                score -= content.count(avoid_word)
            current_style_scores[style_name] = max(0, score)

        # 生成建议
        suggestions = []

        # 检查目标风格指标
        target_score = current_style_scores.get(target_style, 0)
        if target_score < 3:
            suggestions.append(f"建议增加更多{target_style}风格的表达方式")
            suggestions.extend([f"可以使用：{word}" for word in target_features["indicators"][:3]])

        # 检查需要避免的词汇
        for avoid_word in target_features["avoid"]:
            if avoid_word in content:
                suggestions.append(f"建议减少使用'{avoid_word}'，以符合{target_style}风格")

        return {
            "target_style": target_style,
            "current_style_scores": current_style_scores,
            "dominant_style": max(current_style_scores.keys(), key=lambda k: current_style_scores[k]),
            "style_match_score": target_score,
            "suggestions": suggestions[:5],  # 限制建议数量
            "style_description": target_features["sentence_style"]
        }

    except Exception as e:
        logger.error(f"写作风格分析失败: {str(e)}")
        return {"error": f"写作风格分析失败: {str(e)}"}


def get_writing_tools() -> List:
    """
    获取所有写作相关工具的列表

    Returns:
        工具列表
    """
    return [
        tavily_search,
        validate_outline,
        format_article,
        get_available_knowledge_bases,
        search_knowledge_base,
        keyword_knowledge_search,
        hybrid_search,
        content_analyzer,
        topic_expander,
        writing_style_advisor
    ]


# 为了兼容性，创建一个初始化函数别名
def initialize_rag_knowledge_base():
    """兼容性函数，实际调用关键词知识库初始化"""
    return initialize_keyword_knowledge_base()


def clean_debug_tags(module_name: str) -> None:
    """
    清理调试标记（生产环境使用）

    Args:
        module_name: 模块名称
    """
    # --#DEBUG#--
    if DEBUG_MODE:
        print(f"[DEBUG] 清理模块 {module_name} 的调试标记")
    # --#DEBUG#--

    # 在实际实现中，这里会移除所有 --#DEBUG#-- 标记的代码
    logger.info(f"已清理模块 {module_name} 的调试代码")


# 工具配置验证
def validate_tool_config() -> Dict[str, bool]:
    """
    验证工具配置是否正确

    Returns:
        配置验证结果
    """
    config_status = {
        "tavily_api_key": bool(os.getenv("TAVILY_API_KEY")),
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "debug_mode": DEBUG_MODE
    }

    # --#DEBUG#--
    if DEBUG_MODE:
        print(f"[DEBUG] 工具配置状态: {config_status}")
    # --#DEBUG#--

    return config_status
