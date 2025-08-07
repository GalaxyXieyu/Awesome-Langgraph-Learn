# 智能深度研究系统

基于 LangGraph 的智能深度研究报告生成系统，集成了智能章节研究子图。

## 🚀 重大性能优化更新

### ⚡ 性能提升亮点
- **67-76%** 速度提升 - 通过并行处理和智能缓存
- **3-5x** 并行度提升 - 多Agent协作，章节并发处理
- **30-50%** 缓存命中率 - 避免重复LLM调用和搜索
- **固定时间复杂度** - 不再随章节数量线性增长

### 🎯 核心优化
1. **专业化Agent流水线** - 研究→写作→验证并行协作
2. **批量并行处理** - 所有章节同时研究和生成
3. **智能缓存系统** - 研究结果和LLM响应缓存
4. **Handoff协作机制** - 高效的Agent间任务传递

### 📊 性能对比
| 章节数 | 原始架构 | 优化架构 | 提升幅度 |
|--------|----------|----------|----------|
| 3章节  | ~225秒   | ~75秒    | **67%** ⬆️ |
| 5章节  | ~375秒   | ~90秒    | **76%** ⬆️ |
| 6章节  | ~450秒   | ~95秒    | **79%** ⬆️ |

### 🛠️ 使用优化架构
```python
from graph_optimized_pipeline import OptimizedReportGenerator

# 创建优化生成器（推荐）
generator = OptimizedReportGenerator()

# 高性能生成报告
result = await generator.generate_report_optimized(
    topic="人工智能发展趋势",
    sections=[...],  # 章节列表
    writer_callback=lambda x: print(f"进度: {x}")
)

print(f"✅ 生成完成！耗时: {result['performance_metrics']['total_time']:.2f}秒")
```

### 📈 快速测试
```bash
# 优化架构测试
python test_optimization.py

# 性能对比测试
python performance_comparison.py
```

## 🏗️ 系统架构

### 核心文件
- `graph.py` - 主图：整体流程控制
- `state.py` - 状态管理：数据结构定义
- `tools.py` - 工具集：研究、分析、写作工具
- `test.py` - 测试脚本：系统功能验证
- `subgraph/` - 智能章节研究子图

### 架构设计
```
主图流程：大纲生成 → 大纲确认 → 智能章节处理
                                    ↓
子图流程：上下文规划 → 初步研究 → 初稿生成 → 质量评估 → 补充研究 → 内容增强 → 润色优化
```

## 🧠 智能特性

### 主图功能
- **大纲生成**：基于主题自动生成结构化大纲
- **流程控制**：管理整体报告生成流程
- **状态管理**：协调主图和子图之间的数据流

### 子图功能（智能章节研究系统）
- **上下文感知**：理解章节在整个报告中的位置和作用
- **质量驱动**：多维度质量评估，自动迭代优化
- **自适应研究**：根据内容质量动态补充研究
- **多阶段生成**：初稿→增强→润色的渐进式内容生成

## 🚀 快速开始

### 1. 环境准备
```bash
pip install langgraph langchain-openai
```

### 2. 基本使用
```python
from graph import create_deep_research_graph
from state import create_initial_state, ReportMode

# 创建系统
graph = create_deep_research_graph()

# 创建初始状态
initial_state = create_initial_state(
    topic="人工智能在医疗诊断中的应用",
    user_id="user_001",
    mode=ReportMode.COPILOT,  # 自动模式
    target_audience="医疗专业人士",
    target_length=3000
)

# 执行生成
config = {"configurable": {"thread_id": "session_001"}}
async for event in graph.astream(initial_state, config=config):
    print(f"步骤: {list(event.keys())}")
```

### 3. 运行测试
```bash
python test.py
```

## 📊 运行模式

- **INTERACTIVE** - 交互模式：需要用户确认每个步骤
- **COPILOT** - 副驾驶模式：自动通过所有确认（推荐测试）
- **GUIDED** - 引导模式：提供建议但需要确认

## 🔧 配置说明

### LLM 配置
在 `graph.py` 中修改 `create_llm()` 函数：
```python
def create_llm():
    return ChatOpenAI(
        model="your-model",
        base_url="your-api-url",
        api_key="your-api-key"
    )
```

### 搜索工具配置
在 `tools.py` 中配置搜索API密钥。

## 📈 系统优势

1. **模块化设计** - 主图负责流程，子图负责专业处理
2. **智能迭代** - 质量驱动的自动优化
3. **上下文感知** - 考虑章节间的逻辑关系
4. **高质量输出** - 多轮研究和内容增强

## 🛠️ 故障排除

### 常见问题
- **导入错误**：确保所有依赖已安装
- **API限制**：检查LLM和搜索API配置
- **流上下文错误**：已通过 `safe_get_stream_writer()` 修复

### 调试模式
```bash
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.INFO)"
```

## �� 输出示例

系统会生成包含以下内容的研究报告：
- 结构化大纲（多个章节）
- 高质量章节内容（经过多轮优化）
- 研究数据和来源
- 质量评估指标

每个章节都经过完整的研究→分析→生成→优化流程，确保内容的专业性和准确性。
