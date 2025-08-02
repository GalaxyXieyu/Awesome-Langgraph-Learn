# LangGraph 会话存储解决方案演示

## 📚 项目概述

本项目演示了LangGraph应用中不同会话存储解决方案的实现和对比：
- **内存存储 (MemorySaver)** - 适用于开发和测试
- **Redis存储 (RedisSaver)** - 适用于高性能生产环境

## 📁 项目结构

```
RedisMemory-Graph/
├── README.md              # 项目说明
├── requirements.txt       # 依赖包
├── graph.py              # 简单聊天机器人图
├── interactive_graph.py  # 复杂交互式写作助手图（基于Redis）
├── test.py               # 基础测试脚本
├── test_interactive.py   # 交互式写作助手测试
└── demo.py               # 完整演示脚本
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd RedisMemory-Graph
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# 设置OpenAI API Key
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. 运行演示

```bash
# 运行简单聊天机器人
python graph.py

# 运行交互式写作助手
python interactive_graph.py

# 运行基础测试
python test.py

# 运行完整的写作助手测试
python test_interactive.py

# 运行完整演示（推荐！）
python demo.py
```

## 📊 存储方案对比

| 存储方案 | 性能 | 持久化 | 扩展性 | 适用场景 |
|---------|------|--------|--------|----------|
| **MemorySaver** | ⭐⭐⭐⭐⭐ | ❌ | ⭐ | 开发测试 |
| **RedisSaver** | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | 高性能生产 |

### 🎯 选择建议

#### 🔥 Redis - 推荐用于生产环境
- **优势**: 极高的读写性能、支持TTL、支持集群
- **适用**: 生产环境、高并发应用、分布式系统
- **注意**: 需要Redis服务

#### 💨 Memory - 仅用于开发测试
- **优势**: 最快的性能、零配置
- **适用**: 开发测试、演示原型
- **注意**: 重启后数据丢失

## 🔧 代码示例

### 1. 简单聊天机器人

```python
from graph import create_chat_bot, chat_with_memory

# 创建Redis版本的聊天机器人
app = create_chat_bot("redis")

# 开始对话
response = chat_with_memory(app, "你好！我叫小明", "session_001")
print(response)

# 测试记忆功能
response = chat_with_memory(app, "我叫什么名字？", "session_001")
print(response)  # 应该能记住"小明"
```

### 2. 交互式写作助手

```python
from interactive_graph import run_writing_assistant

# 运行写作助手（自动模式）
result = run_writing_assistant(
    topic="人工智能的发展趋势",
    mode="copilot",  # 自动模式，无需用户交互
    thread_id="writing_session_001"
)

# 查看生成的文章
if "article" in result:
    print(f"标题: {result['outline']['title']}")
    print(f"文章: {result['article']}")
```

### 性能测试

```python
from test import performance_test

# 运行性能测试
results = performance_test()
print(f"内存存储: {results['memory']:.3f}秒")
print(f"Redis存储: {results['redis']:.3f}秒")
```

## 📈 测试结果

运行 `python test.py` 可以看到：

- ✅ 内存存储功能测试
- ✅ Redis存储功能测试
- ✅ 跨会话记忆测试
- ⚡ 性能对比测试

## 🔗 相关资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [Redis 官方文档](https://redis.io/documentation)

---

**⚠️ 注意**: 请确保设置了 `OPENAI_API_KEY` 环境变量才能正常运行。
