# Evaluator 工作流程和使用指南

## 一、理解 Custom Code Evaluator 的工作方式

### 1.1 两种运行模式

**Custom Code Evaluator** 可以在两个地方运行：

1. **本地运行**（当前主要方式）：
   - 代码在本地：`evaluation/evaluators/report.py`
   - 作为 Python 函数对象使用
   - 直接调用，不需要上传

2. **平台运行**（可选）：
   - 代码上传到 LangSmith 平台
   - 在平台上作为 "Custom Code Evaluator" 运行
   - 通过 Web UI 或 API 调用

### 1.2 当前项目的工作流程

```
┌─────────────────────────────────────────────────┐
│  本地开发 Evaluator                              │
│  evaluation/evaluators/report.py                │
│  - ReportEvaluators.structure_evaluator        │
│  - ReportEvaluators.relevance_evaluator        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  使用 Evaluator（本地）                          │
│  evaluation/evaluation.py                       │
│  - EvaluationRunner.evaluate_prompt()          │
│  - 传入 evaluator 函数对象                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  可选：上传到平台                                │
│  evaluation/evaluator_manager.py                │
│  - push() 提取代码并上传                        │
└─────────────────────────────────────────────────┘
```

## 二、EvaluatorManager 的实际功能

### 2.1 核心功能说明

**EvaluatorManager** 主要做三件事：

#### 功能 1：代码提取 ⭐ **最重要**

```python
manager = EvaluatorManager()
source_code = manager._get_evaluator_source_code("structure_evaluator", "ReportEvaluators")
```

**作用**：
- 从本地 Python 文件（如 `report.py`）提取 evaluator 函数
- 包含所有必要的导入语句
- 处理类方法的缩进和装饰器
- **输出**：完整的 Python 代码字符串

**为什么需要这个？**
- 如果你在平台上创建 Custom Code Evaluator，需要粘贴代码
- 这个功能帮你自动提取代码，不用手动复制粘贴

#### 功能 2：推送到平台（可选）

```bash
python -m evaluation.evaluator_manager push --name structure_evaluator --dataset report_generator
```

**作用**：
- 尝试通过 LangSmith API 上传 evaluator 代码
- 如果 API 不支持，会输出源代码供手动上传

#### 功能 3：配置管理

**配置文件**：`evaluation/evaluators_config.yaml`
- 记录所有 evaluator 的元数据
- 文件路径、类名、描述、关联数据集

## 三、实际工作流：如何使用 Evaluator

### 3.1 当前项目的工作流程（推荐）

```python
# 步骤 1：本地开发 evaluator（已经在 report.py 中）
# evaluation/evaluators/report.py
class ReportEvaluators:
    @staticmethod
    @run_evaluator
    def structure_evaluator(run, example) -> EvaluationResult:
        # 你的评估逻辑
        ...

# 步骤 2：使用 evaluator 评估 prompt
from evaluation.evaluation import EvaluationRunner
from evaluation.evaluators.report import ReportEvaluators

runner = EvaluationRunner()

# 方式 1：直接使用本地 evaluator 函数对象
results = runner.evaluate_prompt(
    prompt_name="report_generator",
    dataset_name="report_generator",
    evaluators=[
        ReportEvaluators.structure_evaluator,  # ✅ 直接使用本地函数
        ReportEvaluators.relevance_evaluator
    ]
)

# 方式 2：使用配置中的 evaluator 名称（会自动加载）
from prompts.prompt_manager import PromptManager
prompt_manager = PromptManager()
results = prompt_manager.evaluate_prompt('report_generator')
# 会自动从 prompts_config.yaml 读取 evaluator 名称
# 然后加载对应的函数对象
```

### 3.2 关键理解：Evaluator 是函数对象

**重要**：在 Python 中，evaluator 是**函数对象**，不是代码字符串：

```python
# ✅ 正确：传入函数对象
evaluators = [
    ReportEvaluators.structure_evaluator  # 这是函数对象
]

# ❌ 错误：不能传入字符串
evaluators = ["structure_evaluator"]  # 这样不行，需要先转换为函数对象
```

### 3.3 完整的评估工作流

