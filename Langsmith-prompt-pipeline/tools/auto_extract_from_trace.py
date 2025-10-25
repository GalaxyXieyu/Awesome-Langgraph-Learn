"""
通用的自动化中间结果提取工具
从 LangSmith Trace 中自动提取所有 LLM 调用的输入，无需手动适配

核心思路：
1. 运行一次完整流程（自动记录到 LangSmith）
2. 从 Trace 中自动提取所有 LLM 节点的输入
3. 保存为 Dataset，可在 Playground 中使用

优势：
- ✅ 零手动构建：运行一次即可
- ✅ 通用化：适用于任何 LangGraph 项目
- ✅ 零代码侵入：不需要修改现有代码
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from langsmith import Client


class TraceExtractor:
    """从 LangSmith Trace 自动提取中间结果"""
    
    def __init__(self):
        try:
            self.client = Client()
        except Exception as e:
            print(f"\n[错误] 无法连接到 LangSmith")
            print(f"  原因: {e}")
            print(f"\n请确保:")
            print(f"  1. 已设置 LANGSMITH_API_KEY 环境变量")
            print(f"  2. API Key 有效且有权限")
            print(f"\n设置方法:")
            print(f"  export LANGSMITH_API_KEY='your-api-key'")
            raise
        
        self.cache_dir = Path(".trace_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def list_recent_runs(self, project_name: str = None, limit: int = 10) -> List[Dict]:
        """
        列出最近的运行记录
        
        Args:
            project_name: 项目名称（默认使用当前项目）
            limit: 返回的记录数量
            
        Returns:
            运行记录列表
        """
        print(f"\n查找最近的运行记录...")
        print("=" * 60)
        
        try:
            runs = list(self.client.list_runs(
                project_name=project_name,
                limit=limit
            ))
            
            if not runs:
                print("未找到运行记录")
                print("\n提示：请先运行一次完整流程")
                print("  python main.py --query '你的查询'")
                return []
            
            print(f"\n找到 {len(runs)} 条运行记录:\n")
            
            for i, run in enumerate(runs, 1):
                print(f"{i}. Run ID: {run.id}")
                print(f"   名称: {run.name}")
                print(f"   时间: {run.start_time}")
                if run.inputs:
                    query = str(run.inputs.get('user_query', ''))[:50]
                    print(f"   查询: {query}...")
                print(f"   状态: {run.status}")
                print("-" * 60)
            
            return runs
            
        except Exception as e:
            print(f"[ERROR] 获取运行记录失败: {e}")
            return []
    
    def extract_llm_calls_from_run(self, run_id: str) -> Dict[str, Any]:
        """
        从一次运行中提取所有 LLM 调用及其输入
        
        Args:
            run_id: 运行 ID
            
        Returns:
            {
                'run_info': {...},
                'llm_calls': [
                    {
                        'node_name': '...',
                        'inputs': {...},
                        'outputs': {...},
                        'prompt_name': '...'
                    }
                ]
            }
        """
        print(f"\n[开始] 提取 Run {run_id[:8]}... 的 LLM 调用...")
        
        try:
            # 获取主运行
            main_run = self.client.read_run(run_id)
            
            # 获取所有子运行（包含 LLM 调用）
            child_runs = list(self.client.list_runs(
                trace_id=run_id,
                is_root=False
            ))
            
            llm_calls = []
            
            print(f"  分析 {len(child_runs)} 个子运行...")
            
            for child in child_runs:
                # 检查是否是 LLM 调用
                # LangChain 的 LLM 调用通常有 'llm' 或 'chat_model' 类型
                if child.run_type in ['llm', 'chat_model']:
                    call_info = {
                        'run_id': str(child.id),
                        'node_name': child.name,
                        'run_type': child.run_type,
                        'inputs': child.inputs,
                        'outputs': child.outputs,
                        'prompt_name': self._extract_prompt_name(child),
                        'start_time': child.start_time,
                    }
                    llm_calls.append(call_info)
                    
                    print(f"  [OK] 找到 LLM 调用: {child.name}")
            
            result = {
                'run_id': str(run_id),
                'run_info': {
                    'name': main_run.name,
                    'start_time': str(main_run.start_time),
                    'inputs': main_run.inputs,
                    'outputs': main_run.outputs,
                },
                'llm_calls': llm_calls,
                'total_llm_calls': len(llm_calls)
            }
            
            print(f"\n[完成] 共提取 {len(llm_calls)} 个 LLM 调用")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 提取失败: {e}")
            raise
    
    def _extract_prompt_name(self, run) -> Optional[str]:
        """从 run 中提取提示词名称"""
        # 尝试从 metadata 或 extra 中获取
        if hasattr(run, 'extra') and run.extra:
            metadata = run.extra.get('metadata', {})
            if 'prompt_name' in metadata:
                return metadata['prompt_name']
        
        # 从 name 推断
        if 'parameter_parser' in run.name.lower():
            return 'parameter_parser'
        elif 'report_generator' in run.name.lower():
            return 'report_generator'
        
        return None
    
    def save_llm_inputs(
        self,
        run_id: str,
        scenario_name: str = None
    ) -> Dict[str, Any]:
        """
        保存某次运行的所有 LLM 输入
        
        Args:
            run_id: 运行 ID
            scenario_name: 场景名称（默认使用 run_id 前8位）
            
        Returns:
            保存的数据
        """
        # 提取 LLM 调用
        data = self.extract_llm_calls_from_run(run_id)
        
        if not data['llm_calls']:
            print("\n[警告] 未找到任何 LLM 调用")
            return data
        
        # 生成场景名称
        if not scenario_name:
            # 尝试从输入中提取主题
            inputs = data['run_info'].get('inputs', {})
            query = inputs.get('user_query', inputs.get('query', ''))
            if query:
                scenario_name = query[:20].replace(' ', '_').replace('/', '_')
            else:
                scenario_name = run_id[:8]
        
        # 保存完整数据
        filepath = self.cache_dir / f"{scenario_name}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] 数据已保存: {filepath}")
        
        # 按节点分别保存输入（便于单独使用）
        for i, call in enumerate(data['llm_calls'], 1):
            node_name = call['node_name'].replace(' ', '_')
            node_file = self.cache_dir / f"{scenario_name}_node{i}_{node_name}.json"
            
            # 保存该节点的输入
            with open(node_file, 'w', encoding='utf-8') as f:
                json.dump(call['inputs'], f, ensure_ascii=False, indent=2)
            
            print(f"  [OK] 节点 {i} ({node_name}) 输入已保存: {node_file.name}")
        
        return data
    
    def create_dataset_from_runs(
        self,
        run_ids: List[str],
        dataset_name: str = "auto_extracted_llm_inputs",
        llm_node_filter: str = None
    ):
        """
        从多个运行中创建 LangSmith Dataset
        
        Args:
            run_ids: 运行 ID 列表
            dataset_name: 数据集名称
            llm_node_filter: 只提取特定节点的输入（如 "report_generator"）
        """
        print(f"\n[开始] 创建 Dataset: {dataset_name}")
        print(f"{'='*60}")
        
        try:
            # 检查数据集是否已存在
            existing = list(self.client.list_datasets(dataset_name=dataset_name))
            if existing:
                print(f"[警告] 数据集 '{dataset_name}' 已存在")
                dataset_id = str(existing[0].id)
                print(f"  使用现有数据集 ID: {dataset_id}")
            else:
                dataset = self.client.create_dataset(
                    dataset_name=dataset_name,
                    description=f"自动从 Trace 提取的 LLM 输入数据"
                )
                dataset_id = str(dataset.id)
                print(f"[OK] 创建数据集: {dataset_name}")
            
            # 处理每个 run
            total_examples = 0
            for run_id in run_ids:
                print(f"\n处理 Run: {run_id}")
                
                # 提取 LLM 调用
                data = self.extract_llm_calls_from_run(run_id)
                
                # 添加到数据集
                for call in data['llm_calls']:
                    # 如果指定了过滤，只添加匹配的节点
                    if llm_node_filter and llm_node_filter not in call['node_name']:
                        continue
                    
                    # 创建 example
                    self.client.create_example(
                        dataset_id=dataset_id,
                        inputs=call['inputs'],
                        outputs=call['outputs'] or {},
                        metadata={
                            'run_id': run_id,
                            'node_name': call['node_name'],
                            'prompt_name': call['prompt_name'],
                            'start_time': str(call['start_time'])
                        }
                    )
                    
                    total_examples += 1
                    print(f"  [OK] 添加示例: {call['node_name']}")
            
            print(f"\n{'='*60}")
            print(f"[完成] Dataset 创建完成!")
            print(f"  - 数据集名称: {dataset_name}")
            print(f"  - 总示例数: {total_examples}")
            print(f"  - 查看: https://smith.langchain.com/datasets")
            print(f"\n使用方法:")
            print(f"  1. 访问 LangSmith Playground")
            print(f"  2. 选择你的提示词")
            print(f"  3. 点击 'Select Dataset' → '{dataset_name}'")
            print(f"  4. 切换提示词，输入会自动填充 ✅")
            
            return dataset_id
            
        except Exception as e:
            print(f"[ERROR] 创建 Dataset 失败: {e}")
            raise
    
    def interactive_mode(self):
        """交互式模式"""
        print("\n" + "=" * 60)
        print("自动化中间结果提取工具 - 交互模式")
        print("=" * 60)
        
        # 列出最近的运行
        runs = self.list_recent_runs(limit=10)
        
        if not runs:
            return
        
        print("\n请选择操作:")
        print("1. 保存某次运行的 LLM 输入")
        print("2. 从多次运行创建 LangSmith Dataset")
        print("3. 退出")
        
        choice = input("\n选择 (1/2/3): ").strip()
        
        if choice == '1':
            run_num = input("\n选择运行编号 (1-10): ").strip()
            try:
                run_idx = int(run_num) - 1
                run_id = str(runs[run_idx].id)
                
                scenario_name = input("场景名称（留空使用自动生成）: ").strip() or None
                
                self.save_llm_inputs(run_id, scenario_name)
                
            except (ValueError, IndexError):
                print("[ERROR] 无效的选择")
        
        elif choice == '2':
            run_nums = input("\n选择运行编号（多个用逗号分隔，如 1,2,3）: ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in run_nums.split(',')]
                run_ids = [str(runs[i].id) for i in indices]
                
                dataset_name = input("Dataset 名称（留空使用默认）: ").strip() or "auto_extracted_llm_inputs"
                
                llm_filter = input("只提取特定节点？（留空=全部，如 'report_generator'）: ").strip() or None
                
                self.create_dataset_from_runs(run_ids, dataset_name, llm_filter)
                
            except (ValueError, IndexError):
                print("[ERROR] 无效的选择")
        
        elif choice == '3':
            print("\n再见！")
        
        else:
            print("[ERROR] 无效的选择")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("通用的自动化中间结果提取工具")
    print("=" * 60)
    print("\n核心功能:")
    print("  • 从 LangSmith Trace 自动提取所有 LLM 调用的输入")
    print("  • 无需手动构建，无需修改代码")
    print("  • 通用化，适用于任何 LangGraph 项目")
    print("\n使用方法:")
    print("  1. 运行你的 Graph（会自动记录到 LangSmith）")
    print("  2. 运行此工具提取中间结果")
    print("  3. 创建 Dataset，在 Playground 中使用")
    
    extractor = TraceExtractor()
    extractor.interactive_mode()


if __name__ == "__main__":
    main()

