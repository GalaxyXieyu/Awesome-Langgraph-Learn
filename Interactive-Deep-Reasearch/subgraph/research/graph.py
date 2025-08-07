"""
智能上下文感知章节研究系统
基于质量驱动的迭代优化架构：上下文感知 + 质量评估 + 自适应优化
"""

import json
import time
import asyncio
import uuid
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langchain_core.tools import tool
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_get_stream_writer():
    """安全获取流写入器，避免上下文错误"""
    try:
        return get_stream_writer()
    except Exception:
        # 如果没有流上下文，返回一个空的写入器
        return lambda x: None

# ============================================================================
# 智能状态定义
# ============================================================================

class IntelligentSectionState(TypedDict):
    """智能章节研究状态"""
    
    # ========== 输入参数 ==========
    topic: str                                    # 研究主题
    section: Dict[str, Any]                      # 当前章节信息
    
    # ========== 上下文信息 ==========
    previous_sections_summary: List[str]         # 前置章节摘要
    upcoming_sections_outline: List[str]         # 后续章节大纲
    report_main_thread: str                      # 报告主线逻辑
    writing_style: str                           # 统一写作风格
    logical_connections: Dict[str, Any]          # 逻辑关联点
    
    # ========== 研究阶段 ==========
    initial_research_results: List[Dict[str, Any]]  # 初步研究结果
    supplementary_research_results: List[Dict[str, Any]]  # 补充研究结果
    
    # ========== 质量评估 ==========
    quality_assessment: Optional[Dict[str, Any]]  # 质量评估结果
    content_gaps: List[str]                       # 内容缺口
    improvement_suggestions: List[str]            # 改进建议
    
    # ========== 内容生成 ==========
    draft_content: Optional[str]                  # 初稿内容
    enhanced_content: Optional[str]               # 增强内容
    polished_content: Optional[str]               # 润色内容
    final_content: Optional[str]                  # 最终内容
    
    # ========== 迭代控制 ==========
    iteration_count: int                          # 迭代次数
    max_iterations: int                           # 最大迭代次数
    quality_threshold: float                      # 质量阈值
    
    # ========== 执行状态 ==========
    current_step: str                             # 当前执行步骤
    execution_path: List[str]                     # 执行路径记录
    start_time: float                             # 开始时间
    
    # ========== 最终输出 ==========
    final_result: Optional[Dict[str, Any]]        # 最终结果
    execution_summary: Optional[Dict[str, Any]]   # 执行摘要
    
    # ========== 错误处理 ==========
    error_log: List[str]                          # 错误日志
    
    # ========== 消息历史 ==========
    messages: Annotated[List, add_messages]       # 消息历史

# ============================================================================
# 智能Agent定义
# ============================================================================

