# Docker 环境搭建指南

本项目提供完整的 Docker Compose 配置，一键拉起 PostgreSQL、Redis、Langfuse 等全套依赖，无需手动安装。

## 快速开始

### 1. 准备环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key 和其他配置
```

### 2. 启动服务

**方式 A：完整环境（含 Langfuse 可观测性）**

Langfuse 需要 ClickHouse + MinIO，首次启动约需 2-3 分钟拉取镜像。

```bash
docker compose up -d
```

**方式 B：精简环境（仅 PostgreSQL + Redis）**

如果你不需要 Langfuse，只想跑通教程中的 Checkpoint 和缓存示例：

```bash
docker compose -f docker-compose.minimal.yml up -d
```

### 3. 验证服务状态

```bash
# 查看所有容器状态
docker compose ps

# 查看日志
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f langfuse-web
```

### 4. 访问各服务

| 服务 | 地址 | 说明 |
|------|------|------|
| Langfuse | http://localhost:3000 | 可观测性界面，首次启动需注册 |
| PostgreSQL | localhost:5432 | 数据库连接端口 |
| Redis | localhost:6379 | 缓存连接端口 |
| MinIO Console | http://localhost:9091 | 对象存储管理界面 |
| Jupyter | http://localhost:8888 | 浏览器内直接运行 Notebook |

### 5. Notebook 中使用 Docker 服务

容器内运行的 Notebook 已通过环境变量注入连接信息，直接使用即可：

```python
import os

# PostgreSQL 连接
postgres_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB')}"

# Redis 连接
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_password = os.getenv('REDIS_PASSWORD')

# Langfuse 连接
langfuse_host = os.getenv('LANGFUSE_HOST', 'http://langfuse-web:3000')
```

如果你在宿主机直接运行 Python（不通过 Jupyter 容器），连接地址用 `localhost`：

```python
# 宿主机运行时使用 localhost
postgres_url = "postgresql://langgraph:langgraph@localhost:5432/langgraph"
redis_url = "redis://:redis@localhost:6379/0"
```

## 服务说明

### PostgreSQL
- 用于 LangGraph Checkpoint 持久化
- Langfuse 数据存储
- 默认数据库: `langgraph`

### Redis
- LangGraph 节点级缓存
- Langfuse 异步任务队列
- 已启用 AOF 持久化

### Langfuse
- 首次访问 http://localhost:3000 需创建组织/项目
- 创建项目后获取 Public Key / Secret Key，填入 `.env`
- 重启容器生效: `docker compose restart langfuse-web langfuse-worker`

### Jupyter
- 工作目录挂载到 `./turtorial`
- 无需 Token，直接访问 http://localhost:8888
- 已预装常见数据科学包

## 常用命令

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷（谨慎！）
docker compose down -v

# 重启单个服务
docker compose restart langfuse-web

# 进入 PostgreSQL 执行 SQL
docker exec -it langgraph_postgres psql -U langgraph -d langgraph

# 进入 Redis CLI
docker exec -it langgraph_redis redis-cli -a redis

# 查看 Langfuse 初始化密钥
docker compose logs langfuse-web | grep "API keys"
```

## 故障排查

| 问题 | 解决 |
|------|------|
| Langfuse 启动慢 | ClickHouse 首次初始化需要时间，等待 healthcheck 通过 |
| 端口冲突 | 修改 `.env` 或 `docker-compose.yml` 中的端口映射 |
| Jupyter 包缺失 | `docker exec langgraph_jupyter pip install xxx` |
| 数据丢失 | 检查 `docker-compose down` 是否误加了 `-v` |
