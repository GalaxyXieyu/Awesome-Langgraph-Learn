# 多 LLM 流程调试方案

## 问题描述

在多个 LLM 串联的流程中（如：参数解析 → 搜索 → 报告生成），想在 Playground 单独调试某个环节时，该环节的输入依赖上游 LLM 的输出，导致：

**痛点**：
- ❌ 每次切换提示词都需要手动重新输入中间结果
- ❌ 无法快速对比多个提示词版本的效果
- ❌ 测试效率低，重复劳动多

## 解决方案

### 方案架构

```
运行一次完整流程
    ↓
保存中间结果（多个典型场景）
    ↓
┌─────────────┬──────────────────┐
│             │                  │
本地批量测试  LangSmith Dataset  手动填充
（推荐）      （Playground）     （备用）
```

---

## 方案 A：本地批量测试（推荐 ⭐⭐⭐⭐⭐）

**适用场景**：快速迭代提示词，需要对比多个版本效果

### 使用步骤

#### 1. 保存典型场景的中间结果

运行完整流程，或手动保存中间结果：

```bash
# 运行工具脚本
python tools/middle_result_dataset.py
```

这会创建几个典型场景：
- `ai_formal_deep` - 正式风格的深度 AI 报告
- `fintech_concise_shallow` - 简洁风格的金融科技概览
- `new_energy_detailed_medium` - 详细风格的新能源汽车报告

查看已保存的场景：
```bash
ls .middle_results_cache/
```

#### 2. 创建提示词的多个版本

```bash
# 复制现有提示词
cp prompts/report_generator.yaml prompts/report_generator_v2.yaml

# 修改 v2 版本（比如调整 system message）
code prompts/report_generator_v2.yaml
```

#### 3. 运行批量对比测试

```python
from tools.prompt_comparison_test import PromptComparisonTest

tester = PromptComparisonTest()

# 用相同的输入测试多个提示词版本
results = tester.compare_prompts(
    prompt_files=[
        "report_generator.yaml",      # 原始版本
        "report_generator_v2.yaml"    # 修改后的版本
    ],
    scenario_name="ai_formal_deep",   # 使用保存的场景
    save_results=True
)
```

#### 4. 查看对比结果

```bash
# 查看统计摘要
cat comparison_results/comparison_*.json

# 对比完整输出
diff comparison_results/ai_formal_deep_report_generator_*.md
```

### 优势

- ✅ **零手动输入**：输入参数固化在场景文件中
- ✅ **批量对比**：一次运行测试多个版本
- ✅ **结果可追溯**：自动保存每次测试的完整输出
- ✅ **快速迭代**：修改提示词后立即重新测试
- ✅ **本地运行**：无需联网，速度快

---

## 方案 B：LangSmith Dataset（团队协作 ⭐⭐⭐⭐）

**适用场景**：团队共享测试数据，在 Playground 中可视化对比

### 使用步骤

#### 1. 保存中间结果（同方案 A）

```bash
python tools/middle_result_dataset.py
```

#### 2. 创建 LangSmith Dataset

```python
from tools.middle_result_dataset import MiddleResultDataset

manager = MiddleResultDataset()

# 将本地场景上传到 LangSmith
manager.create_langsmith_dataset(
    dataset_name="report_generator_middle_results"
)
```

#### 3. 在 Playground 中使用

1. 访问 https://smith.langchain.com/
2. 进入 **Prompts** → 选择 `report_generator`
3. 点击 **Open in Playground**
4. 在 Playground 中点击 **Select Dataset**
5. 选择 `report_generator_middle_results`
6. 现在可以：
   - 切换不同的提示词版本
   - 选择不同的场景（Dataset 中的 example）
   - **输入会自动填充**，无需手动输入

#### 4. 批量测试

在 Playground 中：
- 修改提示词
- 点击 **Run on Dataset**
- 自动对所有场景运行测试
- 查看对比结果

### 优势

- ✅ **团队共享**：Dataset 可以被团队成员共同使用
- ✅ **可视化对比**：Playground 提供直观的对比界面
- ✅ **自动填充**：选择 Dataset 后输入自动填充
- ✅ **支持评估**：可以配置评估器自动打分

---

## 方案 C：从 Trace 导出（快速调试 ⭐⭐⭐）

**适用场景**：临时调试某次运行的问题

### 使用步骤

1. 运行一次完整流程（会自动记录到 LangSmith）
2. 访问 https://smith.langchain.com/
3. 找到该次运行的 Trace
4. 点击进入 Trace 详情
5. 找到 `generate_report_node` 的 LLM 调用
6. 点击右上角 **Open in Playground**
7. 输入会自动填充，但是：
   - ⚠️ 切换提示词后输入可能丢失
   - 💡 解决：先复制输入参数，切换后粘贴回去

### 优势

- ✅ **快速启动**：从 Trace 一键打开
- ✅ **保留上下文**：包含完整的执行上下文
- ⚠️ **不适合批量对比**：切换提示词需要重新填充

---

## 方案对比

| 特性 | 本地批量测试 | LangSmith Dataset | 从 Trace 导出 |
|------|------------|------------------|--------------|
| 批量对比 | ✅ 支持 | ✅ 支持 | ❌ 不支持 |
| 输入固化 | ✅ 完全固化 | ✅ 完全固化 | ⚠️ 需手动保存 |
| 切换提示词 | ✅ 无缝切换 | ✅ 自动填充 | ⚠️ 可能丢失 |
| 团队协作 | ⚠️ 需共享文件 | ✅ 原生支持 | ❌ 不支持 |
| 运行速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 结果追溯 | ✅ 本地文件 | ✅ LangSmith | ⚠️ 需手动保存 |

