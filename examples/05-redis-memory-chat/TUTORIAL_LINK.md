# 关联教程

本示例对应教程章节：**LG-05 持久化与记忆系统**

## 涵盖知识点

- 使用 Redis 替代 Postgres 作为 Checkpointer
- 跨会话保持对话历史
- `RedisSaver` + RedisJSON 配置

## 文件说明

- `graph.py` - 核心图定义和 Redis 配置
- `tools.py` - 工具函数
- `test.py` - 测试脚本

## 延伸阅读

- `turtorial/LG-05-persistence-memory/05.5-postgres-saver-store.md`（对比 Postgres 方案）
