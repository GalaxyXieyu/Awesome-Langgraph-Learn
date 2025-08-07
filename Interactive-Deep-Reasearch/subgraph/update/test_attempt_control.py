"""
测试尝试次数控制逻辑
"""

from context_builder import build_supervisor_context, determine_next_action_by_state


def test_attempt_control():
    """测试尝试次数控制逻辑"""
    print("🧪 测试尝试次数控制逻辑...")
    
    # 测试场景1：第一次尝试研究
    print("\n=== 场景1：第一次尝试研究 ===")
    state1 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"}
        ],
        "current_section_index": 0,
        "research_results": {},
        "writing_results": {},
        "section_attempts": {},
        "topic": "人工智能发展",
        "iteration_count": 1,
        "max_iterations": 10,
        "execution_path": ["supervisor"]
    }
    
    context1 = build_supervisor_context(state1)
    action1, reason1 = determine_next_action_by_state(state1)
    print(f"决策: {action1} | 理由: {reason1}")
    print("当前章节信息:")
    print(context1["current_section_info"])
    
    # 测试场景2：研究尝试了3次但质量不达标
    print("\n=== 场景2：研究已达最大尝试次数 ===")
    state2 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "简短内容",  # 质量不达标但已尝试3次
                "timestamp": 1234567890
            }
        },
        "writing_results": {},
        "section_attempts": {
            "sec1": {"research": 3, "writing": 0}  # 已尝试3次研究
        },
        "topic": "人工智能发展",
        "iteration_count": 4,
        "max_iterations": 10,
        "execution_path": ["supervisor", "research", "research", "research"]
    }
    
    context2 = build_supervisor_context(state2)
    action2, reason2 = determine_next_action_by_state(state2)
    print(f"决策: {action2} | 理由: {reason2}")
    print("当前章节信息:")
    print(context2["current_section_info"])
    
    # 测试场景3：写作也达到最大尝试次数
    print("\n=== 场景3：写作也达到最大尝试次数 ===")
    state3 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"},
            {"id": "sec2", "title": "未来趋势", "description": "预测AI未来发展"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "研究内容",
                "timestamp": 1234567890
            }
        },
        "writing_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "写作内容",
                "word_count": 100,  # 质量不达标
                "timestamp": 1234567891
            }
        },
        "section_attempts": {
            "sec1": {"research": 3, "writing": 3}  # 都已尝试3次
        },
        "topic": "人工智能发展",
        "iteration_count": 7,
        "max_iterations": 10,
        "execution_path": ["supervisor"] * 7
    }
    
    context3 = build_supervisor_context(state3)
    action3, reason3 = determine_next_action_by_state(state3)
    print(f"决策: {action3} | 理由: {reason3}")
    print("当前章节信息:")
    print(context3["current_section_info"])
    
    # 测试场景4：正常完成流程
    print("\n=== 场景4：正常完成流程 ===")
    state4 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "详细的研究内容" * 50,
                "timestamp": 1234567890
            }
        },
        "writing_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "高质量的写作内容" * 30,
                "word_count": 600,
                "timestamp": 1234567891
            }
        },
        "section_attempts": {
            "sec1": {"research": 1, "writing": 1}  # 一次成功
        },
        "topic": "人工智能发展",
        "iteration_count": 3,
        "max_iterations": 10,
        "execution_path": ["supervisor", "research", "writing"]
    }
    
    context4 = build_supervisor_context(state4)
    action4, reason4 = determine_next_action_by_state(state4)
    print(f"决策: {action4} | 理由: {reason4}")
    print("当前章节信息:")
    print(context4["current_section_info"])


if __name__ == "__main__":
    test_attempt_control()
