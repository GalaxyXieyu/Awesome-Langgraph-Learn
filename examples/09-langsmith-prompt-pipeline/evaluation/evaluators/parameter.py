"""
参数解析评估器
专门用于评估 parameter_parser 提示词的输出质量
"""
from typing import Dict, Any
from langsmith.evaluation import EvaluationResult, run_evaluator
import json


class ParameterEvaluators:
    """参数解析评估器集合"""
    
    @staticmethod
    @run_evaluator
    def structure_evaluator(run, example) -> EvaluationResult:
        """
        结构评估器 - 检查 JSON 输出格式
        
        检查：
        - 是否是有效的 JSON
        - 是否包含必需字段
        """
        try:
            output = run.outputs.get("report", "") if run.outputs else ""
            
            if not output:
                return EvaluationResult(
                    key="structure_valid",
                    score=0,
                    comment="输出为空"
                )
            
            # 尝试解析 JSON
            try:
                parsed = json.loads(output)
                is_valid_json = True
            except json.JSONDecodeError as e:
                return EvaluationResult(
                    key="structure_valid",
                    score=0,
                    comment=f"JSON 格式错误: {str(e)}"
                )
            
            # 检查必需字段
            required_fields = ["topic", "year_range", "style", "depth"]
            missing_fields = [f for f in required_fields if f not in parsed]
            
            if missing_fields:
                score = 1 - (len(missing_fields) / len(required_fields))
                return EvaluationResult(
                    key="structure_valid",
                    score=score,
                    comment=f"缺少字段: {', '.join(missing_fields)}"
                )
            
            return EvaluationResult(
                key="structure_valid",
                score=1.0,
                comment="结构完整且有效"
            )
            
        except Exception as e:
            return EvaluationResult(
                key="structure_valid",
                score=0,
                comment=f"评估失败: {str(e)}"
            )
    
    @staticmethod
    @run_evaluator
    def parameter_extraction_evaluator(run, example) -> EvaluationResult:
        """
        参数提取评估器 - 检查提取的参数是否准确
        
        对比期望输出和实际输出
        """
        try:
            output = run.outputs.get("report", "") if run.outputs else ""
            expected = example.outputs.get("expected_params", {}) if example.outputs else {}
            
            if not output or not expected:
                return EvaluationResult(
                    key="parameter_extraction",
                    score=0,
                    comment="缺少输出或期望值"
                )
            
            # 解析输出
            try:
                actual = json.loads(output)
            except json.JSONDecodeError:
                return EvaluationResult(
                    key="parameter_extraction",
                    score=0,
                    comment="输出不是有效的 JSON"
                )
            
            # 对比每个字段
            total_fields = len(expected)
            correct_fields = 0
            errors = []
            
            for field, expected_value in expected.items():
                actual_value = actual.get(field, "")
                
                # 简单的字符串匹配（可根据需要增强）
                if str(actual_value).strip().lower() == str(expected_value).strip().lower():
                    correct_fields += 1
                else:
                    errors.append(f"{field}: 期望'{expected_value}' 实际'{actual_value}'")
            
            score = correct_fields / total_fields if total_fields > 0 else 0
            
            if score == 1.0:
                comment = "所有参数提取正确"
            else:
                comment = f"正确 {correct_fields}/{total_fields} 个参数。错误: {'; '.join(errors[:3])}"
            
            return EvaluationResult(
                key="parameter_extraction",
                score=score,
                comment=comment
            )
            
        except Exception as e:
            return EvaluationResult(
                key="parameter_extraction",
                score=0,
                comment=f"评估失败: {str(e)}"
            )
    
    @staticmethod
    @run_evaluator
    def field_type_evaluator(run, example) -> EvaluationResult:
        """
        字段类型评估器 - 检查字段值的类型和格式
        
        检查：
        - year_range 是否符合年份格式
        - style/depth 是否在允许的范围内
        """
        try:
            output = run.outputs.get("report", "") if run.outputs else ""
            
            if not output:
                return EvaluationResult(
                    key="field_type_valid",
                    score=0,
                    comment="输出为空"
                )
            
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                return EvaluationResult(
                    key="field_type_valid",
                    score=0,
                    comment="JSON 格式错误"
                )
            
            checks = {}
            
            # 检查 year_range 格式
            year_range = parsed.get("year_range", "")
            if year_range:
                # 简单检查是否包含数字
                has_numbers = any(char.isdigit() for char in str(year_range))
                checks["year_range_format"] = has_numbers
            else:
                checks["year_range_format"] = False
            
            # 检查 style（可选值）
            style = parsed.get("style", "").lower()
            valid_styles = ["专业", "通俗", "学术", "简洁", "detailed", "concise"]
            checks["style_valid"] = any(s in style for s in valid_styles) if style else True
            
            # 检查 depth（可选值）
            depth = parsed.get("depth", "").lower()
            valid_depths = ["简要", "详细", "深入", "brief", "detailed", "deep"]
            checks["depth_valid"] = any(d in depth for d in valid_depths) if depth else True
            
            passed = sum(checks.values())
            total = len(checks)
            score = passed / total
            
            failed = [k for k, v in checks.items() if not v]
            comment = f"通过 {passed}/{total} 项检查"
            if failed:
                comment += f"。未通过: {', '.join(failed)}"
            
            return EvaluationResult(
                key="field_type_valid",
                score=score,
                comment=comment
            )
            
        except Exception as e:
            return EvaluationResult(
                key="field_type_valid",
                score=0,
                comment=f"评估失败: {str(e)}"
            )


# 导出所有评估器
__all__ = ['ParameterEvaluators']

