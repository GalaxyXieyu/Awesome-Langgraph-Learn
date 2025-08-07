"""
测试Supervisor决策逻辑
"""

from context_builder import build_supervisor_context


def test_supervisor_context():
    """测试supervisor上下文构建"""
    print("🧪 测试Supervisor上下文构建...")
    
    # 测试场景1：第一章节没有任何结果
    print("\n=== 场景1：第一章节未开始 ===")
    state1 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"},
            {"id": "sec2", "title": "未来趋势", "description": "预测AI未来发展"}
        ],
        "current_section_index": 0,
        "research_results": {},
        "writing_results": {},
        "topic": "人工智能发展",
        "iteration_count": 1,
        "max_iterations": 10,
        "execution_path": ["supervisor"]
    }
    
    context1 = build_supervisor_context(state1)
    print("状态摘要:")
    print(context1["status_summary"])
    print("\n当前章节信息:")
    print(context1["current_section_info"])
    
    # 测试场景2：第一章节研究完成，未开始写作
    print("\n=== 场景2：研究完成，未开始写作 ===")
    state2 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"},
            {"id": "sec2", "title": "未来趋势", "description": "预测AI未来发展"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "人工智能技术在2023年取得了重大突破。根据最新数据，全球AI市场规模达到1500亿美元，预计2025年将达到3900亿美元，年复合增长率38.1%。技术方面，大语言模型的参数规模不断扩大，GPT系列模型展现出强大的通用能力。在应用层面，AI技术在医疗、金融、教育等领域得到广泛应用，推动了产业数字化转型。算法优化使得AI模型的性能提升了300%，同时计算成本大幅降低。" * 2,  # 确保超过500字符
                "timestamp": 1234567890
            }
        },
        "writing_results": {},
        "topic": "人工智能发展",
        "iteration_count": 2,
        "max_iterations": 10,
        "execution_path": ["supervisor", "research"]
    }
    
    context2 = build_supervisor_context(state2)
    print("状态摘要:")
    print(context2["status_summary"])
    print("\n当前章节信息:")
    print(context2["current_section_info"])
    
    # 测试场景3：第一章节完全完成
    print("\n=== 场景3：第一章节完全完成 ===")
    state3 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"},
            {"id": "sec2", "title": "未来趋势", "description": "预测AI未来发展"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "详细的研究内容..." * 50,  # 确保超过500字符
                "timestamp": 1234567890
            }
        },
        "writing_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "基于研究数据的专业写作内容，包含详细分析和数据支撑..." * 20,
                "word_count": 800,
                "timestamp": 1234567891
            }
        },
        "topic": "人工智能发展",
        "iteration_count": 3,
        "max_iterations": 10,
        "execution_path": ["supervisor", "research", "writing"]
    }
    
    context3 = build_supervisor_context(state3)
    print("状态摘要:")
    print(context3["status_summary"])
    print("\n当前章节信息:")
    print(context3["current_section_info"])
    
    # 测试场景4：研究质量不达标
    print("\n=== 场景4：研究质量不达标 ===")
    state4 = {
        "sections": [
            {"id": "sec1", "title": "AI技术现状", "description": "分析当前AI技术发展"}
        ],
        "current_section_index": 0,
        "research_results": {
            "sec1": {
                "title": "AI技术现状",
                "content": "简短的研究内容，不够详细",  # 少于500字符
                "timestamp": 1234567890
            }
        },
        "writing_results": {},
        "topic": "人工智能发展",
        "iteration_count": 2,
        "max_iterations": 10,
        "execution_path": ["supervisor", "research"]
    }
    
    context4 = build_supervisor_context(state4)
    print("状态摘要:")
    print(context4["status_summary"])
    print("\n当前章节信息:")
    print(context4["current_section_info"])


if __name__ == "__main__":
    test_supervisor_context()
