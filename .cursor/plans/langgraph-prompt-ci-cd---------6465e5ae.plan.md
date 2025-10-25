<!-- 6465e5ae-2c9c-4fc7-a90d-4e8d26838a57 98d4c91a-fabc-455a-a5d8-d51b0b6765bc -->
# PromptManager 极简自动化方案

## 一、核心理念

**远程是唯一真相源，极简设计**

- Hub 上每个 Prompt 只有一个版本（不带后缀）
- 本地 YAML 是工作副本
- 默认行为：自动从 Hub 拉取
- 手动操作：显式推送到 Hub
- 不区分环境（生产部署是独立流程）

## 二、核心工作流程

### 场景A：日常使用（自动同步）

**只需运行程序，自动拉取最新版本**

1. 程序启动
2. PromptManager 自动检测 Hub 是否有更新
3. 有更新 → 自动下载到本地
4. 使用最新版本

**用户无感知，完全自动化**

### 场景B：修改 Prompt（手动推送）

**修改 → 测试 → 推送**

1. 修改本地文件 `prompts/parameter_parser.yaml`
2. 本地测试（可选，禁用自动拉取）
3. 运行推送命令：`manager.push('parameter_parser')`
4. 自动验证 → 自动测试 → 推送到 Hub
5. 其他人下次使用时自动拉取到最新版

### 场景C：版本备份（可选）

**重要版本可以创建快照**

- 推送时可选择创建版本备份
- 备份名称：`parameter_parser-v1.0.0`
- 用于回滚或历史追溯

## 三、PromptManager 核心方法

### 方法1：自动拉取 `get()`

```
功能：加载 Prompt 配置，自动从 Hub 同步最新版本

参数：
- prompt_name: Prompt 名称（如 'parameter_parser'）

流程：
1. 检查 Hub 是否有这个 Prompt
2. 如果有 → 下载到本地（覆盖旧版本）
3. 如果没有 → 使用本地版本
4. 加载本地 YAML 文件
5. 返回配置字典

提示信息：
- "📥 从 Hub 同步: parameter_parser"
- "✅ 使用本地缓存"
```

### 方法2：手动推送 `push()`

```
功能：推送本地修改到 Hub

参数：
- prompt_name: Prompt 名称
- with_test: 是否运行测试（默认 True）
- create_backup: 是否创建版本备份（默认 False）

流程：
1. 验证 YAML 格式
2. （可选）运行 LangSmith 测试
3. 测试不通过 → 询问是否强制推送
4. 推送到 Hub（名称就是 prompt_name）
5. （可选）创建版本备份到 prompt_name-vX.X.X

返回：成功/失败
```

### 方法3：LangSmith 测试 `test_with_langsmith()`

```
功能：使用 LangSmith 自动测试 Prompt 质量

参数：
- prompt_name: Prompt 名称

流程：
1. 加载测试数据集
2. 使用多个评估器打分：
   - 格式检查（是否有 system/human 消息）
   - 长度检查（是否合理）
   - 变量检查（是否有未替换的变量）
   - 质量检查（内容质量评分）
3. 汇总结果，返回质量分数（0-1）

返回：TestResult（包含分数、详情、建议）
```

### 方法4：同步检查 `check_sync()`

```
功能：检查本地和远程的同步状态

参数：
- prompt_name: Prompt 名称

显示信息：
- 本地文件修改时间
- 远程版本信息
- 是否有未推送的本地修改
- 操作建议
```

### 方法5：版本管理 `list_versions()` 和 `rollback()`

```
list_versions(prompt_name):
  - 列出 Hub 上的所有版本备份
  - 返回版本号列表

rollback(prompt_name, version):
  - 从版本备份恢复
  - 推送到主版本
```

## 四、配置文件（极简版）

### prompts_config.yaml

```yaml
# 同步配置
sync:
  auto_pull: true              # 默认自动拉取（建议保持 true）
  
# Prompt 配置
prompts:
  parameter_parser:
    file: parameter_parser.yaml
    hub_name: "parameter_parser"     # Hub 上的名称（可选，默认用 key）
    test_dataset: "test_cases"       # 测试数据集名称
    min_quality_score: 0.8           # 最低质量要求
    
  report_generator:
    file: report_generator.yaml
    hub_name: "report_generator"
    test_dataset: "test_cases"
    min_quality_score: 0.85
```

**说明**：

- 不需要环境配置（已移除）
- Hub 名称就是 prompt 的 key，不带任何后缀
- 测试数据集用于 LangSmith 自动测试

