# LangGraph Redis 存储演示

这个项目演示了如何在 LangGraph 中使用官方 Redis 存储来实现会话持久化。

## 🎯 项目概述

- **核心功能**: 使用 Redis 存储 LangGraph 会话数据
- **存储方式**: 官方 `RedisSaver` + RedisJSON
- **LLM 模型**: Qwen2.5-72B (自定义配置)
- **记忆功能**: 跨会话保持对话历史

## 📁 文件结构

```
RedisMemory-Graph/
├── graph.py          # 核心图定义和 Redis 配置
├── tools.py          # 工具函数
├── test.py           # 简化测试脚本
└── README.md         # 本文档
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 激活环境
conda activate langgraph311

# 安装依赖
pip install langgraph-checkpoint-redis redis
```

### 2. 运行测试

```bash
python test.py
```

## 🔧 核心代码解析

### Redis 存储的正确使用方法

```python
from graph import create_chat_bot_with_redis
from langgraph.checkpoint.redis import RedisSaver
from tools import chat_with_memory

# 1. 获取工作流和 Redis URL
workflow, redis_url = create_chat_bot_with_redis()

# 2. 使用官方 Redis 上下文管理器
with RedisSaver.from_conn_string(redis_url) as checkpointer:
    # 3. 创建索引（首次使用时必须调用）
    checkpointer.setup()
    
    # 4. 编译图
    app = workflow.compile(checkpointer=checkpointer)
    
    # 5. 开始对话
    response = chat_with_memory(app, "你好", "session_001")
```

### LLM 配置

```python
def create_llm():
    """统一的 LLM 配置"""
    return ChatOpenAI(
        model="qwen2.5-72b-instruct-awq",
        temperature=0.7,
        base_url="https://llm.3qiao.vip:23436/v1",
        api_key="sk-0rnrrSH0OsiaWCiv6b37C1E4E60c4b9394325001Ec19A197",
    )
```

## 📊 Redis 数据结构

LangGraph 在 Redis 中使用 RedisJSON 存储结构化数据：

### 键命名规范

```
checkpoint_blob:{thread_id}:__empty__:{channel}:{checkpoint_id}
checkpoint_write:{thread_id}:__empty__:{task_id}:{write_id}
checkpoint:{thread_id}:__empty__:{checkpoint_id}
```

### 数据示例

```json
{
  "type": "json",
  "channel": "messages",
  "blob": "[{\"kwargs\":{\"content\":\"我叫小明\",\"type\":\"human\"}}]"
}
```

## ⚠️ 重要注意事项

### 1. 必须使用上下文管理器

```python
# ✅ 正确
with RedisSaver.from_conn_string(redis_url) as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)
    # 所有操作都在这里

# ❌ 错误
checkpointer = RedisSaver.from_conn_string(redis_url)  # 这样不行
```

### 2. 必须调用 setup()

```python
with RedisSaver.from_conn_string(redis_url) as checkpointer:
    checkpointer.setup()  # 创建必要的索引
    app = workflow.compile(checkpointer=checkpointer)
```

### 3. Redis 服务器要求

- ✅ 支持 **RediSearch** 模块
- ✅ 支持 **RedisJSON** 模块
- ✅ Redis 版本 6.0+

## 🧪 测试结果示例

```
🚀 LangGraph Redis 测试
========================================
🔴 测试 LangGraph Redis 存储
----------------------------------------
✅ 使用 Qwen2.5-72B 模型
🔗 连接 Redis: redis://default:mfzstl2v@dbconn.sealoshzh.site:41277
✅ RedisSaver 创建成功
✅ 索引创建成功
✅ Graph 编译成功
👤 我叫小明，我是程序员
🤖 很高兴认识你，小明！作为程序员...
👤 我叫什么名字？我的职业是什么？
🤖 你叫小明，是一名程序员。
📊 记忆测试: ✅ 通过

📊 查看 Redis 数据
------------------------------
🔍 找到 23 个相关键
📈 统计: 总共 69 个键，23 个 LangGraph 相关
📊 测试结果: ✅ 通过
✅ 测试完成！
```

## 🔍 常见问题

### Q: 为什么会报 "no such index" 错误？
A: Redis 服务器缺少 RediSearch 模块，需要使用 Redis Stack 或安装相应模块。

### Q: 如何查看 Redis 中的数据？
A: 运行 `test.py` 会自动显示存储的数据结构。

### Q: 可以跨会话保持记忆吗？
A: 可以，只要使用相同的 `thread_id`，数据会持久化在 Redis 中。

## 💡 最佳实践

1. **环境管理**: 使用 `langgraph311` 环境，所有依赖已配置好
2. **错误处理**: 在生产环境中添加 Redis 连接失败的回退机制
3. **线程管理**: 为不同用户/会话使用不同的 `thread_id`
4. **数据清理**: 定期清理过期的会话数据

## 🚀 扩展使用

### 在其他项目中使用

```python
# 复制核心函数
from RedisMemory-Graph.graph import create_chat_bot_with_redis
from RedisMemory-Graph.tools import chat_with_memory

# 在你的项目中使用
workflow, redis_url = create_chat_bot_with_redis()
with RedisSaver.from_conn_string(redis_url) as checkpointer:
    checkpointer.setup()
    app = workflow.compile(checkpointer=checkpointer)
    response = chat_with_memory(app, "你好", "my_session")
```

## 🛠️ 故障排除

### 环境问题

```bash
# 检查当前环境
conda info --envs
echo "当前环境: $CONDA_DEFAULT_ENV"

# 检查 Python 路径
which python

# 检查已安装包
pip list | grep -E "(redis|langgraph)"
```

### Redis 连接测试

```python
import redis
client = redis.from_url('your-redis-url')
client.ping()  # 应该返回 True
```

### 常见错误及解决方案

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `ModuleNotFoundError: No module named 'redis'` | 环境不匹配 | 确保在 `langgraph311` 环境中运行 |
| `no such index` | 缺少 RediSearch | 使用支持 RediSearch 的 Redis 服务 |
| `Connection refused` | Redis 服务未启动 | 检查 Redis 服务器状态 |

## 📈 性能优化

- **连接池**: 在生产环境中使用 Redis 连接池
- **数据过期**: 设置合适的 TTL 避免数据堆积
- **索引优化**: 根据查询模式优化 RediSearch 索引

---

**总结**: 这个项目展示了 LangGraph 官方 Redis 存储的完整使用流程，从连接配置到数据查看，提供了一个可直接使用的参考实现。关键是理解上下文管理器的使用和 `setup()` 方法的重要性。
