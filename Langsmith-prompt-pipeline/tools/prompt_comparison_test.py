"""
提示词对比测试工具
用相同的中间结果测试多个提示词版本，快速对比效果
"""
import os
from typing import List, Dict, Any
from pathlib import Path
from langchain_core.output_parsers import StrOutputParser

from tools.middle_result_dataset import MiddleResultDataset
from prompts.prompt_manager import PromptManager
from config.azure_config import AzureConfig


class PromptComparisonTest:
    """提示词对比测试器"""
    
    def __init__(self):
        self.dataset_manager = MiddleResultDataset()
        self.prompt_manager = PromptManager(auto_pull=False)  # 不自动拉取，使用本地版本
        self.llm = AzureConfig.get_llm(temperature=0.7)
        self.results_dir = Path("comparison_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def test_single_prompt_version(
        self,
        prompt_file: str,
        middle_result: Dict[str, Any],
        scenario_name: str = "test"
    ) -> Dict[str, Any]:
        """
        测试单个提示词版本
        
        Args:
            prompt_file: 提示词文件名（如 "report_generator.yaml"）
            middle_result: 中间结果（输入参数）
            scenario_name: 场景名称
            
        Returns:
            测试结果
        """
        try:
            # 加载提示词配置
            prompt_path = Path("prompts") / prompt_file
            if not prompt_path.exists():
                raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")
            
            # 读取 YAML 配置
            import yaml
            with open(prompt_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 创建 prompt
            prompt = self.prompt_manager.create_chat_prompt(config)
            
            # 构建链
            chain = prompt | self.llm | StrOutputParser()
            
            print(f"  测试: {prompt_file} (版本: {config.get('version', 'N/A')})")
            print(f"    场景: {scenario_name}")
            print(f"    主题: {middle_result.get('topic', 'N/A')}")
            
            # 生成报告
            report = chain.invoke(middle_result)
            
            # 统计信息
            stats = {
                "length": len(report),
                "lines": len(report.split("\n")),
                "words": len(report.split()),
                "has_title": report.count("#") >= 3
            }
            
            print(f"    [OK] 生成完成: {stats['length']} 字符, {stats['lines']} 行")
            
            return {
                "prompt_file": prompt_file,
                "version": config.get('version', 'N/A'),
                "scenario": scenario_name,
                "inputs": middle_result,
                "output": report,
                "stats": stats,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            print(f"    [ERROR] 生成失败: {e}")
            return {
                "prompt_file": prompt_file,
                "scenario": scenario_name,
                "inputs": middle_result,
                "output": None,
                "stats": {},
                "success": False,
                "error": str(e)
            }
    
    def compare_prompts(
        self,
        prompt_files: List[str],
        scenario_name: str = "default",
        save_results: bool = True
    ) -> List[Dict[str, Any]]:
        """
        对比多个提示词版本
        
        Args:
            prompt_files: 提示词文件列表
            scenario_name: 测试场景名称
            save_results: 是否保存结果到文件
            
        Returns:
            对比结果列表
        """
        print(f"\n{'='*60}")
        print(f"开始提示词对比测试")
        print(f"{'='*60}")
        
        # 加载中间结果
        try:
            middle_result = self.dataset_manager.load_middle_result(scenario_name)
        except FileNotFoundError as e:
            print(f"\n[ERROR] {e}")
            print(f"\n提示：请先运行以下命令保存中间结果:")
            print(f"  python tools/middle_result_dataset.py")
            return []
        
        print(f"\n场景: {scenario_name}")
        print(f"输入参数:")
        print(f"  - 主题: {middle_result.get('topic')}")
        print(f"  - 风格: {middle_result.get('style')}")
        print(f"  - 深度: {middle_result.get('depth')}")
        
        # 测试每个提示词版本
        results = []
        for prompt_file in prompt_files:
            print(f"\n{'-'*60}")
            result = self.test_single_prompt_version(
                prompt_file=prompt_file,
                middle_result=middle_result,
                scenario_name=scenario_name
            )
            results.append(result)
        
        # 保存结果
        if save_results:
            self._save_comparison_results(results, scenario_name)
        
        # 打印对比摘要
        self._print_comparison_summary(results)
        
        return results
    
    def _save_comparison_results(
        self,
        results: List[Dict[str, Any]],
        scenario_name: str
    ):
        """保存对比结果到文件"""
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存详细结果
        result_file = self.results_dir / f"comparison_{scenario_name}_{timestamp}.json"
        
        # 准备保存的数据（移除输出内容以减小文件大小）
        save_data = []
        for r in results:
            save_data.append({
                "prompt_file": r["prompt_file"],
                "version": r.get("version"),
                "scenario": r["scenario"],
                "stats": r["stats"],
                "success": r["success"],
                "error": r["error"]
            })
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] 对比结果已保存: {result_file}")
        
        # 保存每个版本的完整输出
        for r in results:
            if r["success"]:
                output_file = self.results_dir / f"{scenario_name}_{r['prompt_file'].replace('.yaml', '')}_{timestamp}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(r["output"])
                print(f"  [OK] 输出已保存: {output_file.name}")
    
    def _print_comparison_summary(self, results: List[Dict[str, Any]]):
        """打印对比摘要"""
        print(f"\n{'='*60}")
        print(f"对比摘要")
        print(f"{'='*60}\n")
        
        # 表格标题
        print(f"{'提示词文件':<30} {'版本':<10} {'字符数':<10} {'行数':<10} {'状态':<10}")
        print(f"{'-'*60}")
        
        # 表格内容
        for r in results:
            status = "[OK]" if r["success"] else "[FAIL]"
            print(
                f"{r['prompt_file']:<30} "
                f"{r.get('version', 'N/A'):<10} "
                f"{r['stats'].get('length', 0):<10} "
                f"{r['stats'].get('lines', 0):<10} "
                f"{status:<10}"
            )
        
        print(f"\n提示：")
        print(f"  - 查看详细输出: ls {self.results_dir}/")
        print(f"  - 对比文件差异: diff {self.results_dir}/*.md")


def main():
    """主函数 - 使用示例"""
    print("=== 提示词对比测试工具 ===\n")
    
    tester = PromptComparisonTest()
    
    # 示例1：对比原始版本和修改版本
    # 假设你有两个版本：report_generator.yaml 和 report_generator_v2.yaml
    
    print("使用说明:")
    print("1. 确保已保存中间结果场景（运行 tools/middle_result_dataset.py）")
    print("2. 准备多个提示词版本文件（如 report_generator.yaml, report_generator_v2.yaml）")
    print("3. 运行此脚本进行对比测试\n")
    
    # 示例：对比测试
    # 你可以取消注释下面的代码来运行
    
    """
    # 对比两个版本
    results = tester.compare_prompts(
        prompt_files=[
            "report_generator.yaml",           # 原始版本
            "report_generator_v2.yaml"         # 修改后的版本
        ],
        scenario_name="ai_formal_deep",        # 使用保存的场景
        save_results=True
    )
    
    # 也可以测试多个场景
    for scenario in ["ai_formal_deep", "fintech_concise_shallow"]:
        results = tester.compare_prompts(
            prompt_files=[
                "report_generator.yaml",
                "report_generator_v2.yaml"
            ],
            scenario_name=scenario,
            save_results=True
        )
    """
    
    print("\n快速开始：")
    print("  1. 保存中间结果：")
    print("     python tools/middle_result_dataset.py")
    print()
    print("  2. 复制提示词文件创建新版本：")
    print("     cp prompts/report_generator.yaml prompts/report_generator_v2.yaml")
    print()
    print("  3. 修改 report_generator_v2.yaml 中的提示词")
    print()
    print("  4. 运行对比测试：")
    print("     # 在代码中取消注释示例代码，或者：")
    print("     from tools.prompt_comparison_test import PromptComparisonTest")
    print("     tester = PromptComparisonTest()")
    print("     tester.compare_prompts(['report_generator.yaml', 'report_generator_v2.yaml'], 'ai_formal_deep')")


if __name__ == "__main__":
    main()

