# Dataset 捕获装饰器使用指南

## 概述

`@capture_dataset` 装饰器可以自动捕获 LLM 节点的输入参数，并选择性地推送到 LangSmith Dataset。

## 核心参数

```python
@capture_dataset(
    prompt_name: str,           # 提示词名称
    dataset_name: str,          # Dataset 名称（推荐与 prompt_name 相同）
    capture_output: bool = True,  # 是否捕获输出
    auto_sync: bool = True      # 🔑 是否自动推送到 LangSmith
)
```

### auto_sync 参数详解

| 值 | 行为 | 适用场景 |
|----|------|---------|
| `True` (默认) | 运行后**立即推送**到 LangSmith | 日常开发、快速迭代 |
| `False` | 只保存到本地 `.dataset_cache/` | 离线开发、批量收集后统一推送 |

## 快速开始

### 方式 1：自动推送（推荐）

```python
from tools.capture import capture_dataset, capture_inputs

@traceable
@capture_dataset(
    prompt_name="report_generator",
    dataset_name="report_generator",
    auto_sync=True  # 默认值，可省略
)
def generate_report_node(self, state: ReportState):
    # 准备 LLM 输入参数
    inputs = {
        "topic": state.get("topic", ""),
        "year_range": state.get("year_range", ""),
        "style": state.get("style", "formal"),
        "depth": state.get("depth", "medium"),
        "focus_areas": state.get("focus_areas", ""),
        "search_results": state.get("search_results_formatted", "")
    }
    
    # 显式标记捕获（推荐）
    capture_inputs(inputs, metadata={"user_query": state.get("user_query")})
    
    # 调用 LLM
    chain = prompt | self.llm | StrOutputParser()
    report = chain.invoke(inputs)
    
    return {"report": report}
```

**效果**：
- ✅ 数据保存到本地：`.dataset_cache/report_generator/run_xxx.json`
- ✅ **立即推送到 LangSmith**：`report_generator` Dataset
- ✅ 无需手动运行 `dataset_sync.py`

### 方式 2：仅本地保存

```python
@traceable
@capture_dataset(
    prompt_name="report_generator",
    dataset_name="report_generator",
    auto_sync=False  # 关闭自动推送
)
def generate_report_node(self, state: ReportState):
    inputs = {...}
    capture_inputs(inputs)
    ...
```

**效果**：
- ✅ 数据保存到本地：`.dataset_cache/report_generator/run_xxx.json`
- ❌ 不推送到 LangSmith
- 📌 需要时手动运行：`python tools/dataset_sync.py`

## 完整示例

### 示例 1：两个节点，都自动推送

```python
class ReportNodes:
    def __init__(self):
        self.llm = AzureConfig.get_llm()
        self.fast_llm = AzureConfig.get_fast_llm()
        self.prompt_manager = PromptManager()
    
    @traceable
    @capture_dataset(
        prompt_name="parameter_parser",
        dataset_name="parameter_parser"  # auto_sync=True 默认
    )
    def parse_parameters_node(self, state):
        inputs = {"user_query": state.get("user_query", "")}
        capture_inputs(inputs)
        
        prompt = self.prompt_manager.create_chat_prompt(...)
        response = self.fast_llm.invoke(prompt.format_messages(**inputs))
        ...
    
    @traceable
    @capture_dataset(
        prompt_name="report_generator",
        dataset_name="report_generator"  # auto_sync=True 默认
    )
    def generate_report_node(self, state):
        inputs = {
            "topic": state.get("topic", ""),
            "style": state.get("style", "formal"),
            ...
        }
        capture_inputs(inputs, metadata={"user_query": state.get("user_query")})
        
        chain = prompt | self.llm | StrOutputParser()
        report = chain.invoke(inputs)
        ...
```

**运行一次流程**：
```bash
python main.py --query "生成AI行业报告"
```

**自动创建两个 Dataset**：
- ✅ `parameter_parser` Dataset（包含 `user_query` 参数）
- ✅ `report_generator` Dataset（包含 `topic`, `style` 等参数）

### 示例 2：混合模式

```python
# parameter_parser: 自动推送
@capture_dataset(
    prompt_name="parameter_parser",
    dataset_name="parameter_parser",
    auto_sync=True
)
def parse_parameters_node(self, state):
    ...

# report_generator: 仅本地保存
@capture_dataset(
    prompt_name="report_generator",
    dataset_name="report_generator",
    auto_sync=False  # 先收集，稍后批量推送
)
def generate_report_node(self, state):
    ...
```

**场景**：
- `parameter_parser` 数据少且重要，立即推送
- `report_generator` 数据多，先本地收集，测试完再推送

## 工作流程

### 自动推送模式（auto_sync=True）

```
运行流程
  ↓
捕获 inputs
  ↓
保存到本地 (.dataset_cache/)
  ↓
立即推送到 LangSmith ✨
  ↓
完成
```

**控制台输出**：
```
[Capture] 已保存: parameter_parser → run_20251027_143022.json
[Sync] 已同步到 LangSmith: parameter_parser
```

### 本地保存模式（auto_sync=False）

```
运行流程
  ↓
捕获 inputs
  ↓
保存到本地 (.dataset_cache/)
  ↓
完成（暂不推送）
```

**稍后手动推送**：
```bash
python tools/dataset_sync.py
```

## 在 Playground 中使用

1. **访问 LangSmith**：https://smith.langchain.com/datasets

2. **选择 Dataset**：
   - `parameter_parser`（包含 `user_query`）
   - `report_generator`（包含 `topic`, `style`, `depth` 等）

