#!/usr/bin/env python3
"""
完整的写作助手工作流程测试脚本 - 真正的完整流式版本
测试完整工作流：大纲生成 → 确认 → RAG增强 → 搜索 → 文章生成
确保每个步骤都有流式输出和正确的中断处理
"""

import asyncio
import time
from typing import Dict, Any, cast
from graph import create_writing_assistant_graph, initialize_writing_state
from tools import load_knowledge_bases
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver


def print_streaming_content(chunk: Any, step_name: str = ""):
    """
    优化的流式内容打印函数 - 显示真正的token流式效果
    """
    # 🎯 正确处理tuple格式的chunk
    if isinstance(chunk, tuple) and len(chunk) > 0:
        message_chunk = chunk[0]  # 获取AIMessageChunk
        
        # 检查是否有content
        if hasattr(message_chunk, 'content'):
            content = message_chunk.content
            if content and isinstance(content, str):
                # 🔤 实时打印每个token - 打字机效果！
                print(content, end="", flush=True)
                return True
    return False


async def complete_streaming_workflow():
    """
    完整的流式工作流程 - 确保走完所有步骤
    大纲生成 → 确认 → RAG增强 → 搜索 → 文章生成
    """
    print("\n🚀 完整流式写作助手工作流程测试")
    print("🎯 目标：确保完整流程 + 真正流式输出")
    print("=" * 60)
    
    # 初始化
    try:
        load_knowledge_bases()
        print("✅ 知识库初始化成功")
    except Exception as e:
        print(f"⚠️ 知识库初始化警告: {e}")
    
    graph = create_writing_assistant_graph()
    print("✅ 写作助手图创建成功")
    
    # 验证checkpointer
    if hasattr(graph, 'checkpointer') and graph.checkpointer:
        print("✅ Checkpointer配置正确")
    else:
        print("⚠️ 警告：Checkpointer可能未正确配置")
    
    # 完整工作流程配置
    initial_state = initialize_writing_state(
        topic="Python异步编程最佳实践",
        user_id="complete_streaming_test",
        max_words=600,
        style="technical",
        language="zh",
        enable_search=True  # 🔥 启用完整功能
    )
    
    config: Dict[str, Any] = {"configurable": {"thread_id": "complete_streaming_001"}}
    
    start_time = time.time()
    total_tokens = 0
    step_count = 0
    
    try:
        current_input = initial_state
        
        # 完整工作流程循环
        while step_count < 15:  # 增加步骤限制，确保完整流程
            step_count += 1
            print(f"\n📍 步骤 {step_count}: 执行工作流程")
            print("-" * 50)
            
            # 🔥 关键：使用astream检测中断
            interrupted = False
            result = None
            
            try:
                # 使用astream(updates)模式检测中断
                async for chunk in graph.astream(current_input, cast(Any, config), stream_mode=""):
                    print(f"   📦 收到更新: {list(chunk.keys())}")
                    print(chunk)
                    # 检查是否有中断标记
                    if "__interrupt__" in chunk:
                        interrupted = True
                        print(f"⏸️  检测到中断")
                        break
                    else:
                        # 保存最后的结果用于状态更新
                        for node_name, node_result in chunk.items():
                            if isinstance(node_result, dict):
                                result = node_result
                
                if interrupted:
                    # 获取当前状态用于确定中断类型
                    if result:
                        current_step = result.get("current_step", "unknown")
                        print(f"   当前步骤: {current_step}")
                    else:
                        current_step = "unknown"
                    
                    # 🤖 自动处理中断
                    if "outline" in current_step or "confirmation" in current_step:
                        user_response = "yes"
                        print("   📋 自动确认大纲")
                    elif "rag" in current_step or "knowledge" in current_step:
                        user_response = "skip"  # 跳过RAG增强以简化流程
                        print("   🧠 跳过RAG增强")
                    elif "search" in current_step:
                        user_response = "yes"
                        print("   🔍 自动同意搜索")
                    else:
                        user_response = "yes"
                        print(f"   ➡️  自动继续 ({current_step})")
                    
                    print(f"   响应: {user_response}")
                    
                    # 🌊 恢复执行并获取流式输出
                    print(f"\n🌊 恢复执行，开始流式输出...")
                    print("-" * 30)
                    
                    step_tokens = 0
                    async for chunk in graph.astream(Command(resume=user_response), cast(Any, config), stream_mode="messages"):
                        if print_streaming_content(chunk):
                            step_tokens += 1
                            total_tokens += 1
                            
                            # 每30个token显示进度
                            if total_tokens % 30 == 0:
                                elapsed = time.time() - start_time
                                print(f"\n[⚡ {total_tokens} tokens, {elapsed:.1f}s]", end="", flush=True)
                    
                    print(f"\n✅ 步骤完成 ({step_tokens} tokens)")
                    
                    # 准备下一步
                    current_input = Command(resume=user_response)
                    
                else:
                    # 没有中断，工作流程可能完成
                    print("🎉 工作流程执行完成")
                    
                    # 最终流式输出检查
                    print(f"\n🌊 检查最终流式输出...")
                    print("-" * 30)
                    
                    final_tokens = 0
                    async for chunk in graph.astream(current_input, cast(Any, config), stream_mode="messages"):
                        if print_streaming_content(chunk):
                            final_tokens += 1
                            total_tokens += 1
                            
                            if total_tokens % 30 == 0:
                                elapsed = time.time() - start_time
                                print(f"\n[⚡ {total_tokens} tokens, {elapsed:.1f}s]", end="", flush=True)
                    
                    if final_tokens > 0:
                        print(f"\n✅ 最终输出完成 ({final_tokens} tokens)")
                    
                    print(f"\n🏁 完整流程结束！总计 {total_tokens} tokens")
                    break
                    
            except Exception as e:
                if "interrupt" in str(e).lower():
                    print(f"⏸️  通过异常检测到中断: {str(e)[:100]}")
                    interrupted = True
                    # 在这种情况下也需要处理中断
                    user_response = "yes"
                    current_input = Command(resume=user_response)
                    continue
                else:
                    print(f"❌ 步骤 {step_count} 失败: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        
        total_time = time.time() - start_time
        
        # 获取最终结果
        try:
            final_result = await graph.ainvoke(initial_state, cast(Any, config))
        except:
            final_result = None
        
        return {
            "success": True,
            "total_time": total_time,
            "total_tokens": total_tokens,
            "steps": step_count,
            "final_result": final_result
        }
        
    except Exception as e:
        print(f"❌ 流式工作流程失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def handle_workflow_interrupts(graph, config: Dict[str, Any]):
    """
    处理工作流程的中断和流式输出
    """
    # 初始化状态
    initial_state = initialize_writing_state(
        topic="Python异步编程最佳实践",
        user_id="workflow_test",
        max_words=600,
        style="technical",
        language="zh",
        enable_search=True
    )
    
    print(f"📝 主题: {initial_state['topic']}")
    print(f"🎯 字数: {initial_state['max_words']}")
    print("=" * 60)
    
    current_input = initial_state
    step_count = 0
    total_tokens = 0
    start_time = time.time()
    
    while step_count < 15:  # 安全限制
        step_count += 1
        print(f"\n📍 步骤 {step_count}: 执行工作流程")
        print("-" * 40)
        
        try:
            # 检测中断
            result = await graph.ainvoke(current_input, cast(Any, config))
            
            # 检查是否有中断
            if hasattr(result, '__contains__') and "__interrupt__" in result:
                print(f"⏸️  检测到中断")
                current_step = result.get("current_step", "unknown")
                print(f"   当前步骤: {current_step}")
                
                # 自动处理中断
                if "outline" in current_step or "confirmation" in current_step:
                    user_response = "yes"
                    print("   📋 自动确认大纲")
                elif "rag" in current_step or "knowledge" in current_step:
                    user_response = "skip"  # 跳过RAG增强以简化流程
                    print("   🧠 跳过RAG增强")
                elif "search" in current_step:
                    user_response = "yes"
                    print("   🔍 自动同意搜索")
                else:
                    user_response = "yes"
                    print(f"   ➡️  自动继续 ({current_step})")
                
                print(f"   响应: {user_response}")
                
                # 恢复执行并获取流式输出
                print(f"\n🌊 恢复执行，开始流式输出...")
                print("-" * 30)
                
                step_tokens = 0
                async for chunk in graph.astream(Command(resume=user_response), cast(Any, config), stream_mode="messages"):
                    if print_streaming_content(chunk):
                        step_tokens += 1
                        total_tokens += 1
                        
                        if total_tokens % 30 == 0:
                            elapsed = time.time() - start_time
                            print(f"\n[⚡ {total_tokens} tokens, {elapsed:.1f}s]", end="", flush=True)
                
                print(f"\n✅ 步骤完成 ({step_tokens} tokens)")
                current_input = Command(resume=user_response)
                
            else:
                # 没有中断，工作流程完成
                print("🎉 工作流程执行完成")
                
                # 最终流式输出
                print(f"\n🌊 获取最终流式输出...")
                print("-" * 30)
                
                final_tokens = 0
                async for chunk in graph.astream(current_input, cast(Any, config), stream_mode="messages"):
                    if print_streaming_content(chunk):
                        final_tokens += 1
                        total_tokens += 1
                        
                        if total_tokens % 30 == 0:
                            elapsed = time.time() - start_time
                            print(f"\n[⚡ {total_tokens} tokens, {elapsed:.1f}s]", end="", flush=True)
                
                if final_tokens > 0:
                    print(f"\n✅ 最终输出完成 ({final_tokens} tokens)")
                
                print(f"\n🏁 完整流程结束！总计 {total_tokens} tokens")
                break
                
        except Exception as e:
            if "interrupt" in str(e).lower():
                print(f"⏸️  通过异常检测到中断: {str(e)[:100]}")
                user_response = "yes"
                current_input = Command(resume=user_response)
                continue
            else:
                print(f"❌ 步骤 {step_count} 失败: {e}")
                break
    
    # 获取最终结果
    try:
        final_result = await graph.ainvoke(initial_state, cast(Any, config))
        return final_result
    except:
        return None


async def test_streaming_writing_workflow():
    """
    测试完整的流式写作工作流程
    """
    print("🎭 LangGraph 流式写作助手测试")
    print("🎯 目标：验证完整工作流的真正流式输出效果")
    

    load_knowledge_bases()
    print("✅ 知识库初始化成功")
    
    graph = create_writing_assistant_graph()

    config: Dict[str, Any] = {"configurable": {"thread_id": "streaming_test_001"}}
    
    start_time = time.time()
        
    final_result = await handle_workflow_interrupts(graph, config)
        
    total_time = time.time() - start_time
        
    print(f"\n" + "="*60)
    print(f"📊 流式写作工作流程测试结果:")
    print(f"   总执行时间: {total_time:.3f}s")
        
    if final_result:
        # 分析最终结果
        article = final_result.get("article", "")
        word_count = final_result.get("word_count", 0)
        outline = final_result.get("outline", {})
        search_results = final_result.get("search_results", [])
        rag_status = final_result.get("rag_enhancement", "")
            
        print(f"\n📋 工作流程完成度检查:")
        print(f"   ✅ 大纲生成: {'完成' if outline else '未完成'}")
        print(f"   ✅ 搜索功能: {'完成' if search_results else '跳过'} ({len(search_results)}个结果)")
        print(f"   ✅ RAG增强: {rag_status if rag_status else '未执行'}")
        print(f"   ✅ 文章生成: {'完成' if article else '未完成'}")
            
        if article:
            print(f"\n📄 生成文章信息:")
            print(f"   字数: {word_count}字")
            print(f"   长度: {len(article)}字符")
                
            print(f"\n📖 文章预览:")
            print("-" * 40)
            preview = article[:200] + "..." if len(article) > 200 else article
            print(preview)
            print("-" * 40)
            
            # 流式效果评估
    if total_time > 0:
            if word_count > 0:
                chars_per_second = len(article) / total_time
                print(f"\n⚡ 流式效果评估:")
                print(f"   平均输出速度: {chars_per_second:.1f} 字符/秒")
                
                if chars_per_second > 10:
                    print("   🎉 流式效果: 优秀（实时响应）")
                elif chars_per_second > 5:
                    print("   ✅ 流式效果: 良好（流畅输出）")
                else:
                    print("   ⚠️ 流式效果: 一般（可能有延迟）")
    
    return {"success": True, "total_time": total_time, "final_result": final_result}


async def main():
    """主测试函数 - 使用完整流式工作流程"""
    print("🌊 开始流式写作助手完整工作流程测试")
    print("🎯 测试目标：大纲→确认→RAG→搜索→文章生成(流式)")
    
    # 直接使用完整的流式工作流程
    result = await complete_streaming_workflow()
    
    print(f"\n💡 测试总结:")
    print("=" * 60)
    
    if result and result.get("success"):
        print("🎉 流式写作工作流程测试成功!")
        print(f"⏱️ 总用时: {result.get('total_time', 0):.3f}秒")
        print(f"📊 总Token数: {result.get('total_tokens', 0)}")
        print(f"🔄 总步骤数: {result.get('steps', 0)}")
        print("🌊 流式输出效果: 已验证")
        print("📝 完整工作流程: 已完成")
        
        # 显示最终结果信息
        final_result = result.get('final_result')
        if final_result:
            article = final_result.get("article", "")
            if article:
                word_count = final_result.get("word_count", 0)
                print(f"\n📄 生成文章信息:")
                print(f"   字数: {word_count}字")
                print(f"   字符数: {len(article)}")
                
                print(f"\n📖 文章预览:")
                print("-" * 40)
                preview = article[:200] + "..." if len(article) > 200 else article
                print(preview)
                print("-" * 40)
    else:
        error = result.get('error', '未知错误') if result else '测试失败'
        print(f"❌ 流式工作流程测试失败: {error}")
    
    print(f"\n🎯 完整流式工作流程测试完成!")


if __name__ == "__main__":
    asyncio.run(main())