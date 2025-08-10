#!/usr/bin/env python3
"""
测试清理后的输出 - 验证不再有噪音消息
"""

import time
from stream_writer import create_workflow_processor


class OutputCapture:
    """捕获writer输出"""
    
    def __init__(self):
        self.messages = []
    
    def __call__(self, message):
        """模拟stream writer"""
        self.messages.append(message)
        msg_type = message.get('message_type', 'unknown')
        content = message.get('content', '')
        
        # 高亮显示不希望看到的内容
        if any(keyword in content for keyword in ['🧠', '智能调度分析完成', '质量反馈', '置信度']):
            print(f"❌ 噪音消息: [{msg_type}] '{content[:100]}...'")
        else:
            print(f"✅ 清洁消息: [{msg_type}] '{content[:50]}{'...' if len(content) > 50 else ''}'")


def test_clean_output():
    """测试清理后的输出"""
    print("🧪 测试清理后的输出效果")
    print("=" * 50)
    
    # 创建processor
    processor = create_workflow_processor("intelligent_research", "深度研究")
    
    output_capture = OutputCapture()
    processor.writer.writer = output_capture
    
    # 模拟一些消息
    test_messages = [
        # 步骤开始
        ('custom', {
            'message_type': 'step_start',
            'content': '开始智能研究处理',
            'node': 'intelligent_research',
            'timestamp': time.time()
        }),
        
        # 工具调用
        ('custom', {
            'message_type': 'tool_call',
            'content': '正在搜索: 人工智能发展趋势',
            'node': 'research',
            'timestamp': time.time(),
            'metadata': {
                'tool_name': 'web_search_tool',
                'tool_args': {'query': '人工智能发展趋势'}
            }
        }),
        
        # 内容流
        ('custom', {
            'message_type': 'content_streaming',
            'content': '人工智能技术正在快速发展...',
            'node': 'writing',
            'timestamp': time.time()
        }),
        
        # 步骤完成
        ('custom', {
            'message_type': 'step_complete',
            'content': '研究分析完成',
            'node': 'research',
            'timestamp': time.time(),
            'metadata': {
                'duration': 2.3,
                'word_count': 150
            }
        }),
        
        # 这种消息应该被标记为噪音（如果还存在）
        ('custom', {
            'message_type': 'reasoning',
            'content': '🧠 智能调度分析完成：决策优化中...',
            'node': 'supervisor',
            'timestamp': time.time()
        })
    ]
    
    print(f"📊 处理 {len(test_messages)} 个测试消息...")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"🔍 消息 #{i}:")
        processor.process_chunk(message)
    
    print(f"\n📈 总输出: {len(output_capture.messages)} 条消息")
    
    # 检查是否有噪音消息
    noise_messages = []
    clean_messages = []
    
    for msg in output_capture.messages:
        content = msg.get('content', '')
        if any(keyword in content for keyword in ['🧠', '智能调度分析完成', '质量反馈', '置信度']):
            noise_messages.append(msg)
        else:
            clean_messages.append(msg)
    
    print(f"\n📊 消息分类:")
    print(f"   ✅ 清洁消息: {len(clean_messages)}条")
    print(f"   ❌ 噪音消息: {len(noise_messages)}条")
    
    if noise_messages:
        print(f"\n⚠️  发现噪音消息:")
        for i, msg in enumerate(noise_messages, 1):
            content = msg.get('content', '')
            print(f"   {i}. '{content[:100]}{'...' if len(content) > 100 else ''}'")
        print("\n❌ 清理不完整！")
    else:
        print(f"\n🎉 清理成功！没有发现噪音消息。")
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    test_clean_output()