"""
测试 Evaluator Manager 功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.evaluator_manager import EvaluatorManager
from config.langsmith_config import LangSmithConfig


def test_list_evaluators():
    """测试列出所有 evaluators"""
    print("=" * 60)
    print("测试 1: 列出所有 Evaluators")
    print("=" * 60)
    
    manager = EvaluatorManager()
    evaluators = manager.list_evaluators()
    
    print(f"\n找到 {len(evaluators)} 个 Evaluators:")
    print("-" * 60)
    for name, desc in evaluators.items():
        print(f"  {name:<35} {desc}")
    print("-" * 60)
    
    return len(evaluators) > 0


def test_extract_source_code():
    """测试提取源代码"""
    print("\n" + "=" * 60)
    print("测试 2: 提取 Evaluator 源代码")
    print("=" * 60)
    
    manager = EvaluatorManager()
    
    # 测试提取 structure_evaluator
    try:
        source = manager._get_evaluator_source_code(
            "structure_evaluator",
            "ReportEvaluators"
        )
        
        if source:
            print(f"\n[OK] 成功提取源代码 ({len(source)} 字符)")
            print(f"前 200 个字符预览:")
            print("-" * 60)
            print(source[:200] + "...")
            print("-" * 60)
            return True
        else:
            print("[ERROR] 源代码为空")
            return False
            
    except Exception as e:
        print(f"[ERROR] 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validate():
    """测试验证功能"""
    print("\n" + "=" * 60)
    print("测试 3: 验证 Evaluator")
    print("=" * 60)
    
    manager = EvaluatorManager()
    
    # 测试验证 structure_evaluator
    result = manager.validate("structure_evaluator")
    
    if result['is_valid']:
        print(f"\n[OK] structure_evaluator 验证通过")
        return True
    else:
        print(f"\n[ERROR] 验证失败:")
        for error in result['errors']:
            print(f"  - {error}")
        return False


def test_extract_all_evaluators():
    """测试提取所有 evaluators 的源代码"""
    print("\n" + "=" * 60)
    print("测试 4: 提取所有 Evaluators 源代码")
    print("=" * 60)
    
    manager = EvaluatorManager()
    evaluators = manager.list_evaluators()
    
    success_count = 0
    fail_count = 0
    
    for name in evaluators.keys():
        try:
            config = manager.config['evaluators'][name]
            source = manager._get_evaluator_source_code(
                name,
                config.get('class')
            )
            
            if source:
                print(f"  ✓ {name:<35} ({len(source)} 字符)")
                success_count += 1
            else:
                print(f"  ✗ {name:<35} (源代码为空)")
                fail_count += 1
                
        except Exception as e:
            print(f"  ✗ {name:<35} (错误: {str(e)[:50]})")
            fail_count += 1
    
    print(f"\n结果: {success_count} 成功, {fail_count} 失败")
    return fail_count == 0


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Evaluator Manager 功能测试")
    print("=" * 60)
    
    # 检查 LangSmith 配置
    try:
        client = LangSmithConfig.get_client()
        print("\n[OK] LangSmith 客户端连接成功")
    except Exception as e:
        print(f"\n[WARN] LangSmith 未配置: {e}")
        print("  部分功能（push/pull）需要 LangSmith API Key")
        print("  继续测试其他功能...\n")
    
    # 运行测试
    tests = [
        ("列出 Evaluators", test_list_evaluators),
        ("提取源代码", test_extract_source_code),
        ("验证 Evaluator", test_validate),
        ("提取所有源代码", test_extract_all_evaluators),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 '{test_name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:<10} {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

