# Evaluator 同步更新方案

## 一、现有代码问题分析

### 1.1 当前 Evaluator 管理方式
**文件位置**：
- `evaluation/evaluators/parameter.py` (行 1-207)
- `evaluation/evaluators/report.py` (行 1-277)
- `evaluation/evaluators/__init__.py` (行 1-74)

**问题**：
1. **缺少统一管理**：Evaluator 分散在多个文件中，没有像 `prompt_manager.py` 那样的统一管理接口
2. **无法同步到平台**：无法像 prompt 一样通过 Hub 自动同步到 LangSmith 平台
3. **没有版本管理**：修改 evaluator 后无法追踪版本变化
4. **手动配置繁琐**：在 LangSmith Web UI 中需要手动创建 "Custom code" evaluator，无法自动化

### 1.2 与 Prompt 同步机制对比

| 功能 | Prompt Manager | Evaluator (当前) |
|------|----------------|------------------|
| 统一管理 | ✅ `prompt_manager.py` | ❌ 无 |
| Hub 同步 | ✅ `hub.push()` / `hub.pull()` | ❌ 无 |
| 自动拉取 | ✅ `auto_pull=True` | ❌ 无 |
| 版本管理 | ✅ 版本号追踪 | ❌ 无 |
| 配置化 | ✅ YAML 配置 | ⚠️ Python 代码直接编写 |

## 二、解决方案

### 2.1 使用 LangSmith Evaluator API

根据 LangSmith 官方文档，evaluator 可以通过以下方式管理：

1. **代码 Evaluator (Custom Code)**：
   - 支持上传 Python 代码到平台
   - 可通过 API 创建和管理
   - 参考：https://docs.langsmith.com/api/evaluators

2. **同步策略**：
   - 将本地 Python evaluator 函数转换为字符串
   - 通过 LangSmith Client API 创建/更新 evaluator
   - 实现类似 prompt 的 push/pull 机制

### 2.2 新架构设计

```
evaluation/
├── evaluators/
│   ├── __init__.py          # 注册表（保持不变）
│   ├── parameter.py          # 参数评估器（保持不变）
│   └── report.py             # 报告评估器（保持不变）
├── evaluator_manager.py      # ⭐ 新增：统一管理 evaluator
└── evaluators_config.yaml    # ⭐ 新增：evaluator 配置（类似 prompts_config.yaml）
```

### 2.3 核心功能

1. **EvaluatorManager 类**（类似 PromptManager）：
   - `push()` - 推送本地 evaluator 到 LangSmith
   - `pull()` - 从 LangSmith 拉取最新 evaluator
   - `list()` - 列出所有 evaluator
   - `validate()` - 验证 evaluator 格式

2. **Evaluator 配置化**：
   - 创建 `evaluators_config.yaml` 存储 evaluator 元数据
   - 包含：名称、描述、对应的数据集、版本等

3. **代码提取与转换**：
   - 从 Python 文件中提取 evaluator 函数
   - 转换为可执行的代码字符串
   - 上传到 LangSmith 作为 "Custom code" evaluator

## 三、实现步骤

### 步骤 1：创建 EvaluatorManager 基础框架
**文件**：`evaluation/evaluator_manager.py`
**功能**：
- 读取 evaluator 函数
- 提取函数代码
- 生成 evaluator 配置

### 步骤 2：实现 LangSmith API 集成
**功能**：
- 使用 LangSmith Client 创建/更新 evaluator
- 处理 evaluator 的创建和同步

### 步骤 3：创建配置文件
**文件**：`evaluation/evaluators_config.yaml`
**内容**：
- evaluator 列表
- 对应的数据集
- 版本信息

### 步骤 4：添加同步命令
**集成到**：`prompt_manager.py` 或独立的命令行工具
**功能**：
- `python -m evaluation.evaluator_manager push <evaluator_name>`
- `python -m evaluation.evaluator_manager pull <evaluator_name>`

### 步骤 5：测试与验证
- 测试单个 evaluator 上传
- 测试同步功能
- 验证在 LangSmith Web UI 中可见

## 四、修改后的架构

```
prompts/
├── prompt_manager.py         # Prompt 管理（已有）
└── prompts_config.yaml       # Prompt 配置（已有）

evaluation/
├── evaluator_manager.py      # ⭐ Evaluator 管理（新增，对称设计）
├── evaluators_config.yaml   # ⭐ Evaluator 配置（新增）
├── evaluation.py            # 评估运行器（保持，可能调用 manager）
└── evaluators/              # Evaluator 源码（保持不变）
    ├── __init__.py
    ├── parameter.py
    └── report.py
```

## 五、TODO

- [ ] 创建 `evaluator_manager.py` 基础类
- [ ] 实现代码提取功能（从 Python 文件提取函数）
- [ ] 实现 LangSmith API 调用（创建/更新 evaluator）
- [ ] 创建 `evaluators_config.yaml` 配置文件
- [ ] 添加同步命令（push/pull）
- [ ] 编写测试脚本
- [ ] 更新文档说明使用方法

## 六、注意事项

1. **API 限制**：LangSmith Evaluator API 可能不如 Prompt Hub 成熟，需要验证实际可用性
2. **代码格式**：需要确保提取的代码字符串格式正确，包含必要的导入
3. **依赖管理**：Custom code evaluator 需要包含所有依赖，可能需要打包处理
4. **版本兼容**：确保与现有 evaluator 使用方式兼容

