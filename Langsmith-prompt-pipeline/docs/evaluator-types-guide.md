# LangSmith Evaluator 类型和使用方式

## 一、LangSmith 提供的评估器类型

根据 LangSmith 平台，主要有**三种评估器类型**：

### 1.1 LLM-as-Judge Evaluator（提示词型评估器）⭐ **推荐用于平台开发**

- **创建方式**：在 Web UI 上编写提示词（System Prompt + Rubric）
- **保存位置**：**会保存到 Prompt Hub** ✅
- **同步方式**：**可以像普通 prompt 一样自动拉取** ✅
- **使用场景**：适合在平台上直接开发，使用 LLM 作为评估器
- **示例**：
  ```
  System: "You are an expert at comparing two answers"
  Rubric: "Correct answers match the reference, incorrect answers differ"
  ```

### 1.2 Custom Code Evaluator（自定义代码评估器）

- **创建方式**：上传 Python 代码
- **保存位置**：评估器独立存储（**不保存到 Prompt Hub**）
- **同步方式**：需要通过 API 管理，**不支持自动拉取**
- **使用场景**：需要复杂的代码逻辑（如当前项目中的 `structure_evaluator`）
- **示例**：当前的 `ReportEvaluators.structure_evaluator`

### 1.3 Composite Evaluator（组合评估器）

- **创建方式**：组合多个评估器
- **保存位置**：评估器配置
- **使用场景**：需要多维度评估

## 二、评估器与 Prompt 的关联方式

### 2.1 Prompt Hub 类型（LLM-as-Judge）

✅ **可以归属到 Prompt**：
- 评估器保存为 Prompt Hub 中的 prompt
- 可以在 `prompts_config.yaml` 中配置关联
- 支持 `auto_pull` 自动同步

### 2.2 Custom Code 类型（当前实现）

⚠️ **独立管理**：
- 评估器独立存储
- 通过 `evaluators_config.yaml` 配置关联
- **不支持自动拉取**（代码通常本地管理）

## 三、查看和管理评估器

### 3.1 在 LangSmith Web UI 中查看

1. **Prompt Hub 类型评估器**：
   - 位置：`https://smith.langchain.com/hub/`
   - 与其他 prompt 一起显示
   - 可以通过 `hub.pull()` 拉取

2. **Custom Code 类型评估器**：
   - 位置：`https://smith.langchain.com/datasets/{dataset_name}/evaluators`
   - 或在数据集页面 → Evaluators 标签
   - **需要手动上传代码**

### 3.2 评估器归属关系

评估器通常关联到：
- **数据集（Dataset）**：评估器用于评估特定数据集上的结果
- **实验（Experiment）**：评估器用于评估实验运行结果
- **Prompt Hub（如果使用 LLM-as-Judge）**：评估器本身就是一个 prompt

## 四、推荐方案

### 4.1 如果选择在平台上开发（推荐）

**使用 LLM-as-Judge 类型**：
1. 在 LangSmith Web UI 创建评估器
2. 选择 "Prompt & Model" 类型
3. 编写 System Prompt 和 Rubric
4. **保存时会自动创建到 Prompt Hub** ✅
5. 可以像普通 prompt 一样同步：
   ```yaml
   # prompts_config.yaml
   prompts:
     structure_evaluator:  # 评估器作为 prompt 存储
       file: "structure_evaluator.yaml"
       hub_name: "structure_evaluator"
       description: "结构评估器"
   ```
6. 使用 `prompt_manager.py` 自动拉取 ✅

### 4.2 如果需要复杂逻辑（当前项目）

**使用 Custom Code 类型**：
1. 在本地编写 Python 代码
2. 使用 `evaluator_manager.py` 提取和上传
3. 或手动上传到平台
4. **不支持自动拉取**（代码本地管理）

## 五、混合方案（最佳实践）

### 5.1 简单评估器 → Prompt Hub

对于简单的 LLM 判断评估器，使用 **LLM-as-Judge** 类型：
- 在平台上直接开发
- 保存到 Prompt Hub
- 支持自动拉取和同步

### 5.2 复杂评估器 → Custom Code

对于需要复杂逻辑的评估器，使用 **Custom Code** 类型：
- 在本地开发
- 通过 API 或手动上传
- 本地版本控制

## 六、总结

| 评估器类型 | 开发位置 | 保存位置 | 自动拉取 | 适用场景 |
|----------|---------|---------|---------|---------|
| **LLM-as-Judge** | Web UI ⭐ | Prompt Hub ✅ | ✅ 支持 | 简单评估逻辑 |
| **Custom Code** | 本地代码 | 独立存储 | ❌ 不支持 | 复杂评估逻辑 |

**建议**：
- 如果主要在平台上开发 → 使用 **LLM-as-Judge**，保存到 Prompt Hub，支持自动拉取
- 如果需要复杂代码逻辑 → 使用 **Custom Code**，本地管理代码

