"""
数据集管理模块
用于创建、管理和维护 LangSmith 数据集
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from langsmith import Client


class DatasetManager:
    """数据集管理器"""
    
    def __init__(self, langsmith_client: Optional[Client] = None):
        """
        初始化数据集管理器
        
        Args:
            langsmith_client: LangSmith Client 实例
        """
        self.client = langsmith_client or Client()
    
    def load_test_cases(self, filepath: str = "examples/test_cases.json") -> List[Dict[str, Any]]:
        """
        从文件加载测试用例
        
        Args:
            filepath: 测试用例文件路径
            
        Returns:
            测试用例列表
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"测试用例文件不存在: {filepath}")
        
        with open(path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        
        print(f"✓ 加载测试用例: {len(test_cases)} 个")
        return test_cases
    
    def create_dataset(
        self, 
        dataset_name: str,
        description: str = "",
        test_cases: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        创建 LangSmith 数据集
        
        Args:
            dataset_name: 数据集名称
            description: 数据集描述
            test_cases: 测试用例列表
            
        Returns:
            数据集 ID
        """
        try:
            # 检查数据集是否已存在
            existing_datasets = list(self.client.list_datasets(dataset_name=dataset_name))
            
            if existing_datasets:
                print(f"⚠️ 数据集 '{dataset_name}' 已存在")
                dataset = existing_datasets[0]
                dataset_id = str(dataset.id)
                print(f"  使用现有数据集 ID: {dataset_id}")
                return dataset_id
            
            # 创建新数据集
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"报告生成测试数据集: {dataset_name}"
            )
            
            dataset_id = str(dataset.id)
            print(f"✓ 创建数据集: {dataset_name}")
            print(f"  数据集 ID: {dataset_id}")
            
            # 如果提供了测试用例，添加到数据集
            if test_cases:
                self.add_examples_to_dataset(dataset_id, test_cases)
            
            return dataset_id
            
        except Exception as e:
            print(f"✗ 创建数据集失败: {e}")
            raise
    
    def add_examples_to_dataset(
        self,
        dataset_id: str,
        test_cases: List[Dict[str, Any]]
    ):
        """
        向数据集添加示例
        
        Args:
            dataset_id: 数据集 ID
            test_cases: 测试用例列表
        """
        try:
            for case in test_cases:
                # 提取输入和期望输出
                inputs = case.get("input", {})
                
                # 期望输出可以是多个字段
                outputs = {
                    "expected_params": case.get("expected_params", {}),
                    "quality_criteria": case.get("quality_criteria", {})
                }
                
                # 创建示例
                self.client.create_example(
                    dataset_id=dataset_id,
                    inputs=inputs,
                    outputs=outputs,
                    metadata={
                        "test_id": case.get("id"),
                        "test_name": case.get("name")
                    }
                )
            
            print(f"✓ 添加 {len(test_cases)} 个示例到数据集")
            
        except Exception as e:
            print(f"✗ 添加示例失败: {e}")
            raise
    
    def create_dataset_from_file(
        self,
        dataset_name: str,
        filepath: str = "examples/test_cases.json",
        description: str = ""
    ) -> str:
        """
        从文件创建数据集
        
        Args:
            dataset_name: 数据集名称
            filepath: 测试用例文件路径
            description: 数据集描述
            
        Returns:
            数据集 ID
        """
        # 加载测试用例
        test_cases = self.load_test_cases(filepath)
        
        # 创建数据集
        dataset_id = self.create_dataset(
            dataset_name=dataset_name,
            description=description,
            test_cases=test_cases
        )
        
        return dataset_id
    
    def list_datasets(self):
        """列出所有数据集"""
        try:
            datasets = list(self.client.list_datasets())
            
            print(f"\n可用的数据集 ({len(datasets)} 个):")
            print("-" * 60)
            
            for ds in datasets:
                print(f"名称: {ds.name}")
                print(f"ID: {ds.id}")
                print(f"描述: {ds.description or 'N/A'}")
                print(f"创建时间: {ds.created_at}")
                print("-" * 60)
            
            return datasets
            
        except Exception as e:
            print(f"✗ 列出数据集失败: {e}")
            return []
    
    def delete_dataset(self, dataset_name: str):
        """
        删除数据集
        
        Args:
            dataset_name: 数据集名称
        """
        try:
            datasets = list(self.client.list_datasets(dataset_name=dataset_name))
            
            if not datasets:
                print(f"⚠️ 数据集 '{dataset_name}' 不存在")
                return
            
            for ds in datasets:
                self.client.delete_dataset(dataset_id=str(ds.id))
                print(f"✓ 删除数据集: {ds.name} ({ds.id})")
            
        except Exception as e:
            print(f"✗ 删除数据集失败: {e}")


if __name__ == "__main__":
    # 测试数据集管理器
    print("测试数据集管理器...\n")
    
    from config.langsmith_config import LangSmithConfig
    
    # 启用 LangSmith
    LangSmithConfig.enable_tracing()
    
    # 创建管理器
    manager = DatasetManager()
    
    # 从文件创建数据集
    try:
        dataset_id = manager.create_dataset_from_file(
            dataset_name="report_generator_test",
            description="报告生成器测试数据集"
        )
        
        print(f"\n✓ 数据集创建完成!")
        print(f"  查看数据集: https://smith.langchain.com/datasets")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")