## 五、完整使用示例

### 示例1：第一次使用

```python
from prompts.prompt_manager import PromptManager

# 初始化
manager = PromptManager()

# 加载 Prompt（自动从 Hub 下载）
config = manager.get('parameter_parser')
# 输出：📥 从 Hub 同步: parameter_parser
#      ✅ 已保存到: prompts/parameter_parser.yaml

# 创建 ChatPromptTemplate
prompt = manager.create_chat_prompt(config)

# 正常使用
messages = prompt.format_messages(user_query="测试")
```

### 示例2：日常使用

```python
manager = PromptManager()

# 加载（自动检查更新）
config = manager.get('parameter_parser')
# 输出：🔍 检查远程更新...
#      ✅ 使用本地缓存（已是最新）

# 如果 Hub 有更新：
# 输出：🔍 检查远程更新...
#      📥 检测到新版本，正在同步...
#      ✅ 已更新
```

### 示例3：修改并推送

```python
# 步骤1：修改本地文件
# vim prompts/parameter_parser.yaml

# 步骤2：本地测试（禁用自动拉取）
manager = PromptManager(auto_pull=False)
config = manager.get('parameter_parser')
# 测试修改效果...

# 步骤3：推送到 Hub
manager_online = PromptManager()  # 重新启用自动拉取
result = manager_online.push('parameter_parser')

# 输出：
# 📤 推送 parameter_parser 到 Hub...
# 📋 验证格式... ✅
# 🧪 运行 LangSmith 测试...
#    - 格式检查: ✅ 1.00
#    - 长度检查: ✅ 0.95
#    - 变量检查: ✅ 1.00
#    - 质量分数: 0.92
# 🚢 推送到 Hub... ✅
# ✅ 已推送到: parameter_parser
#    查看: https://smith.langchain.com/hub/parameter_parser
```

### 示例4：创建版本备份

```python
manager = PromptManager()

# 推送并创建备份
manager.push(
    'parameter_parser',
    with_test=True,
    create_backup=True  # 创建版本备份
)

# 输出：
# ... 正常的推送流程 ...
# 💾 创建版本备份...
# ✅ 已备份到: parameter_parser-v1.2.0
```

### 示例5：检查同步状态

```python
manager = PromptManager()

# 检查状态
manager.check_sync('parameter_parser')

# 输出：
# 📊 同步状态: parameter_parser
#
# 本地版本:
#   文件: prompts/parameter_parser.yaml
#   修改时间: 2025-10-25 15:30:00
#   大小: 2.5 KB
#
# 远程版本 (Hub):
#   名称: parameter_parser
#   状态: ✅ 存在
#
# 同步状态: ✅ 已同步
# 建议: 无需操作
```

### 示例6：回滚到历史版本

```python
manager = PromptManager()

# 查看历史版本
versions = manager.list_versions('parameter_parser')
print(versions)
# ['v1.2.0', 'v1.1.0', 'v1.0.0']

# 回滚到 v1.1.0
manager.rollback('parameter_parser', 'v1.1.0')

# 输出：
# 🔄 回滚 parameter_parser 到 v1.1.0
# 📥 从 Hub 拉取: parameter_parser-v1.1.0
# 🚢 推送到: parameter_parser
# ✅ 回滚完成
```

## 六、LangSmith 自动测试详解

### 测试原理

**使用 LangSmith 的 evaluate 功能自动打分**

1. **测试数据集**：一组测试输入（存储在 LangSmith）
2. **评估器**：多个打分标准（格式、长度、质量等）
3. **测试运行**：用每个测试输入运行 Prompt，评估器打分
4. **结果汇总**：计算平均分和通过率

### 内置评估器

**评估器1：格式检查**

- 检查是否是 ChatPromptTemplate 格式
- 是否有 system 和 human 消息
- 分数：符合标准 = 1.0，不符合 = 0.5

**评估器2：长度检查**

- 检查 Prompt 长度是否合理（500-5000字符）
- 太短或太长都扣分
- 分数：0.0 - 1.0

**评估器3：变量检查**

- 检查是否有未替换的变量（如 `{variable}`）
- 有未替换变量 = 0.0，全部替换 = 1.0

**评估器4：质量检查**（可选，使用 LLM）

- 使用 LLM 评估 Prompt 的连贯性和清晰度
- 分数：0.0 - 1.0

### 测试数据集配置

在 `examples/test_cases.json` 中定义测试用例：

