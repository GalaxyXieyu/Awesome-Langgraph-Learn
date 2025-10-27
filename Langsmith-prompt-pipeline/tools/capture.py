"""
Dataset 捕获装饰器
用于自动捕获 LLM 节点的输入参数，支持推送到 LangSmith Dataset
"""
import json
import functools
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextvars import ContextVar

# 使用 ContextVar 在装饰器和捕获点之间传递数据
_capture_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('_capture_context', default=None)


class DatasetCapture:
    """Dataset 捕获管理器"""
    
    def __init__(self, cache_dir: str = ".dataset_cache"):
        """
        初始化捕获管理器
        
        Args:
            cache_dir: 本地缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def save_capture(
        self,
        prompt_name: str,
        dataset_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None
    ):
        """
        保存捕获的数据到本地缓存
        
        Args:
            prompt_name: 提示词名称
            dataset_name: Dataset 名称
            inputs: 输入参数（调用 LLM 时的 inputs）
            outputs: 输出结果（可选）
            metadata: 元数据（可选）
            run_id: 运行 ID（可选）
        """
        # 创建提示词专属目录
        prompt_dir = self.cache_dir / prompt_name
        prompt_dir.mkdir(exist_ok=True)
        
        # 生成文件名（基于时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"run_{timestamp}.json"
        filepath = prompt_dir / filename
        
        # 构建数据结构
        capture_data = {
            "prompt_name": prompt_name,
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "run_id": run_id,
            "inputs": inputs,
            "outputs": outputs or {},
            "metadata": metadata or {},
            "synced": False  # 标记是否已同步到 LangSmith
        }
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(capture_data, f, ensure_ascii=False, indent=2)
        
        print(f"[Capture] 已保存: {prompt_name} → {filepath.name}")
    
    def list_captures(self, prompt_name: Optional[str] = None) -> list:
        """
        列出所有捕获的数据
        
        Args:
            prompt_name: 筛选特定提示词（可选）
            
        Returns:
            捕获数据列表
        """
        captures = []
        
        if prompt_name:
            # 只列出特定提示词
            prompt_dir = self.cache_dir / prompt_name
            if prompt_dir.exists():
                files = list(prompt_dir.glob("run_*.json"))
            else:
                files = []
        else:
            # 列出所有提示词
            files = list(self.cache_dir.glob("*/run_*.json"))
        
        for filepath in sorted(files):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_filepath'] = str(filepath)
                captures.append(data)
        
        return captures
    
    def mark_as_synced(self, filepath: str):
        """
        标记某个捕获数据为已同步
        
        Args:
            filepath: 文件路径
        """
        path = Path(filepath)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data['synced'] = True
            data['synced_at'] = datetime.now().isoformat()
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


# 全局捕获管理器实例
_global_capture_manager = DatasetCapture()

# 全局 LangSmith Client（延迟初始化）
_langsmith_client = None


def _get_langsmith_client():
    """获取 LangSmith Client（单例模式）"""
    global _langsmith_client
    if _langsmith_client is None:
        from langsmith import Client
        _langsmith_client = Client()
    return _langsmith_client


def _sync_to_langsmith(
    dataset_name: str,
    inputs: Dict[str, Any],
    outputs: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    同步单条数据到 LangSmith Dataset
    
    Args:
        dataset_name: Dataset 名称
        inputs: 输入参数
        outputs: 输出结果
        metadata: 元数据
    """
    client = _get_langsmith_client()
    
    # 获取或创建 Dataset
    try:
        datasets = list(client.list_datasets(dataset_name=dataset_name))
        if datasets:
            dataset_id = str(datasets[0].id)
        else:
            dataset = client.create_dataset(
                dataset_name=dataset_name,
                description=f"自动捕获的 {dataset_name} 测试数据"
            )
            dataset_id = str(dataset.id)
    except:
        # 如果获取失败，尝试创建
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=f"自动捕获的 {dataset_name} 测试数据"
        )
        dataset_id = str(dataset.id)
    
    # 创建 example
    client.create_example(
        dataset_id=dataset_id,
        inputs=inputs,
        outputs=outputs or {},
        metadata=metadata or {}
    )
    
    print(f"[Sync] 已同步到 LangSmith: {dataset_name}")


