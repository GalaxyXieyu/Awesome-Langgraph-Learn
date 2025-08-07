"""
测试target_section逻辑
"""

def test_target_section_logic():
    """测试目标章节逻辑"""
    print("🧪 测试target_section逻辑...")
    
    # 模拟sections数据
    sections = [
        {"id": "section_1", "title": "第一章：AI技术现状"},
        {"id": "section_2", "title": "第二章：未来趋势"},
        {"id": "section_3", "title": "第三章：应用案例"}
    ]
    
    # 模拟state
    state = {
        "sections": sections,
        "current_section_index": 0
    }
    
    # 模拟Supervisor返回的target_section
    target_section = "section_2"
    
    print(f"当前章节索引: {state['current_section_index']}")
    print(f"目标章节ID: {target_section}")
    
    # 查找目标章节的索引
    target_index = None
    for i, section in enumerate(sections):
        if section.get("id", "") == target_section:
            target_index = i
            break
    
    if target_index is not None:
        print(f"找到目标章节索引: {target_index}")
        print(f"目标章节标题: {sections[target_index]['title']}")
        
        # 更新章节索引
        old_index = state["current_section_index"]
        state["current_section_index"] = target_index
        
        print(f"章节索引已更新: {old_index} → {target_index}")
        print(f"当前章节: {sections[target_index]['title']}")
    else:
        print(f"未找到目标章节: {target_section}")
    
    return state


def test_section_progression():
    """测试章节进度逻辑"""
    print("\n🧪 测试章节进度逻辑...")
    
    sections = [
        {"id": "sec1", "title": "第一章"},
        {"id": "sec2", "title": "第二章"}
    ]
    
    # 场景1：第一章节完成，应该移动到第二章节
    state1 = {
        "sections": sections,
        "current_section_index": 0,
        "research_results": {"sec1": {"content": "研究内容"}},
        "writing_results": {"sec1": {"content": "写作内容", "word_count": 500}},
        "section_attempts": {"sec1": {"research": 1, "writing": 1}}
    }
    
    print("场景1：第一章节完成")
    print(f"当前索引: {state1['current_section_index']}")
    print(f"研究结果: {list(state1['research_results'].keys())}")
    print(f"写作结果: {list(state1['writing_results'].keys())}")
    
    # 模拟move_to_next_section逻辑
    current_index = state1["current_section_index"]
    new_index = current_index + 1
    
    if new_index < len(sections):
        state1["current_section_index"] = new_index
        print(f"移动到下一章节: {current_index} → {new_index}")
        print(f"新章节: {sections[new_index]['title']}")
    else:
        print("所有章节已完成")


if __name__ == "__main__":
    test_target_section_logic()
    test_section_progression()
