"""
演示脚本：展示简单聊天vs复杂写作助手的区别
"""

import time
from graph import create_chat_bot, chat_with_memory
from interactive_graph import run_writing_assistant
from langchain_core.messages import HumanMessage


def demo_simple_chat():
    """演示简单聊天机器人"""
    print("🤖 简单聊天机器人演示")
    print("=" * 40)
    
    # 创建Redis聊天机器人
    app = create_chat_bot("redis")
    thread_id = "demo_chat_001"
    
    # 对话序列
    conversations = [
        "你好！我是小明，一名程序员。",
        "我刚才说我是做什么工作的？",
        "请给我一些Python学习建议。",
        "你还记得我的名字吗？"
    ]
    
    print("💬 开始对话...")
    for i, message in enumerate(conversations, 1):
        print(f"\n👤 用户 ({i}): {message}")
        
        start_time = time.time()
        response = chat_with_memory(app, message, thread_id)
        response_time = time.time() - start_time
        
        print(f"🤖 助手: {response}")
        print(f"⏱️ 响应时间: {response_time:.2f}秒")
        
        time.sleep(1)  # 短暂暂停
    
    print("\n✅ 简单聊天演示完成")


def demo_writing_assistant():
    """演示交互式写作助手"""
    print("\n📝 交互式写作助手演示")
    print("=" * 40)
    
    topics = [
        "Python编程语言的优势",
        "人工智能在教育中的应用",
        "可持续发展的重要性"
    ]
    
    for i, topic in enumerate(topics, 1):
        print(f"\n📋 主题 {i}: {topic}")
        print("-" * 30)
        
        start_time = time.time()
        
        # 运行写作助手（自动模式）
        result = run_writing_assistant(
            topic=topic,
            mode="copilot",  # 自动模式，避免交互中断
            thread_id=f"demo_writing_{i:03d}"
        )
        
        generation_time = time.time() - start_time
        
        if "article" in result and result["article"]:
            outline = result.get("outline", {})
            article = result["article"]
            
            print(f"✅ 文章生成成功！")
            print(f"📊 统计信息:")
            print(f"   - 标题: {outline.get('title', '未知')}")
            print(f"   - 章节数: {len(outline.get('sections', []))}")
            print(f"   - 字数: {len(article)}")
            print(f"   - 生成时间: {generation_time:.2f}秒")
            print(f"   - 搜索结果: {len(result.get('search_results', []))}")
            
            print(f"\n📄 文章预览:")
            print(f"{article[:200]}...")
            
        else:
            print(f"❌ 文章生成失败: {result.get('error', '未知错误')}")
        
        if i < len(topics):
            print("\n" + "⏳ 等待3秒...")
            time.sleep(3)
    
    print("\n✅ 写作助手演示完成")


def compare_features():
    """功能对比"""
    print("\n⚖️ 功能对比分析")
    print("=" * 40)
    
    comparison = {
        "简单聊天机器人": {
            "特点": [
                "基于LangGraph的简单状态图",
                "支持对话记忆（Redis存储）",
                "快速响应",
                "适合日常对话"
            ],
            "技术栈": [
                "StateGraph + ChatOpenAI",
                "RedisSaver checkpointer",
                "简单的消息状态管理"
            ],
            "使用场景": [
                "客服机器人",
                "日常聊天助手",
                "简单问答系统"
            ]
        },
        "交互式写作助手": {
            "特点": [
                "复杂的多节点工作流",
                "支持大纲生成、搜索、文章生成",
                "用户确认和交互中断",
                "结构化输出（JSON解析）"
            ],
            "技术栈": [
                "复杂StateGraph + 多个节点",
                "JsonOutputParser + Pydantic模型",
                "条件路由和中断处理",
                "流式输出和进度跟踪"
            ],
            "使用场景": [
                "内容创作平台",
                "学术写作助手",
                "营销文案生成"
            ]
        }
    }
    
    for system_name, info in comparison.items():
        print(f"\n🔹 {system_name}")
        
        print("   📋 特点:")
        for feature in info["特点"]:
            print(f"      • {feature}")
        
        print("   🔧 技术栈:")
        for tech in info["技术栈"]:
            print(f"      • {tech}")
        
        print("   🎯 使用场景:")
        for scenario in info["使用场景"]:
            print(f"      • {scenario}")


def demo_redis_persistence():
    """演示Redis持久化特性"""
    print("\n💾 Redis持久化特性演示")
    print("=" * 40)
    
    print("🔄 测试会话持久化...")
    
    # 使用相同的thread_id进行多次对话
    app = create_chat_bot("redis")
    thread_id = "persistence_demo"
    
    # 第一轮对话
    print("\n📝 第一轮对话:")
    response1 = chat_with_memory(app, "我的爱好是摄影和旅行", thread_id)
    print(f"👤 用户: 我的爱好是摄影和旅行")
    print(f"🤖 助手: {response1}")
    
    # 第二轮对话（测试记忆）
    print("\n📝 第二轮对话:")
    response2 = chat_with_memory(app, "你还记得我的爱好吗？", thread_id)
    print(f"👤 用户: 你还记得我的爱好吗？")
    print(f"🤖 助手: {response2}")
    
    # 验证记忆效果
    if "摄影" in response2 or "旅行" in response2:
        print("✅ Redis持久化正常工作！")
    else:
        print("⚠️ 记忆效果可能不理想")
    
    print("\n🔀 测试多会话隔离...")
    
    # 不同的thread_id应该有独立的记忆
    thread_id_2 = "isolation_demo"
    response3 = chat_with_memory(app, "我的爱好是什么？", thread_id_2)
    print(f"👤 用户 (新会话): 我的爱好是什么？")
    print(f"🤖 助手: {response3}")
    
    if "摄影" not in response3 and "旅行" not in response3:
        print("✅ 会话隔离正常工作！")
    else:
        print("⚠️ 会话隔离可能有问题")


def main():
    """主演示函数"""
    print("🚀 LangGraph Redis存储方案演示")
    print("=" * 50)
    print("本演示展示了两种不同复杂度的LangGraph应用：")
    print("1. 简单聊天机器人 - 基础对话功能")
    print("2. 交互式写作助手 - 复杂工作流程")
    print("两者都使用Redis作为会话存储后端")
    print("=" * 50)
    
    try:
        # 演示简单聊天
        demo_simple_chat()
        
        # 演示写作助手
        demo_writing_assistant()
        
        # 功能对比
        compare_features()
        
        # Redis持久化演示
        demo_redis_persistence()
        
        print("\n" + "=" * 50)
        print("🎉 演示完成！")
        print("\n📋 总结:")
        print("• 简单聊天机器人适合快速对话场景")
        print("• 写作助手适合复杂的内容生成任务")
        print("• Redis存储确保了会话的持久化和隔离")
        print("• 两种方案都可以根据需求进行扩展")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("请检查:")
        print("1. OPENAI_API_KEY 环境变量是否设置")
        print("2. Redis连接是否正常")
        print("3. 依赖包是否正确安装")


if __name__ == "__main__":
    main()