```json
[
  {
    "inputs": {
      "user_query": "生成一份关于人工智能的报告",
      "topic": "人工智能",
      "year_range": "2024",
      "style": "formal",
      "depth": "medium"
    }
  },
  {
    "inputs": {
      "user_query": "分析金融科技行业",
      "topic": "金融科技",
      "year_range": "2023-2024",
      "style": "detailed",
      "depth": "deep"
    }
  }
]
```

首次使用时，PromptManager 会自动在 LangSmith 创建这个数据集。

## 七、团队协作流程

### 开发者 A：修改 Prompt

```
1. 修改本地 YAML 文件
2. 本地测试效果
3. 推送到 Hub: manager.push('parameter_parser')
```

### 开发者 B：自动获取最新版本

```
1. 运行程序
2. PromptManager 自动从 Hub 拉取 A 的修改
3. 看到最新版本，无需手动操作
```

### 多人并发修改

```
如果多人同时修改：
- 后推送的人会覆盖先推送的
- 建议：修改前先运行 check_sync() 确认是否有人更新
- 如果有冲突，先拉取，合并修改，再推送
```

## 八、实施步骤

### 阶段1：实现自动拉取（2-3小时）

**任务：**

1. 实现 `_auto_pull_if_needed()` 方法
2. 从 Hub 拉取 Prompt
3. 转换为 YAML 格式并保存
4. 集成到 `get()` 方法
5. 测试拉取功能

**验收标准：**

- 首次运行能从 Hub 下载
- 后续运行能检测更新
- 显示清晰的提示信息

### 阶段2：实现手动推送（2-3小时）

**任务：**

1. 实现 `push()` 方法
2. 集成格式验证
3. 推送到 Hub（使用 `hub.push()`）
4. 添加版本备份功能
5. 测试推送功能

**验收标准：**

- 能成功推送到 Hub
- 验证失败时阻止推送
- 可选择创建版本备份

### 阶段3：集成 LangSmith 测试（3-4小时）

**任务：**

1. 实现 `test_with_langsmith()` 方法
2. 创建 4 个内置评估器
3. 自动创建/加载测试数据集
4. 汇总测试结果
5. 集成到 `push()` 流程

**验收标准：**

- 能在 LangSmith UI 看到测试结果
- 评估器正确打分
- 低分时能阻止或警告

### 阶段4：完善辅助功能（1-2小时）

**任务：**

1. 实现 `check_sync()` 方法
2. 实现 `list_versions()` 方法
3. 实现 `rollback()` 方法
4. 简化配置文件

**验收标准：**

- 能查看同步状态
- 能列出和回滚版本
- 配置文件简洁明了

### 阶段5：文档和示例（1小时）

**任务：**

1. 更新使用文档
2. 编写完整示例
3. 记录最佳实践

## 九、核心优势

### 优势1：极简设计

- 只有一个版本，不区分环境
- 方法签名简单，无复杂参数
- 配置文件精简

### 优势2：自动同步

- 默认行为就是最新版本
- 多设备无缝切换
- 团队协作零摩擦

### 优势3：安全可控

- 推送是显式操作
- 自动测试保证质量
- 支持版本备份和回滚

### 优势4：零学习成本

- 就两个核心操作：自动拉取、手动推送
- 类似 Git pull/push
- 简单直观

## 十、总结

### 核心理念

**"远程是真相，本地是镜像，极简至上"**

### 使用方式

```python
# 使用（自动拉取）
config = manager.get('parameter_parser')

# 修改后推送
manager.push('parameter_parser')

# 就这么简单！
```

### 预期收益

- ✅ 永远使用最新版本
- ✅ 多设备无缝切换
- ✅ 团队协作简单
- ✅ 质量自动保障
- ✅ 极简易用

### To-dos

- [ ] 实现自动拉取：从 Hub 下载 Prompt，转换为 YAML 格式，保存到本地
- [ ] 实现手动推送：验证格式、可选测试、推送到 Hub、可选版本备份
- [ ] 集成 LangSmith 自动测试：创建评估器、运行测试、汇总结果
- [ ] 实现辅助方法：check_sync、list_versions、rollback
- [ ] 简化配置文件：移除环境配置，只保留必要配置
- [ ] 编写完整文档和使用示例

### To-dos

- [ ] 实现自动拉取：从 Hub 下载并保存为 YAML
- [ ] 实现手动推送：验证、测试、推送到 Hub
- [ ] 集成 LangSmith 测试：评估器、数据集、结果汇总
- [ ] 实现辅助功能：同步检查、版本管理、回滚
- [ ] 简化配置文件：移除环境配置
- [ ] 编写文档和示例