#!/usr/bin/env python3
"""
详细测试流式输出，捕获实际的Writer输出
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
        print(f"📤 Writer输出: {message}")


def test_detailed_stream_output():
    """详细测试流式输出"""
    print("🧪 详细测试流式输出功能")
    print("=" * 60)
    
    # 创建自定义processor，并捕获输出
    processor = create_workflow_processor("subgraph_test", "子图流测试")
    
    # 替换writer的输出函数
    output_capture = OutputCapture()
    processor.writer.writer = output_capture
    
    # 测试数据 - 包含不同类型的AIMessageChunk
    test_data = [
        # 短内容chunk
        (
            ('content_creation:c086b8a3',), 
            'messages',
            (MockAIMessageChunk('不断'), {'timestamp': time.time()})
        ),
        
        # 中等长度chunk
        (
            ('writing:def456',), 
            'messages',
            (MockAIMessageChunk('深入分析当前市场趋势和发展机遇'), {'node': 'writer'})
        ),
        
        # 长内容chunk (超过300字符，应该触发content_streaming)
        (
            ('research:abc123',), 
            'messages',
            (MockAIMessageChunk(
                '人工智能技术正在经历快速发展，从机器学习到深度学习，再到大型语言模型，'
                '每一次技术突破都带来了新的应用可能性。在企业应用方面，AI技术已经深入到'
                '客服、内容生成、数据分析、风险控制等各个业务环节。特别是生成式AI的兴起，'
                '为内容创作、代码开发、设计等创意工作带来了革命性的变化。同时，AI技术的'
                '普及也带来了新的挑战，包括数据隐私、算法偏见、技能替代等问题需要社会各界'
                '共同关注和解决。'
            ), {'source': 'research'})
        )
    ]
    
    print(f"📊 开始处理 {len(test_data)} 个测试chunk...")
    
    for i, chunk in enumerate(test_data, 1):
        print(f"\n🔍 === 处理Chunk #{i} ===")
        subgraph_id, chunk_type, chunk_data = chunk
        message, metadata = chunk_data
        
        print(f"📋 原始信息:")
        print(f"   - 子图ID: {subgraph_id}")
        print(f"   - Chunk类型: {chunk_type}")
        print(f"   - 消息类型: {type(message).__name__}")
        print(f"   - 内容长度: {len(message.content)}字符")
        print(f"   - 内容预览: '{message.content[:50]}{'...' if len(message.content) > 50 else ''}'")
        
        # 处理chunk
        result = processor.process_chunk(chunk)
        print(f"🔄 处理结果: {result}")
    
    print(f"\n📈 总计输出了 {len(output_capture.messages)} 条消息")
    
    # 分析输出消息类型
    msg_types = {}
    for msg in output_capture.messages:
        msg_type = msg.get('message_type', 'unknown')
        msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
    
    print(f"\n📊 消息类型统计:")
    for msg_type, count in msg_types.items():
        print(f"   - {msg_type}: {count}条")
    
    # 显示内容流消息
    content_msgs = [msg for msg in output_capture.messages if msg.get('message_type') == 'content_streaming']
    if content_msgs:
        print(f"\n📝 内容流消息 ({len(content_msgs)}条):")
        for i, msg in enumerate(content_msgs, 1):
            content = msg.get('content', '')
            print(f"   {i}. [{len(content)}字符] '{content[:100]}{'...' if len(content) > 100 else ''}'")
    else:
        print("\n❌ 没有检测到内容流消息！")
    
    print("\n✅ 详细测试完成！")


if __name__ == "__main__":
    test_detailed_stream_output()