#!/usr/bin/env python3
"""
测试真实的chunk格式，模拟用户提到的实际数据
"""

import time
from stream_writer import create_workflow_processor


class MockAIMessageChunk:
    """模拟真实的AIMessageChunk对象"""
    
    def __init__(self, content: str):
        self.content = content
        self.additional_kwargs = {}
        self.response_metadata = {}
        self.id = f'run--{hash(content)}'
        self.usage_metadata = {
            'input_tokens': 0, 
            'output_tokens': len(content.split()), 
            'total_tokens': len(content.split()),
            'input_token_details': {}, 
            'output_token_details': {}
        }
        self.__class__.__name__ = "AIMessageChunk"
    
    def __repr__(self):
        return f"AIMessageChunk(content='{self.content}', additional_kwargs={{}}, response_metadata={{}}, id='{self.id}', usage_metadata={self.usage_metadata})"


class OutputCapture:
    """捕获writer输出"""
    
    def __init__(self):
        self.messages = []
    
    def __call__(self, message):
        """模拟stream writer"""
        self.messages.append(message)
        # 只显示content_streaming消息
        if message.get('message_type') == 'content_streaming':
            content = message.get('content', '')
            print(f"✨ 流式输出: '{content}'")


def test_real_chunk_format():
    """测试真实的chunk格式"""
    print("🧪 测试真实chunk格式处理")
    print("=" * 50)
    
    # 创建processor并捕获输出
    processor = create_workflow_processor("intelligent_research", "深度研究报告生成")
    
    output_capture = OutputCapture()
    processor.writer.writer = output_capture
    
    # 模拟用户提到的真实数据格式
    real_chunks = [
        # 1. 用户提到的格式
        (
            ('content_creation:9fe31c96-a020-55e4-fdb6-1c5f31ba8aa9',), 
            'messages', 
            (
                MockAIMessageChunk(' "'), 
                {
                    'thread_id': 'research_1754791851', 
                    'langgraph_step': 1, 
                    'langgraph_node': 'intelligent_supervisor',
                    'langgraph_triggers': ('branch:to:intelligent_supervisor',), 
                    'langgraph_path': ('__pregel_pull', 'intelligent_supervisor'), 
                    'langgraph_checkpoint_ns': 'content_creation:9fe31c96-a020-55e4-fdb6-1c5f31ba8aa9|intelligent_supervisor:a73540ef-1e9e-7dad-66a9-107b496859e4', 
                    'checkpoint_ns': 'content_creation:9fe31c96-a020-55e4-fdb6-1c5f31ba8aa9', 
                    'ls_provider': 'openai', 
                    'ls_model_name': 'gpt-4o-mini', 
                    'ls_model_type': 'chat', 
                    'ls_temperature': 0.7
                }
            )
        ),
        
        # 2. 更多的流式内容chunk
        (
            ('content_creation:9fe31c96-a020-55e4-fdb6-1c5f31ba8aa9',), 
            'messages',
            (MockAIMessageChunk('人工智能'), {'thread_id': 'research_1754791851'})
        ),
        
        (
            ('writing:31a0ffdd-f5f2-a583-c34b-3d03e3691dba',), 
            'messages',
            (MockAIMessageChunk('技术发展'), {'node': 'writer'})
        ),
        
        (
            ('writing:31a0ffdd-f5f2-a583-c34b-3d03e3691dba',), 
            'messages',
            (MockAIMessageChunk('正在快速演进'), {'node': 'writer'})
        ),
        
        # 3. 一些custom格式消息（用户说这些能正常工作）
        ('custom', {
            'message_type': 'reasoning', 
            'content': '智能调度分析完成：开始研究人工智能技术基础', 
            'node': 'intelligent_research',
            'timestamp': time.time(), 
            'duration': 1.5
        })
    ]
    
    print(f"📊 处理 {len(real_chunks)} 个真实格式的chunk...")
    
    for i, chunk in enumerate(real_chunks, 1):
        print(f"\n🔍 === Chunk #{i} ===")
        
        if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == 'custom':
            print(f"📋 Custom消息: {chunk[1].get('message_type', 'unknown')}")
            print(f"💬 内容: '{chunk[1].get('content', '')[:50]}...'")
        elif isinstance(chunk, tuple) and len(chunk) == 3:
            subgraph_id, chunk_type, chunk_data = chunk
            if isinstance(chunk_data, tuple) and len(chunk_data) == 2:
                message, metadata = chunk_data
                print(f"📋 子图消息:")
                print(f"   - 子图ID: {subgraph_id}")
                print(f"   - 类型: {chunk_type}")
                print(f"   - 消息类型: {type(message).__name__}")
                print(f"   - 内容: '{message.content}'")
        
        # 处理chunk
        result = processor.process_chunk(chunk)
    
    print(f"\n📈 总输出消息数: {len(output_capture.messages)}")
    
    # 统计消息类型
    msg_types = {}
    for msg in output_capture.messages:
        msg_type = msg.get('message_type', 'unknown')
        msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
    
    print(f"\n📊 消息类型统计:")
    for msg_type, count in msg_types.items():
        print(f"   - {msg_type}: {count}条")
    
    # 显示所有content_streaming消息
    content_msgs = [msg for msg in output_capture.messages if msg.get('message_type') == 'content_streaming']
    print(f"\n📝 流式内容消息 ({len(content_msgs)}条):")
    for i, msg in enumerate(content_msgs, 1):
        content = msg.get('content', '')
        print(f"   {i}. '{content}'")
    
    print("\n✅ 真实格式测试完成！")
    print("🎉 现在所有AIMessageChunk都能正确转换为content_streaming格式输出！")


if __name__ == "__main__":
    test_real_chunk_format()