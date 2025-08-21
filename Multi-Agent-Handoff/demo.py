"""
Multi-Agent Handoff 演示脚本

展示多智能体系统的基本使用方法
"""

import os
import sys
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import create_multi_agent_system


def demo_basic_usage():
    """演示基本用法"""
    print("🎯 演示1: 基本的多智能体协作")
    print("-" * 40)
    
    # 创建系统
    system = create_multi_agent_system()
    
    # 测试任务
    task = "请帮我研究Python 3.12的新特性，分析其对性能的影响，并撰写一份技术报告"
    
    print(f"任务: {task}")
    print("\n开始执行...")
    
    try:
        result = system.run(task)
        
        print("\n📊 执行结果:")
        print(f"- 当前活跃Agent: {result.get('active_agent')}")
        print(f"- 系统状态: {result.get('system_status')}")
        print(f"- 消息数量: {len(result.get('messages', []))}")
        
        if result.get('handoff_history'):
            print(f"- Handoff次数: {len(result['handoff_history'])}")
            print("\n🔄 Handoff流程:")
            for i, handoff in enumerate(result['handoff_history'], 1):
                print(f"  {i}. {handoff.from_agent} → {handoff.to_agent}")
                print(f"     原因: {handoff.reason}")
        
        if result.get('messages'):
            last_msg = result['messages'][-1]
            if last_msg.get('content'):
                print(f"\n💬 最终回复:")
                print(last_msg['content'][:500] + "..." if len(last_msg['content']) > 500 else last_msg['content'])
                
    except Exception as e:
        print(f"❌ 执行失败: {e}")


def demo_streaming():
    """演示流式执行"""
    print("\n\n🎯 演示2: 流式执行")
    print("-" * 40)
    
    system = create_multi_agent_system()
    task = "分析人工智能在教育领域的应用前景"
    
    print(f"任务: {task}")
    print("\n流式执行中...")
    
    try:
        chunk_count = 0
        for chunk in system.stream(task):
            chunk_count += 1
            print(f"\n📦 Chunk {chunk_count}:")
            for node_name, node_output in chunk.items():
                if hasattr(node_output, 'get') and node_output.get('messages'):
                    last_message = node_output['messages'][-1]
                    if last_message.get('content'):
                        content = last_message['content']
                        preview = content[:150] + "..." if len(content) > 150 else content
                        print(f"  {node_name}: {preview}")
            
            # 限制演示输出
            if chunk_count >= 5:
                print("  ... (更多输出)")
                break
                
    except Exception as e:
        print(f"❌ 流式执行失败: {e}")


def demo_interactive():
    """交互式演示"""
    print("\n\n🎯 演示3: 交互式模式")
    print("-" * 40)
    print("输入任务让多智能体系统处理 (输入 'quit' 退出)")
    
    system = create_multi_agent_system()
    
    while True:
        try:
            user_input = input("\n🤖 请输入任务: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q', '退出']:
                print("👋 再见!")
                break
            
            if not user_input:
                continue
            
            print(f"\n处理中... (任务: {user_input[:50]}{'...' if len(user_input) > 50 else ''})")
            
            result = system.run(user_input)
            
            # 简化输出
            if result.get('messages'):
                last_msg = result['messages'][-1]
                if last_msg.get('content'):
                    print(f"\n💡 回复:")
                    print(last_msg['content'][:800] + "..." if len(last_msg['content']) > 800 else last_msg['content'])
            
            # 显示handoff信息
            if result.get('handoff_history'):
                recent_handoffs = result['handoff_history'][-3:]  # 只显示最近3次
                print(f"\n🔄 本次Handoff: {' → '.join([h.from_agent for h in recent_handoffs] + [recent_handoffs[-1].to_agent])}")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 处理错误: {e}")


def main():
    """主函数"""
    print("🚀 LangGraph Multi-Agent Handoff 演示")
    print("=" * 50)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查API密钥
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    
    if not has_openai and not has_anthropic:
        print("\n⚠️ 注意: 没有检测到API密钥")
        print("请确保设置了 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 环境变量")
        response = input("继续演示吗? (y/N): ")
        if response.lower() not in ['y', 'yes', '是']:
            return
    
    print("\n选择演示模式:")
    print("1. 基本用法演示")
    print("2. 流式执行演示") 
    print("3. 交互式演示")
    print("4. 运行全部演示")
    
    choice = input("\n请选择 (1-4) [4]: ").strip() or "4"
    
    try:
        if choice == "1":
            demo_basic_usage()
        elif choice == "2":
            demo_streaming()
        elif choice == "3":
            demo_interactive()
        elif choice == "4":
            demo_basic_usage()
            demo_streaming()
            
            # 询问是否进入交互模式
            if input("\n是否进入交互模式? (y/N): ").lower() in ['y', 'yes', '是']:
                demo_interactive()
        else:
            print("无效选择")
            return
        
        print("\n✨ 演示完成!")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()