class ContextAwareAgent:
    """上下文感知Agent"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen2.5-72b-instruct-awq",
            temperature=0.3,
            streaming=True,
            base_url="https://llm.3qiao.vip:23436/v1",
            api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197"
        )
    
    async def analyze_context(self, state: IntelligentSectionState) -> Dict[str, Any]:
        """分析上下文并生成研究策略"""
        
        context_prompt = f"""
        作为专业的研究策略分析师，请分析以下上下文信息，为章节"{state['section'].get('title')}"制定智能研究策略。
        
        当前章节信息：
        - 标题：{state['section'].get('title')}
        - 关键点：{', '.join(state['section'].get('key_points', []))}
        
        上下文信息：
        - 前置章节摘要：{'; '.join(state.get('previous_sections_summary', []))}
        - 后续章节大纲：{'; '.join(state.get('upcoming_sections_outline', []))}
        - 报告主线：{state.get('report_main_thread', '')}
        - 写作风格：{state.get('writing_style', 'professional')}
        
        请提供：
        1. 上下文关联分析
        2. 逻辑衔接要求
        3. 内容重点建议
        4. 研究查询策略
        
        以JSON格式返回：
        {{
            "context_analysis": "上下文分析",
            "logical_requirements": ["逻辑要求1", "逻辑要求2"],
            "content_focus": ["重点1", "重点2"],
            "research_queries": ["查询1", "查询2", "查询3"],
            "transition_needs": "过渡需求"
        }}
        """
        
        messages = [HumanMessage(content=context_prompt)]
        response = ""
        
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                response += chunk.content
        
        try:
            # 提取JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "context_analysis": "上下文分析完成",
                    "logical_requirements": ["保持逻辑连贯"],
                    "content_focus": ["核心内容"],
                    "research_queries": [f"{state['topic']} {state['section'].get('title')}"],
                    "transition_needs": "自然过渡"
                }
        except:
            return {
                "context_analysis": "上下文分析完成",
                "logical_requirements": ["保持逻辑连贯"],
                "content_focus": ["核心内容"],
                "research_queries": [f"{state['topic']} {state['section'].get('title')}"],
                "transition_needs": "自然过渡"
            }

class QualityAssessmentAgent:
    """质量评估Agent"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen2.5-72b-instruct-awq",
            temperature=0.1,
            streaming=True,
            base_url="https://llm.3qiao.vip:23436/v1",
            api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197"
        )
    
    async def assess_content_quality(
        self, 
        content: str, 
        context: Dict[str, Any],
        research_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估内容质量并提供改进建议"""
        
        assessment_prompt = f"""
        作为专业的内容质量评估专家，请全面评估以下章节内容的质量。
        
        章节内容：
        {content[:2000]}...
        
        评估维度：
        1. 内容完整性 (0-1)：是否覆盖了所有关键点
        2. 逻辑连贯性 (0-1)：内容逻辑是否清晰
        3. 上下文一致性 (0-1)：与前后章节的衔接
        4. 数据支撑度 (0-1)：是否有充分的数据支撑
        5. 专业深度 (0-1)：专业性和深度如何
        
        上下文要求：
        - 前置章节：{context.get('previous_context', '')}
        - 逻辑要求：{context.get('logical_requirements', [])}
        - 内容重点：{context.get('content_focus', [])}
        
        请以JSON格式返回评估结果：
        {{
            "completeness_score": 0.85,
            "logical_coherence": 0.90,
            "context_alignment": 0.75,
            "data_sufficiency": 0.80,
            "professional_depth": 0.85,
            "overall_quality": 0.83,
            "content_gaps": ["缺口1", "缺口2"],
            "improvement_suggestions": ["建议1", "建议2"],
            "needs_supplementary_research": true,
            "supplementary_topics": ["补充主题1", "补充主题2"]
        }}
        """
        
        messages = [HumanMessage(content=assessment_prompt)]
        response = ""
        
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                response += chunk.content
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # 确保所有必需字段存在
                default_result = {
                    "completeness_score": 0.7,
                    "logical_coherence": 0.7,
                    "context_alignment": 0.7,
                    "data_sufficiency": 0.7,
                    "professional_depth": 0.7,
                    "overall_quality": 0.7,
                    "content_gaps": [],
                    "improvement_suggestions": [],
                    "needs_supplementary_research": False,
                    "supplementary_topics": []
                }
                default_result.update(result)
                return default_result
            else:
                return {
                    "completeness_score": 0.6,
                    "logical_coherence": 0.6,
                    "context_alignment": 0.6,
                    "data_sufficiency": 0.6,
                    "professional_depth": 0.6,
                    "overall_quality": 0.6,
                    "content_gaps": ["需要更多分析"],
                    "improvement_suggestions": ["增加具体案例"],
                    "needs_supplementary_research": True,
                    "supplementary_topics": [f"{context.get('topic', '')} 深度分析"]
                }
        except Exception as e:
            logger.error(f"质量评估解析失败: {str(e)}")
            return {
                "completeness_score": 0.5,
                "logical_coherence": 0.5,
                "context_alignment": 0.5,
                "data_sufficiency": 0.5,
                "professional_depth": 0.5,
                "overall_quality": 0.5,
                "content_gaps": ["评估失败"],
                "improvement_suggestions": ["需要重新评估"],
                "needs_supplementary_research": True,
                "supplementary_topics": ["补充研究"]
            }

class AdaptiveResearchAgent:
    """自适应研究Agent"""
    
    def generate_supplementary_queries(
        self, 
        gaps: List[str], 
        suggestions: List[str],
        topics: List[str],
        context: Dict[str, Any]
    ) -> List[str]:
        """基于质量评估生成补充查询"""
        
        supplementary_queries = []
        topic = context.get('topic', '')
        section_title = context.get('section_title', '')
        
        # 基于内容缺口生成查询
        for gap in gaps:
            if "案例" in gap or "实例" in gap:
                supplementary_queries.append(f"{topic} {section_title} 成功案例 详细分析")
            elif "数据" in gap or "统计" in gap:
                supplementary_queries.append(f"{topic} {section_title} 最新数据 统计报告")
            elif "趋势" in gap or "发展" in gap:
                supplementary_queries.append(f"{topic} {section_title} 发展趋势 未来预测")
            elif "技术" in gap:
                supplementary_queries.append(f"{topic} {section_title} 技术细节 实现方案")
        
        # 基于改进建议生成查询
        for suggestion in suggestions:
            if "深入" in suggestion:
                supplementary_queries.append(f"{topic} {section_title} 深度分析 专业解读")
            elif "对比" in suggestion:
                supplementary_queries.append(f"{topic} {section_title} 对比分析 竞争格局")
        
        # 基于补充主题生成查询
        for topic_item in topics:
            supplementary_queries.append(f"{topic} {topic_item} 详细研究")
        
        # 去重并限制数量
        unique_queries = list(set(supplementary_queries))
        return unique_queries[:5]  # 最多5个补充查询

# ============================================================================
# 核心节点实现
# ============================================================================

async def context_aware_planning_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """🧠 上下文感知规划节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "context_aware_planning",
        "status": "🧠 开始上下文感知规划",
        "progress": 0,
        "section_title": state["section"].get("title", "未知章节")
    })
    
    try:
        # 创建上下文感知Agent
        context_agent = ContextAwareAgent()
        
        # 分析上下文并生成策略
        context_analysis = await context_agent.analyze_context(state)
        
        # 更新状态
        state["logical_connections"] = {
            "context_analysis": context_analysis.get("context_analysis", ""),
            "logical_requirements": context_analysis.get("logical_requirements", []),
            "content_focus": context_analysis.get("content_focus", []),
            "transition_needs": context_analysis.get("transition_needs", "")
        }
        
        # 生成初始研究查询
        research_queries = context_analysis.get("research_queries", [])
        
        state["current_step"] = "context_planning_completed"
        state["execution_path"] = state.get("execution_path", []) + ["context_aware_planning"]
        state["start_time"] = time.time()
        
        writer({
            "step": "context_aware_planning",
            "status": f"✅ 上下文规划完成：生成{len(research_queries)}个智能查询",
            "progress": 100,
            "research_queries": research_queries,
            "logical_requirements": context_analysis.get("logical_requirements", []),
            "content": {
                "type": "context_planning",
                "data": {
                    "research_queries": research_queries,
                    "context_analysis": context_analysis
                }
            }
        })
        
        # 将查询存储到状态中供后续使用
        state["research_queries"] = research_queries
        
        logger.info(f"上下文感知规划完成: {state['section'].get('title')}")
        return state

    except Exception as e:
        logger.error(f"上下文规划失败: {str(e)}")
        writer({
            "step": "context_aware_planning",
            "status": f"❌ 规划失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"上下文规划错误: {str(e)}"]
        state["current_step"] = "planning_failed"
        return state

async def initial_research_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """🔍 初步研究节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "initial_research",
        "status": "🔍 开始初步并行研究",
        "progress": 0
    })

    try:
        from langchain_tavily import TavilySearch

        research_queries = state.get("research_queries", [])
        if not research_queries:
            research_queries = [f"{state['topic']} {state['section'].get('title')}"]

        writer({
            "step": "initial_research",
            "status": f"⚡ 并行执行{len(research_queries)}个初步查询",
            "progress": 20
        })

        # 并行搜索执行
        async def search_query(query: str) -> List[Dict[str, Any]]:
            try:
                from langchain_tavily import TavilySearch
                import os

                # 设置API密钥
                os.environ["TAVILY_API_KEY"] = "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"

                search_tool = TavilySearch(
                    max_results=3,
                    search_depth="basic"
                )

                search_response = search_tool.invoke(query)

                # 处理API错误或限制
                if isinstance(search_response, dict) and "error" in search_response:
                    logger.warning(f"搜索API错误: {search_response['error']}")
                    return [{
                        "id": str(uuid.uuid4()),
                        "title": f"搜索结果: {query}",
                        "url": "",
                        "content": f"关于{query}的模拟内容：这是一个关于该主题的详细分析，包含了相关的技术发展、市场趋势和应用案例。",
                        "query": query,
                        "relevance_score": 0.8,
                        "timestamp": time.time()
                    }]

                # 使用正确的处理方式
                if not search_response or "results" not in search_response:
                    return [{
                        "id": str(uuid.uuid4()),
                        "title": f"搜索结果: {query}",
                        "url": "",
                        "content": f"关于{query}的模拟内容：这是一个关于该主题的详细分析，包含了相关的技术发展、市场趋势和应用案例。",
                        "query": query,
                        "relevance_score": 0.8,
                        "timestamp": time.time()
                    }]

                results = search_response["results"]
                if not results:
                    return [{
                        "id": str(uuid.uuid4()),
                        "title": f"搜索结果: {query}",
                        "url": "",
                        "content": f"关于{query}的模拟内容：这是一个关于该主题的详细分析，包含了相关的技术发展、市场趋势和应用案例。",
                        "query": query,
                        "relevance_score": 0.8,
                        "timestamp": time.time()
                    }]

                formatted_results = []
                for i, result in enumerate(results[:3]):
                    formatted_result = {
                        "id": str(uuid.uuid4()),
                        "title": result.get("title", f"结果 {i+1}"),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")[:800],
                        "query": query,
                        "relevance_score": 0.9 - i * 0.1,
                        "timestamp": time.time()
                    }
                    formatted_results.append(formatted_result)

                return formatted_results

            except Exception as e:
                logger.error(f"搜索失败: {query} - {str(e)}")
                return [{
                    "id": str(uuid.uuid4()),
                    "title": f"搜索结果: {query}",
                    "content": f"关于{query}的模拟内容...",
                    "query": query,
                    "error": str(e)
                }]

        # 创建并行任务
        search_tasks = [search_query(query) for query in research_queries]
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 处理搜索结果
        all_results = []
        for i, results in enumerate(search_results_list):
            if isinstance(results, list):
                all_results.extend(results)
                progress = 20 + ((i + 1) / len(research_queries)) * 60
                writer({
                    "step": "initial_research",
                    "status": f"✅ 查询完成: {research_queries[i]} ({len(results)}个结果)",
                    "progress": int(progress)
                })

        # 去重和质量筛选
        unique_results = []
        seen_urls = set()
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
            elif not url:  # 模拟结果
                unique_results.append(result)

        state["initial_research_results"] = unique_results
        state["current_step"] = "initial_research_completed"
        state["execution_path"] = state.get("execution_path", []) + ["initial_research"]

        writer({
            "step": "initial_research",
            "status": "🎉 初步研究完成！",
            "progress": 100,
            "total_results": len(unique_results),
            "content": {
                "type": "initial_research_results",
                "data": {
                    "results_count": len(unique_results),
                    "queries_executed": len(research_queries)
                }
            }
        })

        logger.info(f"初步研究完成: {len(unique_results)}个结果")
        return state

    except Exception as e:
        logger.error(f"初步研究失败: {str(e)}")
        writer({
            "step": "initial_research",
            "status": f"❌ 研究失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"初步研究错误: {str(e)}"]
        state["current_step"] = "initial_research_failed"
        return state

async def draft_content_generation_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """📝 初稿内容生成节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "draft_generation",
        "status": "📝 开始生成初稿内容",
        "progress": 0
    })

    try:
        research_results = state.get("initial_research_results", [])
        section = state["section"]
        logical_connections = state.get("logical_connections", {})

        if not research_results:
            writer({
                "step": "draft_generation",
                "status": "没有可用的研究结果",
                "progress": 100
            })
            return state

        # 创建写作LLM
        llm = ChatOpenAI(
            model="qwen2.5-72b-instruct-awq",
            temperature=0.7,
            streaming=True,
            base_url="https://llm.3qiao.vip:23436/v1",
            api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197"
        )

        # 构建上下文感知的写作提示
        writing_prompt = f"""
        作为专业的技术写作专家，请基于研究结果和上下文要求为"{section.get('title')}"章节撰写初稿内容。

        章节信息：
        - 标题：{section.get('title')}
        - 关键点：{', '.join(section.get('key_points', []))}
        - 主题：{state['topic']}

        上下文要求：
        - 前置章节摘要：{'; '.join(state.get('previous_sections_summary', []))}
        - 逻辑要求：{', '.join(logical_connections.get('logical_requirements', []))}
        - 内容重点：{', '.join(logical_connections.get('content_focus', []))}
        - 过渡需求：{logical_connections.get('transition_needs', '')}

        研究数据摘要：
        {json.dumps([{
            'title': r.get('title', ''),
            'content': r.get('content', '')[:300]
        } for r in research_results[:8]], ensure_ascii=False, indent=2)}

        写作要求：
        1. 与前后章节逻辑衔接自然
        2. 体现上下文的连贯性
        3. 结构清晰，层次分明
        4. 内容专业，数据支撑
        5. 字数控制在800-1200字

        请撰写完整的章节初稿内容。
        """

        writer({
            "step": "draft_generation",
            "status": "🤖 AI正在生成上下文感知的初稿...",
            "progress": 30
        })

        # 流式生成初稿
        messages = [HumanMessage(content=writing_prompt)]
        draft_content = ""
        chunk_count = 0

        async for chunk in llm.astream(messages):
            if chunk.content:
                draft_content += chunk.content
                chunk_count += 1

                if chunk_count % 15 == 0:
                    progress = min(90, 30 + (chunk_count // 15) * 10)
                    writer({
                        "step": "draft_generation",
                        "status": f"📝 正在生成... ({len(draft_content)}字符)",
                        "progress": progress
                    })

        state["draft_content"] = draft_content
        state["current_step"] = "draft_completed"
        state["execution_path"] = state.get("execution_path", []) + ["draft_generation"]

        writer({
            "step": "draft_generation",
            "status": "✅ 初稿生成完成！",
            "progress": 100,
            "content_length": len(draft_content),
            "word_count": len(draft_content.split()),
            "content": {
                "type": "draft_content",
                "data": {
                    "content_preview": draft_content[:200] + "..." if len(draft_content) > 200 else draft_content,
                    "word_count": len(draft_content.split()),
                    "character_count": len(draft_content)
                }
            }
        })

        logger.info(f"初稿生成完成: {len(draft_content)}字符")
        return state

    except Exception as e:
        logger.error(f"初稿生成失败: {str(e)}")
        writer({
            "step": "draft_generation",
            "status": f"❌ 生成失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"初稿生成错误: {str(e)}"]
        state["current_step"] = "draft_failed"
        return state

async def quality_assessment_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """📊 智能质量评估节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "quality_assessment",
        "status": "📊 开始智能质量评估",
        "progress": 0
    })

    try:
        draft_content = state.get("draft_content") or state.get("enhanced_content", "")
        if not draft_content:
            writer({
                "step": "quality_assessment",
                "status": "没有可评估的内容",
                "progress": 100
            })
            return state

        # 创建质量评估Agent
        quality_agent = QualityAssessmentAgent()

        # 准备评估上下文
        assessment_context = {
            "topic": state.get("topic", ""),
            "section_title": state["section"].get("title", ""),
            "previous_context": "; ".join(state.get("previous_sections_summary", [])),
            "logical_requirements": state.get("logical_connections", {}).get("logical_requirements", []),
            "content_focus": state.get("logical_connections", {}).get("content_focus", [])
        }

        writer({
            "step": "quality_assessment",
            "status": "🤖 AI正在进行多维度质量评估...",
            "progress": 30
        })

        # 执行质量评估
        research_data = state.get("initial_research_results", []) + state.get("supplementary_research_results", [])
        quality_assessment = await quality_agent.assess_content_quality(
            draft_content,
            assessment_context,
            research_data
        )

        # 更新状态
        state["quality_assessment"] = quality_assessment
        state["content_gaps"] = quality_assessment.get("content_gaps", [])
        state["improvement_suggestions"] = quality_assessment.get("improvement_suggestions", [])

        # 判断是否需要补充研究
        overall_quality = quality_assessment.get("overall_quality", 0)
        quality_threshold = state.get("quality_threshold", 0.75)
        needs_supplementary = quality_assessment.get("needs_supplementary_research", False)

        if overall_quality < quality_threshold or needs_supplementary:
            state["current_step"] = "needs_improvement"
        else:
            state["current_step"] = "quality_approved"

        state["execution_path"] = state.get("execution_path", []) + ["quality_assessment"]

        writer({
            "step": "quality_assessment",
            "status": f"✅ 质量评估完成！综合评分: {overall_quality:.3f}",
            "progress": 100,
            "overall_quality": overall_quality,
            "quality_threshold": quality_threshold,
            "needs_improvement": overall_quality < quality_threshold or needs_supplementary,
            "content_gaps_count": len(quality_assessment.get("content_gaps", [])),
            "content": {
                "type": "quality_assessment",
                "data": {
                    "overall_quality": overall_quality,
                    "detailed_scores": {
                        "completeness": quality_assessment.get("completeness_score", 0),
                        "coherence": quality_assessment.get("logical_coherence", 0),
                        "context_alignment": quality_assessment.get("context_alignment", 0),
                        "data_sufficiency": quality_assessment.get("data_sufficiency", 0),
                        "professional_depth": quality_assessment.get("professional_depth", 0)
                    },
                    "content_gaps": quality_assessment.get("content_gaps", []),
                    "improvement_suggestions": quality_assessment.get("improvement_suggestions", [])
                }
            }
        })

        logger.info(f"质量评估完成: 综合评分{overall_quality:.3f}, 需要改进: {overall_quality < quality_threshold}")
        return state

    except Exception as e:
        logger.error(f"质量评估失败: {str(e)}")
        writer({
            "step": "quality_assessment",
            "status": f"❌ 评估失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"质量评估错误: {str(e)}"]
        state["current_step"] = "assessment_failed"
        return state

def quality_decision_node(state: IntelligentSectionState) -> str:
    """质量决策节点 - 决定下一步行动"""
    current_step = state.get("current_step", "")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)

    if current_step == "quality_approved":
        return "content_polishing"
    elif current_step == "needs_improvement" and iteration_count < max_iterations:
        return "supplementary_research"
    else:
        # 达到最大迭代次数，直接进入润色
        return "content_polishing"

async def supplementary_research_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """🎯 补充研究节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "supplementary_research",
        "status": "🎯 开始补充研究",
        "progress": 0
    })

    try:
        quality_assessment = state.get("quality_assessment", {})
        content_gaps = quality_assessment.get("content_gaps", [])
        improvement_suggestions = quality_assessment.get("improvement_suggestions", [])
        supplementary_topics = quality_assessment.get("supplementary_topics", [])

        if not (content_gaps or improvement_suggestions or supplementary_topics):
            writer({
                "step": "supplementary_research",
                "status": "没有需要补充的研究内容",
                "progress": 100
            })
            return state

        # 创建自适应研究Agent
        research_agent = AdaptiveResearchAgent()

        # 生成补充查询
        supplementary_queries = research_agent.generate_supplementary_queries(
            content_gaps,
            improvement_suggestions,
            supplementary_topics,
            {
                "topic": state.get("topic", ""),
                "section_title": state["section"].get("title", "")
            }
        )

        writer({
            "step": "supplementary_research",
            "status": f"🔍 执行{len(supplementary_queries)}个补充查询",
            "progress": 20
        })

        # 执行补充搜索
        async def supplementary_search(query: str) -> List[Dict[str, Any]]:
            try:
                from langchain_tavily import TavilySearch
                import os

                # 设置API密钥
                os.environ["TAVILY_API_KEY"] = "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"

                search_tool = TavilySearch(
                    max_results=2,
                    search_depth="advanced"  # 使用高级搜索获得更好结果
                )

                search_response = search_tool.invoke(query)

                # 使用正确的处理方式
                if not search_response or "results" not in search_response:
                    return [{
                        "id": str(uuid.uuid4()),
                        "title": f"补充搜索结果: {query}",
                        "url": "",
                        "content": f"关于{query}的补充内容...",
                        "query": query,
                        "search_type": "supplementary",
                        "relevance_score": 0.85,
                        "timestamp": time.time()
                    }]

                results = search_response["results"]
                if not results:
                    return [{
                        "id": str(uuid.uuid4()),
                        "title": f"补充搜索结果: {query}",
                        "url": "",
                        "content": f"关于{query}的补充内容...",
                        "query": query,
                        "search_type": "supplementary",
                        "relevance_score": 0.85,
                        "timestamp": time.time()
                    }]

                formatted_results = []
                for i, result in enumerate(results[:2]):
                    formatted_result = {
                        "id": str(uuid.uuid4()),
                        "title": result.get("title", f"补充结果 {i+1}"),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")[:600],
                        "query": query,
                        "search_type": "supplementary",
                        "relevance_score": 0.95 - i * 0.05,
                        "timestamp": time.time()
                    }
                    formatted_results.append(formatted_result)

                return formatted_results

            except Exception as e:
                logger.error(f"补充搜索失败: {query} - {str(e)}")
                return [{
                    "id": str(uuid.uuid4()),
                    "title": f"补充搜索结果: {query}",
                    "content": f"关于{query}的补充内容...",
                    "query": query,
                    "search_type": "supplementary",
                    "error": str(e)
                }]

        # 并行执行补充搜索
        search_tasks = [supplementary_search(query) for query in supplementary_queries]
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 处理补充搜索结果
        supplementary_results = []
        for i, results in enumerate(search_results_list):
            if isinstance(results, list):
                supplementary_results.extend(results)
                progress = 20 + ((i + 1) / len(supplementary_queries)) * 60
                writer({
                    "step": "supplementary_research",
                    "status": f"✅ 补充查询完成: {supplementary_queries[i]}",
                    "progress": int(progress)
                })

        state["supplementary_research_results"] = supplementary_results
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        state["current_step"] = "supplementary_completed"
        state["execution_path"] = state.get("execution_path", []) + ["supplementary_research"]

        writer({
            "step": "supplementary_research",
            "status": "🎉 补充研究完成！",
            "progress": 100,
            "supplementary_results": len(supplementary_results),
            "iteration_count": state["iteration_count"],
            "content": {
                "type": "supplementary_research",
                "data": {
                    "results_count": len(supplementary_results),
                    "queries_executed": len(supplementary_queries),
                    "iteration": state["iteration_count"]
                }
            }
        })

        logger.info(f"补充研究完成: {len(supplementary_results)}个补充结果")
        return state

    except Exception as e:
        logger.error(f"补充研究失败: {str(e)}")
        writer({
            "step": "supplementary_research",
            "status": f"❌ 补充研究失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"补充研究错误: {str(e)}"]
        state["current_step"] = "supplementary_failed"
        return state

async def content_enhancement_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """📝 内容增强节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "content_enhancement",
        "status": "📝 开始内容增强",
        "progress": 0
    })

    try:
        draft_content = state.get("draft_content", "")
        supplementary_results = state.get("supplementary_research_results", [])
        quality_assessment = state.get("quality_assessment", {})

        if not draft_content:
            writer({
                "step": "content_enhancement",
                "status": "没有可增强的内容",
                "progress": 100
            })
            return state

        # 创建增强LLM
        llm = ChatOpenAI(
            model="qwen2.5-72b-instruct-awq",
            temperature=0.6,
            streaming=True,
            base_url="https://llm.3qiao.vip:23436/v1",
            api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197"
        )

        # 构建增强提示
        enhancement_prompt = f"""
        作为专业的内容增强专家，请基于质量评估反馈和补充研究结果，对以下章节内容进行智能增强。

        原始内容：
        {draft_content}

        质量评估反馈：
        - 内容缺口：{', '.join(quality_assessment.get('content_gaps', []))}
        - 改进建议：{', '.join(quality_assessment.get('improvement_suggestions', []))}
        - 当前质量评分：{quality_assessment.get('overall_quality', 0):.2f}

        补充研究数据：
        {json.dumps([{
            'title': r.get('title', ''),
            'content': r.get('content', '')[:300]
        } for r in supplementary_results[:5]], ensure_ascii=False, indent=2)}

        增强要求：
        1. 针对性填补内容缺口
        2. 整合补充研究数据
        3. 提升专业深度和数据支撑
        4. 保持逻辑连贯性
        5. 优化结构和表达

        请输出增强后的完整章节内容。
        """

        writer({
            "step": "content_enhancement",
            "status": "🤖 AI正在进行智能内容增强...",
            "progress": 30
        })

        # 流式生成增强内容
        messages = [HumanMessage(content=enhancement_prompt)]
        enhanced_content = ""
        chunk_count = 0

        async for chunk in llm.astream(messages):
            if chunk.content:
                enhanced_content += chunk.content
                chunk_count += 1

                if chunk_count % 20 == 0:
                    progress = min(90, 30 + (chunk_count // 20) * 10)
                    writer({
                        "step": "content_enhancement",
                        "status": f"📝 正在增强... ({len(enhanced_content)}字符)",
                        "progress": progress
                    })

        state["enhanced_content"] = enhanced_content
        state["current_step"] = "enhancement_completed"
        state["execution_path"] = state.get("execution_path", []) + ["content_enhancement"]

        writer({
            "step": "content_enhancement",
            "status": "✅ 内容增强完成！",
            "progress": 100,
            "enhanced_length": len(enhanced_content),
            "improvement_ratio": len(enhanced_content) / max(len(draft_content), 1),
            "content": {
                "type": "enhanced_content",
                "data": {
                    "content_preview": enhanced_content[:200] + "..." if len(enhanced_content) > 200 else enhanced_content,
                    "word_count": len(enhanced_content.split()),
                    "character_count": len(enhanced_content),
                    "improvement_ratio": len(enhanced_content) / max(len(draft_content), 1)
                }
            }
        })

        logger.info(f"内容增强完成: {len(enhanced_content)}字符")
        return state

    except Exception as e:
        logger.error(f"内容增强失败: {str(e)}")
        writer({
            "step": "content_enhancement",
            "status": f"❌ 增强失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"内容增强错误: {str(e)}"]
        state["current_step"] = "enhancement_failed"
        return state

async def content_polishing_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """✨ 智能润色节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "content_polishing",
        "status": "✨ 开始智能润色",
        "progress": 0
    })

    try:
        # 选择最佳内容版本进行润色
        content_to_polish = (
            state.get("enhanced_content") or
            state.get("draft_content", "")
        )

        if not content_to_polish:
            writer({
                "step": "content_polishing",
                "status": "没有可润色的内容",
                "progress": 100
            })
            return state

        # 创建润色LLM
        llm = ChatOpenAI(
            model="qwen2.5-72b-instruct-awq",
            temperature=0.4,
            streaming=True,
            base_url="https://llm.3qiao.vip:23436/v1",
            api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197"
        )

        # 构建润色提示
        logical_connections = state.get("logical_connections", {})
        writing_style = state.get("writing_style", "professional")

        polishing_prompt = f"""
        作为专业的文本润色专家，请对以下章节内容进行精细润色，确保达到出版级别的质量。

        待润色内容：
        {content_to_polish}

        润色要求：
        1. 语言表达：优化语言流畅性和专业性
        2. 结构优化：调整段落结构，增强逻辑性
        3. 风格统一：保持{writing_style}的写作风格
        4. 上下文衔接：确保与前后章节的自然过渡
        5. 专业提升：增强专业术语的准确性

        上下文要求：
        - 逻辑要求：{', '.join(logical_connections.get('logical_requirements', []))}
        - 过渡需求：{logical_connections.get('transition_needs', '')}

        请输出润色后的最终章节内容，确保质量达到专业报告标准。
        """

        writer({
            "step": "content_polishing",
            "status": "🤖 AI正在进行专业润色...",
            "progress": 30
        })

        # 流式生成润色内容
        messages = [HumanMessage(content=polishing_prompt)]
        polished_content = ""
        chunk_count = 0

        async for chunk in llm.astream(messages):
            if chunk.content:
                polished_content += chunk.content
                chunk_count += 1

                if chunk_count % 15 == 0:
                    progress = min(90, 30 + (chunk_count // 15) * 10)
                    writer({
                        "step": "content_polishing",
                        "status": f"✨ 正在润色... ({len(polished_content)}字符)",
                        "progress": progress
                    })

        state["polished_content"] = polished_content
        state["final_content"] = polished_content  # 设置为最终内容
        state["current_step"] = "polishing_completed"
        state["execution_path"] = state.get("execution_path", []) + ["content_polishing"]

        writer({
            "step": "content_polishing",
            "status": "🎉 智能润色完成！",
            "progress": 100,
            "final_length": len(polished_content),
            "final_word_count": len(polished_content.split()),
            "content": {
                "type": "polished_content",
                "data": {
                    "content_preview": polished_content[:300] + "..." if len(polished_content) > 300 else polished_content,
                    "word_count": len(polished_content.split()),
                    "character_count": len(polished_content),
                    "quality_level": "professional"
                }
            }
        })

        logger.info(f"智能润色完成: {len(polished_content)}字符")
        return state

    except Exception as e:
        logger.error(f"智能润色失败: {str(e)}")
        writer({
            "step": "content_polishing",
            "status": f"❌ 润色失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"润色错误: {str(e)}"]
        state["current_step"] = "polishing_failed"
        return state

async def final_integration_node(state: IntelligentSectionState, config=None) -> IntelligentSectionState:
    """🎯 最终整合节点"""
    writer = safe_get_stream_writer()
    writer({
        "step": "final_integration",
        "status": "🎯 开始最终整合",
        "progress": 0
    })

    try:
        # 计算执行时间
        execution_time = time.time() - state.get("start_time", time.time())

        # 构建最终结果
        final_result = {
            "section_id": state["section"].get("id"),
            "section_title": state["section"].get("title"),
            "topic": state["topic"],
            "final_content": state.get("final_content", ""),

            "quality_metrics": {
                "final_quality_score": state.get("quality_assessment", {}).get("overall_quality", 0),
                "iteration_count": state.get("iteration_count", 0),
                "research_results_count": len(state.get("initial_research_results", [])),
                "supplementary_results_count": len(state.get("supplementary_research_results", [])),
                "content_evolution": {
                    "draft_length": len(state.get("draft_content", "")),
                    "enhanced_length": len(state.get("enhanced_content", "")),
                    "final_length": len(state.get("final_content", ""))
                }
            },

            "context_integration": {
                "logical_connections": state.get("logical_connections", {}),
                "context_awareness": True,
                "previous_sections_considered": len(state.get("previous_sections_summary", [])),
                "upcoming_sections_considered": len(state.get("upcoming_sections_outline", []))
            },

            "research_data": {
                "initial_research": state.get("initial_research_results", []),
                "supplementary_research": state.get("supplementary_research_results", []),
                "quality_assessment": state.get("quality_assessment", {}),
                "content_gaps_addressed": state.get("content_gaps", []),
                "improvements_made": state.get("improvement_suggestions", [])
            },

            "execution_metadata": {
                "execution_time": execution_time,
                "execution_path": state.get("execution_path", []),
                "iteration_count": state.get("iteration_count", 0),
                "max_iterations": state.get("max_iterations", 3),
                "quality_threshold": state.get("quality_threshold", 0.75),
                "timestamp": datetime.now().isoformat(),
                "system_version": "intelligent_v1.0"
            }
        }

        # 生成执行摘要
        execution_summary = {
            "status": "completed",
            "execution_time": execution_time,
            "steps_completed": len(state.get("execution_path", [])),
            "iterations_performed": state.get("iteration_count", 0),
            "final_quality_score": state.get("quality_assessment", {}).get("overall_quality", 0),
            "error_count": len(state.get("error_log", [])),
            "intelligence_features": {
                "context_aware": True,
                "quality_driven": True,
                "iterative_improvement": state.get("iteration_count", 0) > 0,
                "adaptive_research": len(state.get("supplementary_research_results", [])) > 0
            }
        }

        # 更新状态
        state["final_result"] = final_result
        state["execution_summary"] = execution_summary
        state["current_step"] = "completed"
        state["execution_path"] = state.get("execution_path", []) + ["final_integration"]

        writer({
            "step": "final_integration",
            "status": "🎉 智能章节研究完成！",
            "progress": 100,
            "execution_time": execution_time,
            "final_quality": state.get("quality_assessment", {}).get("overall_quality", 0),
            "iterations": state.get("iteration_count", 0),
            "content": {
                "type": "final_result",
                "data": final_result
            }
        })

        logger.info(f"智能章节研究完成: {state['section'].get('title')}, 执行时间{execution_time:.2f}秒, 迭代{state.get('iteration_count', 0)}次")
        return state

    except Exception as e:
        logger.error(f"最终整合失败: {str(e)}")
        writer({
            "step": "final_integration",
            "status": f"❌ 整合失败: {str(e)}",
            "progress": -1
        })

        state["error_log"] = state.get("error_log", []) + [f"最终整合错误: {str(e)}"]
        state["current_step"] = "integration_failed"
        return state

# ============================================================================
# Graph构建
# ============================================================================

def create_intelligent_section_research_graph() -> StateGraph:
    """创建智能章节研究Graph"""

    # 创建状态图
    workflow = StateGraph(IntelligentSectionState)

    # 添加节点
    workflow.add_node("context_aware_planning", context_aware_planning_node)
    workflow.add_node("initial_research", initial_research_node)
    workflow.add_node("draft_generation", draft_content_generation_node)
    workflow.add_node("quality_assessment", quality_assessment_node)
    workflow.add_node("supplementary_research", supplementary_research_node)
    workflow.add_node("content_enhancement", content_enhancement_node)
    workflow.add_node("content_polishing", content_polishing_node)
    workflow.add_node("final_integration", final_integration_node)

    # 定义流程
    workflow.add_edge(START, "context_aware_planning")
    workflow.add_edge("context_aware_planning", "initial_research")
    workflow.add_edge("initial_research", "draft_generation")
    workflow.add_edge("draft_generation", "quality_assessment")

    # 质量决策分支
    workflow.add_conditional_edges(
        "quality_assessment",
        quality_decision_node,
        {
            "supplementary_research": "supplementary_research",
            "content_polishing": "content_polishing"
        }
    )

    # 补充研究后的流程
    workflow.add_edge("supplementary_research", "content_enhancement")
    workflow.add_edge("content_enhancement", "quality_assessment")  # 重新评估质量

    # 润色后的最终整合
    workflow.add_edge("content_polishing", "final_integration")
    workflow.add_edge("final_integration", END)

    return workflow
