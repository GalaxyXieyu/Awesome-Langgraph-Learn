# 如何在 LangSmith 平台查看评估器

## 一、查看位置

### 1.1 LLM-as-Judge 类型评估器（保存到 Prompt Hub）

**位置**：`https://smith.langchain.com/hub/`

- 这些评估器会显示在 Prompt Hub 中
- 名称可能类似：`structure_evaluator`, `relevance_evaluator`
- 可以像普通 prompt 一样查看和拉取

### 1.2 Custom Code 类型评估器

**位置 1**：数据集页面
```
https://smith.langchain.com/datasets/{dataset_name}
```
然后点击 **"Evaluators"** 标签

**位置 2**：直接访问（如果知道数据集名称）
```
https://smith.langchain.com/datasets/{dataset_name}/evaluators
```

例如：
- `https://smith.langchain.com/datasets/report_generator/evaluators`
- `https://smith.langchain.com/datasets/parameter_parser/evaluators`

### 1.3 实验（Experiment）中的评估器

如果评估器被用于某个实验：
```
https://smith.langchain.com/o/default/projects/{project_name}/experiments/{experiment_name}
```

## 二、评估器归属关系

### 2.1 关联到数据集（Dataset）

✅ **最常见**：评估器通常关联到数据集
- 每个数据集可以有多个评估器
- 在数据集页面 → Evaluators 标签中查看

### 2.2 关联到 Prompt Hub（LLM-as-Judge）

✅ **如果使用 Prompt & Model 创建**：
- 评估器会保存为 Prompt Hub 中的 prompt
- 可以像 prompt 一样管理
- **支持自动拉取**（通过 `prompt_manager.py`）

### 2.3 当前项目的评估器配置

查看 `prompts_config.yaml`：

```yaml
prompts:
  report_generator:
    evaluators:
      - "structure_evaluator"
      - "content_completeness_evaluator"
      - "relevance_evaluator"
      - "parameter_usage_evaluator"
```

这些评估器应该出现在：
- **数据集**：`report_generator` → Evaluators 标签
- **或 Prompt Hub**：如果使用 LLM-as-Judge 创建

## 三、如何确认评估器是否已上传

### 3.1 检查 Custom Code 评估器

1. 访问数据集页面：
   ```
   https://smith.langchain.com/datasets/report_generator
   ```
2. 点击 **"Evaluators"** 标签
3. 查看是否有你创建的评估器

### 3.2 检查 Prompt Hub 评估器

1. 访问 Prompt Hub：
   ```
   https://smith.langchain.com/hub/
   ```
2. 搜索评估器名称（如 `structure_evaluator`）
3. 如果找到，可以像普通 prompt 一样拉取

## 四、推荐工作流程

### 4.1 简单评估器（推荐平台开发）

1. **在 Web UI 创建**：
   - 数据集 → Evaluators → "Create Evaluator"
   - 选择 "Prompt & Model"
   - 编写 System Prompt 和 Rubric
   - **保存时会创建到 Prompt Hub** ✅

2. **在本地同步**：
   ```bash
   # 使用 prompt_manager 拉取（因为保存到了 Prompt Hub）
   from prompts.prompt_manager import PromptManager
   manager = PromptManager()
   config = manager.get("structure_evaluator")  # 自动拉取
   ```

### 4.2 复杂评估器（本地开发）

1. **在本地开发**：
   ```python
   # evaluation/evaluators/report.py
   @run_evaluator
   def structure_evaluator(run, example) -> EvaluationResult:
       # 复杂逻辑
   ```

2. **上传到平台**：
   ```bash
   python -m evaluation.evaluator_manager push --name structure_evaluator --dataset report_generator
   ```

3. **在平台查看**：
   - 访问：`https://smith.langchain.com/datasets/report_generator/evaluators`

## 五、快速查找命令

```python
# 列出所有可用的评估器
python -m evaluation.evaluator_manager list --name dummy

# 验证评估器配置
python -m evaluation.evaluator_manager validate --name structure_evaluator

# 查看评估器源代码（用于手动上传）
python -m evaluation.evaluator_manager push --name structure_evaluator --dataset report_generator
```

