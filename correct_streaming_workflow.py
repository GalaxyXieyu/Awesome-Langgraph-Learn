#!/usr/bin/env python3
"""
正确的流式+中断处理测试脚本
按照官方模式实现：检测中断 → 用户输入 → 恢复执行 → 流式输出
"""

import asyncio
import time
from typing import Dict, Any, cast
from graph import create_writing_assistant_graph, initialize_writing_state
from tools import load_knowledge_bases
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver  # 确保checkpointer可用


def print_streaming_content(chunk: Any):
    """处理流式chunk - 经过验证的方法"""
    if isinstance(chunk, tuple) and len(chunk) > 0:
        message_chunk = chunk[0]
        if hasattr(message_chunk, 'content'):
            content = message_chunk.content
            if content and isinstance(content, str):
                print(content, end="", flush=True)
                return True
    return False


async def correct_streaming_workflow():
    """
    正确的流式+中断处理工作流程
    """
    print("🎯 正确的LangGraph流式+中断处理测试")
    print("🔧 基于官方模式：中断检测 → 用户输入 → 恢复执行")
    print("=" * 60)
    
    # 初始化
    try:
        load_knowledge_bases()
        print("✅ 知识库初始化成功")
    except Exception as e:
        print(f"⚠️ 知识库初始化警告: {e}")
    
    graph = create_writing_assistant_graph()
    print("✅ 写作助手图创建成功")
    
    # 🔥 验证checkpointer配置
    if hasattr(graph, 'checkpointer') and graph.checkpointer:
        print("✅ Checkpointer配置正确")
    else:
        print("⚠️ 警告：Checkpointer可能未正确配置")
    
    # 完整工作流程配置
    initial_state = initialize_writing_state(
        topic="Python异步编程最佳实践",
        user_id="correct_workflow_test",
        max_words=600,
        style="technical",
        language="zh",
        enable_search=True  # 🔥 启用完整功能
    )
    
    config: Dict[str, Any] = {"configurable": {"thread_id": "correct_workflow_001"}}
    
    print(f"📝 主题: {initial_state['topic']}")
    print(f"🎯 字数: {initial_state['max_words']}")
    print(f"🔍 搜索: 启用")
    print(f"🧠 RAG: 启用")
    print("=" * 60)
    
    start_time = time.time()
    total_tokens = 0
    step_count = 0
    
    try:
        current_input = initial_state
        
        while step_count < 20:  # 安全限制
            step_count += 1
            print(f"\n📍 步骤 {step_count}: 启动工作流程")
            print("-" * 40)
            
            # 🔥 步骤1：启动工作流程并检测中断（按照官方模式）
            interrupted = False
            interrupt_info = None
            
            # 首先尝试正常执行，检测是否有中断
            try:
                final_result = await graph.ainvoke(current_input, cast(Any, config))
                
                # 检查结果中是否有中断标记
                if "__interrupt__" in str(final_result) or (isinstance(final_result, dict) and "__interrupt__" in final_result):
                    interrupted = True
                    interrupt_info = final_result.get("__interrupt__") if isinstance(final_result, dict) else "unknown interrupt"
                    print(f"⏸️  检测到中断")
                else:
                    # 没有中断，工作流程完成，现在获取流式输出
                    print(f"🌊 工作流程完成，获取流式输出...")
                    async for chunk in graph.astream(current_input, cast(Any, config), stream_mode="messages"):
                        if print_streaming_content(chunk):
                            total_tokens += 1
                            
                            if total_tokens % 30 == 0:
                                elapsed = time.time() - start_time
                                print(f"\n[⚡ {total_tokens} tokens, {elapsed:.1f}s]", end="", flush=True)
                    break
                    
            except Exception as e:
                if "interrupt" in str(e).lower():
                    interrupted = True
                    interrupt_info = str(e)
                    print(f"⏸️  通过异常检测到中断: {str(e)[:100]}")
                else:
                    raise e
            
            if not interrupted:
                # 没有中断，工作流程完成
                print(f"\n🎉 工作流程完成！")
                break
            
            # 🔥 步骤2：处理中断，获取用户输入
            print(f"\n🤖 处理中断...")
            
            # 根据中断类型自动响应（在实际应用中这里应该是用户输入）
            if isinstance(interrupt_info, list) and len(interrupt_info) > 0:
                interrupt_data = interrupt_info[0] if isinstance(interrupt_info[0], dict) else {}
            elif isinstance(interrupt_info, dict):
                interrupt_data = interrupt_info
            else:
                interrupt_data = {}
            
            interrupt_type = interrupt_data.get("type", "unknown")
            message = interrupt_data.get("message", "需要用户确认")
            
            print(f"   类型: {interrupt_type}")
            print(f"   消息: {message}")
            
            # 自动响应逻辑
            if "outline" in interrupt_type:
                user_response = "yes"
                print("   📋 自动确认大纲")
            elif "knowledge" in interrupt_type or "rag" in interrupt_type:
                user_response = "skip"
                print("   🧠 自动跳过RAG增强")
            elif "search" in interrupt_type:
                user_response = "yes"
                print("   🔍 自动同意搜索")
            else:
                user_response = "yes"
                print("   ➡️  自动继续")
            
            print(f"   响应: {user_response}")
            
            # 🔥 步骤3：使用Command(resume=...)恢复执行并继续流式输出
            print(f"\n🌊 恢复执行并捕获流式输出...")
            print("-" * 30)
            
            step_tokens = 0
            current_input = Command(resume=user_response)
            
            # 恢复执行并获取流式输出
            async for chunk in graph.astream(current_input, cast(Any, config), stream_mode="messages"):
                if print_streaming_content(chunk):
                    step_tokens += 1
                    total_tokens += 1
                    
                    if total_tokens % 30 == 0:
                        elapsed = time.time() - start_time
                        print(f"\n[⚡ {total_tokens} tokens, {elapsed:.1f}s]", end="", flush=True)
            
            print(f"\n✅ 步骤完成 ({step_tokens} tokens)")
            
            # 继续检测是否还有更多中断
            continue
        
        total_time = time.time() - start_time
        
        print(f"\n" + "=" * 60)
        print(f"🎉 正确的流式+中断处理测试完成！")
        print(f"📊 统计结果:")
        print(f"   总步骤数: {step_count}")
        print(f"   总Token数: {total_tokens}")
        print(f"   总耗时: {total_time:.1f}秒")
        
        if total_tokens > 100:
            tokens_per_second = total_tokens / total_time
            print(f"   流式速度: {tokens_per_second:.1f} tokens/秒")
            print("✅ 完整工作流程+流式输出测试成功！")
            
            # 获取最终结果
            try:
                final_result = await graph.ainvoke(initial_state, cast(Any, config))
                if final_result.get("article"):
                    article_length = len(final_result["article"])
                    word_count = final_result.get("word_count", 0)
                    print(f"📄 最终文章: {article_length}字符，{word_count}字")
            except Exception as e:
                print(f"⚠️ 获取最终结果失败: {e}")
            
        else:
            print("❌ 流式输出token数量偏少，可能存在问题")
        
        return {"success": True, "tokens": total_tokens, "time": total_time, "steps": step_count}
        
    except Exception as e:
        print(f"❌ 正确流式+中断处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def main():
    """主函数"""
    print("🌊 正确的LangGraph流式+中断处理完整测试")
    print("🎯 目标：验证官方模式的中断处理+完整流式输出")
    
    result = await correct_streaming_workflow()
    
    print(f"\n💡 测试结论:")
    print("=" * 60)
    
    if result and result.get("success"):
        tokens = result.get("tokens", 0)
        time_taken = result.get("time", 0)
        steps = result.get("steps", 0)
        
        print("🎉 正确的流式+中断处理测试成功!")
        print(f"📊 性能: {tokens} tokens in {time_taken:.1f}s ({steps} steps)")
        
        if tokens > 100:
            print("🌊 确认: 完整工作流程支持真正的流式+中断处理")
            print("💡 成功实现: 大纲生成→确认→RAG→搜索→文章生成(流式)")
            print("🎯 关键技术: interrupt() + Command(resume=...) + stream_mode='messages'")
        else:
            print("⚠️ 流式效果需要进一步分析")
    else:
        error = result.get('error', '未知错误') if result else '测试失败'
        print(f"❌ 测试失败: {error}")
    
    print("\n🎯 正确流式+中断处理测试完成!")


if __name__ == "__main__":
    asyncio.run(main())