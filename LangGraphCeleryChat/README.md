# 🚀 LangGraph Celery Chat - 智能写作助手系统

基于 FastAPI + Celery + Redis + LangGraph 的智能写作助手系统，支持实时流式输出、任务管理和用户交互。

## 📋 系统简介

这是一个**智能写作助手系统**，就像一个会写文章的AI机器人：
- 🔍 **自动研究**: 根据主题自动搜索相关资料
- 📝 **生成大纲**: 智能分析并创建文章结构
- ✍️ **自动写作**: 基于大纲生成完整高质量文章
- 💬 **用户互动**: 支持大纲确认、搜索权限等交互
- 🔄 **会话恢复**: 支持任务中断和恢复功能

### 🌟 核心特性

- **异步任务处理**: 基于 Celery 的分布式任务队列
- **实时流式输出**: Server-Sent Events (SSE) 支持
- **智能写作工作流**: 基于 LangGraph 的状态机
- **用户交互支持**: 支持大纲确认、搜索权限等交互
- **会话管理**: 支持会话恢复和上下文管理
- **多模式支持**: Copilot（自动）和 Interactive（交互）模式

## 🏗️ 系统架构

### 技术栈
- **后端**: FastAPI + Celery + Redis + LangGraph
- **前端**: React/Vue + Server-Sent Events (SSE)
- **基础设施**: Nginx + SSL/TLS + Redis Cluster
- **监控**: Celery Flower + Redis 监控

### 架构特点
- ✅ **生产就绪**: HTTPS 安全传输，支持负载均衡
- ✅ **高可靠性**: 任务持久化，支持失败重试和恢复
- ✅ **高性能**: Redis Streams 提供高吞吐量事件流
- ✅ **可扩展性**: Celery 支持分布式部署和水平扩展
- ✅ **监控完善**: Celery Flower + Redis 监控工具

## 📁 项目结构

```
LangGraphCeleryChat/
├── docs/                   # 文档
│   ├── 技术架构评估报告.md
│   ├── 接口设计规范.md
│   └── 部署指南.md
├── backend/                # 后端服务
│   ├── app/               # FastAPI 应用
│   ├── celery_app/        # Celery 任务
│   ├── adapters/          # LangGraph 适配器
│   ├── models/            # 数据模型
│   └── utils/             # 工具函数
├── frontend/              # 前端应用
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   └── dist/              # 构建输出
├── tests/                 # 测试文件
├── docker/                # Docker 配置
├── nginx/                 # Nginx 配置
└── requirements.txt       # Python 依赖
```

## 🛠️ 系统要求

### 最低要求
- **Python**: 3.11+
- **Redis**: 6.0+
- **内存**: 4GB+
- **存储**: 10GB+
- **网络**: 稳定的互联网连接（用于AI模型调用）

### 推荐配置
- **Python**: 3.11
- **Redis**: 7.0+
- **内存**: 8GB+
- **存储**: 20GB+ SSD
- **CPU**: 4核心+

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd LangGraphCeleryChat

# 创建虚拟环境
conda create -n langgraph python=3.11
conda activate langgraph

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# .env
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# AI 模型配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 3. 启动服务

```bash
# 创建日志目录
mkdir -p logs

# 启动 Redis（如果使用本地Redis）
redis-server

# 启动 Celery Worker
celery -A backend.celery_app worker --loglevel=info

# 启动 FastAPI 服务
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 创建测试任务
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "config": {
      "topic": "测试文章",
      "max_words": 500,
      "style": "technical",
      "language": "zh",
      "mode": "copilot"
    }
  }'
```

## 📚 API 接口使用

### 🏠 基础接口

#### 健康检查
```bash
GET /health
```

#### 创建写作任务
```bash
POST /api/v1/tasks
{
  "user_id": "user_001",
  "conversation_id": "session_id",  // 可选，用于恢复会话
  "config": {
    "topic": "FastAPI 微服务架构设计",
    "max_words": 1000,
    "style": "technical",        // formal, casual, academic, technical
    "language": "zh",            // zh, en
    "mode": "copilot",          // copilot, interactive
    "enable_search": true
  }
}
```

#### 监听实时进度
```javascript
const eventSource = new EventSource('http://localhost:8000/api/v1/events/session_id');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('进度更新:', data);
};
```

#### 响应用户交互
```bash
POST /api/v1/tasks/{task_id}/resume
{
  "response": "yes",           // 用户响应
  "approved": true,            // 是否批准
  "feedback": "请增加更多技术细节",  // 可选反馈
  "modifications": {}          // 可选修改建议
}
```

