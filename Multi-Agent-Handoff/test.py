"""
Multi-Agent Handoff测试脚本

测试多智能体系统的handoff功能和交互能力
"""

import os
import sys
from typing import Dict, Any
import asyncio
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import create_multi_agent_system
from state import MultiAgentState


class MultiAgentTester:
    """多智能体系统测试器"""
    
    def __init__(self, llm_type: str = "openai"):
        """
        初始化测试器
        
        Args:
            llm_type: LLM类型，支持"openai"或"anthropic"
        """
        print(f"初始化多智能体系统 (LLM: {llm_type})")
        try:
            self.system = create_multi_agent_system(llm_type)
            print("✅ 系统初始化成功")
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            raise
    
    def test_basic_handoff(self):
        """测试基本的handoff功能"""
        print("\n" + "="*50)
        print("🧪 测试1: 基本Handoff功能")
        print("="*50)
        
        test_input = "请研究一下Python的最新特性，然后分析其对开发效率的影响，最后写一份总结报告"
        
        try:
            print(f"输入: {test_input}")
            print("\n开始执行...")
            
            result = self.system.run(test_input)
            
            print("\n=== 执行结果 ===")
            self._print_result_summary(result)
            
            return True
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def test_stream_execution(self):
        """测试流式执行"""
        print("\n" + "="*50)
        print("🧪 测试2: 流式执行")
        print("="*50)
        
        test_input = "帮我分析一下机器学习在金融领域的应用现状"
        
        try:
            print(f"输入: {test_input}")
            print("\n开始流式执行...")
            
            for i, chunk in enumerate(self.system.stream(test_input)):
                print(f"\n--- Chunk {i+1} ---")
                for node_name, node_output in chunk.items():
                    if hasattr(node_output, 'get') and node_output.get('messages'):
                        last_message = node_output['messages'][-1]
                        if last_message.get('content'):
                            content = last_message['content'][:200] + "..." if len(last_message['content']) > 200 else last_message['content']
                            print(f"{node_name}: {content}")
                    
                    # 限制输出chunk数量
                    if i >= 10:
                        print("... (省略更多输出)")
                        break
                        
                if i >= 10:
                    break
            
            return True
            
        except Exception as e:
            print(f"❌ 流式测试失败: {e}")
            return False
    
    def test_agent_status_tracking(self):
        """测试Agent状态追踪"""
        print("\n" + "="*50)
        print("🧪 测试3: Agent状态追踪")
        print("="*50)
        
        test_input = "请帮我查询当前所有agent的状态，然后测试状态更新功能"
        
        try:
            print(f"输入: {test_input}")
            result = self.system.run(test_input)
            
            print("\n=== Agent状态信息 ===")
            if 'agents' in result:
                for agent_name, agent_info in result['agents'].items():
                    print(f"🤖 {agent_name}:")
                    print(f"   角色: {agent_info.role}")
                    print(f"   状态: {agent_info.status}")
                    print(f"   最后动作: {agent_info.last_action}")
            
            print("\n=== Handoff历史 ===")
            if 'handoff_history' in result and result['handoff_history']:
                for i, handoff in enumerate(result['handoff_history'][-5:]):  # 显示最后5次handoff
                    print(f"{i+1}. {handoff.from_agent} -> {handoff.to_agent}")
                    print(f"   原因: {handoff.reason}")
                    print(f"   时间: {handoff.timestamp}")
                    
            return True
            
        except Exception as e:
            print(f"❌ 状态追踪测试失败: {e}")
            return False
    
    def test_shared_context(self):
        """测试共享上下文功能"""
        print("\n" + "="*50)
        print("🧪 测试4: 共享上下文功能")
        print("="*50)
        
        test_input = "请在共享上下文中存储一些测试数据，然后让不同的agent访问这些数据"
        
        try:
            print(f"输入: {test_input}")
            result = self.system.run(test_input)
            
            print("\n=== 共享上下文 ===")
            if 'shared_context' in result and result['shared_context']:
                for key, value in result['shared_context'].items():
                    print(f"📦 {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            else:
                print("没有发现共享上下文数据")
            
            return True
            
        except Exception as e:
            print(f"❌ 共享上下文测试失败: {e}")
            return False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n" + "="*50)
        print("🧪 测试5: 错误处理")
        print("="*50)
        
        # 测试空输入
        try:
            print("测试空输入...")
            result = self.system.run("")
            print("✅ 空输入处理正常")
        except Exception as e:
            print(f"⚠️ 空输入异常: {e}")
        
        # 测试超长输入
        try:
            print("测试超长输入...")
            long_input = "请处理这个任务: " + "这是一个很长的任务描述 " * 100
            result = self.system.run(long_input)
            print("✅ 超长输入处理正常")
        except Exception as e:
            print(f"⚠️ 超长输入异常: {e}")
        
        return True
    
    def _print_result_summary(self, result: Dict[str, Any]):
        """打印结果摘要"""
        print(f"活跃Agent: {result.get('active_agent', 'unknown')}")
        print(f"系统状态: {result.get('system_status', 'unknown')}")
        print(f"当前任务: {result.get('current_task', 'unknown')}")
        
        if result.get('messages'):
            print(f"\n📨 消息数量: {len(result['messages'])}")
            last_message = result['messages'][-1]
            if last_message.get('content'):
                content = last_message['content']
                print(f"最后消息: {content[:300]}{'...' if len(content) > 300 else ''}")
        
        if result.get('handoff_history'):
            print(f"\n🔄 Handoff次数: {len(result['handoff_history'])}")
            
        if result.get('task_results'):
            print(f"\n📊 任务结果: {list(result['task_results'].keys())}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行Multi-Agent Handoff测试套件")
        print(f"测试时间: {datetime.now().isoformat()}")
        
        tests = [
            ("基本Handoff功能", self.test_basic_handoff),
            ("流式执行", self.test_stream_execution),
            ("Agent状态追踪", self.test_agent_status_tracking),
            ("共享上下文功能", self.test_shared_context),
            ("错误处理", self.test_error_handling),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ 测试 '{test_name}' 异常: {e}")
                results[test_name] = False
        
        # 打印测试总结
        print("\n" + "="*60)
        print("📋 测试结果总结")
        print("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} - {test_name}")
            if success:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 测试通过")
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 所有测试通过！Multi-Agent Handoff系统运行正常。")
        elif success_rate >= 80:
            print("⚠️ 大部分测试通过，系统基本正常，但有些功能需要检查。")
        else:
            print("❌ 多个测试失败，系统可能存在问题，需要进一步调试。")


def main():
    """主函数"""
    print("Multi-Agent Handoff系统测试")
    print("=" * 40)
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️ 警告: 没有找到API密钥环境变量")
        print("请设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY")
        print("或者确保你的模型配置正确")
    
    # 选择LLM类型
    llm_type = input("选择LLM类型 (openai/anthropic) [openai]: ").strip().lower() or "openai"
    
    try:
        tester = MultiAgentTester(llm_type)
        
        # 选择测试模式
        print("\n选择测试模式:")
        print("1. 运行全部测试")
        print("2. 运行单个测试") 
        print("3. 交互式测试")
        
        choice = input("请输入选择 (1-3) [1]: ").strip() or "1"
        
        if choice == "1":
            tester.run_all_tests()
        elif choice == "2":
            print("\n可用的单个测试:")
            print("1. 基本Handoff功能")
            print("2. 流式执行")
            print("3. Agent状态追踪")
            print("4. 共享上下文功能")
            print("5. 错误处理")
            
            test_choice = input("选择测试 (1-5): ").strip()
            test_methods = {
                "1": tester.test_basic_handoff,
                "2": tester.test_stream_execution,
                "3": tester.test_agent_status_tracking,
                "4": tester.test_shared_context,
                "5": tester.test_error_handling,
            }
            
            if test_choice in test_methods:
                test_methods[test_choice]()
            else:
                print("无效选择")
                
        elif choice == "3":
            print("\n进入交互式测试模式 (输入 'quit' 退出)")
            while True:
                user_input = input("\n请输入测试任务: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                if user_input:
                    try:
                        result = tester.system.run(user_input)
                        tester._print_result_summary(result)
                    except Exception as e:
                        print(f"执行错误: {e}")
        
    except Exception as e:
        print(f"测试初始化失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())