3. **打开 Playground**：
   - 选择对应的提示词
   - 从 Dataset 选择一个 example
   - **切换提示词版本** → inputs 自动匹配 ✅

4. **对比不同版本**：
   - 使用相同的测试数据
   - 测试不同提示词版本的效果
   - 选择最优版本

## 最佳实践

### ✅ 推荐做法

1. **每个提示词独立 Dataset**
   ```python
   # ✅ Good
   @capture_dataset(prompt_name="report_generator", dataset_name="report_generator")
   
   # ❌ Bad - 不同提示词共用同一个 Dataset
   @capture_dataset(prompt_name="report_generator", dataset_name="shared_dataset")
   @capture_dataset(prompt_name="parameter_parser", dataset_name="shared_dataset")
   ```

2. **日常开发用自动推送**
   ```python
   # 开发阶段：auto_sync=True（默认）
   @capture_dataset(prompt_name="xxx", dataset_name="xxx")
   ```

3. **显式调用 capture_inputs**
   ```python
   # ✅ 清晰明确
   inputs = {...}
   capture_inputs(inputs, metadata={...})
   chain.invoke(inputs)
   ```

4. **合理使用 metadata**
   ```python
   capture_inputs(inputs, metadata={
       "user_query": state.get("user_query"),  # 原始查询
       "prompt_version": prompt_config.get("version"),  # 提示词版本
       "scenario": "production"  # 场景标记
   })
   ```

### ⚠️ 注意事项

1. **自动推送会增加延迟**
   - 每次捕获都会调用 LangSmith API
   - 通常延迟 < 100ms，可接受

2. **网络异常不影响主流程**
   ```python
   # 同步失败只会打印警告，不会中断流程
   [WARN] 自动同步失败: Network error
   ```

3. **离线开发时关闭自动推送**
   ```python
   @capture_dataset(..., auto_sync=False)
   ```

## 常见场景

### 场景 1：快速迭代提示词

```python
# 自动推送，立即在 Playground 查看
@capture_dataset(prompt_name="xxx", dataset_name="xxx", auto_sync=True)
```

**流程**：
1. 修改提示词
2. 运行测试：`python main.py --query "测试"`
3. 立即去 Playground 查看效果
4. 继续迭代

### 场景 2：批量收集测试数据

```python
# 先本地收集，统一推送
@capture_dataset(prompt_name="xxx", dataset_name="xxx", auto_sync=False)
```

**流程**：
1. 运行多次测试收集数据：
   ```bash
   for i in {1..20}; do
     python main.py --query "测试场景 $i"
   done
   ```

2. 查看数据：
   ```bash
   python tools/dataset_sync.py --list
   ```

3. 统一推送：
   ```bash
   python tools/dataset_sync.py
   ```

### 场景 3：生产环境关闭捕获

```python
import os

# 根据环境变量决定是否启用捕获
ENABLE_CAPTURE = os.getenv("ENABLE_DATASET_CAPTURE", "false").lower() == "true"

if ENABLE_CAPTURE:
    @capture_dataset(prompt_name="xxx", dataset_name="xxx")
    def my_node(self, state):
        ...
else:
    # 生产环境不捕获
    @traceable
    def my_node(self, state):
        ...
```

## 控制台输出说明

### 自动推送模式

```
[Capture] 已保存: parameter_parser → run_20251027_143022.json
[Sync] 已同步到 LangSmith: parameter_parser
```

### 仅本地模式

```
[Capture] 已保存: parameter_parser → run_20251027_143022.json
```

### 同步失败（不影响主流程）

```
[Capture] 已保存: parameter_parser → run_20251027_143022.json
[WARN] 自动同步失败: Authentication failed
```

## 故障排查

### Q: 自动推送失败怎么办？

**检查**：
1. `.env` 文件中 `LANGSMITH_API_KEY` 是否正确
2. 网络连接是否正常
3. 查看错误信息：`[WARN] 自动同步失败: ...`

**临时方案**：
```python
# 改为本地保存
@capture_dataset(..., auto_sync=False)

# 稍后手动推送
python tools/dataset_sync.py
```

### Q: 如何查看本地缓存？

```bash
# 查看缓存目录
ls -la .dataset_cache/

# 查看具体数据
cat .dataset_cache/report_generator/run_xxx.json | python -m json.tool

# 列出所有捕获
python tools/dataset_sync.py --list
```

### Q: 如何清理缓存？

```bash
# 删除所有本地缓存
rm -rf .dataset_cache/

# 只清理已同步的
python tools/dataset_sync.py --clean
```

## 参数速查表

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt_name` | str | 必需 | 提示词名称（如 "report_generator"） |
| `dataset_name` | str | "default" | Dataset 名称（推荐与 prompt_name 相同） |
| `capture_output` | bool | True | 是否捕获节点的输出结果 |
| `auto_sync` | bool | **True** | 🔑 **是否自动推送到 LangSmith** |

## 总结

### 🎯 核心优势

- **自动推送**：运行即上传，无需手动同步
- **灵活控制**：`auto_sync` 参数随时切换模式
- **不影响主流程**：同步失败不会中断程序
- **双重保险**：本地+远程都有备份

### 🚀 推荐配置

**日常开发**：
```python
@capture_dataset(prompt_name="xxx", dataset_name="xxx")  # auto_sync=True 默认
```

**批量收集**：
```python
@capture_dataset(prompt_name="xxx", dataset_name="xxx", auto_sync=False)
```

**生产环境**：不使用装饰器或设置环境变量控制

