"""
LangGraph 主流程定义
构建完整的报告生成工作流
"""
from typing import Dict, Any, AsyncIterator
from langgraph.graph import StateGraph, END

from graph.state import ReportState
from graph.nodes import ReportNodes


class ReportGraphBuilder:
    """报告生成 Graph 构建器"""
    
    def __init__(self):
        """初始化 Graph 构建器"""
        self.nodes = ReportNodes()
    
    def build_graph(self) -> StateGraph:
        """
        构建报告生成工作流图
        
        流程:
        1. parse_parameters: 解析用户输入，提取参数
        2. web_search: 执行联网搜索
        3. generate_report: 使用多参数 Prompt 生成报告
        4. quality_check: 检查报告质量
        5. END: 结束
        
        Returns:
            编译后的 Graph
        """
        # 创建 StateGraph
        workflow = StateGraph(ReportState)
        
        # 添加节点
        workflow.add_node("parse_parameters", self.nodes.parse_parameters_node)
        workflow.add_node("web_search", self.nodes.web_search_node)
        workflow.add_node("generate_report", self.nodes.generate_report_node)
        workflow.add_node("quality_check", self.nodes.quality_check_node)
        
        # 设置入口点
        workflow.set_entry_point("parse_parameters")
        
        # 添加边（定义流程）
        workflow.add_edge("parse_parameters", "web_search")
        workflow.add_edge("web_search", "generate_report")
        workflow.add_edge("generate_report", "quality_check")
        workflow.add_edge("quality_check", END)
        
        # 编译图
        app = workflow.compile()
        
        print("✓ LangGraph 工作流构建完成")
        print("  节点: parse_parameters -> web_search -> generate_report -> quality_check")
        
        return app
    
    def run(self, user_query: str, **kwargs) -> Dict[str, Any]:
        """
        运行报告生成流程
        
        Args:
            user_query: 用户查询
            **kwargs: 额外的初始状态参数
            
        Returns:
            最终状态
        """
        # 构建 Graph
        app = self.build_graph()
        
        # 初始化状态
        initial_state: ReportState = {
            "user_query": user_query,
            "topic": kwargs.get("topic", ""),
            "year_range": kwargs.get("year_range", ""),
            "style": kwargs.get("style", ""),
            "depth": kwargs.get("depth", ""),
            "focus_areas": kwargs.get("focus_areas", ""),
            "search_query": "",
            "search_results": [],
            "search_results_formatted": "",
            "report": "",
            "metadata": {},
            "error": None
        }
        
        print("\n" + "="*60)
        print("开始运行报告生成流程")
        print("="*60)
        print(f"用户查询: {user_query}")
        
        # 运行 Graph
        try:
            final_state = app.invoke(initial_state)
            
            print("\n" + "="*60)
            print("流程执行完成")
            print("="*60)
            
            # 显示摘要
            if final_state.get("error"):
                print(f"⚠️ 执行过程中有错误: {final_state['error']}")
            else:
                print("✓ 报告生成成功")
            
            metadata = final_state.get("metadata", {})
            print(f"\n元数据:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            
            return final_state
            
        except Exception as e:
            print(f"\n✗ 流程执行失败: {e}")
            raise
    
    async def arun(self, user_query: str, **kwargs) -> Dict[str, Any]:
        """
        异步流式运行报告生成流程
        
        Args:
            user_query: 用户查询
            **kwargs: 额外的初始状态参数
            
        Returns:
            最终状态
        """
        # 构建 Graph
        app = self.build_graph()
        
        # 初始化状态
        initial_state: ReportState = {
            "user_query": user_query,
            "topic": kwargs.get("topic", ""),
            "year_range": kwargs.get("year_range", ""),
            "style": kwargs.get("style", ""),
            "depth": kwargs.get("depth", ""),
            "focus_areas": kwargs.get("focus_areas", ""),
            "search_query": "",
            "search_results": [],
            "search_results_formatted": "",
            "report": "",
            "metadata": {},
            "error": None
        }
        
        print("\n" + "="*60)
        print("开始运行报告生成流程 (流式输出)")
        print("="*60)
        print(f"用户查询: {user_query}")
        
        # 使用 astream 流式运行 Graph
        try:
            final_state = None
            async for chunk in app.astream(initial_state):
                # chunk 是一个字典，键是节点名称，值是该节点的输出状态
                for node_name, node_output in chunk.items():
                    print(f"\n{'='*60}")
                    print(f"节点: {node_name}")
                    print(f"{'='*60}")
                    
                    # 显示关键状态更新
                    if "search_query" in node_output and node_output["search_query"]:
                        print(f"  搜索查询: {node_output['search_query']}")
                    
                    if "search_results" in node_output and node_output["search_results"]:
                        print(f"  搜索结果数: {len(node_output['search_results'])}")
                    
                    if "topic" in node_output and node_output["topic"]:
                        print(f"  主题: {node_output['topic']}")
                    
                    if "year_range" in node_output and node_output["year_range"]:
                        print(f"  年份范围: {node_output['year_range']}")
                    
                    if "style" in node_output and node_output["style"]:
                        print(f"  风格: {node_output['style']}")
                    
                    if "report" in node_output and node_output["report"]:
                        report_preview = node_output["report"][:200]
                        print(f"  报告预览: {report_preview}...")
                    
                    if "metadata" in node_output and node_output["metadata"]:
                        print(f"  元数据: {node_output['metadata']}")
                    
                    if "error" in node_output and node_output["error"]:
                        print(f"  ⚠️ 错误: {node_output['error']}")
                    
                    # 保存最后的状态
                    final_state = node_output
            
            print("\n" + "="*60)
            print("流程执行完成")
            print("="*60)
            
            # 显示摘要
            if final_state:
                if final_state.get("error"):
                    print(f"⚠️ 执行过程中有错误: {final_state['error']}")
                else:
                    print("✓ 报告生成成功")
                
                metadata = final_state.get("metadata", {})
                if metadata:
                    print(f"\n元数据:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                
                return final_state
            else:
                return {}
            
        except Exception as e:
            print(f"\n✗ 流程执行失败: {e}")
            raise


def create_report_graph() -> StateGraph:
    """
    便捷函数：创建报告生成 Graph
    
    Returns:
        编译后的 Graph
    """
    builder = ReportGraphBuilder()
    return builder.build_graph()


if __name__ == "__main__":
    import asyncio
    
    # 测试 Graph
    print("测试报告生成 Graph...\n")
    print("选择测试模式:")
    print("1. 同步模式 (invoke)")
    print("2. 异步流式模式 (astream)")
    
    # 创建 Graph 构建器
    builder = ReportGraphBuilder()
    
    # 默认使用异步流式模式
    async def test_astream():
        result = await builder.arun(
            user_query="帮我写一份人工智能行业2023-2024年发展的详细分析报告，关注技术创新和市场趋势"
        )
        
        # 输出完整报告
        if result.get("report"):
            print("\n" + "="*60)
            print("生成的完整报告")
            print("="*60)
            print(result["report"])
    
    def test_sync():
        result = builder.run(
            user_query="帮我写一份人工智能行业2023-2024年发展的详细分析报告，关注技术创新和市场趋势"
        )
        
        # 输出报告预览
        if result.get("report"):
            print("\n" + "="*60)
            print("生成的报告预览")
            print("="*60)
            report = result["report"]
            preview_length = 800
            print(report[:preview_length])
            if len(report) > preview_length:
                print(f"\n... (还有 {len(report) - preview_length} 字符)")
    
    # 默认运行异步流式模式
    print("\n使用异步流式模式 (astream)...")
    asyncio.run(test_astream())

