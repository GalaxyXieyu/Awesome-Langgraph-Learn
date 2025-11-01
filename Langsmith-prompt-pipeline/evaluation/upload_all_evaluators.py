"""
批量上传所有本地评估器到 LangSmith 平台
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.evaluator_manager import EvaluatorManager


def upload_all_evaluators():
    """上传所有配置中的评估器到 LangSmith 平台"""
    print("=" * 60)
    print("批量上传本地评估器到 LangSmith 平台")
    print("=" * 60)
    
    manager = EvaluatorManager()
    
    # 获取所有评估器
    evaluators = manager.list_evaluators()
    
    if not evaluators:
        print("\n[WARN] 未找到任何评估器配置")
        return
    
    print(f"\n找到 {len(evaluators)} 个评估器:")
    for name in evaluators.keys():
        print(f"  - {name}")
    
    print("\n开始上传...\n")
    print("-" * 60)
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    for evaluator_name, description in evaluators.items():
        print(f"\n[{evaluator_name}]")
        print("-" * 60)
        
        try:
            # 获取配置
            config = manager.config.get('evaluators', {}).get(evaluator_name, {})
            dataset_name = config.get('dataset', 'default')
            
            # 尝试推送
            success = manager.push(
                evaluator_name=evaluator_name,
                dataset_name=dataset_name,
                description=description
            )
            
            if success:
                results['success'].append(evaluator_name)
                print(f"✅ {evaluator_name} 上传成功")
            else:
                results['failed'].append(evaluator_name)
                print(f"⚠️  {evaluator_name} 上传失败（可能需要手动上传）")
                
        except Exception as e:
            results['failed'].append(evaluator_name)
            print(f"❌ {evaluator_name} 上传出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("上传结果汇总")
    print("=" * 60)
    print(f"\n✅ 成功: {len(results['success'])} 个")
    for name in results['success']:
        print(f"   - {name}")
    
    print(f"\n⚠️  失败: {len(results['failed'])} 个")
    for name in results['failed']:
        print(f"   - {name}")
        print(f"     💡 可以查看: evaluation/{name}_source.py")
    
    if results['failed']:
        print(f"\n💡 对于上传失败的评估器：")
        print(f"  1. 查看提取的源代码文件: evaluation/{{evaluator_name}}_source.py")
        print(f"  2. 访问 LangSmith Web UI:")
        for name in results['failed']:
            config = manager.config.get('evaluators', {}).get(name, {})
            dataset = config.get('dataset', 'default')
            print(f"     - {name}: https://smith.langchain.com/datasets/{dataset}/evaluators")
        print(f"  3. 点击 'Create Custom Code Evaluator'")
        print(f"  4. 粘贴对应评估器的源代码")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    upload_all_evaluators()

