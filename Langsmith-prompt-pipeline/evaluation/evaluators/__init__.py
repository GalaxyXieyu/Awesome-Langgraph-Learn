"""
评估器模块
按提示词类型组织的评估器集合

每个提示词有对应的评估器类：
- ReportEvaluators: 用于 report_generator
- ParameterEvaluators: 用于 parameter_parser
"""

from evaluation.evaluators.report import ReportEvaluators
from evaluation.evaluators.parameter import ParameterEvaluators

# 评估器注册表 - 根据名称获取评估器
EVALUATOR_REGISTRY = {
    # ReportEvaluators
    "structure_evaluator": ReportEvaluators.structure_evaluator,
    "content_completeness_evaluator": ReportEvaluators.content_completeness_evaluator,
    "relevance_evaluator": ReportEvaluators.relevance_evaluator,
    "parameter_usage_evaluator": ReportEvaluators.parameter_usage_evaluator,
    
    # ParameterEvaluators
    "parameter_extraction_evaluator": ParameterEvaluators.parameter_extraction_evaluator,
    "field_type_evaluator": ParameterEvaluators.field_type_evaluator,
}


def get_evaluator(name: str):
    """
    根据名称获取评估器
    
    Args:
        name: 评估器名称
        
    Returns:
        评估器函数
        
    Raises:
        KeyError: 如果评估器不存在
    """
    if name not in EVALUATOR_REGISTRY:
        raise KeyError(f"评估器 '{name}' 不存在。可用的评估器: {list(EVALUATOR_REGISTRY.keys())}")
    return EVALUATOR_REGISTRY[name]


def get_evaluators_for_prompt(prompt_config: dict) -> list:
    """
    根据提示词配置获取评估器列表
    
    Args:
        prompt_config: 提示词配置字典（来自 prompts_config.yaml）
        
    Returns:
        评估器列表
    """
    evaluator_names = prompt_config.get("evaluators", [])
    evaluators = []
    
    for name in evaluator_names:
        try:
            evaluators.append(get_evaluator(name))
        except KeyError as e:
            print(f"⚠️ 警告: {e}")
    
    return evaluators


__all__ = [
    'ReportEvaluators',
    'ParameterEvaluators',
    'EVALUATOR_REGISTRY',
    'get_evaluator',
    'get_evaluators_for_prompt',
]