def capture_dataset(
    prompt_name: str,
    dataset_name: str = "default",
    capture_output: bool = True,
    auto_sync: bool = True
):
    """
    Dataset 捕获装饰器
    
    自动捕获被装饰函数中调用 LLM 时传入的 inputs 参数
    
    使用方式：
        @traceable
        @capture_dataset(prompt_name="report_generator", dataset_name="report_generator")
        def generate_report_node(self, state):
            inputs = {...}
            capture_inputs(inputs)  # 显式标记捕获
            chain.invoke(inputs)
    
    Args:
        prompt_name: 提示词名称（如 "report_generator"）
        dataset_name: Dataset 名称（如 "report_generator"）
        capture_output: 是否捕获输出（默认 True）
        auto_sync: 是否自动同步到 LangSmith（默认 True）
                   - True: 立即推送到 LangSmith Dataset
                   - False: 只保存到本地缓存
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 设置捕获上下文
            context = {
                'prompt_name': prompt_name,
                'dataset_name': dataset_name,
                'capture_output': capture_output,
                'inputs': None,
                'outputs': None,
                'metadata': {}
            }
            token = _capture_context.set(context)
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 捕获输出（如果需要）
                if capture_output and result:
                    context['outputs'] = result
                
                # 如果捕获到了 inputs，保存数据
                if context.get('inputs'):
                    # 提取 run_id（如果有 LangSmith trace）
                    run_id = None
                    try:
                        from langsmith.run_helpers import get_current_run_tree
                        run_tree = get_current_run_tree()
                        if run_tree:
                            run_id = str(run_tree.id)
                    except:
                        pass
                    
                    # 保存捕获数据
                    _global_capture_manager.save_capture(
                        prompt_name=prompt_name,
                        dataset_name=dataset_name,
                        inputs=context['inputs'],
                        outputs=context.get('outputs'),
                        metadata=context.get('metadata'),
                        run_id=run_id
                    )
                    
                    # 自动同步到 LangSmith（如果启用）
                    if auto_sync:
                        try:
                            _sync_to_langsmith(
                                dataset_name=dataset_name,
                                inputs=context['inputs'],
                                outputs=context.get('outputs'),
                                metadata={
                                    'prompt_name': prompt_name,
                                    'run_id': run_id,
                                    **context.get('metadata', {})
                                }
                            )
                        except Exception as e:
                            # 同步失败不影响主流程
                            print(f"[WARN] 自动同步失败: {e}")
                
                return result
                
            finally:
                # 清理上下文
                _capture_context.reset(token)
        
        return wrapper
    return decorator


def capture_inputs(
    inputs: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
):
    """
    显式标记要捕获的 inputs
    
    在被 @capture_dataset 装饰的函数中调用此函数，显式标记要捕获的数据
    
    使用方式：
        @capture_dataset(prompt_name="report_generator")
        def generate_report_node(self, state):
            inputs = {
                "topic": state.get("topic"),
                "style": state.get("style"),
                ...
            }
            
            # 显式标记捕获
            capture_inputs(inputs, metadata={"user_query": state.get("user_query")})
            
            chain.invoke(inputs)
    
    Args:
        inputs: 要捕获的输入参数字典
        metadata: 额外的元数据（可选）
    """
    context = _capture_context.get()
    
    if context is None:
        # 不在捕获上下文中，忽略
        return
    
    # 保存 inputs 到上下文
    context['inputs'] = inputs.copy()  # 深拷贝避免后续修改
    
    # 保存 metadata
    if metadata:
        context['metadata'].update(metadata)


# ========== 数据管理功能 ==========

def list_all_captures(prompt_name: Optional[str] = None, verbose: bool = True):
    """
    列出所有捕获的数据
    
    Args:
        prompt_name: 筛选特定提示词
        verbose: 是否显示详细信息
    """
    captures = _global_capture_manager.list_captures(prompt_name)
    
    if not captures:
        if verbose:
            print("\n[INFO] 没有找到捕获数据")
        return []
    
    if verbose:
        print(f"\n找到 {len(captures)} 条捕获数据:\n")
        print("="*80)
        
        for i, capture in enumerate(captures, 1):
            synced_status = "✓ 已同步" if capture.get('synced') else "  未同步"
            
            print(f"{i}. [{synced_status}] {capture['prompt_name']} → {capture['dataset_name']}")
            print(f"   时间: {capture['timestamp']}")
            print(f"   Inputs: {list(capture['inputs'].keys())}")
            
            # 显示部分 inputs 内容
            for key, value in list(capture['inputs'].items())[:3]:
                value_str = str(value)[:50]
                if len(str(value)) > 50:
                    value_str += "..."
                print(f"     - {key}: {value_str}")
            
            if len(capture['inputs']) > 3:
                print(f"     ... 还有 {len(capture['inputs']) - 3} 个字段")
            
            print("-"*80)
    
    return captures


def sync_all_captures(dataset_filter: Optional[str] = None, skip_synced: bool = True):
    """
    批量同步所有未同步的数据到 LangSmith
    
    Args:
        dataset_filter: 只同步特定 Dataset
        skip_synced: 跳过已同步的数据
    
    Returns:
        同步统计信息
    """
    from collections import defaultdict
    
    print("\n" + "="*60)
    print("批量同步工具")
    print("="*60)
    
    # 获取所有捕获数据
    all_captures = _global_capture_manager.list_captures()
    
    if not all_captures:
        print("\n[INFO] 没有找到需要同步的数据")
        return {"total": 0, "synced": 0}
    
    # 按 dataset_name 分组
    grouped = defaultdict(list)
    for capture in all_captures:
        # 过滤
        if skip_synced and capture.get('synced', False):
            continue
        if dataset_filter and capture['dataset_name'] != dataset_filter:
            continue
        
        grouped[capture['dataset_name']].append(capture)
    
    if not grouped:
        print("\n[INFO] 没有需要同步的新数据")
        return {"total": len(all_captures), "synced": 0}
    
    # 显示统计
    print(f"\n找到 {len(all_captures)} 条捕获数据")
    print(f"待同步: {sum(len(v) for v in grouped.values())} 条")
    print(f"\n按 Dataset 分组:")
    for dataset_name, captures in grouped.items():
        print(f"  - {dataset_name}: {len(captures)} 条")
    
    # 同步每个 Dataset
    synced_count = 0
    for dataset_name, captures in grouped.items():
        print(f"\n{'='*60}")
        print(f"同步到 Dataset: {dataset_name}")
        print(f"{'='*60}")
        
        for i, capture in enumerate(captures, 1):
            try:
                _sync_to_langsmith(
                    dataset_name=dataset_name,
                    inputs=capture['inputs'],
                    outputs=capture.get('outputs', {}),
                    metadata={
                        'prompt_name': capture['prompt_name'],
                        'timestamp': capture['timestamp'],
                        'run_id': capture.get('run_id'),
                        **capture.get('metadata', {})
                    }
                )
                
                # 标记为已同步
                filepath = capture.get('_filepath')
                if filepath:
                    _global_capture_manager.mark_as_synced(filepath)
                
                synced_count += 1
                print(f"  [{i}/{len(captures)}] ✓ {capture['prompt_name']}")
                
            except Exception as e:
                print(f"  [{i}/{len(captures)}] ✗ 失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"同步完成！共同步 {synced_count} 条数据")
    print(f"{'='*60}\n")
    
    return {"total": len(all_captures), "synced": synced_count}


def clean_synced_captures():
    """清理已同步的本地缓存"""
    captures = _global_capture_manager.list_captures()
    
    cleaned_count = 0
    for capture in captures:
        if capture.get('synced'):
            filepath = Path(capture['_filepath'])
            if filepath.exists():
                filepath.unlink()
                cleaned_count += 1
    
    print(f"\n[OK] 已清理 {cleaned_count} 个已同步的缓存文件")


def get_capture_manager():
    """获取全局捕获管理器"""
    return _global_capture_manager


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dataset 捕获工具 - 管理和同步捕获的数据"
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有捕获的数据'
    )
    
    parser.add_argument(
        '--sync',
        action='store_true',
        help='批量同步未同步的数据到 LangSmith'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理已同步的本地缓存'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        help='只处理特定 Dataset'
    )
    
    parser.add_argument(
        '--prompt',
        type=str,
        help='只列出特定提示词的数据'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试示例'
    )
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if not any([args.list, args.sync, args.clean, args.test]):
        parser.print_help()
        exit(0)
    
    # 执行操作
    if args.list:
        # 列出数据
        list_all_captures(prompt_name=args.prompt)
    
    elif args.sync:
        # 批量同步
        sync_all_captures(dataset_filter=args.dataset)
    
    elif args.clean:
        # 清理缓存
        clean_synced_captures()
    
    elif args.test:
        # 测试装饰器
        print("测试 Dataset 捕获装饰器...\n")
        
        # 模拟一个节点函数
        @capture_dataset(prompt_name="test_prompt", dataset_name="test_dataset", auto_sync=False)
        def mock_llm_node(topic: str, style: str):
            """模拟 LLM 节点"""
            print(f"  执行节点: topic={topic}, style={style}")
            
            # 准备 inputs
            inputs = {
                "topic": topic,
                "style": style,
                "year_range": "2023-2024"
            }
            
            # 显式标记捕获
            capture_inputs(inputs, metadata={"test": True})
            
            # 模拟 LLM 调用
            result = f"这是关于 {topic} 的 {style} 风格报告"
            
            return {"report": result}
        
        # 测试调用
        print("1. 第一次调用")
        mock_llm_node("人工智能", "formal")
        
        print("\n2. 第二次调用")
        mock_llm_node("金融科技", "casual")
        
        # 列出捕获的数据
        print("\n3. 列出捕获的数据")
        captures = list_all_captures()
        print(f"   共捕获 {len(captures)} 条数据")
        
        print("\n[OK] 测试完成！")

