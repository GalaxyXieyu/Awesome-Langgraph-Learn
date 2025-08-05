#!/usr/bin/env python3
"""
调试图流程 - 检查节点和边的定义
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_graph_structure():
    """调试图结构"""
    print("🔍 调试图结构...")
    
    try:
        from graph.graph import create_writing_assistant_graph
        
        # 创建图
        workflow = create_writing_assistant_graph()
        
        print("✅ 图创建成功")
        print(f"📊 图类型: {type(workflow)}")
        
        # 检查节点
        if hasattr(workflow, 'nodes'):
            print(f"\n📋 节点列表 ({len(workflow.nodes)}):")
            for i, (node_name, node_func) in enumerate(workflow.nodes.items(), 1):
                print(f"  {i}. {node_name} -> {node_func.__name__ if hasattr(node_func, '__name__') else type(node_func)}")
        
        # 检查边
        if hasattr(workflow, 'edges'):
            print(f"\n🔗 边列表 ({len(workflow.edges)}):")
            for i, (from_node, to_node) in enumerate(workflow.edges.items(), 1):
                print(f"  {i}. {from_node} -> {to_node}")
        
        # 检查条件边
        if hasattr(workflow, 'conditional_edges'):
            print(f"\n🔀 条件边列表 ({len(workflow.conditional_edges)}):")
            for i, (from_node, condition_info) in enumerate(workflow.conditional_edges.items(), 1):
                if isinstance(condition_info, dict):
                    condition_func = condition_info.get('condition')
                    condition_map = condition_info.get('condition_map', {})
                    print(f"  {i}. {from_node} -> {condition_func.__name__ if hasattr(condition_func, '__name__') else 'unknown'}")
                    for condition_result, target_node in condition_map.items():
                        print(f"     '{condition_result}' -> {target_node}")
                else:
                    print(f"  {i}. {from_node} -> {condition_info}")
        
        # 检查起始和结束节点
        if hasattr(workflow, 'entry_point'):
            print(f"\n🚀 起始节点: {workflow.entry_point}")
        
        print(f"\n📋 预期的完整流程:")
        print(f"  1. START -> generate_outline")
        print(f"  2. generate_outline -> outline_confirmation")
        print(f"  3. outline_confirmation -> route_after_confirmation")
        print(f"     - 'yes' -> rag_enhancement")
        print(f"     - 'no' -> generate_outline")
        print(f"  4. rag_enhancement -> route_after_rag_enhancement")
        print(f"     - 总是 -> search_confirmation")
        print(f"  5. search_confirmation -> route_after_search_confirmation")
        print(f"     - 'yes' -> search_execution")
        print(f"     - 'no' -> article_generation")
        print(f"  6. search_execution -> should_continue_after_search")
        print(f"     - 总是 -> article_generation")
        print(f"  7. article_generation -> END")
        
        return True
        
    except Exception as e:
        print(f"❌ 图创建失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def debug_confirmation_configs():
    """调试确认配置"""
    print("\n🔍 调试确认配置...")
    
    try:
        from graph.graph import CONFIRMATION_CONFIGS
        
        print(f"📋 确认配置 ({len(CONFIRMATION_CONFIGS)}):")
        for key, config in CONFIRMATION_CONFIGS.items():
            print(f"  {key}:")
            print(f"    类型: {config.get('type')}")
            print(f"    消息模板: {config.get('message_template', '')[:50]}...")
            print(f"    指令: {config.get('instructions')}")
            print(f"    状态键: {config.get('state_key')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 确认配置获取失败: {e}")
        return False

def main():
    print("🚀 调试图流程")
    print("=" * 60)
    
    success1 = debug_graph_structure()
    success2 = debug_confirmation_configs()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 图结构调试完成！")
        print("💡 检查上面的流程是否符合预期")
    else:
        print("❌ 图结构调试失败")
    
    print("✅ 调试完成")

if __name__ == "__main__":
    main()
