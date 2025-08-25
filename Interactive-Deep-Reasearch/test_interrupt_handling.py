#!/usr/bin/env python3
"""
测试中断处理功能
模拟LangGraph中断场景并验证writer系统的处理能力
"""

import time
from typing import Any, Dict
from writer.core import (
    create_workflow_processor, 
    create_interrupt_handler,
    InterruptHandler,
    AgentWorkflowProcessor
)

class MockInterrupt:
    """模拟LangGraph中断对象"""
    def __init__(self, interrupt_id: str, action_request: Dict[str, Any], description: str, config: Dict[str, Any] = None):
        self.id = interrupt_id
        self.value = {
            'action_request': action_request,
            'description': description,
            'config': config or {'allow_accept': True, 'allow_edit': True, 'allow_respond': True}
        }

def test_interrupt_detection():
    """测试中断检测功能"""
    print("=== 测试中断检测功能 ===")
    
    # 创建工作流处理器
    processor = create_workflow_processor("test_node", "test_agent")
    
    # 模拟中断chunk - 基于你提供的错误格式
    interrupt_obj = MockInterrupt(
        interrupt_id='915603b6ebbb3ccef74e59dfc606cad1',
        action_request={
            'action': 'web_search',
            'args': {'query': '报告背景、目的和结构安排的介绍方法'}
        },
        description="准备调用 web_search 工具：\n- 参数为: {'query': '报告背景、目的和结构安排的介绍方法'}\n\n是否允许继续？\n输入 'yes' 接受工具调用\n输入 'no' 拒绝工具调用\n输入 'edit' 修改工具参数后调用工具\n输入 'response' 不调用工具直接反馈信息"
    )
    
    # 构建中断chunk
    interrupt_chunk = (
        ('content_creation:4714b360-2616-a8ea-bfa2-09886fce18fe', 'research:de5cf5a4-2b73-65ad-f879-7aaad94ffe08'),
        'updates',
        {'__interrupt__': (interrupt_obj,)}
    )
    
    # 处理中断chunk
    result = processor.process_chunk(interrupt_chunk)
    
    print(f"处理结果: {result}")
    print("中断检测测试完成\n")
    
    return result.get('interrupt_processed', False)

def test_interrupt_handler():
    """测试中断处理器功能"""
    print("=== 测试中断处理器功能 ===")
    
    # 创建中断处理器
    handler = create_interrupt_handler("test_node", "test_agent")
    
    # 模拟中断请求
    interrupt_id = "test_interrupt_001"
    action = "web_search"
    args = {"query": "测试查询"}
    description = "测试中断描述"
    
    print("1. 发送中断请求...")
    handler.handle_interrupt_request(interrupt_id, action, args, description)
    
    # 检查待处理中断
    pending = handler.get_pending_interrupts()
    print(f"待处理中断: {list(pending.keys())}")
    
    # 模拟用户批准
    print("2. 模拟用户批准...")
    success = handler.handle_user_response(interrupt_id, "yes", True)
    print(f"处理结果: {'成功' if success else '失败'}")
    
    # 检查中断是否已清理
    pending_after = handler.get_pending_interrupts()
    print(f"处理后待处理中断: {list(pending_after.keys())}")
    
    print("中断处理器测试完成\n")
    
    return success

def test_interrupt_rejection():
    """测试中断拒绝功能"""
    print("=== 测试中断拒绝功能 ===")
    
    handler = create_interrupt_handler("test_node", "test_agent")
    
    interrupt_id = "test_interrupt_002"
    action = "web_search"
    args = {"query": "另一个测试查询"}
    description = "测试拒绝中断"
    
    print("1. 发送中断请求...")
    handler.handle_interrupt_request(interrupt_id, action, args, description)
    
    # 模拟用户拒绝
    print("2. 模拟用户拒绝...")
    success = handler.handle_user_response(interrupt_id, "no", False)
    print(f"处理结果: {'成功' if success else '失败'}")
    
    print("中断拒绝测试完成\n")
    
    return success

def test_multiple_interrupts():
    """测试多个中断处理"""
    print("=== 测试多个中断处理 ===")
    
    handler = create_interrupt_handler("test_node", "test_agent")
    
    # 创建多个中断
    interrupts = [
        ("interrupt_001", "web_search", {"query": "查询1"}, "第一个中断"),
        ("interrupt_002", "file_read", {"path": "/test/path"}, "第二个中断"),
        ("interrupt_003", "api_call", {"url": "https://test.com"}, "第三个中断")
    ]
    
    # 发送所有中断请求
    print("1. 发送多个中断请求...")
    for interrupt_id, action, args, description in interrupts:
        handler.handle_interrupt_request(interrupt_id, action, args, description)
    
    pending = handler.get_pending_interrupts()
    print(f"待处理中断数量: {len(pending)}")
    
    # 逐个处理中断
    print("2. 逐个处理中断...")
    for i, (interrupt_id, _, _, _) in enumerate(interrupts):
        approved = i % 2 == 0  # 奇数批准，偶数拒绝
        response = "yes" if approved else "no"
        success = handler.handle_user_response(interrupt_id, response, approved)
        print(f"  处理 {interrupt_id}: {'批准' if approved else '拒绝'} - {'成功' if success else '失败'}")
    
    # 检查所有中断是否已清理
    final_pending = handler.get_pending_interrupts()
    print(f"最终待处理中断数量: {len(final_pending)}")
    
    print("多个中断处理测试完成\n")
    
    return len(final_pending) == 0

def main():
    """运行所有测试"""
    print("开始测试中断处理功能...\n")
    
    tests = [
        ("中断检测", test_interrupt_detection),
        ("中断处理器", test_interrupt_handler),
        ("中断拒绝", test_interrupt_rejection),
        ("多个中断", test_multiple_interrupts)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            print(f"✅ {test_name}: {'通过' if result else '失败'}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"❌ {test_name}: 异常 - {str(e)}")
        
        time.sleep(0.5)  # 短暂延迟以便观察输出
    
    print("\n=== 测试总结 ===")
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    for test_name, result, error in results:
        status = "✅ 通过" if result else f"❌ 失败{f' ({error})' if error else ''}"
        print(f"  {test_name}: {status}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
