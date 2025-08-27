"""
PostgreSQL Checkpoint 使用示例
演示如何在研究系统中使用自定义 checkpoint 功能
"""
import os
import uuid
from datetime import datetime
from config.checkpoint import ResearchPostgresSaver


def example_research_session():
    """模拟一个研究会话的完整流程"""
    print("=" * 60)
    print("🔬 研究会话示例")
    print("=" * 60)
    
    # 初始化 checkpointer
    checkpointer = ResearchPostgresSaver()
    checkpointer.setup()
    
    # 模拟用户开始一个新的研究任务
    session_id = f"research_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    user_id = "researcher_001"
    topic = "大语言模型在科学研究中的应用"
    
    print(f"👤 用户: {user_id}")
    print(f"📋 研究主题: {topic}")
    print(f"🆔 会话ID: {session_id}")
    print()
    
    # 阶段1: 大纲生成
    print("📝 阶段1: 生成研究大纲...")
    config_1 = {
        "configurable": {
            "thread_id": thread_id,
            "session_id": session_id,
            "user_id": user_id,
            "topic": topic,
            "task_type": "outline_generation"
        }
    }
    
    checkpoint_1 = {
        "v": 4,
        "ts": datetime.now().isoformat(),
        "id": f"checkpoint_{uuid.uuid4().hex[:8]}",
        "channel_values": {
            "topic": topic,
            "current_step": "outline_generation",
            "messages": [
                {"role": "user", "content": f"请研究: {topic}"},
                {"role": "assistant", "content": "我将为您生成研究大纲..."}
            ],
            "outline": {
                "sections": [
                    {"title": "大语言模型概述", "description": "介绍大语言模型的基本概念和发展历程"},
                    {"title": "科学研究应用场景", "description": "分析大语言模型在各科学领域的具体应用"},
                    {"title": "技术挑战与解决方案", "description": "讨论当前面临的技术难题和可能的解决路径"},
                    {"title": "未来发展趋势", "description": "预测大语言模型在科学研究中的发展方向"}
                ]
            }
        },
        "channel_versions": {"__start__": 1, "topic": 1, "messages": 1, "outline": 1},
        "versions_seen": {"__input__": {}, "__start__": {"__start__": 1}}
    }
    
    metadata_1 = {"step": 1, "node_name": "outline_generator", "timestamp": datetime.now().isoformat()}
    
    # 存储第一个 checkpoint
    checkpointer.put(config_1, checkpoint_1, metadata_1, {})
    print("✅ 大纲生成完成，checkpoint 已保存")
    
    # 阶段2: 网络搜索
    print("\n🔍 阶段2: 执行网络搜索...")
    config_2 = config_1.copy()
    config_2["configurable"]["task_type"] = "web_search"
    
    checkpoint_2 = checkpoint_1.copy()
    checkpoint_2.update({
        "ts": datetime.now().isoformat(),
        "id": f"checkpoint_{uuid.uuid4().hex[:8]}",
        "channel_values": {
            **checkpoint_1["channel_values"],
            "current_step": "web_search",
            "search_results": [
                {
                    "title": "大语言模型在生物信息学中的应用",
                    "url": "https://example.com/bio-llm",
                    "summary": "研究显示大语言模型在蛋白质结构预测方面表现出色...",
                    "relevance_score": 0.95
                },
                {
                    "title": "AI辅助科学发现的最新进展",
                    "url": "https://example.com/ai-science",
                    "summary": "人工智能正在革命性地改变科学研究方法...",
                    "relevance_score": 0.88
                }
            ]
        },
        "channel_versions": {**checkpoint_1["channel_versions"], "search_results": 1}
    })
    
    metadata_2 = {"step": 2, "node_name": "web_searcher", "timestamp": datetime.now().isoformat()}
    
    # 存储第二个 checkpoint
    checkpointer.put(config_2, checkpoint_2, metadata_2, {})
    print("✅ 网络搜索完成，checkpoint 已保存")
    
    # 阶段3: 分析和写作
    print("\n✍️ 阶段3: 分析和写作...")
    config_3 = config_1.copy()
    config_3["configurable"]["task_type"] = "writing"
    
    checkpoint_3 = checkpoint_2.copy()
    checkpoint_3.update({
        "ts": datetime.now().isoformat(),
        "id": f"checkpoint_{uuid.uuid4().hex[:8]}",
        "channel_values": {
            **checkpoint_2["channel_values"],
            "current_step": "writing",
            "report_sections": [
                {
                    "title": "大语言模型概述",
                    "content": "大语言模型（Large Language Models, LLMs）是基于深度学习的自然语言处理模型...",
                    "word_count": 500,
                    "status": "completed"
                },
                {
                    "title": "科学研究应用场景",
                    "content": "在生物信息学领域，大语言模型展现出了巨大的潜力...",
                    "word_count": 750,
                    "status": "in_progress"
                }
            ]
        },
        "channel_versions": {**checkpoint_2["channel_versions"], "report_sections": 1}
    })
    
    metadata_3 = {"step": 3, "node_name": "writer", "timestamp": datetime.now().isoformat()}
    
    # 存储第三个 checkpoint
    checkpointer.put(config_3, checkpoint_3, metadata_3, {})
    print("✅ 写作进度已保存，checkpoint 已保存")
    
    # 完成会话
    checkpointer.update_session_status(session_id, "completed")
    print("\n🎉 研究会话完成！")
    
    return session_id, user_id


def demonstrate_query_features(session_id: str, user_id: str):
    """演示查询功能"""
    print("\n" + "=" * 60)
    print("📊 查询功能演示")
    print("=" * 60)
    
    checkpointer = ResearchPostgresSaver()
    
    # 查询用户的所有会话
    print(f"\n👤 查询用户 {user_id} 的会话历史:")
    sessions = checkpointer.get_user_sessions(user_id, limit=5)
    for session in sessions:
        print(f"  📋 {session['session_id']}: {session['topic']}")
        print(f"     状态: {session['status']}, 创建时间: {session['created_at']}")
    
    # 查询特定会话信息
    print(f"\n📊 查询会话 {session_id} 的详细信息:")
    session_info = checkpointer.get_session_info(session_id)
    if session_info:
        print(f"  主题: {session_info['topic']}")
        print(f"  状态: {session_info['status']}")
        print(f"  创建时间: {session_info['created_at']}")
        print(f"  更新时间: {session_info['updated_at']}")


def main():
    """主函数"""
    # 确保启用 PostgreSQL checkpoint
    os.environ['USE_POSTGRES_CHECKPOINT'] = 'true'
    
    # 运行研究会话示例
    session_id, user_id = example_research_session()
    
    # 演示查询功能
    demonstrate_query_features(session_id, user_id)
    
    print("\n" + "=" * 60)
    print("✨ 示例完成！你现在可以:")
    print("1. 在你的研究系统中使用 PostgreSQL checkpoint")
    print("2. 查询用户的研究历史")
    print("3. 恢复中断的研究会话")
    print("4. 分析研究进度和效果")
    print("=" * 60)


if __name__ == "__main__":
    main()
