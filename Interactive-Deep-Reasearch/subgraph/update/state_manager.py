"""
LangGraph State 管理工具
基于官方文档的最佳实践
"""

import asyncio
from typing import Dict, Any, List, Optional
from langgraph.checkpoint.memory import InMemorySaver
from graph import create_intelligent_research_graph, IntelligentResearchState


class StateManager:
    """LangGraph状态管理器"""
    
    def __init__(self, checkpointer=None):
        """
        初始化状态管理器
        
        Args:
            checkpointer: 检查点保存器，默认使用InMemorySaver
        """
        self.checkpointer = checkpointer or InMemorySaver()
        self.graph = None
        
    def create_graph(self):
        """创建并编译图"""
        workflow = create_intelligent_research_graph()
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        return self.graph
    
    def get_current_state(self, thread_id: str) -> Dict[str, Any]:
        """
        获取当前状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            当前状态快照
        """
        if not self.graph:
            raise ValueError("Graph not created. Call create_graph() first.")
            
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.graph.get_state(config)
        
        return {
            "values": snapshot.values,
            "next_nodes": snapshot.next,
            "config": snapshot.config,
            "metadata": snapshot.metadata,
            "created_at": snapshot.created_at,
            "tasks": snapshot.tasks
        }
    
    async def get_current_state_async(self, thread_id: str) -> Dict[str, Any]:
        """异步获取当前状态"""
        if not self.graph:
            raise ValueError("Graph not created. Call create_graph() first.")
            
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await self.graph.aget_state(config)
        
        return {
            "values": snapshot.values,
            "next_nodes": snapshot.next,
            "config": snapshot.config,
            "metadata": snapshot.metadata,
            "created_at": snapshot.created_at,
            "tasks": snapshot.tasks
        }
    
    def get_state_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取状态历史
        
        Args:
            thread_id: 线程ID
            limit: 限制返回数量
            
        Returns:
            状态历史列表（按时间倒序）
        """
        if not self.graph:
            raise ValueError("Graph not created. Call create_graph() first.")
            
        config = {"configurable": {"thread_id": thread_id}}
        history = list(self.graph.get_state_history(config, limit=limit))
        
        return [
            {
                "values": snapshot.values,
                "next_nodes": snapshot.next,
                "config": snapshot.config,
                "metadata": snapshot.metadata,
                "created_at": snapshot.created_at,
                "step": snapshot.metadata.get("step", -1)
            }
            for snapshot in history
        ]
    
    def update_state(self, thread_id: str, values: Dict[str, Any], as_node: Optional[str] = None):
        """
        更新状态
        
        Args:
            thread_id: 线程ID
            values: 要更新的值
            as_node: 作为哪个节点更新
            
        Returns:
            新的配置
        """
        if not self.graph:
            raise ValueError("Graph not created. Call create_graph() first.")
            
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.update_state(config, values, as_node=as_node)
    
    def get_final_report(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        获取最终报告（如果任务完成）
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最终报告或None
        """
        current_state = self.get_current_state(thread_id)
        values = current_state.get("values", {})
        
        if values.get("task_completed", False):
            return values.get("final_report")
        return None
    
    def get_progress_info(self, thread_id: str) -> Dict[str, Any]:
        """
        获取进度信息
        
        Args:
            thread_id: 线程ID
            
        Returns:
            进度信息字典
        """
        current_state = self.get_current_state(thread_id)
        values = current_state.get("values", {})
        
        sections = values.get("sections", [])
        current_index = values.get("current_section_index", 0)
        research_results = values.get("research_results", {})
        writing_results = values.get("writing_results", {})
        
        return {
            "total_sections": len(sections),
            "current_section": current_index,
            "completed_research": len(research_results),
            "completed_writing": len(writing_results),
            "task_completed": values.get("task_completed", False),
            "next_action": values.get("next_action", "unknown"),
            "current_section_title": sections[current_index].get("title", "") if current_index < len(sections) else "完成"
        }
    
    def print_state_summary(self, thread_id: str):
        """打印状态摘要"""
        try:
            progress = self.get_progress_info(thread_id)
            print(f"\n📊 线程 {thread_id} 状态摘要:")
            print(f"  总章节数: {progress['total_sections']}")
            print(f"  当前章节: {progress['current_section'] + 1}/{progress['total_sections']}")
            print(f"  当前章节标题: {progress['current_section_title']}")
            print(f"  已完成研究: {progress['completed_research']}")
            print(f"  已完成写作: {progress['completed_writing']}")
            print(f"  下一步行动: {progress['next_action']}")
            print(f"  任务完成: {'✅' if progress['task_completed'] else '❌'}")
            
            if progress['task_completed']:
                final_report = self.get_final_report(thread_id)
                if final_report:
                    print(f"  📄 最终报告: {final_report.get('title', '未知标题')}")
                    print(f"  📝 总字数: {final_report.get('total_words', 0)}")
                    
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")


# 使用示例
async def demo_state_management():
    """演示状态管理功能"""
    print("🧪 演示LangGraph状态管理...")
    
    # 创建状态管理器
    manager = StateManager()
    graph = manager.create_graph()
    
    # 创建初始状态
    initial_state = IntelligentResearchState(
        messages=[],
        user_input="人工智能发展趋势",
        topic="人工智能发展趋势",
        sections=[
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术"},
            {"id": "sec2", "title": "未来趋势", "description": "预测AI未来发展"}
        ],
        current_section_index=0,
        research_results={},
        writing_results={},
        polishing_results={},
        final_report={},
        execution_path=[],
        next_action="research",
        task_completed=False,
        error_log=[],
        section_attempts={}
    )
    
    thread_id = "demo_thread"
    config = {"configurable": {"thread_id": thread_id}}
    
    print("🚀 开始执行图...")
    
    # 异步执行图（模拟）
    step_count = 0
    async for event in graph.astream(initial_state, config=config):
        step_count += 1
        print(f"\n📝 步骤 {step_count}: {list(event.keys())}")
        
        # 获取当前状态
        current_state = await manager.get_current_state_async(thread_id)
        print(f"  当前状态值数量: {len(current_state['values'])}")
        print(f"  下一步节点: {current_state['next_nodes']}")
        
        # 打印进度信息
        manager.print_state_summary(thread_id)
        
        # 检查是否完成
        if current_state['values'].get('task_completed', False):
            print("✅ 任务完成！")
            break
            
        if step_count >= 5:  # 限制演示步数
            print("⚠️ 演示步数限制，停止执行")
            break
    
    # 获取状态历史
    print("\n📚 获取状态历史...")
    history = manager.get_state_history(thread_id, limit=3)
    for i, snapshot in enumerate(history):
        print(f"  历史 {i+1}: 步骤 {snapshot['step']}, 创建时间 {snapshot['created_at']}")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_state_management())
