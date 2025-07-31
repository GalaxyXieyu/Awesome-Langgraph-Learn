#!/usr/bin/env python3
"""
TEST_Interrupt_Mechanisms.py - LangGraph中断机制测试
测试动态中断、静态中断和Command恢复机制
验证人机交互(Human-in-the-loop)的实现方式
"""

import time
import uuid
from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


class InterruptTestState(TypedDict):
    """中断测试状态"""
    step: str
    data: str
    user_input: Optional[str]
    approval: Optional[str]
    counter: int
    log: List[str]


# ============================================================================
# 动态中断测试节点
# ============================================================================

def step1_generate_data(state: InterruptTestState) -> InterruptTestState:
    """步骤1：生成数据，然后中断等待用户确认"""
    state["log"].append(f"步骤1开始 - {time.strftime('%H:%M:%S')}")
    
    # 模拟数据生成
    generated_data = f"生成的数据内容 - {time.strftime('%H:%M:%S')}"
    state["data"] = generated_data
    state["step"] = "data_generated"
    
    state["log"].append(f"数据生成完成: {generated_data}")
    
    # 🔥 动态中断：等待用户确认数据
    user_decision = interrupt({
        "type": "data_approval",
        "message": "请确认生成的数据是否满意：",
        "data": generated_data,
        "options": {
            "approve": "批准数据，继续处理",
            "regenerate": "重新生成数据",
            "edit": "编辑数据内容"
        },
        "ui_hints": {
            "show_data_preview": True,
            "allow_inline_edit": True
        }
    })
    
    state["log"].append(f"用户决策: {user_decision}")
    
    # 处理用户决策
    if user_decision == "approve":
        state["approval"] = "approved"
        state["step"] = "data_approved"
    elif user_decision == "regenerate":
        state["approval"] = "regenerate_requested"
        state["step"] = "regeneration_needed"
    else:  # edit
        state["approval"] = "edit_requested"
        state["step"] = "edit_needed"
    
    state["counter"] += 1
    return state


def step2_process_data(state: InterruptTestState) -> InterruptTestState:
    """步骤2：处理数据"""
    if state["approval"] != "approved":
        state["log"].append("数据未批准，跳过处理步骤")
        return state
    
    state["log"].append(f"步骤2开始 - {time.strftime('%H:%M:%S')}")
    
    # 模拟数据处理
    processed_data = f"处理后的数据: {state['data']} -> 已处理"
    state["data"] = processed_data
    state["step"] = "data_processed"
    
    state["log"].append(f"数据处理完成: {processed_data}")
    return state


def step3_final_review(state: InterruptTestState) -> InterruptTestState:
    """步骤3：最终审核，再次中断"""
    if state["step"] != "data_processed":
        state["log"].append("数据未处理，跳过最终审核")
        return state
    
    state["log"].append(f"步骤3开始 - {time.strftime('%H:%M:%S')}")
    
    # 🔥 动态中断：最终审核
    final_decision = interrupt({
        "type": "final_approval",
        "message": "请进行最终审核：",
        "processed_data": state["data"],
        "processing_log": state["log"],
        "options": {
            "publish": "发布结果",
            "revise": "需要修改",
            "cancel": "取消操作"
        },
        "ui_hints": {
            "show_processing_history": True,
            "show_data_comparison": True
        }
    })
    
    state["log"].append(f"最终决策: {final_decision}")
    
    # 处理最终决策
    if final_decision == "publish":
        state["step"] = "published"
        state["approval"] = "published"
    elif final_decision == "revise":
        state["step"] = "revision_needed"
    else:  # cancel
        state["step"] = "cancelled"
    
    state["counter"] += 1
    return state


# ============================================================================
# 静态中断测试节点
# ============================================================================

def debug_step_a(state: InterruptTestState) -> InterruptTestState:
    """调试步骤A"""
    state["log"].append(f"执行调试步骤A - {time.strftime('%H:%M:%S')}")
    state["step"] = "debug_a_completed"
    print("🔧 调试步骤A完成")
    return state


def debug_step_b(state: InterruptTestState) -> InterruptTestState:
    """调试步骤B"""
    state["log"].append(f"执行调试步骤B - {time.strftime('%H:%M:%S')}")
    state["step"] = "debug_b_completed"
    print("🔧 调试步骤B完成")
    return state


