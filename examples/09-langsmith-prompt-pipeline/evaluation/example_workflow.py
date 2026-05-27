"""
Evaluator 实际工作流程示例
演示如何使用 evaluator 进行完整的工作流
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.evaluation import EvaluationRunner
from evaluation.evaluators.report import ReportEvaluators
from prompts.prompt_manager import PromptManager


def example_1_direct_use():
    """示例 1：直接使用本地 evaluator 函数对象"""
    print("=" * 60)
    print("示例 1: 直接使用本地 evaluator 函数对象")
    print("=" * 60)
    
    # 创建评估运行器
    runner = EvaluationRunner()
    
    # 方式 1：直接传入函数对象
    results = runner.evaluate_prompt(
        prompt_name="report_generator",
        dataset_name="report_generator",
        evaluators=[
            ReportEvaluators.structure_evaluator,  # ✅ 直接使用函数对象
            ReportEvaluators.content_completeness_evaluator,
            ReportEvaluators.relevance_evaluator,
            ReportEvaluators.parameter_usage_evaluator
        ]
    )
    
    print(f"\n评估结果:")
    print(f"  总分: {results.get('quality_score', 0):.2%}")
    print(f"  测试用例数: {results.get('total_tests', 0)}")


def example_2_use_config():
    """示例 2：使用配置文件中的 evaluator 名称"""
    print("\n" + "=" * 60)
    print("示例 2: 使用配置文件中的 evaluator")
    print("=" * 60)
    
    # 使用 PromptManager（会自动从配置读取 evaluator）
    manager = PromptManager()
    
    # 从 prompts_config.yaml 读取 evaluator 配置
    result = manager.evaluate_prompt('report_generator')
    
    print(f"\n评估结果:")
    print(f"  总分: {result.get('quality_score', 0):.2%}")
    print(f"  各维度分数: {result.get('scores', {})}")


def example_3_extract_code():
    """示例 3：提取 evaluator 代码（用于上传到平台）"""
    print("\n" + "=" * 60)
    print("示例 3: 提取 evaluator 代码（用于上传到平台）")
    print("=" * 60)
    
    from evaluation.evaluator_manager import EvaluatorManager
    
    manager = EvaluatorManager()
    
    # 提取代码
    source_code = manager._get_evaluator_source_code(
        "structure_evaluator",
        "ReportEvaluators"
    )
    
    print(f"\n提取的源代码 ({len(source_code)} 字符):")
    print("-" * 60)
    print(source_code[:300] + "...")  # 显示前 300 字符
    print("-" * 60)
    
    print("\n💡 使用方法:")
    print("  1. 访问 LangSmith Web UI")
    print("  2. 进入数据集 → Evaluators")
    print("  3. 点击 'Create Custom Code Evaluator'")
    print("  4. 粘贴上面的代码")


def example_4_push_to_platform():
    """示例 4：推送 evaluator 到平台"""
    print("\n" + "=" * 60)
    print("示例 4: 推送 evaluator 到平台")
    print("=" * 60)
    
    from evaluation.evaluator_manager import EvaluatorManager
    
    manager = EvaluatorManager()
    
    # 尝试推送
    success = manager.push(
        evaluator_name="structure_evaluator",
        dataset_name="report_generator",
        description="结构评估器 - 检查报告的基本结构"
    )
    
    if success:
        print("\n✅ 成功推送到平台")
        print("  可以在 LangSmith Web UI 查看")
    else:
        print("\n⚠️  API 不支持或失败，代码已保存到本地文件")
        print("  可以手动上传到平台")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Evaluator 工作流程示例")
    print("=" * 60)
    
    print("\n选择示例:")
    print("  1. 直接使用本地 evaluator 函数对象")
    print("  2. 使用配置文件中的 evaluator")
    print("  3. 提取 evaluator 代码（用于上传）")
    print("  4. 推送 evaluator 到平台")
    print("\n注意：实际运行需要配置 LangSmith API Key")
    print("=" * 60)
    
    # 运行示例（根据需要取消注释）
    # example_1_direct_use()
    # example_2_use_config()
    # example_3_extract_code()
    # example_4_push_to_platform()
    
    print("\n💡 关键理解:")
    print("  - Evaluator 是函数对象，在本地使用不需要上传")
    print("  - EvaluatorManager 主要用于提取代码和管理配置")
    print("  - 如果在平台创建了 evaluator，可以从平台获取代码（需要 API 支持）")


if __name__ == "__main__":
    main()

