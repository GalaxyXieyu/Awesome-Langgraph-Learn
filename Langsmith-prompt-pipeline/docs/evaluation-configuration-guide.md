# 评估器配置指南

> 如何为每个提示词配置专属的评估器和测试数据集

---

## 📖 目录

- [核心概念](#核心概念)
- [配置文件详解](#配置文件详解)
- [方法名更新](#方法名更新)
- [use_full_pipeline 参数详解](#use_full_pipeline-参数详解)
- [Dataset 选择策略](#dataset-选择策略)
- [自动版本号](#自动版本号)
- [完整示例](#完整示例)

---

## 核心概念

### 评估器与提示词的关系

```
每个提示词 → 专属 Dataset + 专属评估器组合

parameter_parser（参数解析）
  ├─ Dataset: parameter_parser
  ├─ 评估器:
  │   ├─ structure_evaluator（通用）
  │   └─ parameter_extraction_evaluator（专属）
  └─ 权重: [0.3, 0.7]

report_generator（报告生成）
  ├─ Dataset: report_generator
  ├─ 评估器:
  │   ├─ structure_evaluator（通用）
  │   ├─ content_completeness_evaluator（通用）
  │   ├─ relevance_evaluator（通用）
  │   └─ report_quality_evaluator（专属）
  └─ 权重: [0.15, 0.20, 0.35, 0.30]
```

---

## 配置文件详解

### prompts_config.yaml 的完整配置

```yaml
# Prompts 配置文件

# 版本管理配置
versioning:
  auto_increment: true         # ⭐ 自动递增版本号
  version_format: "semantic"   # semantic: v1.2.3 | timestamp: v20241027-153000
  create_backup: true          # ⭐ 推送时自动创建备份

# Prompt 配置
prompts:
  # 示例：参数解析 Prompt
  parameter_parser:
    file: "parameter_parser.yaml"
    hub_name: "parameter_parser"
    test_dataset: "parameter_parser"  # ⭐ 独立 Dataset
    min_quality_score: 0.8
    description: "从用户输入中提取结构化参数"
    
    # ⭐ 专属评估器配置
    evaluators:
      - "structure_evaluator"              # 通用评估器
      - "parameter_extraction_evaluator"   # 专属评估器（需自定义）
    
    # ⭐ 评估器权重（可选，不设置则平均分配）
    evaluator_weights:
      structure_evaluator: 0.3
      parameter_extraction_evaluator: 0.7
    
  # 示例：报告生成 Prompt
  report_generator:
    file: "report_generator.yaml"
    hub_name: "report_generator"
    test_dataset: "report_generator"  # ⭐ 独立 Dataset
    min_quality_score: 0.85
    description: "生成结构化的分析报告"
    
    # ⭐ 专属评估器配置
    evaluators:
      - "structure_evaluator"
      - "content_completeness_evaluator"
      - "relevance_evaluator"             # LLM 评估器（最重要）
      - "parameter_usage_evaluator"
    
    # ⭐ 评估器权重
    evaluator_weights:
      structure_evaluator: 0.15
      content_completeness_evaluator: 0.20
      relevance_evaluator: 0.35          # 权重最高
      parameter_usage_evaluator: 0.30
```

### 配置项说明

| 配置项 | 说明 | 示例 | 是否必需 |
|-------|------|------|---------|
| `file` | YAML 文件名 | `report_generator.yaml` | ✅ |
| `hub_name` | Hub 上的名称 | `report_generator` | ✅ |
| `test_dataset` | 测试数据集名称 | `report_generator` | ✅ |
| `min_quality_score` | 最低质量分数 | `0.85` | ✅ |
| `evaluators` | 评估器列表 | `["structure_evaluator", ...]` | 🔶 可选 |
| `evaluator_weights` | 评估器权重 | `{structure: 0.15, ...}` | 🔶 可选 |

---

## 方法名更新

### 推荐使用 `evaluate_prompt()`

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# ✅ 推荐：使用新方法名
result = manager.evaluate_prompt('report_generator', use_full_pipeline=True)

# ⚠️ 兼容：旧方法名仍然可用
result = manager.evaluate_prompt('report_generator', use_full_pipeline=True)
```

**为什么改名？**
- `evaluate_prompt` 更直观，明确表示"评估提示词"
- ~~`test_with_langsmith` 太长且不够语义化~~ **已改为 `evaluate_prompt`**
- 保留旧方法名是为了向后兼容

---

## use_full_pipeline 参数详解

### 参数作用

```python
use_full_pipeline: bool = False
```

| 值 | 测试内容 | 速度 | 适用场景 |
|----|---------|------|---------|
| `False`（默认）| 只测试 Prompt 格式 | ⚡ 快（5-10秒） | 开发阶段，快速验证格式 |
| `True` | 完整流程 + 所有评估器 | 🐢 慢（30-60秒） | 推送前，全面质量评估 |

### 详细对比

#### use_full_pipeline=False（快速模式）

```python
result = manager.evaluate_prompt('report_generator', use_full_pipeline=False)

# 测试内容：
# ✅ Prompt 格式是否正确
# ✅ 参数是否能正确格式化
# ✅ 基本的格式检查
# ❌ 不运行完整流程
# ❌ 不调用 LLM
# ❌ 不使用专业评估器

# 适用场景：
# - 开发阶段频繁测试
# - 只修改了 Prompt 格式
# - 快速验证语法错误
```

#### use_full_pipeline=True（完整模式）

```python
result = manager.evaluate_prompt('report_generator', use_full_pipeline=True)

# 测试内容：
# ✅ 运行完整的报告生成流程
# ✅ 调用 LLM 生成真实输出
# ✅ 运行所有配置的评估器
# ✅ 使用真实 Dataset
# ✅ 计算加权平均分数

# 适用场景：
# - 推送前的最终验证
# - 优化后对比效果
# - 版本对比评估
```

### 实际运行对比

**快速模式输出**：
```
[EVAL] 评估提示词: report_generator
  [OK] 格式验证通过
     - 测试用例: 5
     - 质量分数: 90%
完成时间: 8 秒
```

**完整模式输出**：
```
[EVAL] 评估提示词: report_generator
  使用完整流程测试（包含专业评估器）

评估结果汇总:
------------------------------------------------------------
  structure_evaluator: 95%
  content_completeness_evaluator: 100%
  relevance_evaluator: 92%
  parameter_usage_evaluator: 97%
------------------------------------------------------------
  总分: 96%（加权平均）
  测试数: 5

查看详细结果: https://smith.langchain.com/

完成时间: 45 秒
```

---

## Dataset 选择策略

### 原则：一个提示词 = 一个独立 Dataset

```
❌ 错误：所有提示词共用一个 Dataset
prompts:
  parameter_parser:
    test_dataset: "test_cases"  # ❌
  report_generator:
    test_dataset: "test_cases"  # ❌
  summary_generator:
    test_dataset: "test_cases"  # ❌

问题：
- Dataset 内容混杂
- 不同提示词的输入格式不同
- 评估结果不准确

✅ 正确：每个提示词有独立 Dataset
prompts:
  parameter_parser:
    test_dataset: "parameter_parser"  # ✅
  report_generator:
    test_dataset: "report_generator"  # ✅
  summary_generator:
    test_dataset: "summary_generator"  # ✅

优点：
- 专属测试用例
- 输入格式一致
- 评估更准确
```

### Dataset 内容设计

**parameter_parser Dataset 示例**：
```json
// datasets/parameter_parser.json
[
  {
    "inputs": {
      "user_query": "写一份 AI 行业 2024 年报告"
    },
    "outputs": {
      "expected_params": {
        "topic": "AI 行业",
        "year_range": "2024"
      }
    }
  },
  {
    "inputs": {
      "user_query": "金融科技详细分析，关注支付和区块链"
    },
    "outputs": {
      "expected_params": {
        "topic": "金融科技",
        "focus_areas": "支付,区块链",
        "depth": "detailed"
      }
    }
  }
]
```

**report_generator Dataset 示例**：
```json
// datasets/report_generator.json
[
  {
    "inputs": {
      "user_query": "生成 AI 行业报告"
    },
    "quality_criteria": {
      "min_length": 2000,
      "must_include": ["摘要", "背景", "分析", "结论"],
      "style": "formal"
    }
  }
]
```

---

## 自动版本号

### 配置自动版本号

```yaml
# prompts_config.yaml

versioning:
  auto_increment: true         # ⭐ 启用自动递增
  version_format: "semantic"   # 版本号格式
  create_backup: true          # 自动创建备份
```

### 版本号格式

**1. 语义化版本（推荐）**
```yaml
version_format: "semantic"

# 生成格式：v1.2.3
# - major.minor.patch
# - 1.0.0 → 1.0.1 → 1.0.2 → 1.1.0 → 2.0.0
```

**2. 时间戳版本**
```yaml
version_format: "timestamp"

# 生成格式：v20241027-153000
# - vYYYYMMDD-HHMMSS
# - 适合频繁更新的场景
```

### 使用方式

#### 方式 1：自动版本号（推荐）

```python
manager = PromptManager()

# 推送时自动生成版本号
manager.push('report_generator')

# 自动发生：
# 1. 读取当前版本（从 .versions/report_generator.json）
# 2. 递增版本号：v1.2.3 → v1.2.4
# 3. 推送主版本到 Hub: "report_generator"
# 4. 创建备份版本: "report_generator-v1.2.4"
# 5. 更新本地 YAML: version: v1.2.4
# 6. 保存版本历史
```

输出示例：
```
[4/4] 步骤 4/4: 创建版本备份...
  当前版本: v1.2.3
  新版本: v1.2.4
[OK] 已备份到: report_generator-v1.2.4
  版本号: v1.2.4
[OK] 已更新 YAML 版本号: v1.2.4
```

#### 方式 2：手动指定变更类型

```python
# 小优化（默认）
manager.push('report_generator')  # v1.2.3 → v1.2.4

# 新功能
manager.push('report_generator', change_type='minor')  # v1.2.3 → v1.3.0

# 大改动
manager.push('report_generator', change_type='major')  # v1.2.3 → v2.0.0
```

### 版本历史记录

```json
// prompts/.versions/report_generator.json
{
  "current_version": "v1.2.4",
  "updated_at": "2024-10-27T15:30:00",
  "history": [
    {
      "version": "v1.0.0",
      "timestamp": "2024-10-01T10:00:00",
      "change_type": "initial"
    },
    {
      "version": "v1.1.0",
      "timestamp": "2024-10-15T14:20:00",
      "change_type": "minor"
    },
    {
      "version": "v1.2.0",
      "timestamp": "2024-10-20T09:15:00",
      "change_type": "minor"
    },
    {
      "version": "v1.2.4",
      "timestamp": "2024-10-27T15:30:00",
      "change_type": "patch"
    }
  ]
}
```

---

## 完整示例

### 场景：添加新的提示词 "summary_generator"

#### 步骤 1：配置提示词

```yaml
# prompts_config.yaml

prompts:
  summary_generator:
    file: "summary_generator.yaml"
    hub_name: "summary_generator"
    test_dataset: "summary_generator"  # ⭐ 独立 Dataset
    min_quality_score: 0.80
    description: "生成文章摘要"
    
    # ⭐ 专属评估器
    evaluators:
      - "structure_evaluator"
      - "summary_quality_evaluator"  # 自定义评估器
    
    evaluator_weights:
      structure_evaluator: 0.3
      summary_quality_evaluator: 0.7
```

#### 步骤 2：创建专属评估器

```python
# evaluation/evaluators.py

@run_evaluator
def summary_quality_evaluator(run, example) -> EvaluationResult:
    """摘要质量评估器"""
    output = run.outputs.get("summary", "")
    
    checks = {
        "length": 100 <= len(output) <= 500,  # 长度合理
        "concise": "总之" in output or "综上" in output,  # 有总结
        "key_points": output.count("•") >= 3  # 至少3个要点
    }
    
    score = sum(checks.values()) / len(checks)
    
    return EvaluationResult(
        key="summary_quality",
        score=score,
        comment=f"通过 {sum(checks.values())}/3 项检查"
    )
```

#### 步骤 3：添加评估器映射

```python
# prompts/prompt_manager.py

def _get_evaluators_by_names(self, evaluator_names):
    evaluator_map = {
        'structure_evaluator': ReportEvaluators.structure_evaluator,
        'content_completeness_evaluator': ReportEvaluators.content_completeness_evaluator,
        'relevance_evaluator': ReportEvaluators.relevance_evaluator,
        'parameter_usage_evaluator': ReportEvaluators.parameter_usage_evaluator,
        'summary_quality_evaluator': summary_quality_evaluator,  # ⭐ 添加
    }
    # ...
```

#### 步骤 4：创建测试 Dataset

```bash
# 运行程序自动捕获
python main.py --query "总结这篇文章"
python main.py --query "生成摘要，重点关注核心观点"

# 自动推送到 "summary_generator" Dataset
```

#### 步骤 5：评估和推送

```python
manager = PromptManager()

# 评估（使用专属评估器）
result = manager.evaluate_prompt('summary_generator', use_full_pipeline=True)
print(f"质量分数: {result['quality_score']:.2%}")

# 推送（自动版本号 + 自动备份）
manager.push('summary_generator')
# → 生成 v1.0.0
# → 推送到 Hub: "summary_generator" 和 "summary_generator-v1.0.0"
```

---

## 总结

### 核心要点

1. **每个提示词有独立配置**
   - 独立 Dataset
   - 专属评估器组合
   - 自定义权重

2. **使用新方法名**
   - `manager.evaluate_prompt()` 更清晰

3. **use_full_pipeline 参数**
   - False: 快速格式检查
   - True: 完整流程评估

4. **自动版本号**
   - 推送时自动生成
   - 自动创建备份
   - 自动更新 YAML

5. **EvaluationResult 官方类**
   - 必需：key, score
   - 推荐：comment
   - @run_evaluator 是官方装饰器

### 快速参考

```python
# 配置
# prompts_config.yaml: 定义评估器和权重

# 开发
manager.evaluate_prompt('xxx', use_full_pipeline=False)  # 快速

# 推送前
manager.evaluate_prompt('xxx', use_full_pipeline=True)   # 完整
manager.push('xxx')  # 自动版本号
```

---

**完成！** 🎉 现在你有了一个灵活、可配置、自动化的评估系统。