```python
# 1. 导入必要的模块
from evaluation.evaluation import EvaluationRunner
from prompts.prompt_manager import PromptManager

# 2. 创建评估运行器
runner = EvaluationRunner()

# 3. 运行评估
results = runner.evaluate_prompt(
    prompt_name="report_generator",
    dataset_name="report_generator",
    # evaluators 参数是可选的
    # 如果不提供，会使用配置中的默认评估器
)

# 4. 查看结果
print(f"总分: {results['quality_score']:.2%}")
print(f"各维度分数: {results['scores']}")
```

## 四、如果在远程创建了 Custom Code Evaluator

### 4.1 是否可以拉到本地？

**简短回答**：⚠️ **目前不支持自动拉取**

**原因**：
1. Custom Code Evaluator 的代码存储在 LangSmith 平台
2. 需要 LangSmith API 支持获取 evaluator 代码
3. 目前 `evaluator_manager.py` 主要做**推送**，不支持**拉取**

### 4.2 推荐的工作流程

**场景 1：在远程创建了 Custom Code Evaluator**

**选项 A**：继续使用本地代码（推荐）
```python
# 在本地维护 evaluator 代码
# evaluation/evaluators/report.py

# 在平台上创建 evaluator 时，使用本地提取的代码：
manager = EvaluatorManager()
source_code = manager._get_evaluator_source_code("structure_evaluator")
# 然后复制粘贴到平台
```

**选项 B**：从平台获取代码（需要 API 支持）
```python
# 如果 LangSmith API 支持，可以这样：
# client = LangSmithConfig.get_client()
# evaluator = client.get_evaluator(name="structure_evaluator")
# source_code = evaluator.code
# 然后保存到本地文件
```

**选项 C**：在本地重新实现（最简单）
- 根据平台上的评估器逻辑，在本地重新实现
- 保持本地代码与平台一致

### 4.3 实际使用场景

**在平台上创建 Custom Code Evaluator 的主要目的**：
- ✅ 在 Web UI 中可视化运行评估
- ✅ 与其他团队成员共享评估器
- ✅ 在平台上直接使用评估器评估实验

**本地代码的主要目的**：
- ✅ 版本控制（Git）
- ✅ 本地开发调试
- ✅ 本地自动化评估

## 五、EvaluatorManager 的具体使用示例

### 5.1 提取代码（用于手动上传）

```bash
# 1. 提取 evaluator 源代码
python -m evaluation.evaluator_manager push --name structure_evaluator --dataset report_generator

# 如果 API 不支持，会输出源代码并保存到：
# evaluation/structure_evaluator_source.py

# 2. 手动复制代码到平台
# 访问：https://smith.langchain.com/datasets/report_generator/evaluators
# 点击 "Create Custom Code Evaluator"
# 粘贴源代码
```

### 5.2 验证配置

```bash
# 验证 evaluator 配置是否正确
python -m evaluation.evaluator_manager validate --name structure_evaluator
```

### 5.3 列出所有 evaluators

```bash
python -m evaluation.evaluator_manager list --name dummy
```

## 六、总结：EvaluatorManager 做了什么

| 功能 | 说明 | 是否必须 |
|------|------|---------|
| **代码提取** | 从本地 Python 文件提取 evaluator 代码 | ✅ 有用（方便上传） |
| **推送到平台** | 尝试通过 API 上传 | ⚠️ 可选（代码可以手动上传） |
| **配置管理** | 管理 evaluator 元数据 | ✅ 有用（组织管理） |
| **从平台拉取** | 从平台下载代码 | ❌ 不支持（代码通常本地管理） |

**核心理解**：
- **本地使用**：直接使用函数对象，不需要上传
- **平台使用**：如果需要，可以提取代码并上传
- **EvaluatorManager**：主要帮助**提取代码**和**管理配置**，不是必须的

## 七、推荐工作流程

### 7.1 日常开发（推荐）

```python
# 1. 在本地开发和测试 evaluator
# evaluation/evaluators/report.py

# 2. 直接在本地使用
from evaluation.evaluation import EvaluationRunner
runner = EvaluationRunner()
results = runner.evaluate_prompt("report_generator")

# 3. 如果需要在平台上使用，提取代码上传
python -m evaluation.evaluator_manager push --name structure_evaluator
```

### 7.2 团队协作

1. **本地代码**：Git 版本控制，团队共享
2. **平台评估器**：按需上传，用于 Web UI 可视化

