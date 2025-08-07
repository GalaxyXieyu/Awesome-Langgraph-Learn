"""
测试章节切换逻辑
"""

from context_builder import build_supervisor_context, determine_next_action_by_state


def simulate_supervisor_decision(state):
    """模拟supervisor的决策过程"""
    print(f"\n🧠 Supervisor分析 - 当前章节索引: {state.get('current_section_index', 0)}")
    
    # 构建上下文
    context = build_supervisor_context(state)
    print("状态摘要:")
    print(context["status_summary"])
    print("\n当前章节信息:")
    print(context["current_section_info"])
    
    # 获取决策
    action, reason = determine_next_action_by_state(state)
    print(f"\n决策: {action}")
    print(f"理由: {reason}")
    
    # 模拟supervisor节点的章节切换逻辑
    if action == "move_to_next_section":
        current_index = state.get("current_section_index", 0)
        new_index = current_index + 1
        state["current_section_index"] = new_index
        action = "research"
        print(f"✅ 章节索引已更新: {current_index} → {new_index}")
        print(f"✅ 下一步行动: {action}")
    
    state["next_action"] = action
    return state


def test_section_switching():
    """测试完整的章节切换流程"""
    print("🧪 测试章节切换逻辑...")
    
    # 初始状态：两个章节
    state = {
        "sections": [
            {"id": "sec1", "title": "第一章：AI技术现状", "description": "分析当前AI技术发展"},
            {"id": "sec2", "title": "第二章：未来趋势", "description": "预测AI未来发展"}
        ],
        "current_section_index": 0,
        "research_results": {},
        "writing_results": {},
        "section_attempts": {},
        "topic": "人工智能发展",
        "iteration_count": 0,
        "max_iterations": 10,
        "execution_path": []
    }
    
    print("=== 初始状态 ===")
    state = simulate_supervisor_decision(state)
    
    # 模拟第一章节研究完成
    print("\n=== 第一章节研究完成 ===")
    state["research_results"]["sec1"] = {
        "title": "第一章：AI技术现状",
        "content": "详细的研究内容" * 50,
        "timestamp": 1234567890
    }
    state["section_attempts"]["sec1"] = {"research": 1, "writing": 0}
    state = simulate_supervisor_decision(state)
    
    # 模拟第一章节写作完成
    print("\n=== 第一章节写作完成 ===")
    state["writing_results"]["sec1"] = {
        "title": "第一章：AI技术现状",
        "content": "高质量的写作内容" * 30,
        "word_count": 600,
        "timestamp": 1234567891
    }
    state["section_attempts"]["sec1"]["writing"] = 1
    state = simulate_supervisor_decision(state)
    
    # 验证是否正确切换到第二章节
    print("\n=== 验证章节切换结果 ===")
    current_index = state.get("current_section_index", 0)
    sections = state.get("sections", [])
    
    if current_index < len(sections):
        current_section = sections[current_index]
        print(f"✅ 当前章节索引: {current_index}")
        print(f"✅ 当前章节标题: {current_section.get('title', '')}")
        print(f"✅ 下一步行动: {state.get('next_action', '')}")
    else:
        print("⚠️ 章节索引超出范围")
    
    # 模拟第二章节的处理
    print("\n=== 第二章节开始研究 ===")
    state = simulate_supervisor_decision(state)


def test_edge_cases():
    """测试边界情况"""
    print("\n🧪 测试边界情况...")
    
    # 测试：只有一个章节的情况
    print("\n=== 单章节完成后的处理 ===")
    state = {
        "sections": [
            {"id": "sec1", "title": "唯一章节", "description": "唯一的章节"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {"title": "唯一章节", "content": "内容" * 100, "timestamp": 123}
        },
        "writing_results": {
            "sec1": {"title": "唯一章节", "content": "内容" * 50, "word_count": 500, "timestamp": 124}
        },
        "section_attempts": {"sec1": {"research": 1, "writing": 1}},
        "topic": "测试主题",
        "iteration_count": 2,
        "max_iterations": 10,
        "execution_path": ["supervisor", "research", "writing"]
    }
    
    state = simulate_supervisor_decision(state)
    print(f"单章节完成后的决策: {state.get('next_action', '')}")


if __name__ == "__main__":
    test_section_switching()
    test_edge_cases()
