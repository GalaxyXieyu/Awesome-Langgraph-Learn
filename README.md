# LangGraph 学习仓库

本仓库是关于 LangGraph 框架的学习与实践集合，包含了多个示例、教程和项目。每个目录都是一个独立的模块，用于演示 LangGraph 的特定功能或应用场景。

## 项目结构

以下是本仓库中主要项目的概览：

- **LangGraphCeleryChat**: 一个基于 LangGraph 和 Celery 构建的聊天应用示例，用于处理异步任务。
- **Multi-Agent-Handoff**: 演示了如何创建一个多智能体系统，并在不同智能体之间传递任务。
- **RedisMemory-Graph**: 一个将 Redis 作为 LangGraph 图的持久化记忆解决方案的项目。
- **context_project**: 一个专注于在图中进行上下文管理和工程的示例。
- **turtorial**: 包含一系列关于 LangGraph 概念的 Markdown 指南和教程。
- **utils**: 用于不同项目的通用工具脚本。

## 如何开始

要探索特定的项目，请进入其对应的目录，并遵循其独立的 README 文件（如有）中的说明。大部分项目都是自包含的，并附有独立的依赖和安装指南。

例如，要运行多智能体演示：

```bash
cd Multi-Agent-Handoff
# 遵循 Multi-Agent-Handoff/README.md 中的安装说明
```

## 项目目的

本仓库的主要目标是作为一个个人知识库和使用 LangGraph 构建应用的实践指南。它涵盖了从基础的图构建到更高级的概念，如多智能体协作、持久化记忆和异步执行等。