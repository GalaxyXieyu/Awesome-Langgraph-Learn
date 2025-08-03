"""
简单测试脚本 - 替代 Jupyter Notebook
测试集成后的智能深度研究系统
"""

# 智能深度研究系统测试 - 集成版本
from graph import create_deep_research_graph
from state import create_initial_state, ReportMode
from datetime import datetime
import asyncio
import json
import time
from typing import Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

def setup_system():
    """初始化系统"""
    print("🧠 初始化智能深度研究系统（集成智能章节研究子图）")
    
    user_id = "test_integrated_stream"
    graph = create_deep_research_graph()
    config = {"configurable": {"thread_id": f"deep_research_{user_id}_{int(datetime.now().timestamp())}"}}

    # 创建测试状态
    initial_state = create_initial_state(
        topic="人工智能在医疗诊断中的应用",
        user_id=user_id,
        mode=ReportMode.COPILOT,  # 使用自动模式，减少人工干预
        report_type="research",
        target_audience="医疗专业人士",
        depth_level="deep",
        target_length=3000
    )

    print(f"✅ 系统初始化完成")
    print(f"📋 研究主题: {initial_state['topic']}")
    print(f"🎯 目标受众: {initial_state['target_audience']}")
    print(f"🤖 运行模式: {initial_state['mode']}")
    print(f"📏 目标长度: {initial_state['target_length']} 字")
    
    return graph, initial_state, config

async def run_simple_test():
    """运行简单测试"""
    print("\n🚀 开始简单测试")
    print("-" * 40)
    
    # 初始化系统
    graph, initial_state, config = setup_system()
    
    # 手动添加一个简化的大纲用于快速测试
    initial_state["outline"] = {
        "title": "人工智能在医疗诊断中的应用研究报告",
        "executive_summary": "本报告分析AI在医疗诊断领域的应用现状和发展前景。",
        "sections": [
            {
                "id": "section_1",
                "title": "AI医疗诊断技术概述",
                "description": "介绍AI在医疗诊断中的基本概念和核心技术",
                "key_points": ["机器学习", "深度学习", "医学影像分析"]
            }
        ]
    }
    
    # 设置审批状态为已通过，直接进入内容创建
    initial_state["approval_status"] = {
        "outline_confirmation": True,
        "research_permission": True,
        "analysis_approval": True
    }
    
    print(f"📊 测试章节数量: {len(initial_state['outline']['sections'])}")
    print("🎯 开始智能章节处理...")
    
    start_time = time.time()
    events_count = 0
    
    try:
        async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
            events_count += 1
            print(f"📨 事件 {events_count}: {list(event.keys())}")
            
            for node_name, node_output in event.items():
                if node_name == "content_creation":
                    # 检查进度
                    if "status" in str(node_output):
                        print(f"📍 状态更新: {node_name}")
                    
                    # 检查是否完成
                    if node_output.get("content_creation_completed"):
                        execution_time = time.time() - start_time
                        print(f"\n🎉 测试完成!")
                        print(f"⏱️ 执行时间: {execution_time:.2f} 秒")
                        
                        completed_count = node_output.get("completed_sections_count", 0)
                        print(f"📊 完成章节: {completed_count}")
                        
                        # 显示生成的内容示例
                        sections = node_output.get("sections", [])
                        if sections and sections[0].get("content"):
                            content = sections[0]["content"]
                            preview = content[:150] + "..." if len(content) > 150 else content
                            print(f"📄 内容示例: {preview}")
                            
                            quality = sections[0].get("quality_metrics", {}).get("final_quality_score", 0)
                            print(f"📈 质量评分: {quality:.2f}")
                        
                        return True
            
            # 限制事件数量和时间
            if events_count > 20 or time.time() - start_time > 180:  # 3分钟超时
                print("⚠️ 测试超时或达到事件限制")
                break
        
        print("❌ 测试未完成")
        return False
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

async def run_outline_test():
    """测试大纲生成"""
    print("\n📋 测试大纲生成")
    print("-" * 40)
    
    # 初始化系统
    graph, initial_state, config = setup_system()
    
    print("🚀 开始大纲生成...")
    
    try:
        events_count = 0
        async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
            events_count += 1
            print(f"📨 事件 {events_count}: {list(event.keys())}")
            
            for node_name, node_output in event.items():
                if node_name == "outline_generation" and node_output.get("outline"):
                    outline = node_output["outline"]
                    print(f"\n✅ 大纲生成成功!")
                    print(f"📝 标题: {outline.get('title', '未知')}")
                    print(f"📊 章节数量: {len(outline.get('sections', []))}")
                    
                    # 显示章节列表
                    sections = outline.get('sections', [])
                    for i, section in enumerate(sections[:3]):
                        print(f"   {i+1}. {section.get('title', '未知章节')}")
                    
                    if len(sections) > 3:
                        print(f"   ... 还有 {len(sections) - 3} 个章节")
                    
                    return True
            
            if events_count > 10:
                print("⚠️ 达到事件限制")
                break
        
        print("❌ 大纲生成失败")
        return False
        
    except Exception as e:
        print(f"❌ 大纲生成异常: {e}")
        return False

def main():
    """主函数"""
    print("🧪 智能深度研究系统 - 简单测试")
    print("=" * 50)
    print("集成了智能章节研究子图的完整系统测试")
    print("=" * 50)
    
    # 选择测试类型
    print("\n请选择测试类型:")
    print("1. 大纲生成测试")
    print("2. 智能章节处理测试（推荐）")
    print("3. 运行完整测试套件")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        print("\n🎯 执行大纲生成测试...")
        result = asyncio.run(run_outline_test())
    elif choice == "2":
        print("\n🎯 执行智能章节处理测试...")
        result = asyncio.run(run_simple_test())
    elif choice == "3":
        print("\n🎯 执行完整测试套件...")
        # 导入完整测试
        import subprocess
        result = subprocess.run(["python", "test_integrated_system.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        result = result.returncode == 0
    else:
        print("❌ 无效选择")
        return
    
    print(f"\n📊 测试结果: {'✅ 成功' if result else '❌ 失败'}")

if __name__ == "__main__":
    main()
