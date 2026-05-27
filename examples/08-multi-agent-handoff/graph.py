"""
Multi-Agent Handoff图实现

展示了如何使用LangGraph创建包含多个React Agent的交互系统
"""

from typing import Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from state import MultiAgentState, create_initial_state
from tools import (
    transfer_to_researcher, transfer_to_analyst, transfer_to_writer, transfer_to_supervisor,
    get_agent_status, get_handoff_history, update_shared_context, get_shared_context,
    search_information, analyze_data, generate_content
)


# 配置LLM - 可以根据需要选择不同的模型
def get_llm(model_type: str = "openai"):
    """获取LLM实例"""
    if model_type == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini",  # 或其他OpenAI模型
            temperature=0.1
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


class MultiAgentSystem:
    """多智能体系统"""
    
    def __init__(self, llm_type: str = "openai"):
        self.llm = get_llm(llm_type)
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """创建多智能体图"""
        
        # 创建各个专业Agent
        supervisor_agent = self._create_supervisor_agent()
        researcher_agent = self._create_researcher_agent()
        analyst_agent = self._create_analyst_agent()
        writer_agent = self._create_writer_agent()
        
        # 创建状态图
        workflow = StateGraph(MultiAgentState)
        
        # 添加节点
        workflow.add_node("supervisor", supervisor_agent)
        workflow.add_node("researcher", researcher_agent)
        workflow.add_node("analyst", analyst_agent)
        workflow.add_node("writer", writer_agent)
        
        # 设置入口点
        workflow.add_edge(START, "supervisor")
        
        # 添加条件边 - 基于active_agent字段路由
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {
                "researcher": "researcher",
                "analyst": "analyst", 
                "writer": "writer",
                "supervisor": "supervisor",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "researcher",
            self._route_to_agent,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer", 
                "supervisor": "supervisor",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "analyst",
            self._route_to_agent,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "supervisor": "supervisor", 
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "writer",
            self._route_to_agent,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "supervisor": "supervisor",
                "END": END
            }
        )
        
        # 编译图
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _route_to_agent(self, state: MultiAgentState) -> Literal["researcher", "analyst", "writer", "supervisor", "END"]:
        """路由逻辑 - 根据active_agent决定下一步"""
        
        # 检查是否有明确的结束信号
        if state.system_status == "completed":
            return "END"
            
        # 如果没有消息或最后一条消息来自人类，保持当前agent
        if not state.messages:
            return state.active_agent
            
        last_message = state.messages[-1]
        
        # 如果最后消息是工具调用结果，检查是否有handoff
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            # 这里可以添加更复杂的路由逻辑
            pass
            
        # 默认路由到active_agent
        active = state.active_agent
        if active in ["researcher", "analyst", "writer", "supervisor"]:
            return active
        else:
            return "supervisor"  # 默认回到supervisor
    
    def _create_supervisor_agent(self):
        """创建监督者Agent"""
        supervisor_tools = [
            transfer_to_researcher,
            transfer_to_analyst, 
            transfer_to_writer,
            get_agent_status,
            get_handoff_history,
            update_shared_context,
            get_shared_context
        ]
        
        supervisor_prompt = """你是一个多智能体系统的监督者。你的职责是：

1. 理解用户的需求和任务
2. 决定将任务分配给哪个专业agent
3. 协调各个agents之间的协作
4. 监控任务进度并提供总结

可用的专业agents：
- researcher: 负责信息搜索、资料收集和研究分析
- analyst: 负责数据分析、统计分析和深度洞察  
- writer: 负责内容创作、文档编写和内容编辑

当你需要将任务转交给其他agent时，请使用相应的transfer工具，并说明转交的原因和上下文。

当所有子任务完成后，请提供一个完整的总结报告。
"""
        
        return create_react_agent(
            self.llm,
            supervisor_tools,
            prompt=supervisor_prompt
        )
    
    def _create_researcher_agent(self):
        """创建研究者Agent"""
        researcher_tools = [
            search_information,
            transfer_to_analyst,
            transfer_to_writer,
            transfer_to_supervisor,
            update_shared_context,
            get_shared_context
        ]
        
        researcher_prompt = """你是一个专业的研究者Agent。你的专长包括：

1. 信息搜索和资料收集
2. 文献调研和资料整理
3. 研究方法设计和执行
4. 数据收集和初步处理

当你完成研究任务后：
- 如果需要进一步的数据分析，请转交给analyst
- 如果需要撰写研究报告，请转交给writer
- 如果任务已完成，请转交回supervisor进行总结

请始终保持客观、严谨的研究态度，确保信息的准确性和可靠性。
"""
        
        return create_react_agent(
            self.llm,
            researcher_tools,
            prompt=researcher_prompt
        )
    
    def _create_analyst_agent(self):
        """创建分析者Agent"""
        analyst_tools = [
            analyze_data,
            transfer_to_researcher,
            transfer_to_writer,
            transfer_to_supervisor,
            update_shared_context,
            get_shared_context
        ]
        
        analyst_prompt = """你是一个专业的数据分析师Agent。你的专长包括：

1. 数据分析和统计分析
2. 模式识别和趋势预测
3. 数据可视化和解释
4. 洞察提取和建议提供

当你完成分析任务后：
- 如果需要更多数据或资料，请转交给researcher
- 如果需要撰写分析报告，请转交给writer  
- 如果任务已完成，请转交回supervisor进行总结

请确保你的分析结果准确、客观，并提供明确的见解和建议。
"""
        
        return create_react_agent(
            self.llm,
            analyst_tools,
            prompt=analyst_prompt
        )
    
    def _create_writer_agent(self):
        """创建写作者Agent"""
        writer_tools = [
            generate_content,
            transfer_to_researcher,
            transfer_to_analyst,
            transfer_to_supervisor,
            update_shared_context,
            get_shared_context
        ]
        
        writer_prompt = """你是一个专业的内容创作者Agent。你的专长包括：

1. 各类文档和报告的写作
2. 内容结构化和组织
3. 语言表达优化和编辑
4. 根据目标受众调整写作风格

当你完成写作任务后：
- 如果需要更多素材或数据，请转交给researcher或analyst
- 如果内容已完成，请转交回supervisor进行总结和审核

请确保你的内容结构清晰、表达准确、风格适合目标受众。
"""
        
        return create_react_agent(
            self.llm,
            writer_tools,
            prompt=writer_prompt
        )
    
    def run(self, user_input: str, config: dict = None):
        """运行多智能体系统"""
        if config is None:
            config = {"configurable": {"thread_id": "multi-agent-handoff"}}
        
        # 创建初始状态
        initial_state = create_initial_state()
        initial_state.messages = [{"role": "human", "content": user_input}]
        initial_state.current_task = user_input
        initial_state.system_status = "processing"
        
        # 运行图
        result = self.graph.invoke(initial_state, config=config)
        return result
    
    def stream(self, user_input: str, config: dict = None):
        """流式运行多智能体系统"""
        if config is None:
            config = {"configurable": {"thread_id": "multi-agent-handoff"}}
        
        # 创建初始状态
        initial_state = create_initial_state()
        initial_state.messages = [{"role": "human", "content": user_input}]
        initial_state.current_task = user_input
        initial_state.system_status = "processing"
        
        # 流式运行图
        for chunk in self.graph.stream(initial_state, config=config):
            yield chunk


def create_multi_agent_system(llm_type: str = "openai") -> MultiAgentSystem:
    """创建多智能体系统实例"""
    return MultiAgentSystem(llm_type=llm_type)


if __name__ == "__main__":
    # 简单测试
    system = create_multi_agent_system()
    result = system.run("请帮我研究一下人工智能在医疗领域的应用，并写一份简要报告")
    
    print("=== 最终结果 ===")
    if result.get("messages"):
        print(result["messages"][-1]["content"])
    
    print("\n=== Handoff历史 ===")
    for handoff in result.get("handoff_history", []):
        print(f"{handoff.from_agent} -> {handoff.to_agent}: {handoff.reason}")