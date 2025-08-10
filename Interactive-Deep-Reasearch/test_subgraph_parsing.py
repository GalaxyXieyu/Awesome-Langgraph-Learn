#!/usr/bin/env python3
"""
测试子图chunk解析是否正常工作
验证AIMessageChunk能否被正确处理
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


def test_subgraph_chunk_parsing():
    """测试子图chunk解析"""
    print("🧪 测试子图chunk解析功能")
    print("=" * 50)
    
    # 创建processor
    processor = create_workflow_processor("test_subgraph", "测试子图解析")
    
    # 模拟用户提到的数据格式
    test_chunks = [
        # 1. 子图messages格式: (('subgraph_id',), 'messages', (AIMessageChunk, metadata))
        (
            ('content_creation:c086b8a3-a6bb-821b-173b-c53129ac7420', 'writing:31a0ffdd-f5f2-a583-c34b-3d03e3691dba'),
            'messages',
            (MockAIMessageChunk('不断'), {'timestamp': time.time()})
        ),
        
        # 2. 更多chunk
        (
            ('research:abc123', 'analysis:def456'), 
            'messages',
            (MockAIMessageChunk('深入分析市场趋势'), {'node': 'analyzer'})
        ),
        
        # 3. 完整句子的chunk
        (
            ('writing:xyz789',),
            'messages', 
            (MockAIMessageChunk('人工智能技术正在快速发展'), {'metadata': {}})
        )
    ]
    
    print("🔍 处理测试数据...")
    
    for i, chunk in enumerate(test_chunks, 1):
        print(f"\n--- 测试Chunk #{i} ---")
        print(f"原始数据: {chunk}")
        
        # 处理chunk
        result = processor.process_chunk(chunk)
        print(f"处理结果: {result}")
    
    # 获取总结
    summary = processor.get_summary()
    print(f"\n📊 处理总结:")
    print(f"- 总chunk数: {summary['total_chunks_processed']}")
    print(f"- 完成章节: {summary['sections_completed']}")
    print(f"- 研究发现: {summary['research_findings']}")
    
    print("\n✅ 测试完成！")
    
    # 检查是否能正确识别AIMessageChunk
    chunk_with_content = test_chunks[0]
    subgraph_id, chunk_type, chunk_data = chunk_with_content
    message, metadata = chunk_data
    
    print(f"\n🔬 详细检查:")
    print(f"- 消息类型: {type(message).__name__}")
    print(f"- 消息内容: '{message.content}'")
    print(f"- 是否有内容: {bool(message.content)}")
    print(f"- 内容长度: {len(message.content) if message.content else 0}")


if __name__ == "__main__":
    test_subgraph_chunk_parsing()