def debug_step_c(state: InterruptTestState) -> InterruptTestState:
    """调试步骤C"""
    state["log"].append(f"执行调试步骤C - {time.strftime('%H:%M:%S')}")
    state["step"] = "debug_c_completed"
    print("🔧 调试步骤C完成")
    return state


# ============================================================================
# 创建测试图
# ============================================================================

def create_dynamic_interrupt_graph():
    """创建动态中断测试图"""
    workflow = StateGraph(InterruptTestState)
    
    workflow.add_node("step1", step1_generate_data)
    workflow.add_node("step2", step2_process_data)
    workflow.add_node("step3", step3_final_review)
    
    workflow.set_entry_point("step1")
    workflow.add_edge("step1", "step2")
    workflow.add_edge("step2", "step3")
    workflow.add_edge("step3", END)
    
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def create_static_interrupt_graph():
    """创建静态中断测试图"""
    workflow = StateGraph(InterruptTestState)
    
    workflow.add_node("debug_a", debug_step_a)
    workflow.add_node("debug_b", debug_step_b)
    workflow.add_node("debug_c", debug_step_c)
    
    workflow.set_entry_point("debug_a")
    workflow.add_edge("debug_a", "debug_b")
    workflow.add_edge("debug_b", "debug_c")
    workflow.add_edge("debug_c", END)
    
    checkpointer = InMemorySaver()
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["debug_b"],  # 在debug_b之前中断
        interrupt_after=["debug_c"]    # 在debug_c之后中断
    )


def initialize_state() -> InterruptTestState:
    """初始化状态"""
    return InterruptTestState(
        step="initialized",
        data="",
        user_input=None,
        approval=None,
        counter=0,
        log=[f"状态初始化 - {time.strftime('%H:%M:%S')}"]
    )


# ============================================================================
# 测试函数
# ============================================================================

def test_dynamic_interrupts():
    """测试动态中断"""
    print("🔄 动态中断测试 - 人机交互模式")
    print("-" * 50)
    
    graph = create_dynamic_interrupt_graph()
    initial_state = initialize_state()
    config = {"configurable": {"thread_id": f"dynamic_{uuid.uuid4()}"}}
    
    print("🚀 第一阶段：执行到第一个中断点")
    result1 = graph.invoke(initial_state, config)
    
    if "__interrupt__" in result1:
        interrupt_info = result1["__interrupt__"][0]
        print(f"✅ 成功触发第一个中断！")
        print(f"📋 中断类型: {interrupt_info.value.get('type')}")
        print(f"💬 中断消息: {interrupt_info.value.get('message')}")
        print(f"📊 生成数据: {interrupt_info.value.get('data')}")
        
        # 模拟用户批准
        print(f"\n👤 用户决策：批准数据")
        result2 = graph.invoke(Command(resume="approve"), config)
        
        if "__interrupt__" in result2:
            interrupt_info_2 = result2["__interrupt__"][0]
            print(f"✅ 成功触发第二个中断！")
            print(f"📋 中断类型: {interrupt_info_2.value.get('type')}")
            print(f"💬 中断消息: {interrupt_info_2.value.get('message')}")
            
            # 模拟用户发布
            print(f"\n👤 用户决策：发布结果")
            final_result = graph.invoke(Command(resume="publish"), config)
            
            print(f"🎉 动态中断测试完成！")
            print(f"📊 最终状态: {final_result.get('step')}")
            print(f"🔢 中断次数: {final_result.get('counter')}")
            
            # 显示执行日志
            print(f"\n📋 执行日志:")
            for i, log in enumerate(final_result.get('log', []), 1):
                print(f"   {i}. {log}")
            
            return True
    
    return False


def test_static_interrupts():
    """测试静态中断"""
    print("\n🔧 静态中断测试 - 调试模式")
    print("-" * 50)
    
    graph = create_static_interrupt_graph()
    initial_state = initialize_state()
    config = {"configurable": {"thread_id": f"static_{uuid.uuid4()}"}}
    
    print("🚀 第一阶段：执行到debug_b之前的中断点")
    result1 = graph.invoke(initial_state, config)
    print(f"📊 当前状态: {result1.get('step')}")
    
    print(f"\n🚀 第二阶段：继续执行到debug_c之后的中断点")
    result2 = graph.invoke(None, config)  # 传入None继续执行
    print(f"📊 当前状态: {result2.get('step')}")
    
    print(f"\n🚀 第三阶段：完成剩余执行")
    final_result = graph.invoke(None, config)
    print(f"📊 最终状态: {final_result.get('step')}")
    
    # 显示执行日志
    print(f"\n📋 执行日志:")
    for i, log in enumerate(final_result.get('log', []), 1):
        print(f"   {i}. {log}")
    
    return True