## 🔧 核心功能

### 🔄 WorkflowAdapter 重构优化

系统经过重大架构重构，实现了更简洁、高效、易维护的设计：

#### 核心改进

| 改进项目 | 之前的问题 | 现在的解决方案 | 好处 |
|---------|-----------|---------------|------|
| **统一接口** | 分离的初始调用和恢复调用方法 | 统一的 `execute_workflow()` 接口 | 更简单易用 |
| **图调用方式** | 重复构建复杂的图结构 | 直接使用外部预编译图 | 性能更好，避免重复 |
| **流式数据格式** | 多层数据转换和嵌套结构 | 外部图直接输出 Redis Streams 兼容格式 | 减少处理时间 |
| **架构简化** | 功能重复，代码冗余 | 删除冗余代码，保持单一职责 | 更容易维护和调试 |

#### 技术特性
- **职责分离**: 适配器只负责适配，不重新实现图逻辑
- **直接集成**: 使用外部图的完整功能，避免重复构建
- **标准格式**: Redis Streams 兼容的数据格式
- **统一接口**: 支持任意 LangGraph 应用
- **中断处理**: 自动映射到 Redis Streams
- **状态管理**: 完整的任务状态持久化

### 实时通信
- **Server-Sent Events**: 替代 WebSocket，更稳定
- **Redis Streams**: 高性能事件流处理
- **多客户端支持**: 支持多个前端同时连接

### 任务管理
- **异步执行**: Celery 分布式任务队列
- **任务持久化**: Redis 状态存储
- **进度跟踪**: 实时进度更新
- **智能会话恢复**: 支持基于 conversationId 的会话恢复和创建

### 🔄 智能 Resume 功能

系统提供了完整的会话管理和恢复机制：

#### 会话创建和恢复逻辑
- **自动判断**: 根据 `conversationId` 参数自动判断是恢复现有会话还是创建新会话
- **Redis 检查**: 查询 Redis 中是否存在该 conversationId 的会话数据
- **智能处理**:
  - 如果会话存在 → 进入 resume 模式（恢复现有会话）
  - 如果会话不存在 → 进入创建模式（新建会话）

#### API 接口
```python
# 创建新任务（支持会话恢复）
POST /api/v1/tasks
{
    "config": {
        "topic": "人工智能在医疗诊断中的应用",
        "mode": "interactive"
    },
    "user_id": "user_123",
    "conversation_id": "conv_456"  # 可选，用于恢复现有会话
}

# 获取会话摘要
GET /api/v1/conversations/{conversation_id}/summary

# 验证恢复请求
POST /api/v1/conversations/{conversation_id}/validate-resume?task_id={task_id}

# 恢复任务（增强版错误处理）
POST /api/v1/tasks/{task_id}/resume
```

#### 使用示例
```python
import requests

# 场景1: 创建新会话
response = requests.post("http://localhost:8000/api/v1/tasks", json={
    "config": {"topic": "AI技术发展", "mode": "interactive"},
    "user_id": "user_123"
    # 不提供 conversation_id，系统自动创建新会话
})
new_session = response.json()
print(f"新会话ID: {new_session['session_id']}")

# 场景2: 恢复现有会话
response = requests.post("http://localhost:8000/api/v1/tasks", json={
    "config": {"topic": "AI技术应用", "mode": "interactive"},
    "user_id": "user_123",
    "conversation_id": new_session['session_id']  # 使用现有会话ID
})
resumed_session = response.json()
print(f"恢复会话: {resumed_session['is_resumed']}")

# 场景3: 获取会话摘要
summary = requests.get(f"http://localhost:8000/api/v1/conversations/{new_session['session_id']}/summary")
print(f"会话统计: {summary.json()['statistics']}")
```

## 📊 监控和运维

### Celery Flower 监控
访问 `http://localhost:5555` 查看：
- 任务执行状态
- Worker 性能指标
- 队列长度统计
- 失败任务分析

### Redis 监控
```bash
# Redis 性能监控
redis-cli info
redis-cli monitor

# 查看事件流
redis-cli XREAD STREAMS task_events:session_123 $
```

### 应用日志
```bash
# 查看应用日志
tail -f logs/app.log

# 查看 Celery 日志
tail -f logs/celery.log
```

## 🔒 安全配置

### HTTPS 配置
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### JWT 认证
```python
# 生成 JWT Token
from backend.utils.auth import create_access_token

token = create_access_token(data={"user_id": "user_123"})
```

