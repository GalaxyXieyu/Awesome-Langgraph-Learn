# LangSmith Prompt 管理与迭代优化实战指南

> 🎯 一个完整的提示词管理系统，展示如何使用 LangSmith 进行提示词的优雅管理和迭代优化

[![LangChain](https://img.shields.io/badge/LangChain-Latest-blue)](https://python.langchain.com/)
[![LangSmith](https://img.shields.io/badge/LangSmith-Integrated-green)](https://smith.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-orange)](https://langchain-ai.github.io/langgraph/)

---

## 项目简介

本项目是一个**基于 LangGraph 和 LangSmith 的智能报告生成系统**，更重要的是，它展示了如何**优雅地管理和迭代优化提示词**。

### 核心价值

1. **提示词管理最佳实践** - ChatPromptTemplate 标准化、YAML 格式存储、版本管理
2. **LangSmith 完整集成** - 追踪、评估、数据集管理、Hub 推送
3. **自动化工作流** - 自动拉取、自动测试、一键推送
4. **多参数设计** - 灵活可配置的提示词系统

---

## 核心功能点

### 功能点1：ChatPromptTemplate 标准化

**问题**：早期提示词混合系统指令和用户任务，难以维护和扩展。

**解决方案**：使用 ChatPromptTemplate 标准格式，分离 System 和 Human 消息。

```yaml
_type: chat_prompt
messages:
  - role: system
    content: |
      你是一位资深的数据分析专家，拥有以下能力：
      ## 核心能力
      - 信息提取与结构化
      - 深度洞察分析
      ...
  
  - role: human
    content: |
      请根据以下参数生成报告：
      主题：{topic}
      风格：{style}
      ...
```

**优势**：
- ✅ 职责清晰：System 定义角色，Human 描述任务
- ✅ 行为可控：System message 精确控制 AI 行为
- ✅ 易于扩展：可添加 Few-shot 示例
- ✅ 符合标准：LangChain/LangSmith 最佳实践

### 功能点2：多参数提示词设计

**问题**：单一提示词无法适应不同场景，为每个场景写新提示词维护成本高。

**解决方案**：设计支持多参数的灵活提示词系统。

```python
# 6个核心参数
{
    "topic": "人工智能",           # 报告主题
    "year_range": "2023-2024",    # 年份范围
    "style": "formal",            # 风格：formal/casual/detailed/concise
    "depth": "medium",            # 深度：shallow/medium/deep
    "focus_areas": "技术创新,市场", # 关注领域
    "search_results": "..."       # 动态搜索结果
}
```

**优势**：
- ✅ 一个提示词适应多种场景
- ✅ 用户可精确控制输出
- ✅ 便于 A/B 测试参数影响
- ✅ 提高提示词复用率

### 功能点3：YAML 格式提示词管理

**问题**：提示词存储在代码中难以管理，JSON 格式不支持注释和换行。

**解决方案**：使用 YAML 格式存储提示词。

```yaml
# parameter_parser.yaml
name: parameter_parser
version: v1.0
description: 从用户输入中提取结构化参数

input_variables:
  - user_query
  - topic
  - year_range

messages:
  - role: system
    content: |
      # 清晰的注释
      你的系统指令...
  
  - role: human
    content: |
      用户任务：{user_query}
```

**优势**：
- ✅ 人类可读：支持注释、多行文本
- ✅ Git 友好：diff 清晰，易于版本对比
- ✅ 结构清晰：层次分明
- ✅ 易于维护：独立文件，不混入代码

### 功能点4：LangSmith Dataset 管理

**问题**：手动测试提示词效果耗时且不够系统。

**解决方案**：创建标准化测试数据集，使用 LangSmith evaluate 自动评估。

```json
// examples/test_cases.json
[
  {
    "id": "test_001",
    "input": {
      "user_query": "生成AI行业报告",
      "topic": "人工智能",
      "style": "formal"
    },
    "expected_output": {
      "min_length": 2000,
      "must_include": ["技术创新", "市场规模"]
    }
  }
]
```

**评估流程**：
1. 创建数据集到 LangSmith
2. 定义评估器（格式、长度、质量）
3. 运行评估，获取分数
4. 对比不同版本效果

### 功能点5：PromptManager 自动化管理

**问题**：手动上传下载提示词繁琐，多人协作容易出现版本冲突。

**解决方案**：实现 PromptManager 自动化管理系统。

**核心理念**：远程是唯一真相源

```python
# 自动拉取（默认行为）
manager = PromptManager()
config = manager.get('parameter_parser')
# → 自动从 Hub 同步最新版本

# 手动推送
manager.push('parameter_parser')
# → 验证 → 测试 → 推送到 Hub
```

**4步推送流程**：
1. **验证格式** - 检查 YAML 格式正确性
2. **自动测试** - 运行 LangSmith 评估，计算质量分数
3. **推送到 Hub** - 更新远程版本
4. **创建备份** - 可选的版本快照

### 功能点6：LangSmith 追踪与调试

**问题**：AI 应用的执行过程像黑盒，难以调试和优化。

**解决方案**：使用 LangSmith 自动追踪每次执行。

**可查看的信息**：
- 📥 **输入参数**：所有传入的参数和变量
- 🔄 **中间步骤**：每个节点的执行过程
- 📤 **输出结果**：最终生成的内容
- ⏱️ **性能数据**：执行时间、Token 使用量
- 🎯 **质量评分**：评估器的打分结果

**使用方式**：
```python
# 自动追踪（默认开启）
python main.py --query "生成报告"

# 查看追踪
# → 访问 https://smith.langchain.com/
```

### 功能点7：提示词版本管理策略

**问题**：如何管理提示词的多个版本？保留所有历史版本还是只保留最新？

**解决方案**：本地只保留最新版本，历史版本通过 Hub 管理。

**版本命名规则**：
- 主版本：`parameter_parser`（Hub 上的当前版本）
- 历史版本：`parameter_parser-v1.0.0`（Hub 上的备份）
- 本地文件：`parameter_parser.yaml`（无版本号）

**版本迭代流程**：
```bash
# 1. 修改本地文件
vim prompts/parameter_parser.yaml

# 2. 测试效果
python main.py --query "测试"

# 3. 推送到 Hub（可选创建备份）
python -c "
from prompts.prompt_manager import PromptManager
manager = PromptManager()
manager.push('parameter_parser', create_backup=True)
"

# 4. 其他人自动拉取最新版本
# （下次运行时自动同步）
```

---

## 快速开始

### 1. 环境配置

```bash
# 克隆项目
cd Langsmith-prompt-pipeline

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export AZURE_OPENAI_API_KEY="your-key"
export LANGSMITH_API_KEY="your-key"
export PERPLEXITY_API_KEY="your-key"
```

### 2. 生成第一份报告

```bash
python main.py --query "人工智能行业2024年发展分析"
```

### 3. 查看 LangSmith 追踪

访问 https://smith.langchain.com/ 查看完整的执行过程。

### 4. 使用 PromptManager

```python
from prompts.prompt_manager import PromptManager

# 初始化（自动拉取最新版本）
manager = PromptManager()

# 加载提示词
config = manager.get('parameter_parser')
prompt = manager.create_chat_prompt(config)

# 使用提示词
messages = prompt.format_messages(
    user_query="生成AI报告",
    topic="人工智能",
    style="formal"
)
```

---

## 项目结构

```
Langsmith-prompt-pipeline/
├── prompts/                           # 📝 提示词管理
│   ├── prompt_manager.py             # PromptManager 核心代码
│   ├── prompts_config.yaml           # 提示词配置
│   ├── parameter_parser.yaml         # 参数解析提示词
│   ├── report_generator.yaml         # 报告生成提示词
│   ├── example_usage.py              # 使用示例
│   ├── PROMPT_MANAGER_GUIDE.md       # 详细使用指南
│   └── .versions/                    # 版本信息（自动生成）
│
├── graph/                             # 🔄 LangGraph 工作流
│   ├── state.py                      # 状态定义
│   ├── nodes.py                      # 节点实现
│   └── graph.py                      # Graph 构建
│
├── evaluation/                        # 📊 评估系统
│   ├── datasets.py                   # 数据集管理
│   └── evaluators.py                 # 评估器
│
├── tools/                             # 🔧 工具模块
│   └── search_tool.py                # Perplexity 搜索
│
├── config/                            # ⚙️ 配置模块
│   ├── azure_config.py               # Azure OpenAI 配置
│   └── langsmith_config.py           # LangSmith 配置
│
├── examples/                          # 📋 测试数据
│   └── test_cases.json               # 测试用例
│
├── main.py                            # 🎯 主程序入口
├── requirements.txt                   # 📦 依赖包
└── README.md                          # 📖 本文档
```

---

## 核心功能演示

### 功能1：多参数报告生成

```bash
# 正式风格的深度分析
python main.py \
  --query "金融科技行业分析" \
  --year-range "2023-2024" \
  --style formal \
  --depth deep \
  --focus-areas "数字支付,区块链,智能投顾"

# 简洁风格的快速概览
python main.py \
  --query "AI市场趋势" \
  --style concise \
  --depth shallow
```

### 功能2：提示词自动测试

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 运行 LangSmith 自动测试
result = manager.test_with_langsmith('parameter_parser')

print(f"质量分数: {result['quality_score']:.2%}")
print(f"测试用例: {result['total']}")

# 输出示例：
# 质量分数: 92%
# 测试用例: 5
```

### 功能3：提示词版本管理

```python
from prompts.prompt_manager import PromptManager

manager = PromptManager()

# 检查同步状态
manager.check_sync('parameter_parser')

# 查看历史版本
versions = manager.list_versions('parameter_parser')

# 回滚到指定版本
manager.rollback('parameter_parser', 'v1.0.0')
```

### 功能4：提示词推送与同步

```python
# 修改本地文件后推送
manager = PromptManager()

# 推送并自动测试
result = manager.push('parameter_parser', with_test=True)

# 推送并创建版本备份
result = manager.push('parameter_parser', create_backup=True)
```

---

## 使用场景

### 场景1：团队协作

**开发者 A**：
```bash
# 修改提示词
vim prompts/parameter_parser.yaml

# 推送到 Hub
python -c "
from prompts.prompt_manager import PromptManager
manager = PromptManager()
manager.push('parameter_parser')
"
```

**开发者 B**：
```bash
# 运行程序（自动拉取 A 的修改）
python main.py --query "测试"
# → 自动从 Hub 同步最新版本
```

### 场景2：A/B 测试

```bash
# 测试不同风格的效果
python main.py --query "AI报告" --style formal > formal.txt
python main.py --query "AI报告" --style casual > casual.txt

# 对比效果，选择最优
diff formal.txt casual.txt
```

### 场景3：提示词优化迭代

```python
# 1. 评估当前版本
result_v1 = manager.test_with_langsmith('report_generator')
print(f"v1 质量分: {result_v1['quality_score']}")

# 2. 修改提示词（优化 system message）

# 3. 重新测试
result_v2 = manager.test_with_langsmith('report_generator')
print(f"v2 质量分: {result_v2['quality_score']}")

# 4. 如果提升，推送新版本
if result_v2['quality_score'] > result_v1['quality_score']:
    manager.push('report_generator', create_backup=True)
```

---

## LangSmith 完整工作流

### 1. 创建测试数据集

```python
from evaluation.datasets import DatasetManager

dm = DatasetManager()

# 从 JSON 创建数据集
dm.create_dataset_from_json('test_cases', 'examples/test_cases.json')
```

### 2. 定义评估器

```python
from langsmith.evaluation import run_evaluator, EvaluationResult

@run_evaluator
def format_check(run, example):
    """检查输出格式"""
    output = run.outputs.get("report", "")
    has_content = len(output) > 500
    return EvaluationResult(
        key="format_check",
        score=1.0 if has_content else 0.0
    )
```

### 3. 运行评估

```python
from langsmith.evaluation import evaluate

# 评估函数
def test_function(inputs):
    # 使用提示词生成输出
    config = manager.get('report_generator')
    prompt = manager.create_chat_prompt(config)
    # ...
    return {"report": generated_report}

# 运行评估
results = evaluate(
    test_function,
    data="test_cases",
    evaluators=[format_check, length_check, quality_check]
)
```

### 4. 查看结果

访问 LangSmith UI：
- **Datasets**: 管理测试数据集
- **Experiments**: 查看评估结果
- **Traces**: 查看详细执行过程
- **Hub**: 管理提示词版本

---

## 进阶配置

### 自定义评估器

```python
# evaluation/evaluators.py

@staticmethod
@run_evaluator
def custom_evaluator(run, example) -> EvaluationResult:
    """自定义评估逻辑"""
    output = run.outputs.get("report", "")
    
    # 你的评估逻辑
    score = calculate_score(output)
    
    return EvaluationResult(
        key="custom_metric",
        score=score,
        comment="评估说明"
    )
```

### 添加新的提示词

```yaml
# prompts/new_prompt.yaml
_type: chat_prompt
name: new_prompt
version: v1.0

messages:
  - role: system
    content: |
      系统指令...
  
  - role: human
    content: |
      任务描述...

input_variables:
  - param1
  - param2
```

```yaml
# prompts/prompts_config.yaml
prompts:
  new_prompt:
    file: new_prompt.yaml
    hub_name: new_prompt
    test_dataset: test_cases
    min_quality_score: 0.8
```

---

## 核心 API 参考

### PromptManager

```python
class PromptManager:
    def __init__(self, auto_pull=True):
        """初始化，auto_pull 控制是否自动从 Hub 拉取"""
    
    def get(self, prompt_name: str) -> Dict:
        """加载提示词配置（自动拉取最新版本）"""
    
    def push(self, prompt_name: str, 
             with_test=True, 
             create_backup=False) -> bool:
        """推送本地修改到 Hub"""
    
    def test_with_langsmith(self, prompt_name: str) -> Dict:
        """使用 LangSmith 自动测试提示词质量"""
    
    def check_sync(self, prompt_name: str):
        """检查本地和远程的同步状态"""
    
    def list_versions(self, prompt_name: str) -> List[str]:
        """列出所有历史版本"""
    
    def rollback(self, prompt_name: str, version: str):
        """回滚到指定版本"""
    
    def create_chat_prompt(self, config: Dict) -> ChatPromptTemplate:
        """从配置创建 ChatPromptTemplate"""
```

---

## 最佳实践

### ✅ 推荐做法

1. **保持 auto_pull=True** - 始终使用最新版本
2. **推送前先测试** - 使用 `with_test=True` 确保质量
3. **重要版本创建备份** - 使用 `create_backup=True`
4. **本地为主要修改源** - 避免在 Hub 网页直接修改
5. **使用 System/Human 分离** - 遵循 ChatPromptTemplate 标准

### ❌ 避免做法

1. ~~在 Hub 网页上直接修改~~
2. ~~跳过测试直接推送~~
3. ~~提示词中混合系统指令和用户任务~~
4. ~~多人同时修改同一提示词~~

---

## 常见问题

### Q1: 如何禁用自动拉取？

```python
# 临时禁用（用于本地测试）
manager = PromptManager(auto_pull=False)
```

### Q2: 推送失败怎么办？

检查清单：
1. YAML 格式是否正确
2. LangSmith API Key 是否有效
3. 网络连接是否正常
4. 测试分数是否达标

### Q3: 如何查看提示词在 LangSmith 中的表现？

访问 https://smith.langchain.com/
- **Projects** → 查看追踪
- **Datasets** → 管理测试数据
- **Hub** → 查看提示词版本

### Q4: 多人修改冲突如何处理？

```python
# 修改前检查同步状态
manager.check_sync('parameter_parser')

# 如果有人更新，先拉取
config = manager.get('parameter_parser')  # 自动拉取

# 合并修改后推送
manager.push('parameter_parser')
```

---

## 相关文档

- **`prompts/PROMPT_MANAGER_GUIDE.md`** - PromptManager 详细使用指南
- **`prompts/example_usage.py`** - 完整使用示例
- **`FINAL_IMPLEMENTATION_REPORT.md`** - 实施总结报告

---

## 总结

本项目展示了一个**生产级的提示词管理系统**，包含：

✅ **标准化架构** - ChatPromptTemplate、YAML 格式、版本管理  
✅ **自动化工作流** - 自动拉取、自动测试、一键推送  
✅ **完整 LangSmith 集成** - 追踪、评估、数据集、Hub  
✅ **团队协作友好** - 零手动同步，自动最新  
✅ **最佳实践应用** - 2025年 LangChain/LangSmith 标准  

**核心价值**：
- 🎯 学习如何优雅地管理提示词
- 📊 掌握 LangSmith 完整工作流
- 🔄 实践提示词迭代优化
- 🤝 团队协作最佳实践

---

## 许可证

---