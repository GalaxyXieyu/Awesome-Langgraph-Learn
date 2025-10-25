"""
中间结果数据集管理工具
用于保存和管理多 LLM 流程中的中间结果，方便调试下游节点
"""
import json
from typing import List, Dict, Any
from pathlib import Path
from langsmith import Client


class MiddleResultDataset:
    """中间结果数据集管理器"""
    
    def __init__(self):
        self.client = Client()
        self.cache_dir = Path(".middle_results_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def save_middle_result_from_trace(
        self,
        run_id: str,
        scenario_name: str = "default"
    ):
        """
        从 LangSmith Trace 中提取中间结果并保存
        
        Args:
            run_id: LangSmith 运行的 ID
            scenario_name: 场景名称（用于标识不同的测试场景）
        """
        try:
            # 获取 run 信息
            run = self.client.read_run(run_id)
            
            # 从 run 的 outputs 中提取中间结果
            # 假设是从 parse_parameters_node 和 web_search_node 的输出
            middle_result = {
                "topic": run.outputs.get("topic", ""),
                "year_range": run.outputs.get("year_range", ""),
                "style": run.outputs.get("style", ""),
                "depth": run.outputs.get("depth", ""),
                "focus_areas": run.outputs.get("focus_areas", ""),
                "search_results": run.outputs.get("search_results_formatted", "")
            }
            
            # 保存到本地
            filepath = self.cache_dir / f"{scenario_name}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(middle_result, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] 中间结果已保存: {filepath}")
            return middle_result
            
        except Exception as e:
            print(f"[ERROR] 保存失败: {e}")
            raise
    
    def save_middle_result_manually(
        self,
        topic: str,
        year_range: str,
        style: str,
        depth: str,
        focus_areas: str,
        search_results: str,
        scenario_name: str = "default"
    ):
        """
        手动保存中间结果
        
        适用场景：从一次完整运行中，复制粘贴中间结果
        """
        middle_result = {
            "topic": topic,
            "year_range": year_range,
            "style": style,
            "depth": depth,
            "focus_areas": focus_areas,
            "search_results": search_results
        }
        
        # 保存到本地
        filepath = self.cache_dir / f"{scenario_name}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(middle_result, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 中间结果已保存: {filepath}")
        return filepath
    
    def load_middle_result(self, scenario_name: str = "default") -> Dict[str, Any]:
        """
        加载保存的中间结果
        
        Args:
            scenario_name: 场景名称
            
        Returns:
            中间结果字典
        """
        filepath = self.cache_dir / f"{scenario_name}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(
                f"未找到场景 '{scenario_name}' 的中间结果。\n"
                f"请先运行一次完整流程并保存中间结果。"
            )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_scenarios(self):
        """列出所有已保存的场景"""
        files = list(self.cache_dir.glob("*.json"))
        
        if not files:
            print("暂无保存的场景")
            return []
        
        print(f"\n已保存的场景 ({len(files)} 个):")
        print("-" * 60)
        
        scenarios = []
        for f in files:
            scenario_name = f.stem
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"场景名称: {scenario_name}")
            print(f"  主题: {data.get('topic', 'N/A')}")
            print(f"  风格: {data.get('style', 'N/A')}")
            print(f"  深度: {data.get('depth', 'N/A')}")
            print("-" * 60)
            
            scenarios.append(scenario_name)
        
        return scenarios
    
    def create_langsmith_dataset(
        self,
        dataset_name: str = "report_generator_middle_results",
        scenarios: List[str] = None
    ):
        """
        将保存的中间结果创建为 LangSmith Dataset
        
        Args:
            dataset_name: 数据集名称
            scenarios: 要包含的场景列表（None 表示全部）
        """
        try:
            # 检查数据集是否已存在
            existing = list(self.client.list_datasets(dataset_name=dataset_name))
            if existing:
                print(f"⚠️ 数据集 '{dataset_name}' 已存在")
                dataset_id = str(existing[0].id)
                print(f"  使用现有数据集 ID: {dataset_id}")
            else:
                # 创建数据集
                dataset = self.client.create_dataset(
                    dataset_name=dataset_name,
                    description="报告生成节点的中间结果测试数据集"
                )
                dataset_id = str(dataset.id)
                print(f"[OK] 创建数据集: {dataset_name}")
            
            # 加载场景
            if scenarios is None:
                scenarios = [f.stem for f in self.cache_dir.glob("*.json")]
            
            # 添加示例
            for scenario in scenarios:
                try:
                    middle_result = self.load_middle_result(scenario)
                    
                    # 创建 example
                    self.client.create_example(
                        dataset_id=dataset_id,
                        inputs=middle_result,
                        outputs={},  # 输出可以为空，主要用于存储输入
                        metadata={"scenario": scenario}
                    )
                    
                    print(f"  [OK] 添加场景: {scenario}")
                    
                except Exception as e:
                    print(f"  [ERROR] 添加场景 {scenario} 失败: {e}")
            
            print(f"\n[OK] Dataset 创建完成!")
            print(f"  查看: https://smith.langchain.com/datasets")
            print(f"  使用: 在 Playground 中选择此 Dataset，即可快速切换提示词测试")
            
            return dataset_id
            
        except Exception as e:
            print(f"[ERROR] 创建 Dataset 失败: {e}")
            raise


