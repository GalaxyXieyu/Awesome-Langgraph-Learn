# Interactive Deep Research

> 🔬 智能交互式深度研究系统 - 基于LangGraph的多Agent协作平台

## ✨ 特性

- 🏗️ **模块化架构** - 清晰的代码组织和职责分离
- 🤖 **多Agent协作** - 智能监督者、研究者、写作者协同工作
- ⚡ **流式输出** - 实时响应，支持配置驱动的输出控制
- 🎛️ **配置驱动** - 简单YAML配置控制所有行为
- 🔧 **可扩展** - 易于添加新的子图、工具和功能
- 🔒 **安全配置** - 环境变量管理API密钥，避免硬编码

## 🚀 快速开始

### 1. 环境配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的API密钥：
```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

# Tavily搜索API配置  
TAVILY_API_KEY=your_tavily_api_key_here
```

### 2. 使用示例

```python
from graph import create_deep_research_graph
from state import create_simple_state
from writer.core import create_workflow_processor

# 创建主图
graph = create_deep_research_graph()

# 创建初始状态
state = create_simple_state("研究人工智能的发展趋势")

# 创建输出处理器
processor = create_workflow_processor("main")

# 运行图
for chunk in graph.stream(state):
    result = processor.process_chunk(chunk)
    print(result)
```

## 🏗️ 项目结构

```
Interactive-Deep-Research/
├── core/                    # 🎯 核心模块
│   ├── graph.py            # 主图定义
│   └── state.py            # 状态管理
├── subgraphs/              # 🔄 子图模块
│   └── intelligent_research/
├── tools/                  # 🛠️ 工具模块
│   ├── research/          # 研究工具
│   ├── writing/           # 写作工具
│   └── common/            # 通用工具
├── writer/                 # ✍️ Writer系统
│   ├── core.py           # 核心逻辑
│   ├── config.py         # 配置管理
│   └── config.yaml       # 配置文件
├── tests/                  # 🧪 测试
├── examples/               # 📝 示例
└── docs/                   # 📚 文档
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from core import create_deep_research_graph, create_simple_state
from writer import create_workflow_processor

# 创建主图
graph = create_deep_research_graph()

# 创建初始状态
state = create_simple_state("研究人工智能发展趋势")

# 创建输出处理器
processor = create_workflow_processor("main")

# 运行研究
for chunk in graph.stream(state):
    result = processor.process_chunk(chunk)
    print(result)
```

### 配置Writer输出

编辑 `writer/config.yaml`:

```yaml
# 只显示核心Agent
agents:
  include: ["research", "writing"]
  exclude: ["intelligent_supervisor"]

# 隐藏思考过程
messages:
  exclude: ["reasoning", "thinking"]

# 简化输出
verbosity:
  level: "normal"
  show_metadata: false
```

## 🛠️ 模块详解

### 核心模块 (core/)
- `graph.py` - 主工作流图定义
- `state.py` - 状态管理和数据结构

### 子图模块 (subgraphs/)
- `intelligent_research/` - 智能研究子图，包含多Agent协作逻辑

### 工具模块 (tools/)
- `research/` - 搜索、分析、数据获取工具
- `writing/` - 内容生成、编辑工具
- `common/` - 通用实用工具

### Writer系统 (writer/)
- `core.py` - 流式输出核心逻辑
- `config.py` - YAML配置管理
- `config.yaml` - 默认配置文件

## 📚 最佳实践

### 构建新的Graph

1. **模块化设计** - 将功能拆分成独立的节点
2. **状态驱动** - 通过状态变化控制流程
3. **配置优先** - 所有可变行为都通过配置控制
4. **测试覆盖** - 为每个节点编写单元测试

### 添加新工具

1. 在 `tools/` 下创建相应分类文件夹
2. 实现工具函数并添加到 `__init__.py`
3. 在子图中引用工具
4. 编写工具测试

### 扩展Writer系统

1. 修改 `writer/config.yaml` 添加新的配置选项
2. 在 `writer/config.py` 中添加配置处理逻辑
3. 在 `writer/core.py` 中实现新功能

## 🔧 开发

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_core.py
```

### 开发模式

```bash
# 安装开发依赖
pip install -e .

# 运行示例
python examples/basic_usage.py
```

## 📖 文档

- [Writer配置指南](writer/guide.md) - 详细的Writer配置说明
- [API文档](docs/) - 完整的API参考
- [示例集合](examples/) - 各种使用场景示例

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License