def test_input_validation():
    """测试输入验证中断"""
    print("\n✅ 输入验证测试 - 循环中断模式")
    print("-" * 50)
    
    def validation_node(state: InterruptTestState) -> InterruptTestState:
        """带输入验证的中断节点"""
        state["log"].append("开始输入验证流程")
        
        # 模拟验证循环
        attempts = 0
        while attempts < 3:  # 最多3次尝试
            user_input = interrupt({
                "type": "input_validation",
                "message": f"请输入一个正整数（1-100），尝试 {attempts + 1}/3：",
                "validation_rules": [
                    "必须是数字",
                    "范围在1-100之间",
                    "不能为空"
                ],
                "current_attempt": attempts + 1,
                "max_attempts": 3
            })
            
            try:
                number = int(user_input)
                if 1 <= number <= 100:
                    state["user_input"] = str(number)
                    state["log"].append(f"有效输入: {number}")
                    break
                else:
                    state["log"].append(f"无效输入: {number} (超出范围)")
            except (ValueError, TypeError):
                state["log"].append(f"无效输入: {user_input} (非数字)")
            
            attempts += 1
        
        if attempts >= 3:
            state["step"] = "validation_failed"
            state["log"].append("验证失败：超过最大尝试次数")
        else:
            state["step"] = "validation_completed"
        
        return state
    
    # 创建验证测试图
    workflow = StateGraph(InterruptTestState)
    workflow.add_node("validate", validation_node)
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", END)
    
    checkpointer = InMemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    
    initial_state = initialize_state()
    config = {"configurable": {"thread_id": f"validation_{uuid.uuid4()}"}}
    
    # 模拟验证过程
    print("🚀 开始输入验证")
    
    # 第一次：无效输入
    result1 = graph.invoke(initial_state, config)
    if "__interrupt__" in result1:
        print("✅ 触发验证中断")
        
        # 输入无效数据
        result2 = graph.invoke(Command(resume="abc"), config)
        if "__interrupt__" in result2:
            print("✅ 验证失败，再次中断")
            
            # 输入有效数据
            final_result = graph.invoke(Command(resume="42"), config)
            print(f"🎉 验证成功！用户输入: {final_result.get('user_input')}")
            
            # 显示验证日志
            print(f"\n📋 验证日志:")
            for i, log in enumerate(final_result.get('log', []), 1):
                print(f"   {i}. {log}")
            
            return True
    
    return False


def main():
    """主测试函数"""
    print("🎯 LangGraph中断机制全面测试")
    print("=" * 80)
    print("🔬 测试内容:")
    print("   1. 动态中断 - 生产环境的人机交互")
    print("   2. 静态中断 - 开发调试的步进执行")
    print("   3. 输入验证 - 循环中断直到输入有效")
    print("=" * 80)
    
    # 测试动态中断
    try:
        dynamic_success = test_dynamic_interrupts()
        print(f"\n✅ 动态中断测试: {'成功' if dynamic_success else '失败'}")
    except Exception as e:
        print(f"\n❌ 动态中断测试失败: {str(e)}")
    
    # 测试静态中断
    try:
        static_success = test_static_interrupts()
        print(f"\n✅ 静态中断测试: {'成功' if static_success else '失败'}")
    except Exception as e:
        print(f"\n❌ 静态中断测试失败: {str(e)}")
    
    # 测试输入验证
    try:
        validation_success = test_input_validation()
        print(f"\n✅ 输入验证测试: {'成功' if validation_success else '失败'}")
    except Exception as e:
        print(f"\n❌ 输入验证测试失败: {str(e)}")
    
    print(f"\n💡 中断机制总结:")
    print(f"   🔄 动态中断: 生产环境的人机交互，支持复杂决策")
    print(f"   🔧 静态中断: 开发调试的步进执行，简单继续/停止")
    print(f"   ✅ 输入验证: 循环中断直到输入有效，确保数据质量")
    print(f"   🎯 最佳实践: 动态中断用于生产，静态中断用于调试")


if __name__ == "__main__":
    main()
