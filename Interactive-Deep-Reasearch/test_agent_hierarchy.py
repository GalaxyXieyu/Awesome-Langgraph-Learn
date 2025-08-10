#!/usr/bin/env python3
"""
测试agent层级提取功能
验证能否正确从嵌套subgraph_ids中提取agent信息
"""

import time
from stream_writer import create_workflow_processor


class MockAIMessageChunk:
    """模拟AIMessageChunk对象"""
    
    def __init__(self, content: str):
        self.content = content
        self.__class__.__name__ = "AIMessageChunk"
    
    def __repr__(self):
        return f"AIMessageChunk(content='{self.content}')"


class OutputCapture:
    """捕获writer输出"""
    
    def __init__(self):
        self.messages = []
    
    def __call__(self, message):
        """模拟stream writer"""
        self.messages.append(message)
        msg_type = message.get('message_type', 'unknown')
        content = message.get('content', '')
        agent = message.get('agent', 'no_agent')
        agent_hierarchy = message.get('agent_hierarchy', [])
        
        if msg_type == 'content_streaming':
            hierarchy_str = ' -> '.join(agent_hierarchy) if len(agent_hierarchy) > 1 else agent_hierarchy[0] if agent_hierarchy else 'none'
            print(f"✨ 流式输出: '{content}' | Agent: {agent} | 层级: [{hierarchy_str}]")


def test_agent_hierarchy_extraction():
    """测试agent层级提取功能"""
    print("🧪 测试Agent层级提取功能")
    print("=" * 60)
    
    # 创建processor并捕获输出
    processor = create_workflow_processor("intelligent_research", "深度研究报告生成")
    
    output_capture = OutputCapture()
    processor.writer.writer = output_capture
    
    # 测试不同的agent层级结构
    test_cases = [
        {
            "name": "用户实际案例 - content_creation.writing",
            "chunk": (
                ('content_creation:f33929e8-16fa-ad19-0aa4-2cf5c62417df', 'writing:867f7047-9cfa-94ca-8fd8-9f55b32902d4'),
                'messages',
                (MockAIMessageChunk('市场'), {'thread_id': 'research_1754793810'})
            ),
            "expected_agent": "writing",
            "expected_hierarchy": ["content_creation", "writing"]
        },
        {
            "name": "单层级 - 只有research",
            "chunk": (
                ('research:abc123-456-789',),
                'messages',
                (MockAIMessageChunk('人工智能技术'), {})
            ),
            "expected_agent": "research",
            "expected_hierarchy": ["research"]
        },
        {
            "name": "三层级 - content_creation.research.tools",
            "chunk": (
                ('content_creation:aaa', 'research:bbb', 'tools:ccc'),
                'messages',
                (MockAIMessageChunk('正在搜索...'), {})
            ),
            "expected_agent": "tools",
            "expected_hierarchy": ["content_creation", "research", "tools"]
        },
        {
            "name": "未知agent类型",
            "chunk": (
                ('unknown_agent:xyz',),
                'messages',
                (MockAIMessageChunk('测试内容'), {})
            ),
            "expected_agent": "unknown",
            "expected_hierarchy": ["unknown"]
        }
    ]
    
    print(f"📊 处理 {len(test_cases)} 个测试案例...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 === 测试案例 #{i}: {test_case['name']} ===")
        
        # 显示输入数据
        subgraph_ids, chunk_type, chunk_data = test_case['chunk']
        message, metadata = chunk_data
        print(f"📋 输入:")
        print(f"   - 子图IDs: {subgraph_ids}")
        print(f"   - 消息内容: '{message.content}'")
        print(f"   - 预期Agent: {test_case['expected_agent']}")
        print(f"   - 预期层级: {test_case['expected_hierarchy']}")
        print()
        
        # 处理chunk
        result = processor.process_chunk(test_case['chunk'])
        print(f"🔄 处理结果: {result}")
        print()
    
    print(f"📈 总输出消息数: {len(output_capture.messages)}")
    
    # 验证结果
    print(f"\n📊 结果验证:")
    for i, (test_case, msg) in enumerate(zip(test_cases, output_capture.messages), 1):
        actual_agent = msg.get('agent', 'unknown')
        actual_hierarchy = msg.get('agent_hierarchy', [])
        
        agent_correct = actual_agent == test_case['expected_agent']
        hierarchy_correct = actual_hierarchy == test_case['expected_hierarchy']
        
        status = "✅" if agent_correct and hierarchy_correct else "❌"
        print(f"   {status} 案例 {i}: Agent: {actual_agent} (期望: {test_case['expected_agent']}) | "
              f"层级: {actual_hierarchy} (期望: {test_case['expected_hierarchy']})")
    
    print("\n🎯 测试总结:")
    success_count = sum(1 for i, (test_case, msg) in enumerate(zip(test_cases, output_capture.messages)) 
                       if msg.get('agent') == test_case['expected_agent'] and 
                          msg.get('agent_hierarchy') == test_case['expected_hierarchy'])
    
    print(f"   成功: {success_count}/{len(test_cases)}")
    print(f"   成功率: {success_count/len(test_cases)*100:.1f}%")
    
    if success_count == len(test_cases):
        print("\n🎉 所有测试通过！Agent层级提取功能正常工作！")
    else:
        print(f"\n⚠️  有 {len(test_cases)-success_count} 个测试失败，需要检查代码。")
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    test_agent_hierarchy_extraction()