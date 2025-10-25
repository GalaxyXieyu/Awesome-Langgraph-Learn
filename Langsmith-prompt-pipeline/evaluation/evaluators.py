"""
评估器模块
定义用于评估报告质量的评估器
"""
from typing import Dict, Any
from langsmith.evaluation import EvaluationResult, run_evaluator
from langchain_openai import AzureChatOpenAI
import json


class ReportEvaluators:
    """报告评估器集合"""
    
    @staticmethod
    @run_evaluator
    def structure_evaluator(run, example) -> EvaluationResult:
        """
        第 1 层：结构评估器
        
        检查报告的基本结构是否完整
        - 是否有标题层级
        - 是否有多个段落
        - 长度是否合理
        """
        try:
            # 获取输出
            output = run.outputs.get("report", "") if run.outputs else ""
            
            if not output:
                return EvaluationResult(
                    key="structure_valid",
                    score=0,
                    comment="报告为空"
                )
            
            # 检查项
            checks = {
                "has_title": output.count("#") >= 3,  # 至少 3 个标题
                "has_paragraphs": len(output.split("\n\n")) >= 5,  # 至少 5 个段落
                "min_length": len(output) >= 800,  # 最小长度
                "max_length": len(output) <= 20000,  # 最大长度
            }
            
            passed = sum(checks.values())
            total = len(checks)
            score = passed / total
            
            failed_checks = [k for k, v in checks.items() if not v]
            comment = f"通过 {passed}/{total} 项检查"
            if failed_checks:
                comment += f"。未通过: {', '.join(failed_checks)}"
            
            return EvaluationResult(
                key="structure_valid",
                score=score,
                comment=comment
            )
            
        except Exception as e:
            return EvaluationResult(
                key="structure_valid",
                score=0,
                comment=f"评估失败: {str(e)}"
            )
    
    @staticmethod
    @run_evaluator
    def content_completeness_evaluator(run, example) -> EvaluationResult:
        """
        第 2 层：内容完整性评估器
        
        检查报告是否包含必要的章节
        """
        try:
            output = run.outputs.get("report", "") if run.outputs else ""
            
            if not output:
                return EvaluationResult(
                    key="content_complete",
                    score=0,
                    comment="报告为空"
                )
            
            output_lower = output.lower()
            
            # 必要章节关键词
            required_sections = {
                "摘要/概述": any(kw in output_lower for kw in ["摘要", "概述", "executive", "summary"]),
                "背景": any(kw in output_lower for kw in ["背景", "background", "概况"]),
                "发现/分析": any(kw in output_lower for kw in ["发现", "分析", "finding", "analysis"]),
                "结论/建议": any(kw in output_lower for kw in ["结论", "建议", "conclusion", "recommendation"]),
            }
            
            passed = sum(required_sections.values())
            total = len(required_sections)
            score = passed / total
            
            missing = [k for k, v in required_sections.items() if not v]
            comment = f"包含 {passed}/{total} 个必要章节"
            if missing:
                comment += f"。缺少: {', '.join(missing)}"
            
            return EvaluationResult(
                key="content_complete",
                score=score,
                comment=comment
            )
            
        except Exception as e:
            return EvaluationResult(
                key="content_complete",
                score=0,
                comment=f"评估失败: {str(e)}"
            )
    
    @staticmethod
    @run_evaluator
    def relevance_evaluator(run, example) -> EvaluationResult:
        """
        第 3 层：相关性评估器
        
        使用 LLM 评估报告内容是否与主题相关
        """
        try:
            from config.azure_config import AzureConfig
            
            output = run.outputs.get("report", "") if run.outputs else ""
            inputs = run.inputs if run.inputs else {}
            
            if not output:
                return EvaluationResult(
                    key="relevance",
                    score=0,
                    comment="报告为空"
                )
            
            # 提取输入参数
            topic = inputs.get("topic", inputs.get("user_query", "未知"))
            
            # 使用快速模型进行评估
            llm = AzureConfig.get_fast_llm()
            
            eval_prompt = f"""
请评估以下报告是否与主题相关且内容质量良好。

**主题**: {topic}

**报告内容** (前 1000 字符):
{output[:1000]}

请从以下几个维度评估（每项 0-1 分）：
1. 主题相关性：内容是否紧扣主题
2. 信息丰富度：是否提供了有价值的信息
3. 逻辑连贯性：内容是否有逻辑性
4. 专业性：语言和分析是否专业

返回 JSON 格式：
{{
    "relevance": 0.9,
    "information": 0.8,
    "coherence": 0.85,
    "professionalism": 0.9,
    "overall": 0.88,
    "comment": "简短评价"
}}

只返回 JSON，不要其他内容。
"""
            
            response = llm.invoke(eval_prompt)
            
            # 解析响应
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            overall_score = result.get("overall", 0.5)
            comment = result.get("comment", "无评价")
            
            return EvaluationResult(
                key="relevance",
                score=overall_score,
                comment=comment
            )
            
        except Exception as e:
            # 如果 LLM 评估失败，返回中性分数
            return EvaluationResult(
                key="relevance",
                score=0.5,
                comment=f"LLM 评估失败: {str(e)}，返回中性分数"
            )
    
    @staticmethod
    @run_evaluator
    def parameter_usage_evaluator(run, example) -> EvaluationResult:
        """
        自定义评估器：检查多参数是否被正确使用
        
        验证报告中是否体现了用户指定的参数（风格、深度等）
        """
        try:
            output = run.outputs.get("report", "") if run.outputs else ""
            inputs = run.inputs if run.inputs else {}
            
            if not output:
                return EvaluationResult(
                    key="parameter_usage",
                    score=0,
                    comment="报告为空"
                )
            
            # 检查参数使用情况
            checks = {}
            
            # 检查年份范围
            year_range = inputs.get("year_range", "")
            if year_range:
                years = [y.strip() for y in year_range.replace("-", " ").split()]
                checks["year_mentioned"] = any(year in output for year in years)
            
            # 检查关注领域
            focus_areas = inputs.get("focus_areas", "")
            if focus_areas:
                areas = [a.strip() for a in focus_areas.split(",")]
                checks["focus_covered"] = any(area in output for area in areas[:3])  # 检查前3个
            
            # 检查风格（简单检查）
            style = inputs.get("style", "")
            if style == "formal":
                checks["style_appropriate"] = "分析" in output or "研究" in output
            elif style == "concise":
                checks["style_appropriate"] = len(output) < 5000
            elif style == "detailed":
                checks["style_appropriate"] = len(output) > 3000
            else:
                checks["style_appropriate"] = True
            
            if checks:
                passed = sum(checks.values())
                total = len(checks)
                score = passed / total
                
                comment = f"参数使用检查: {passed}/{total} 通过"
            else:
                score = 1.0
                comment = "无特定参数检查"
            
            return EvaluationResult(
                key="parameter_usage",
                score=score,
                comment=comment
            )
            
        except Exception as e:
            return EvaluationResult(
                key="parameter_usage",
                score=0.5,
                comment=f"评估失败: {str(e)}"
            )


if __name__ == "__main__":
    print("评估器模块已加载")
    print("\n可用评估器:")
    print("1. structure_evaluator - 结构完整性")
    print("2. content_completeness_evaluator - 内容完整性")
    print("3. relevance_evaluator - 相关性和质量")
    print("4. parameter_usage_evaluator - 参数使用情况")

