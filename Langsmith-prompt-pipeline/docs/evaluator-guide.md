# LangSmith Evaluator 完整使用指南

> 📊 如何使用 LangSmith Evaluator 评估和优化提示词质量

---

## 目录

- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [内置评估器](#内置评估器)
- [使用方式](#使用方式)
- [完整工作流](#完整工作流)
- [自定义评估器](#自定义评估器)
- [最佳实践](#最佳实践)

---

## 快速开始

### 5 分钟上手

```bash
# 1. 确保已配置 LangSmith
export LANGSMITH_API_KEY="your-key"

# 2. 运行简单评估
cd Langsmith-prompt-pipeline
python examples/run_evaluation_example.py

# 3. 查看 LangSmith 控制台
# 访问 https://smith.langchain.com/
```

### 最简示例

```python
from evaluation.run_evaluation import EvaluationRunner

# 创建评估运行器
runner = EvaluationRunner()

# 评估提示词
results = runner.evaluate_prompt(
    dataset_name="test_cases",
    test_cases_file="examples/test_cases.json"
)

# 查看结果
print(f"总分: {results['overall_score']:.2%}")
```

---

## 核心概念

### 什么是 Evaluator？

**Evaluator（评估器）** 是 LangSmith 提供的自动化测试工具，用于：
- 评估 LLM 输出质量
- 对比不同版本的提示词
- 自动化质量把关

### Evaluator vs 人工测试

| 维度 | 人工测试 | Evaluator（自动化） |
|-----|---------|------------------|
| **速度** | 慢（1个测试 ≈ 5分钟） | 快（100个测试 ≈ 2分钟） |
| **一致性** | 主观，不同人评分不同 | 客观，标准统一 |
| **覆盖率** | 低（通常 3-5 个用例） | 高（可测试 100+ 用例） |
| **成本** | 高（需要人力） | 低（全自动） |
| **适用场景** | 细微质量判断 | 批量质量检测、版本对比 |

**最佳实践**：结合使用
- Evaluator：快速筛选、批量测试、持续集成
- 人工测试：最终验收、边界情况、创意评估

---

## 内置评估器

本项目提供 4 个专业评估器（`evaluation/evaluators.py`）：

### 1. structure_evaluator（结构评估器）

**作用**：检查报告的基本结构

**评估项**：
- ✅ 标题层级（至少 3 个 `#` 标题）
- ✅ 段落数量（至少 5 个段落）
- ✅ 最小长度（≥ 800 字符）
- ✅ 最大长度（≤ 20000 字符）

**评分逻辑**：
```python
score = 通过检查项数 / 总检查项数
```

**示例输出**：
```
structure_valid: 0.75
comment: 通过 3/4 项检查。未通过: min_length
```

### 2. content_completeness_evaluator（内容完整性评估器）

**作用**：检查报告是否包含必要章节

**必要章节**：
- 摘要/概述（Executive Summary）
- 背景（Background）
- 发现/分析（Findings/Analysis）
- 结论/建议（Conclusion/Recommendation）

**评分逻辑**：
```python
score = 包含章节数 / 必要章节数
```

**示例输出**：
```
content_complete: 1.0
comment: 包含 4/4 个必要章节
```

### 3. relevance_evaluator（相关性评估器）⭐

**作用**：使用 LLM 评估内容质量

**评估维度**：
1. 主题相关性（内容是否紧扣主题）
2. 信息丰富度（是否提供有价值的信息）
3. 逻辑连贯性（内容是否有逻辑性）
4. 专业性（语言和分析是否专业）

**评分逻辑**：
```python
# 使用 GPT-4 进行评分
overall_score = (relevance + information + coherence + professionalism) / 4
```

**示例输出**：
```
relevance: 0.88
comment: 主题相关，内容丰富，逻辑清晰，专业性强
```

### 4. parameter_usage_evaluator（参数使用评估器）

**作用**：检查多参数提示词是否正确使用参数

**检查项**：
- 年份范围是否在报告中提及
- 关注领域是否被覆盖
- 风格是否符合要求（formal/casual/concise/detailed）

**评分逻辑**：
```python
score = 正确使用参数数 / 总参数数
```

**示例输出**：
```
parameter_usage: 1.0
comment: 参数使用检查: 3/3 通过
```

---

## 使用方式

### 方式 1：命令行运行（推荐）

```bash
# 基础评估
python evaluation/run_evaluation.py \
  --dataset test_cases \
  --test-file examples/test_cases.json

# 版本对比
python evaluation/run_evaluation.py \
  --dataset test_cases \
  --compare v1.0 v1.1 v1.2

# 保存报告
python evaluation/run_evaluation.py \
  --dataset test_cases \
  --output evaluation_reports/latest.json
```

### 方式 2：与 PromptManager 集成

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 简单测试（只测试格式）
result = manager.evaluate_prompt(
    'report_generator',
    use_full_pipeline=False
)

# 完整测试（使用所有专业评估器）
result = manager.evaluate_prompt(
    'report_generator',
    use_full_pipeline=True  # ⭐ 推荐
)

print(f"质量分数: {result['quality_score']:.2%}")
for key, score in result['scores'].items():
    print(f"  {key}: {score:.2%}")
```

### 方式 3：在推送前自动评估

```python
manager = PromptManager()

# 推送时自动运行评估
manager.push(
    'report_generator',
    with_test=True,  # 自动评估
    create_backup=True
)

# 输出示例：
# [2/4] 步骤 2/4: 运行 LangSmith 测试...
# [TEST] LangSmith 自动测试: report_generator
#   质量分数: 92%
# [OK] 测试通过
```

### 方式 4：Python 代码调用

```python
from evaluation.run_evaluation import EvaluationRunner
from evaluation.evaluators import ReportEvaluators

runner = EvaluationRunner()

# 自定义评估器
results = runner.evaluate_prompt(
    dataset_name="test_cases",
    experiment_name="my_experiment",
    evaluators=[
        ReportEvaluators.structure_evaluator,
        ReportEvaluators.relevance_evaluator,
    ]
)
```

---

## 完整工作流

### 场景：优化提示词质量

#### 第 1 步：创建测试数据集

**选项 A：从文件创建**

```json
// examples/test_cases.json
[
  {
    "id": "test_001",
    "name": "AI行业正式报告",
    "input": {
      "user_query": "写一份人工智能行业2023-2024年的分析报告"
    },
    "quality_criteria": {
      "min_length": 2000,
      "must_include": ["技术创新", "市场规模"]
    }
  }
]
```

**选项 B：自动捕获（推荐）**

```bash
# 运行程序自动捕获真实测试数据
python main.py --query "人工智能行业分析" --style formal
python main.py --query "金融科技报告" --depth deep

# 自动推送到 LangSmith Dataset ✅
```

#### 第 2 步：运行基准评估

```python
from evaluation.run_evaluation import EvaluationRunner

runner = EvaluationRunner()

# 评估当前版本（v1.0）
baseline = runner.evaluate_prompt(
    dataset_name="report_generator",
    experiment_name="baseline_v1.0"
)

print(f"基准分数: {baseline['overall_score']:.2%}")
```

输出示例：
```
评估结果汇总:
------------------------------------------------------------
  structure_valid: 85%
  content_complete: 90%
  relevance: 78%
  parameter_usage: 92%
------------------------------------------------------------
  总分: 86%
  测试数: 5
```

#### 第 3 步：优化提示词

在 LangSmith Playground 或本地修改提示词：

```yaml
# prompts/report_generator.yaml

messages:
  - role: system
    content: |
      你是一位资深的行业分析专家。
      
      # 优化点 1：更明确的角色定义
      你拥有 10 年以上的行业研究经验，擅长：
      - 数据驱动的深度分析
      - 清晰的逻辑框架
      - 专业的商业洞察
      
      # 优化点 2：更详细的输出要求
      报告结构必须包含：
      1. 执行摘要（200字）
      2. 行业背景（500字）
      3. 核心发现（1000字）
      4. 趋势预测（500字）
      5. 战略建议（300字）
```

#### 第 4 步：评估优化效果

```python
# 评估新版本（v1.1）
improved = runner.evaluate_prompt(
    dataset_name="report_generator",
    experiment_name="improved_v1.1"
)

print(f"优化后分数: {improved['overall_score']:.2%}")
print(f"提升: {(improved['overall_score'] - baseline['overall_score']):.2%}")
```

输出示例：
```
评估结果汇总:
------------------------------------------------------------
  structure_valid: 95%  (+10%)
  content_complete: 100% (+10%)
  relevance: 92%  (+14%)
  parameter_usage: 95%  (+3%)
------------------------------------------------------------
  总分: 95%
  提升: +9%
```

#### 第 5 步：版本对比（可选）

```python
# 对比多个版本
comparison = runner.compare_prompts(
    dataset_name="report_generator",
    prompt_versions=["v1.0", "v1.1", "v1.2"]
)

print(f"推荐版本: {comparison['recommended_version']}")
```

输出示例：
```
版本对比报告
============================================================

各维度对比:
------------------------------------------------------------
维度                       v1.0        v1.1        v1.2
------------------------------------------------------------
content_complete          90.00%      100.00%     100.00%
parameter_usage           92.00%      95.00%      97.00%
relevance                 78.00%      92.00%      88.00%
structure_valid           85.00%      95.00%      98.00%
------------------------------------------------------------

总分对比                  86.25%      95.50%      95.75%

✓ 推荐版本: v1.2
```

#### 第 6 步：推送最优版本

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 推送最优版本
manager.push(
    'report_generator',
    with_test=True,      # 再次验证
    create_backup=True   # 备份旧版本
)
```

---

## 自定义评估器

### 为什么需要自定义评估器？

内置评估器覆盖通用场景，但你可能需要：
- 评估业务特定指标（如专业术语使用率）
- 检查合规性要求（如禁用词汇）
- 评估格式要求（如特定章节）

### 示例：创建自定义评估器

```python
from langsmith.evaluation import run_evaluator, EvaluationResult

@run_evaluator
def terminology_evaluator(run, example) -> EvaluationResult:
    """
    检查专业术语使用情况
    """
    output = run.outputs.get("report", "") if run.outputs else ""
    
    # 定义必需的专业术语
    required_terms = [
        "CAGR",           # 复合年增长率
        "市场份额",
        "竞争格局",
        "SWOT分析"
    ]
    
    # 检查每个术语是否出现
    found_terms = [term for term in required_terms if term in output]
    score = len(found_terms) / len(required_terms)
    
    return EvaluationResult(
        key="terminology_usage",
        score=score,
        comment=f"使用了 {len(found_terms)}/{len(required_terms)} 个专业术语"
    )
```

### 使用自定义评估器

```python
from evaluation.run_evaluation import EvaluationRunner
from evaluation.evaluators import ReportEvaluators

runner = EvaluationRunner()

results = runner.evaluate_prompt(
    dataset_name="test_cases",
    evaluators=[
        ReportEvaluators.structure_evaluator,
        ReportEvaluators.relevance_evaluator,
        terminology_evaluator,  # 自定义评估器
    ]
)
```

### 更多自定义示例

#### 1. 禁用词检查

```python
@run_evaluator
def forbidden_words_evaluator(run, example) -> EvaluationResult:
    """检查是否包含禁用词"""
    output = run.outputs.get("report", "")
    
    forbidden = ["可能", "或许", "大概", "也许"]  # 避免不确定性词汇
    found_forbidden = [word for word in forbidden if word in output]
    
    score = 1.0 if not found_forbidden else 0.5
    
    return EvaluationResult(
        key="no_forbidden_words",
        score=score,
        comment=f"发现 {len(found_forbidden)} 个禁用词" if found_forbidden else "未发现禁用词"
    )
```

#### 2. 数据引用检查

```python
@run_evaluator
def data_citation_evaluator(run, example) -> EvaluationResult:
    """检查是否引用具体数据"""
    output = run.outputs.get("report", "")
    
    # 检查是否包含数字和百分比
    import re
    has_numbers = bool(re.search(r'\d+', output))
    has_percentage = bool(re.search(r'\d+%', output))
    has_year = bool(re.search(r'20\d{2}', output))
    
    checks = [has_numbers, has_percentage, has_year]
    score = sum(checks) / len(checks)
    
    return EvaluationResult(
        key="data_citation",
        score=score,
        comment=f"包含数据引用: {sum(checks)}/3"
    )
```

---

## 最佳实践

### 1. 评估器选择

**场景 A：快速验证提示词格式**
```python
# 使用简单评估器
evaluators = [
    ReportEvaluators.structure_evaluator,
]
```

**场景 B：全面质量评估（推荐）**
```python
# 使用所有评估器
evaluators = [
    ReportEvaluators.structure_evaluator,
    ReportEvaluators.content_completeness_evaluator,
    ReportEvaluators.relevance_evaluator,
    ReportEvaluators.parameter_usage_evaluator,
]
```

**场景 C：生产环境把关**
```python
# 使用所有评估器 + 自定义评估器
evaluators = [
    *ReportEvaluators.__dict__.values(),  # 所有内置
    terminology_evaluator,                 # 自定义
    forbidden_words_evaluator,
]
```

### 2. Dataset 管理

**规则**：
- 1 个提示词 = 1 个独立 Dataset
- Dataset 名称 = 提示词名称（如 `report_generator`）
- 至少 5 个测试用例
- 覆盖不同场景（formal/casual, shallow/deep）

**示例**：
```
Datasets:
  - parameter_parser (参数解析提示词专用)
  - report_generator (报告生成提示词专用)
  - summary_generator (摘要生成提示词专用)
```

### 3. 评估频率

| 阶段 | 频率 | 目的 |
|-----|------|------|
| **开发阶段** | 每次修改后 | 及时发现问题 |
| **优化阶段** | 每个版本 | 对比效果 |
| **推送前** | 必须 | 质量把关 |
| **生产环境** | 每周 | 监控质量下降 |

### 4. 分数阈值设置

```python
# prompts/prompts_config.yaml

prompts:
  report_generator:
    min_quality_score: 0.85  # 最低质量分数
    
    # 各维度最低分数（可选）
    min_scores:
      structure_valid: 0.80
      content_complete: 0.90
      relevance: 0.85
      parameter_usage: 0.80
```

### 5. 错误处理

```python
try:
    result = runner.evaluate_prompt(dataset_name="test_cases")
except Exception as e:
    print(f"评估失败: {e}")
    
    # 降级方案：使用简单评估器
    result = manager.evaluate_prompt(
        'report_generator',
        use_full_pipeline=False
    )
```

---

## 常见问题

### Q1: 评估很慢怎么办？

**原因**：
- LLM 评估器（relevance_evaluator）需要调用 GPT-4
- 测试用例太多

**解决方案**：
```python
# 方案 1：减少测试用例
# 从 100 个减少到 20 个代表性用例

# 方案 2：只用规则评估器（不用 LLM）
evaluators = [
    ReportEvaluators.structure_evaluator,
    ReportEvaluators.content_completeness_evaluator,
    # ReportEvaluators.relevance_evaluator,  # 注释掉
    ReportEvaluators.parameter_usage_evaluator,
]

# 方案 3：提高并发数
runner.evaluate_prompt(
    dataset_name="test_cases",
    max_concurrency=5  # 默认 2
)
```

### Q2: 如何查看详细的评估结果？

访问 LangSmith 控制台：
1. https://smith.langchain.com/
2. 点击 `Projects` → 选择你的项目
3. 找到对应的 experiment
4. 查看每个测试用例的详细分数

### Q3: Dataset 如何更新？

```python
from evaluation.datasets import DatasetManager

dm = DatasetManager()

# 删除旧数据集
dm.delete_dataset("report_generator")

# 重新创建
dm.create_dataset_from_file(
    dataset_name="report_generator",
    filepath="examples/test_cases_updated.json"
)
```

或者使用自动捕获（推荐）：
```bash
# 运行程序，自动捕获新数据
python main.py --query "新的测试场景"

# 自动推送到 Dataset ✅
```

### Q4: 如何对比历史版本？

```python
# 在 LangSmith 控制台
# Projects → Experiments → 选择两个实验 → Compare
```

或使用代码：
```python
runner.compare_prompts(
    dataset_name="test_cases",
    prompt_versions=["v1.0", "v1.1"]  # 指定版本
)
```

---

## 总结

### 核心价值

| 功能 | 价值 |
|-----|------|
| **自动化评估** | 节省 90% 测试时间 |
| **版本对比** | 客观选择最优版本 |
| **质量把关** | 避免低质量提示词上线 |
| **持续监控** | 及时发现质量下降 |

### 快速参考

```bash
# 运行评估
python evaluation/run_evaluation.py --dataset test_cases

# 版本对比
python evaluation/run_evaluation.py --dataset test_cases --compare v1.0 v1.1

# 集成到 PromptManager
python -c "
from prompts.prompt_manager import PromptManager
manager = PromptManager()
result = manager.evaluate_prompt('report_generator', use_full_pipeline=True)
print(f'质量分数: {result[\"quality_score\"]:.2%}')
"

# 运行示例
python examples/run_evaluation_example.py
```

### 推荐工作流

```
1. 开发提示词
   ↓
2. 运行程序 → 自动捕获测试数据
   ↓
3. 运行评估 → 获取基准分数
   ↓
4. 优化提示词
   ↓
5. 重新评估 → 对比效果
   ↓
6. 推送最优版本（自动评估）
```

---

## 相关链接

- [LangSmith 官方文档](https://docs.langchain.com/langsmith/)
- [Evaluator API 文档](https://docs.langchain.com/langsmith/evaluation)
- [项目 README](../README.md)
- [Dataset 捕获指南](capture-decorator-guide.md)

