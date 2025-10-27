# LangSmith Prompt 工程化平台

> 🚀 企业级提示词开发、测试、优化的完整解决方案

[![LangChain](https://img.shields.io/badge/LangChain-Latest-blue)](https://python.langchain.com/)
[![LangSmith](https://img.shields.io/badge/LangSmith-Integrated-green)](https://smith.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-orange)](https://langchain-ai.github.io/langgraph/)

---

## 📖 目录

- [快速开始](#-快速开始)
- [核心 SOP：提示词开发工作流](#-核心-sop提示词开发工作流)
- [系统架构](#-系统架构)
- [核心功能](#-核心功能)
- [使用指南](#-使用指南)
- [高级特性](#-高级特性)

---

## 🚀 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <your-repo>
cd Langsmith-prompt-pipeline

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys
```

**必需的环境变量**：
```bash
# LangSmith（必需）
LANGSMITH_API_KEY="lsv2_pt_xxxxxxxxxxxx"
LANGSMITH_PROJECT="prompt-pipeline"

# LLM 配置（支持 Azure OpenAI 或 OpenAI）
LLM_PROVIDER="azure"  # 或 "openai"

# Azure OpenAI
AZURE_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_DEPLOYMENT="gpt-4"
AZURE_API_KEY="your-key"
AZURE_API_VERSION="2024-02-15-preview"

# 或标准 OpenAI
OPENAI_API_KEY="sk-xxxxx"
OPENAI_MODEL="gpt-4o"
```

### 2. 验证安装

```bash
# 测试 LLM 连接
python config/azure_config.py

# 测试 LangSmith 连接
python config/langsmith_config.py

# 测试提示词管理器
python prompts/prompt_manager.py
```

### 3. 运行第一个示例

```bash
# 生成报告（自动追踪到 LangSmith）
python main.py --query "分析2024年AI行业发展趋势"
```

访问 [LangSmith 控制台](https://smith.langchain.com/) 查看运行追踪 🎉

---

## 🎯 核心 SOP：提示词开发工作流

### 标准操作流程（5步循环）

```
┌─────────────────────────────────────────────────────────────┐
│  1. 开发   2. 测试   3. 评估   4. 优化   5. 部署           │
│  ↓         ↓         ↓         ↓         ↓                  │
│  YAML  →  Dataset →  LangSmith→ 调优  →  Hub 推送           │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: 开发提示词

**创建或编辑 YAML 文件**（标准化格式）：

```yaml
# prompts/parameter_parser.yaml
version: v1.0.0
description: "从用户输入中提取结构化参数"

messages:
  - role: system
    content: |
      你是一个专业的参数提取助手。
      从用户查询中提取以下参数：
      - topic: 主题
      - year_range: 年份范围
      - style: 报告风格
      - depth: 深度级别
      
      以 JSON 格式输出。

  - role: user
    content: "{user_query}"

input_variables:
  - user_query

metadata:
  author: "Your Name"
  tags: ["parameter_extraction", "json_output"]
```

**配置提示词信息**（`prompts/prompts_config.yaml`）：

```yaml
prompts:
  parameter_parser:
    file: "parameter_parser.yaml"
    hub_name: "parameter_parser"
    test_dataset: "parameter_parser"  # 关联的测试数据集
    
    # 专属评估器
    evaluators:
      - "structure_evaluator"
      - "parameter_extraction_evaluator"
    
    # 评估器权重
    evaluator_weights:
      structure_evaluator: 0.3
      parameter_extraction_evaluator: 0.7
```

### Step 2: 创建测试数据集

**方式 1：手动创建**

```python
from evaluation.datasets import DatasetManager

manager = DatasetManager()

test_cases = [
    {
        "input": {"user_query": "分析2023-2024年AI行业发展趋势，要详细的"},
        "expected_params": {
            "topic": "AI行业发展趋势",
            "year_range": "2023-2024",
            "depth": "详细"
        }
    },
    # 更多测试用例...
]

# 创建数据集
manager.create_dataset(
    dataset_name="parameter_parser",
    test_cases=test_cases
)
```

**方式 2：自动捕获**（推荐）

```python
# 在代码中使用 @capture_middle_result 装饰器
from tools.capture import capture_middle_result

@capture_middle_result(
    dataset_name="parameter_parser",
    step_name="parse_params"
)
def parse_parameters(user_query: str):
    # 你的逻辑
    return result
```

运行程序后，中间结果自动保存到 LangSmith Dataset！

### Step 3: 运行评估

**方式 1：使用 PromptManager（推荐）**

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 评估提示词质量
result = manager.evaluate_prompt('parameter_parser')

print(f"质量评分: {result['quality_score']:.2%}")
print(f"测试用例数: {result['total']}")
```

**方式 2：使用 EvaluationRunner（高级）**

```python
from evaluation.evaluation import EvaluationRunner

runner = EvaluationRunner()

# 评估单个提示词
result = runner.evaluate_prompt(
    prompt_name='parameter_parser',
    dataset_name='parameter_parser',
    experiment_name='v1_test'
)

# 对比多个配置
comparison = runner.compare_prompts(
    prompt_name='parameter_parser',
    dataset_name='parameter_parser',
    llm_configs={
        "gpt4": {"temperature": 0.3},
        "gpt35": {"temperature": 0.7}
    }
)
```

**查看评估报告**：

```
============================================================
LangSmith Evaluator - 提示词质量评估
============================================================

提示词: parameter_parser
数据集: parameter_parser
实验名称: eval_parameter_parser_20241027_143022
评估器数量: 2

开始评估...

评估结果汇总:
------------------------------------------------------------
  structure_valid: 95.00%
  parameter_extraction: 88.00%
------------------------------------------------------------
  总分: 91.50%
  测试数: 10

查看详细结果: https://smith.langchain.com/
```

### Step 4: 优化迭代

**根据评估结果优化提示词**：

1. **在 LangSmith Playground 中测试**
   - 打开 [LangSmith Playground](https://smith.langchain.com/)
   - 选择你的 Dataset
   - 实时调整提示词
   - 查看输出变化

2. **本地修改 YAML**
   ```yaml
   # 优化后的 parameter_parser.yaml
   messages:
     - role: system
       content: |
         你是专业的参数提取助手。
         
         提取规则：
         1. topic: 必需，提取主题关键词
         2. year_range: 识别年份范围（如 "2023-2024"）
         3. style: 可选，报告风格（专业/通俗）
         4. depth: 可选，深度（简要/详细/深入）
         
         **输出格式**（必须是有效 JSON）：
         {
           "topic": "string",
           "year_range": "string",
           "style": "string",
           "depth": "string"
         }
   ```

3. **重新评估**
   ```bash
   python -c "from prompts.prompt_manager import PromptManager; \
              PromptManager().evaluate_prompt('parameter_parser')"
   ```

4. **版本对比**
   ```python
   # 对比优化前后
   runner.compare_prompts(
       prompt_name='parameter_parser',
       dataset_name='parameter_parser',
       prompt_versions=['v1.0.0', 'v1.1.0']
   )
   ```

### Step 5: 部署到生产

**推送到 LangSmith Hub**：

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 推送到 Hub（带版本号）
manager.push(
    prompt_name='parameter_parser',
    commit_message='优化参数提取准确性',
    change_type='minor'  # 'major' | 'minor' | 'patch'
)
```

**团队协作 - 自动同步**：

```python
# 其他开发者拉取最新版本
manager.pull('parameter_parser')  # 自动拉取最新版本

# 或启用自动拉取（默认开启）
manager = PromptManager(auto_pull=True)
prompt = manager.get('parameter_parser')  # 自动获取最新版
```

**回滚版本**（如有问题）：

```python
# 查看历史版本
manager.list_versions('parameter_parser')

# 回滚到指定版本
manager.rollback('parameter_parser', 'v1.0.0')
```

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  main.py  │  prompts/  │  evaluation/  │  LangSmith UI      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                      核心模块层                              │
├─────────────────┬─────────────────┬────────────────────────┤
│  Prompt 管理    │   评估系统       │   LangGraph 流程       │
│  - YAML存储     │   - 评估器注册表  │   - StateGraph       │
│  - 版本管理     │   - 动态加载      │   - 节点编排          │
│  - Hub同步      │   - 数据集管理    │   - 流式输出          │
└─────────────────┴─────────────────┴────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                      基础服务层                              │
│  LangSmith API  │  LLM (Azure/OpenAI)  │  外部工具          │
└─────────────────────────────────────────────────────────────┘
```

### 核心设计理念

#### 1. **配置驱动** - 一切皆配置
```yaml
# prompts_config.yaml
prompts:
  parameter_parser:
    evaluators: ["structure_evaluator", "parameter_extraction_evaluator"]
    evaluator_weights: {structure_evaluator: 0.3}
```

#### 2. **职责分离** - 单一职责原则
```
PromptManager   → 提示词管理（加载、保存、同步）
EvaluationRunner → 评估流程编排（不包含业务逻辑）
Evaluators      → 按提示词类型组织（report, parameter, summary...）
```

#### 3. **可扩展性** - 插件化架构
```python
# 新增提示词评估器
# 1. 创建 evaluation/evaluators/your_type.py
# 2. 注册到 EVALUATOR_REGISTRY
# 3. 配置到 prompts_config.yaml
# 完成！无需修改核心代码
```

---

## 🔧 核心功能

### 1. Prompt 管理系统

**特性**：
- ✅ YAML 标准化格式（ChatPromptTemplate）
- ✅ 版本管理（语义化版本号）
- ✅ LangSmith Hub 同步
- ✅ 自动拉取最新版本
- ✅ 一键回滚

**文件结构**：
```
prompts/
├── prompts_config.yaml      # 提示词配置清单
├── parameter_parser.yaml    # 参数解析提示词
├── report_generator.yaml    # 报告生成提示词
└── prompt_manager.py        # 管理器核心代码
```

**核心 API**：
```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 获取提示词（自动拉取最新版）
prompt_template = manager.build_prompt_from_name('parameter_parser')

# 推送到 Hub
manager.push('parameter_parser', commit_message='优化提取准确性')

# 评估质量
result = manager.evaluate_prompt('parameter_parser')
```

### 2. 评估系统

**架构设计**：
```
evaluation/
├── evaluation.py           # 评估运行器（流程编排）
├── datasets.py            # 数据集管理
└── evaluators/            # 评估器目录（按提示词类型组织）
    ├── __init__.py        # 评估器注册表
    ├── report.py          # 报告评估器
    └── parameter.py       # 参数评估器
```

**评估器注册表**（动态加载）：
```python
# evaluation/evaluators/__init__.py
EVALUATOR_REGISTRY = {
    # 通用评估器
    "structure_evaluator": ReportEvaluators.structure_evaluator,
    "content_completeness_evaluator": ReportEvaluators.content_completeness_evaluator,
    
    # 参数解析专用
    "parameter_extraction_evaluator": ParameterEvaluators.parameter_extraction_evaluator,
    "field_type_evaluator": ParameterEvaluators.field_type_evaluator,
}

# 根据配置自动加载评估器
evaluators = get_evaluators_for_prompt(prompt_config)
```

**评估器类型**：

| 评估器 | 类型 | 用途 | 适用提示词 |
|--------|------|------|-----------|
| `structure_evaluator` | 规则 | 检查输出结构 | 所有 |
| `content_completeness_evaluator` | 规则 | 检查内容完整性 | report_generator |
| `relevance_evaluator` | LLM | 检查内容相关性 | report_generator |
| `parameter_usage_evaluator` | 规则 | 检查参数使用 | report_generator |
| `parameter_extraction_evaluator` | 规则 | 检查参数提取准确性 | parameter_parser |
| `field_type_evaluator` | 规则 | 检查字段类型 | parameter_parser |

**自定义评估器**：
```python
# evaluation/evaluators/your_type.py
from langsmith.evaluation import EvaluationResult, run_evaluator

class YourEvaluators:
    @staticmethod
    @run_evaluator
    def your_custom_evaluator(run, example) -> EvaluationResult:
        """自定义评估逻辑"""
        output = run.outputs.get("report", "")
        
        # 你的评估逻辑
        score = calculate_score(output)
        
        return EvaluationResult(
            key="your_metric",
            score=score,
            comment="评估说明"
        )
```

### 3. LangGraph 工作流

**多步骤流程编排**：
```python
# graph/graph.py
workflow = StateGraph(ReportState)

# 添加节点
workflow.add_node("parse_parameters", parse_parameters_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("generate_report", generate_report_node)
workflow.add_node("quality_check", quality_check_node)

# 定义流程
workflow.set_entry_point("parse_parameters")
workflow.add_edge("parse_parameters", "web_search")
workflow.add_edge("web_search", "generate_report")
workflow.add_edge("generate_report", "quality_check")
```

**状态管理**：
```python
# graph/state.py
class ReportState(TypedDict):
    user_query: str
    topic: str
    year_range: str
    style: str
    depth: str
    search_results: List[Dict]
    report: str
    metadata: Dict[str, Any]
```

### 4. 中间结果捕获

**自动捕获装饰器**：
```python
from tools.capture import capture_middle_result

@capture_middle_result(
    dataset_name="parameter_parser",
    step_name="parse_params"
)
def parse_parameters(user_query: str):
    # 解析逻辑
    result = extract_params(user_query)
    return result

# 运行后，结果自动保存到 LangSmith Dataset！
```

**手动捕获**：
```python
from tools.capture import MiddleResultCapture

capture = MiddleResultCapture("my_dataset")

# 捕获输入输出
capture.add_example(
    inputs={"query": "用户输入"},
    outputs={"result": "输出结果"},
    metadata={"step": "parse_params"}
)

# 批量上传
capture.upload_to_dataset()
```

### 5. LangSmith 完整集成

**追踪（Tracing）**：
```python
from config.langsmith_config import LangSmithConfig

# 启用追踪
LangSmithConfig.enable_tracing(project_name="my_project")

# 所有 LLM 调用自动追踪到 LangSmith！
```

**数据集管理**：
```python
from evaluation.datasets import DatasetManager

manager = DatasetManager()

# 创建数据集
manager.create_dataset_from_file(
    dataset_name="test_cases",
    filepath="examples/test_cases.json"
)

# 列出所有数据集
manager.list_datasets()

# 删除数据集
manager.delete_dataset("old_dataset")
```

---

## 📘 使用指南

### 场景 1：开发新提示词

```bash
# 1. 创建 YAML 文件
cat > prompts/summary.yaml << 'EOF'
version: v1.0.0
description: "生成内容摘要"
messages:
  - role: system
    content: "你是摘要生成助手，提取关键信息。"
  - role: user
    content: "{content}"
input_variables: ["content"]
EOF

# 2. 配置提示词
# 编辑 prompts/prompts_config.yaml 添加配置

# 3. 创建测试数据集
python -c "
from evaluation.datasets import DatasetManager
manager = DatasetManager()
manager.create_dataset('summary_test', test_cases=[...])
"

# 4. 测试提示词
python -c "
from prompts.prompt_manager import PromptManager
result = PromptManager().evaluate_prompt('summary')
print(f'质量评分: {result[\"quality_score\"]:.2%}')
"

# 5. 推送到 Hub
python -c "
from prompts.prompt_manager import PromptManager
PromptManager().push('summary', commit_message='初始版本')
"
```

### 场景 2：优化现有提示词

```python
from prompts.prompt_manager import PromptManager
from evaluation.evaluation import EvaluationRunner

manager = PromptManager()
runner = EvaluationRunner()

# 1. 评估当前版本
baseline = runner.evaluate_prompt(
    prompt_name='parameter_parser',
    dataset_name='parameter_parser',
    experiment_name='baseline_v1'
)

# 2. 修改 prompts/parameter_parser.yaml

# 3. 评估优化版本
optimized = runner.evaluate_prompt(
    prompt_name='parameter_parser',
    dataset_name='parameter_parser',
    experiment_name='optimized_v2'
)

# 4. 对比结果
print(f"Baseline 分数: {baseline['overall_score']:.2%}")
print(f"优化后分数: {optimized['overall_score']:.2%}")
print(f"提升: {(optimized['overall_score'] - baseline['overall_score']):.2%}")

# 5. 如果提升明显，推送新版本
if optimized['overall_score'] > baseline['overall_score']:
    manager.push('parameter_parser', commit_message='提升准确性', change_type='minor')
```

### 场景 3：A/B 测试不同 LLM 配置

```python
from evaluation.evaluation import EvaluationRunner

runner = EvaluationRunner()

# 对比不同温度参数
comparison = runner.compare_prompts(
    prompt_name='report_generator',
    dataset_name='report_test',
    llm_configs={
        "保守模式": {"temperature": 0.3},
        "均衡模式": {"temperature": 0.7},
        "创造模式": {"temperature": 0.9}
    }
)

# 查看对比结果
print("\n各配置得分:")
for config_name, result in comparison.items():
    print(f"  {config_name}: {result['overall_score']:.2%}")

print(f"\n推荐配置: {comparison['recommended_version']}")
```

### 场景 4：团队协作

**开发者 A - 优化提示词**：
```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 拉取最新版本
manager.pull('parameter_parser')

# 本地修改并测试
result = manager.evaluate_prompt('parameter_parser')

# 推送到 Hub
if result['quality_score'] > 0.9:
    manager.push('parameter_parser', commit_message='优化参数提取')
```

**开发者 B - 使用最新版本**：
```python
from prompts.prompt_manager import PromptManager

# 自动拉取模式（默认）
manager = PromptManager(auto_pull=True)

# 使用提示词（自动获取最新版）
prompt = manager.build_prompt_from_name('parameter_parser')

# 无需手动同步，自动获取团队最新版本！
```

---

## 🎓 高级特性

### 1. 流式输出（Streaming）

```python
from graph.graph import ReportGraphBuilder
import asyncio

async def stream_report():
    builder = ReportGraphBuilder()
    
    # 异步流式运行
    final_state = await builder.arun(
        user_query="分析AI行业2024年发展"
    )
    
    # 逐步输出每个节点的结果
    # parse_parameters -> web_search -> generate_report -> quality_check

asyncio.run(stream_report())
```

### 2. 自定义评估器

```python
# 1. 创建评估器
# evaluation/evaluators/summary.py
class SummaryEvaluators:
    @staticmethod
    @run_evaluator
    def conciseness_evaluator(run, example):
        """简洁性评估"""
        output = run.outputs.get("summary", "")
        word_count = len(output)
        
        # 评分逻辑：100-200字最佳
        if 100 <= word_count <= 200:
            score = 1.0
        else:
            score = max(0, 1 - abs(word_count - 150) / 150)
        
        return EvaluationResult(
            key="conciseness",
            score=score,
            comment=f"字数: {word_count}"
        )

# 2. 注册评估器
# evaluation/evaluators/__init__.py
EVALUATOR_REGISTRY['conciseness_evaluator'] = SummaryEvaluators.conciseness_evaluator

# 3. 配置使用
# prompts_config.yaml
prompts:
  summary:
    evaluators:
      - "structure_evaluator"
      - "conciseness_evaluator"  # 你的自定义评估器
```

### 3. 批量评估

```python
from evaluation.evaluation import EvaluationRunner

runner = EvaluationRunner()

# 批量评估所有提示词
prompts = ['parameter_parser', 'report_generator', 'summary']

results = {}
for prompt_name in prompts:
    results[prompt_name] = runner.evaluate_prompt(
        prompt_name=prompt_name,
        dataset_name=f"{prompt_name}_test"
    )

# 生成质量报告
for name, result in results.items():
    print(f"{name}: {result['overall_score']:.2%}")
```

### 4. 版本回滚

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 查看历史版本
versions = manager.list_versions('parameter_parser')
# v1.0.0, v1.1.0, v1.2.0

# 回滚到稳定版本
manager.rollback('parameter_parser', 'v1.1.0')

# 验证回滚效果
result = manager.evaluate_prompt('parameter_parser')
```

### 5. 自动化 CI/CD

```bash
# .github/workflows/prompt_quality.yml
name: Prompt Quality Check

on: [push, pull_request]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Evaluation
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
        run: |
          python -c "
          from prompts.prompt_manager import PromptManager
          manager = PromptManager()
          
          for prompt in ['parameter_parser', 'report_generator']:
              result = manager.evaluate_prompt(prompt)
              score = result['quality_score']
              
              if score < 0.8:
                  print(f'❌ {prompt} 质量不达标: {score:.2%}')
                  exit(1)
              else:
                  print(f'✅ {prompt} 质量合格: {score:.2%}')
          "
```

---

## 📁 项目结构

```
Langsmith-prompt-pipeline/
├── config/                      # 配置模块
│   ├── azure_config.py          # LLM 配置（Azure/OpenAI）
│   └── langsmith_config.py      # LangSmith 配置
│
├── prompts/                     # 提示词管理
│   ├── prompts_config.yaml      # 提示词配置清单
│   ├── parameter_parser.yaml    # 参数解析提示词
│   ├── report_generator.yaml    # 报告生成提示词
│   └── prompt_manager.py        # 提示词管理器
│
├── evaluation/                  # 评估系统
│   ├── evaluation.py            # 评估运行器
│   ├── datasets.py              # 数据集管理
│   └── evaluators/              # 评估器（按类型组织）
│       ├── __init__.py          # 评估器注册表
│       ├── report.py            # 报告评估器
│       └── parameter.py         # 参数评估器
│
├── graph/                       # LangGraph 工作流
│   ├── graph.py                 # Graph 构建器
│   ├── state.py                 # 状态定义
│   └── nodes.py                 # 节点实现
│
├── tools/                       # 工具模块
│   ├── capture.py               # 中间结果捕获
│   └── search_tool.py           # 搜索工具
│
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖清单
└── README.md                    # 本文档
```

---

## 🔍 常见问题

### Q1: 如何切换 LLM 提供商？

**A**: 修改 `.env` 文件：

```bash
# 使用 Azure OpenAI
LLM_PROVIDER="azure"
AZURE_ENDPOINT="..."
AZURE_DEPLOYMENT="..."

# 或使用标准 OpenAI
LLM_PROVIDER="openai"
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o"
```

### Q2: 评估器如何选择？

**A**: 根据提示词类型选择：

```yaml
# 参数提取类提示词
parameter_parser:
  evaluators:
    - "structure_evaluator"           # 检查 JSON 格式
    - "parameter_extraction_evaluator" # 检查提取准确性
    - "field_type_evaluator"          # 检查字段类型

# 内容生成类提示词
report_generator:
  evaluators:
    - "structure_evaluator"            # 检查结构
    - "content_completeness_evaluator" # 检查完整性
    - "relevance_evaluator"            # 检查相关性（LLM）
```

### Q3: 如何处理大规模测试数据集？

**A**: 使用分批评估：

```python
from evaluation.evaluation import EvaluationRunner

runner = EvaluationRunner()

# 设置并发数
result = runner.evaluate_prompt(
    prompt_name='parameter_parser',
    dataset_name='large_dataset',
    max_concurrency=10  # 并发执行
)
```

### Q4: 如何集成到现有项目？

**A**: 三步集成：

```python
# 1. 安装依赖
pip install langsmith langchain-openai langgraph

# 2. 复制模块到你的项目
cp -r prompts/ evaluation/ config/ your_project/

# 3. 使用
from prompts.prompt_manager import PromptManager
manager = PromptManager()
prompt = manager.build_prompt_from_name('your_prompt')
```

---

## 📚 相关文档

- [LangSmith 官方文档](https://docs.smith.langchain.com/)
- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)

**项目内文档**：
- `docs/evaluator-guide.md` - 评估器开发指南
- `docs/evaluation-configuration-guide.md` - 评估配置详解
- `docs/capture-decorator-guide.md` - 中间结果捕获指南
- `EVALUATION_QA.md` - 评估系统 Q&A
- `FEATURES_SUMMARY.md` - 功能特性总结

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

**开发流程**：
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 💬 联系方式

- 作者: Your Name
- Email: your.email@example.com
- 项目主页: https://github.com/your-username/langsmith-prompt-pipeline

---

<p align="center">
  <b>🌟 如果这个项目对你有帮助，请给一个 Star！🌟</b>
</p>
