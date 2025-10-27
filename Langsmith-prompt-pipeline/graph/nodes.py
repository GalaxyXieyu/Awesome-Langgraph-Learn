"""
LangGraph 节点实现
定义报告生成流程中的各个节点
"""
from typing import Dict, Any
import json
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

from graph.state import ReportState, ReportStateUpdate
from config.azure_config import AzureConfig
from tools.search_tool import SearchTool
from prompts.prompt_manager import PromptManager
from tools.capture import capture_dataset, capture_inputs


class ReportNodes:
    """报告生成流程的节点集合"""
    
    def __init__(self, perplexity_api_key: str = None):
        """
        初始化节点所需的工具和配置
        
        Args:
            perplexity_api_key: Perplexity API Key（可选，默认从环境变量读取）
        """
        self.llm = AzureConfig.get_llm(temperature=0.7)
        self.fast_llm = AzureConfig.get_fast_llm()
        self.search_tool = SearchTool(
            use_perplexity=True,
            perplexity_api_key=perplexity_api_key  # 会自动从环境变量读取
        )
        self.prompt_manager = PromptManager()
    
    @traceable
    @capture_dataset(prompt_name="parameter_parser", dataset_name="parameter_parser")
    def parse_parameters_node(self, state: ReportState) -> ReportStateUpdate:
        """
        参数解析节点
        
        从用户的自然语言输入中提取结构化参数
        """
        print("\n[节点] 解析参数...")
        
        user_query = state.get("user_query", "")
        
        # 通过语义化名称获取 Prompt 配置
        prompt_config = self.prompt_manager.get('parameter_parser')
        
        # 准备输入参数
        user_inputs = {
            "user_query": user_query
        }
        
        # 捕获 inputs（用于 Dataset）
        capture_inputs(user_inputs, metadata={"prompt_version": prompt_config.get('version')})
        
        print(f"  使用 Prompt: {prompt_config.get('name')} {prompt_config.get('version')}")
        
        try:
            # 创建并格式化 Prompt（自动应用默认值）
            messages = self.prompt_manager.create_prompt(prompt_config, user_inputs)
            response = self.fast_llm.invoke(messages)
            
            # 清理响应（移除可能的 markdown 代码块标记）
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            params = json.loads(content)

            return {
                "topic": params.get("topic", "未指定主题"),
                "year_range": params.get("year_range", "2023-2024"),
                "style": params.get("style", "formal"),
                "depth": params.get("depth", "medium"),
                "focus_areas": params.get("focus_areas", "市场趋势,技术发展,竞争格局"),
                "metadata": state.get("metadata", {})
            }
            
        except Exception as e:
            print(f"⚠️ 参数解析失败: {e}")
            print("使用默认参数...")
            
            return {
                "topic": user_query,
                "year_range": "2023-2024",
                "style": "formal",
                "depth": "medium",
                "focus_areas": "市场趋势,技术发展,竞争格局",
                "error": f"参数解析失败: {str(e)}",
                "metadata": state.get("metadata", {})
            }
    
    def web_search_node(self, state: ReportState) -> ReportStateUpdate:
        """
        联网搜索节点
        
        根据主题和参数执行搜索，收集相关信息
        """
        print("\n[节点] 执行 Perplexity 搜索...")
        
        topic = state.get("topic", "")
        year_range = state.get("year_range", "")
        focus_areas = state.get("focus_areas", "")
        
        # 构建搜索查询
        search_query = f"{topic} {year_range} {focus_areas} 分析报告 最新数据"
        
        try:
            # 执行搜索
            results = self.search_tool.search(search_query, max_results=3)
            
            # 格式化搜索结果
            formatted_results = self.search_tool.format_search_results(results)
            
            return {
                "search_query": search_query,
                "search_results": results,
                "search_results_formatted": formatted_results,
                "metadata": state.get("metadata", {})
            }
            
        except Exception as e:
            print(f"⚠️ 搜索失败: {e}")
            
            return {
                "search_query": search_query,
                "search_results": [],
                "search_results_formatted": "搜索服务暂时不可用，将基于有限信息生成报告。",
                "error": f"搜索失败: {str(e)}",
                "metadata": state.get("metadata", {})
            }
    
    @traceable
    @capture_dataset(prompt_name="report_generator", dataset_name="report_generator")
    def generate_report_node(self, state: ReportState) -> ReportStateUpdate:
        """
        报告生成节点
        
        使用多参数 Prompt 生成报告
        """

        # 通过语义化名称获取 Prompt 配置
        prompt_config = self.prompt_manager.get('report_generator')
        
        # 准备输入参数
        user_inputs = {
            "topic": state.get("topic", ""),
            "year_range": state.get("year_range", ""),
            "style": state.get("style", "formal"),
            "depth": state.get("depth", "medium"),
            "focus_areas": state.get("focus_areas", ""),
            "search_results": state.get("search_results_formatted", "")
        }
        
        # 捕获 inputs（用于 Dataset）
        capture_inputs(user_inputs, metadata={
            "user_query": state.get("user_query", ""),
            "prompt_version": prompt_config.get("version")
        })

        try:
            # 方式1: 直接使用 create_prompt 格式化（推荐，简洁）
            # messages = self.prompt_manager.create_prompt(prompt_config, user_inputs)
            # report = self.llm.invoke(messages).content
            
            # 方式2: 使用链式调用（保留灵活性）
            prompt = self.prompt_manager.create_prompt(prompt_config)
            inputs = self.prompt_manager._get_prompt_with_defaults(prompt_config, user_inputs)
            chain = prompt | self.llm | StrOutputParser()
            report = chain.invoke(inputs)
            
            return {
                "report": report,
                "metadata": {
                    **state.get("metadata", {}),
                    "report_length": len(report),
                    "prompt_version": prompt_config.get("version")
                }
            }
            
        except Exception as e:
            print(f"✗ 报告生成失败: {e}")
            
            error_report = f"""
            # 报告生成失败

            抱歉，在生成报告时遇到了问题：{str(e)}

            **请求的参数**:
            - 主题: {inputs['topic']}
            - 年份范围: {inputs['year_range']}
            - 风格: {inputs['style']}
            - 深度: {inputs['depth']}
            - 关注领域: {inputs['focus_areas']}

            请检查配置或稍后重试。
            """
                        
            return {
                "report": error_report,
                "error": f"报告生成失败: {str(e)}",
                "metadata": state.get("metadata", {})
            }
    
    def quality_check_node(self, state: ReportState) -> ReportStateUpdate:
        """
        质量检查节点（可选）
        
        检查生成的报告是否符合基本质量标准
        """
        print("\n[节点] 质量检查...")
        
        report = state.get("report", "")
        
        # 基本检查
        checks = {
            "length": len(report) > 500,  # 长度检查
            "has_title": report.count("#") >= 3,  # 标题检查
            "has_content": len(report.split("\n")) > 10,  # 段落检查
        }
        
        all_passed = all(checks.values())
        
        if all_passed:
            print(f"✓ 质量检查通过")
        else:
            print(f"⚠️ 质量检查发现问题:")
            for check, passed in checks.items():
                if not passed:
                    print(f"  - {check}: 未通过")
        
        return {
            "metadata": {
                **state.get("metadata", {}),
                "quality_checks": checks,
                "quality_passed": all_passed
            }
        }


if __name__ == "__main__":
    # 测试节点
    print("测试报告生成节点...\n")
    
    nodes = ReportNodes()
    
    # 测试状态
    test_state: ReportState = {
        "user_query": "帮我写一份关于人工智能行业2023-2024年发展的详细分析报告，重点关注技术创新和市场规模",
        "topic": "",
        "year_range": "",
        "style": "",
        "depth": "",
        "focus_areas": "",
        "search_query": "",
        "search_results": [],
        "search_results_formatted": "",
        "report": "",
        "metadata": {},
        "error": None
    }
    
    # 测试参数解析
    result = nodes.parse_parameters_node(test_state)
    print(f"\n解析结果: {result}")