**推荐组合**：
- **日常开发**：方案 A（本地批量测试）- 快速迭代
- **团队协作**：方案 B（LangSmith Dataset）- 共享标准
- **临时调试**：方案 C（Trace 导出）- 快速排查

---

## 完整工作流示例

### 场景：优化报告生成提示词

```bash
# 步骤1：运行一次完整流程，观察效果
python main.py --query "人工智能行业2024年发展分析"

# 步骤2：保存中间结果
python tools/middle_result_dataset.py
# 确认场景已保存
ls .middle_results_cache/

# 步骤3：创建新版本提示词
cp prompts/report_generator.yaml prompts/report_generator_v2.yaml

# 步骤4：修改 v2 版本
# 比如：调整 system message，改进报告结构

# 步骤5：批量对比测试
python -c "
from tools.prompt_comparison_test import PromptComparisonTest
tester = PromptComparisonTest()
tester.compare_prompts(
    ['report_generator.yaml', 'report_generator_v2.yaml'],
    'ai_formal_deep'
)
"

# 步骤6：查看对比结果
ls comparison_results/
diff comparison_results/ai_formal_deep_report_generator_*.md

# 步骤7：如果 v2 更好，替换原文件
mv prompts/report_generator_v2.yaml prompts/report_generator.yaml

# 步骤8：推送到 LangSmith Hub（可选）
python -c "
from prompts.prompt_manager import PromptManager
manager = PromptManager()
manager.push('report_generator', with_test=True)
"
```

---

## 高级用法

### 1. 从实际运行中保存中间结果

修改 `graph/nodes.py`，在 `web_search_node` 结束时添加：

```python
def web_search_node(self, state: ReportState) -> ReportStateUpdate:
    # ... 现有代码 ...
    
    # 调试模式：保存中间结果
    if os.getenv("SAVE_MIDDLE_RESULT") == "true":
        from tools.middle_result_dataset import MiddleResultDataset
        debug = MiddleResultDataset()
        debug.save_middle_result_manually(
            topic=state.get("topic"),
            year_range=state.get("year_range"),
            style=state.get("style"),
            depth=state.get("depth"),
            focus_areas=state.get("focus_areas"),
            search_results=state.get("search_results_formatted"),
            scenario_name=state.get("topic", "default").replace(" ", "_")
        )
    
    return {...}
```

运行时自动保存：
```bash
SAVE_MIDDLE_RESULT=true python main.py --query "区块链技术发展"
```

### 2. 对比测试多个场景

```python
from tools.prompt_comparison_test import PromptComparisonTest

tester = PromptComparisonTest()

# 对多个场景批量测试
scenarios = ["ai_formal_deep", "fintech_concise_shallow", "new_energy_detailed_medium"]

for scenario in scenarios:
    print(f"\n{'='*60}")
    print(f"测试场景: {scenario}")
    print(f"{'='*60}")
    
    tester.compare_prompts(
        prompt_files=[
            "report_generator.yaml",
            "report_generator_v2.yaml"
        ],
        scenario_name=scenario,
        save_results=True
    )
```

### 3. 集成到 CI/CD

```yaml
# .github/workflows/prompt_test.yml
name: Prompt Quality Test

on:
  pull_request:
    paths:
      - 'prompts/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run prompt comparison test
        env:
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        run: |
          python -c "
          from tools.prompt_comparison_test import PromptComparisonTest
          tester = PromptComparisonTest()
          results = tester.compare_prompts(
              ['report_generator.yaml'],
              'ai_formal_deep'
          )
          # 检查是否有失败
          if not all(r['success'] for r in results):
              exit(1)
          "
```

---

## 常见问题

### Q1: 中间结果保存在哪里？

**A**: 默认保存在 `.middle_results_cache/` 目录下，每个场景一个 JSON 文件。

### Q2: 如何添加新的测试场景？

**A**: 运行 `python tools/middle_result_dataset.py`，或者：

```python
from tools.middle_result_dataset import MiddleResultDataset

manager = MiddleResultDataset()
manager.save_middle_result_manually(
    topic="你的主题",
    year_range="2024",
    style="formal",
    depth="medium",
    focus_areas="关注点1,关注点2",
    search_results="搜索结果内容...",
    scenario_name="my_new_scenario"
)
```

### Q3: 如何在 Playground 切换提示词后保留输入？

**A**: 
- **方案 B（Dataset）**：选择 Dataset 后切换提示词，输入会自动保留
- **方案 C（Trace）**：先复制输入参数，切换后粘贴回去
- **推荐**：使用方案 A 或 B，避免手动操作

### Q4: 对比结果如何查看？

**A**: 
```bash
# 查看统计摘要
cat comparison_results/comparison_*.json

# 对比完整输出（使用 diff）
diff comparison_results/scenario1_*.md

# 使用 meld 可视化对比（如果安装了）
meld comparison_results/scenario1_report_generator_*.md
```

---

## 总结

针对多 LLM 流程中间结果调试的问题，我们提供了三种解决方案：

1. **本地批量测试**（推荐）：快速迭代，批量对比
2. **LangSmith Dataset**：团队协作，可视化管理
3. **Trace 导出**：临时调试，快速排查

**核心思路**：
- 固化中间结果为测试场景
- 用相同输入测试多个提示词版本
- 自动化对比，提高迭代效率

**最佳实践**：
- 保存 3-5 个典型场景（不同主题、风格、深度）
- 每次修改提示词后立即运行对比测试
- 结合 LangSmith 追踪，了解完整执行过程
- 重要版本创建备份，便于回滚

---

## 工具文件清单

- `tools/middle_result_dataset.py` - 中间结果管理工具
- `tools/prompt_comparison_test.py` - 提示词对比测试工具
- `.middle_results_cache/` - 中间结果缓存目录（自动创建）
- `comparison_results/` - 对比测试结果目录（自动创建）