if __name__ == "__main__":
    # 使用示例
    print("=== 中间结果数据集管理工具 ===\n")
    
    manager = MiddleResultDataset()
    
    # 示例1：手动保存几个典型场景
    print("1. 保存典型场景的中间结果...\n")
    
    # 场景1：正式风格的 AI 行业报告
    manager.save_middle_result_manually(
        topic="人工智能",
        year_range="2023-2024",
        style="formal",
        depth="deep",
        focus_areas="技术创新,市场规模,竞争格局",
        search_results="""
[搜索结果摘要]
1. 2024年全球人工智能市场规模预计达到约1840亿美元，相比2023年增长约28.46%
2. GPT-4、Claude 3、Gemini等大语言模型引领技术创新，多模态能力显著提升
3. 中国AI市场保持高速增长，百度、阿里、腾讯等企业在应用层面取得突破
4. AI安全和监管政策逐步完善，欧盟AI法案、中国生成式AI管理办法相继出台
5. 企业级AI应用加速落地，在客服、营销、研发等领域实现规模化商用
        """.strip(),
        scenario_name="ai_formal_deep"
    )
    
    # 场景2：简洁风格的金融科技概览
    manager.save_middle_result_manually(
        topic="金融科技",
        year_range="2024",
        style="concise",
        depth="shallow",
        focus_areas="数字支付,区块链",
        search_results="""
[搜索结果摘要]
1. 数字支付交易规模持续扩大，移动支付渗透率超过85%
2. 区块链技术在跨境支付、供应链金融等领域应用深化
3. 央行数字货币(CBDC)试点范围扩大，数字人民币场景不断丰富
        """.strip(),
        scenario_name="fintech_concise_shallow"
    )
    
    # 场景3：详细风格的新能源汽车报告
    manager.save_middle_result_manually(
        topic="新能源汽车",
        year_range="2023-2024",
        style="detailed",
        depth="medium",
        focus_areas="市场销量,技术突破,政策支持",
        search_results="""
[搜索结果摘要]
1. 2024年1-9月中国新能源汽车销量达到728.5万辆，同比增长33.8%
2. 固态电池技术取得关键突破，能量密度提升至400Wh/kg以上
3. 智能驾驶L2+级别渗透率超过50%，城市NOA功能快速普及
4. 政策持续支持，购置税减免政策延续，充电设施建设加速
5. 出口市场表现亮眼，比亚迪、上汽等企业国际化步伐加快
        """.strip(),
        scenario_name="new_energy_detailed_medium"
    )
    
    # 列出所有场景
    print("\n2. 查看已保存的场景...\n")
    manager.list_scenarios()
    
    # 创建 LangSmith Dataset
    print("\n3. 创建 LangSmith Dataset...\n")
    try:
        manager.create_langsmith_dataset()
    except Exception as e:
        print(f"创建失败（可能需要配置 LANGSMITH_API_KEY）: {e}")

