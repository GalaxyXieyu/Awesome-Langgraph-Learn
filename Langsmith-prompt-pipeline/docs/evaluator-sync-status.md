# Evaluator 同步功能 - 当前状态

## 一、当前实现模式

### 1.1 **手动辅助模式**（当前）

由于 LangSmith Evaluator API 的具体方法需要进一步确认，当前实现采用**手动辅助模式**：

- ✅ **代码提取**：自动从本地 Python 文件提取 evaluator 源代码
- ✅ **配置管理**：通过 `evaluators_config.yaml` 管理所有 evaluator
- ✅ **验证功能**：验证代码语法和配置完整性
- ⚠️ **API 集成**：如果 LangSmith API 不支持直接创建，会输出源代码供手动上传

### 1.2 工作流程

```
本地 Python 文件
    ↓
EvaluatorManager 提取代码
    ↓
尝试通过 API 上传
    ↓
    ├─ 成功 → 自动同步到平台 ✅
    └─ 失败 → 输出源代码，手动上传 ⚠️
```

## 二、当前可用的功能

### 2.1 基础功能（已实现）

```bash
# 1. 列出所有 evaluators
python -m evaluation.evaluator_manager list --name dummy

# 2. 验证 evaluator
python -m evaluation.evaluator_manager validate --name structure_evaluator

# 3. 推送 evaluator（会尝试 API，失败则输出源代码）
python -m evaluation.evaluator_manager push --name structure_evaluator --dataset report_generator
```

### 2.2 代码提取功能

✅ **已测试通过**：
- 可以正确提取所有 6 个 evaluators 的源代码
- 自动处理类方法的缩进问题
- 保留装饰器（如 `@run_evaluator`）
- 包含必要的导入语句

### 2.3 配置管理

✅ **配置文件**：`evaluation/evaluators_config.yaml`
- 已注册 6 个 evaluators
- 包含文件路径、类名、描述、数据集关联

## 三、与 Prompt Manager 的对比

| 功能 | Prompt Manager | Evaluator Manager (当前) |
|------|----------------|-------------------------|
| **配置文件** | ✅ `prompts_config.yaml` | ✅ `evaluators_config.yaml` |
| **代码提取** | ❌ (YAML 格式) | ✅ (Python 代码) |
| **Hub 推送** | ✅ `hub.push()` | ⚠️ 需要确认 API |
| **自动拉取** | ✅ `auto_pull=True` | ❌ (代码本地管理) |
| **版本管理** | ✅ 支持 | 🔄 待完善 |

## 四、使用方式

### 方式 1：尝试自动推送（推荐先试这个）

```bash
cd Langsmith-prompt-pipeline
python -m evaluation.evaluator_manager push --name structure_evaluator --dataset report_generator
```

**结果**：
- 如果 LangSmith API 支持 → 自动同步 ✅
- 如果 API 不支持 → 输出源代码到文件和终端，手动上传 ⚠️

### 方式 2：手动上传（如果 API 不支持）

如果自动推送失败，会看到：

```
[WARN] LangSmith API 调用失败: ...
源代码已准备好，可以手动上传:
  - 访问: https://smith.langchain.com/datasets/report_generator/evaluators
  - 选择 'Create Custom Code Evaluator'
  - 粘贴以下代码:
```

然后：
1. 打开 LangSmith Web UI
2. 进入对应数据集 → Evaluators
3. 点击 "Create Custom Code Evaluator"
4. 粘贴输出的源代码

### 方式 3：查看提取的源代码

源代码会自动保存到：`evaluation/{evaluator_name}_source.py`

```bash
# 查看提取的源代码
cat evaluation/structure_evaluator_source.py
```

## 五、下一步优化方向

### 5.1 确认 LangSmith API

需要确认 LangSmith Client 是否有以下方法：
- `client.create_evaluator()` 
- `client.update_evaluator()`
- `client.list_evaluators()`

如果 API 不同，需要根据实际文档调整 `_create_or_update_evaluator()` 方法。

### 5.2 完善功能

- [ ] 实现 `pull()` 方法（从平台拉取元数据）
- [ ] 添加版本管理（类似 prompt 的版本号）
- [ ] 支持批量推送所有 evaluators
- [ ] 添加自动发现功能（扫描目录自动注册）

### 5.3 测试验证

- [ ] 在实际 LangSmith 平台上测试 API 调用
- [ ] 验证手动上传的代码能否正常运行
- [ ] 测试与数据集的关联是否正常

## 六、总结

**当前状态**：✅ **核心功能已完成，API 集成待确认**

- ✅ 代码提取：工作正常
- ✅ 配置管理：已实现
- ✅ 验证功能：已实现
- ⚠️ API 集成：需要确认 LangSmith 实际 API 方法

**建议**：
1. 先尝试 `push` 命令，看是否能自动同步
2. 如果失败，查看输出的源代码文件，手动上传到平台
3. 根据实际 API 文档调整 `_create_or_update_evaluator()` 方法