## 🧪 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 运行性能测试
pytest tests/performance/
```

## 📈 性能优化

### Redis 优化
- 使用 Redis Cluster 提高可用性
- 配置合适的内存策略
- 启用 AOF 持久化

### Celery 优化
- 调整 Worker 并发数
- 配置任务路由和优先级
- 启用结果后端缓存

### FastAPI 优化
- 使用 Gunicorn + Uvicorn Workers
- 启用 Gzip 压缩
- 配置连接池

## 🚀 部署指南

### 开发环境部署
按照上面的"快速开始"步骤即可。

### 生产环境部署

#### 使用 Docker 部署

**Dockerfile 示例**：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml 示例**：
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery-worker:
    build: .
    command: celery -A backend.celery_app worker --loglevel=info
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env

  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
      - celery-worker
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  redis_data:
```

#### 启动生产环境
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
docker-compose logs -f celery-worker
```

### 🔒 安全配置

#### 环境变量安全
```bash
# 生产环境 .env
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Redis 密码保护
REDIS_PASSWORD=your-redis-password

# API 密钥
OPENAI_API_KEY=your-production-openai-key
```

#### 防火墙配置
```bash
# 只开放必要端口
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw deny 6379   # Redis（仅内部访问）
ufw deny 8000   # API（通过Nginx代理）
ufw enable
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 🆘 故障排除

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| **Redis 连接失败** | Redis 服务未启动 | `redis-cli ping` 检查状态 |
| **Celery Worker 无响应** | Worker 进程异常 | 重启 Worker: `docker-compose restart celery-worker` |
| **API 响应慢** | 系统资源不足 | 检查 CPU/内存使用情况 |
| **SSL 证书错误** | 证书配置错误 | 检查证书路径和有效期 |

### 调试工具

```bash
# 健康检查脚本
curl -s http://localhost:8000/health | jq '.'

# 检查 Celery Worker 状态
celery -A backend.celery_app inspect active

# 查看应用日志
tail -f logs/app.log

# 启用调试模式
export LOG_LEVEL=DEBUG
uvicorn backend.app.main:app --reload --log-level debug
```

### 监控和日志

#### 系统监控
- **Celery Flower**: 访问 `http://localhost:5555` 查看任务状态
- **Redis 监控**: `redis-cli info` 查看性能指标
- **应用日志**: 查看 `logs/` 目录下的日志文件

#### 性能优化
- **Redis 优化**: 配置内存策略和持久化
- **Celery 优化**: 调整 Worker 并发数和任务路由
- **FastAPI 优化**: 使用 Gunicorn + Uvicorn Workers

## 📞 前端集成示例

### JavaScript 示例
```javascript
class WritingAssistant {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.eventSource = null;
  }

  // 创建写作任务
  async createTask(config) {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'user_001',
        config: config
      })
    });
    return await response.json();
  }

  // 监听实时进度
  listenToProgress(conversationId, callbacks = {}) {
    this.eventSource = new EventSource(
      `${this.baseUrl}/api/v1/events/${conversationId}`
    );

    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.event_type) {
        case 'progress_update':
          callbacks.onProgress?.(data);
          break;
        case 'interrupt_request':
          callbacks.onInterrupt?.(data);
          break;
        case 'task_complete':
          callbacks.onComplete?.(data);
          break;
      }
    };
  }
}

// 使用示例
const assistant = new WritingAssistant();

const task = await assistant.createTask({
  topic: "Vue.js 3.0 新特性详解",
  max_words: 1500,
  style: "technical",
  language: "zh",
  mode: "interactive"
});

assistant.listenToProgress(task.session_id, {
  onProgress: (data) => console.log(`进度: ${data.progress}%`),
  onComplete: (data) => console.log('任务完成!')
});
```

---

## 📋 总结

这是一个**生产级的智能写作助手系统**，集成了以下核心能力：

### ✨ 核心优势
- **🤖 智能化**: AI 自动研究和写作，质量高
- **⚡ 实时性**: 流式输出，用户可实时查看写作进度  
- **🔄 交互式**: 支持用户参与和确认，确保内容符合要求
- **🛠️ 稳定性**: 经过架构重构优化，运行更稳定可靠
- **🚀 易部署**: 提供完整的开发和生产环境部署方案
- **📚 易集成**: 详细的 API 文档和前端集成示例

### 🎯 适用场景
- 📝 技术文档写作
- 📰 新闻文章生成  
- 📚 学习资料整理
- 💼 商业报告撰写
- 🎓 学术论文辅助

**注意**: 这是一个企业级的 LangGraph 智能写作解决方案，适合需要高可靠性、可扩展性和专业写作能力的应用场景。
