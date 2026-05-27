"""
LangGraph State 定义
定义报告生成流程中的状态结构
"""
from typing import TypedDict, List, Dict, Any, Optional


class ReportState(TypedDict):
    """
    报告生成流程的状态定义
    
    这个状态会在整个 Graph 流程中传递和更新
    """
    
    # 用户输入
    user_query: str  # 用户的原始查询
    
    # 解析后的参数
    topic: str  # 报告主题
    year_range: str  # 年份范围
    style: str  # 编写风格
    depth: str  # 分析深度
    focus_areas: str  # 关注领域
    
    # 中间数据
    search_query: str  # 构建的搜索查询
    search_results: List[Dict[str, Any]]  # 搜索结果列表
    search_results_formatted: str  # 格式化的搜索结果
    
    # 输出结果
    report: str  # 最终生成的报告
    
    # 元数据
    metadata: Dict[str, Any]  # 流程元数据（如耗时、token 数等）
    error: Optional[str]  # 错误信息（如果有）


class ReportStateUpdate(TypedDict, total=False):
    """
    状态更新定义（所有字段可选）
    用于节点返回部分状态更新
    """
    user_query: str
    topic: str
    year_range: str
    style: str
    depth: str
    focus_areas: str
    search_query: str
    search_results: List[Dict[str, Any]]
    search_results_formatted: str
    report: str
    metadata: Dict[str, Any]
    error: Optional[str]

