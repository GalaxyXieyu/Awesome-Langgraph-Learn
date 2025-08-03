# LangGraph Celery Chat System

基于 HTTPS + Celery + Redis 的 LangGraph 智能对话系统，专为生产环境设计。

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

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 启动 Redis 服务
redis-server

# 启动 Celery Worker
celery -A backend.celery_app worker --loglevel=info

# 启动 Celery Flower 监控
celery -A backend.celery_app flower

# 启动 FastAPI 服务
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 基本使用

```python
import requests

# 创建新任务
response = requests.post("https://localhost:8000/api/v1/tasks", json={
    "topic": "人工智能在医疗诊断中的应用",
    "mode": "interactive",
    "config": {
        "target_audience": "医疗专业人士",
        "depth_level": "deep",
        "target_length": 3000
    }
})

task_id = response.json()["task_id"]

# 监听事件流
import sseclient

events = sseclient.SSEClient(f"https://localhost:8000/api/v1/events/{session_id}")
for event in events:
    print(f"事件: {event.event}, 数据: {event.data}")
```

## 🔧 核心功能

### LangGraph 适配器
- **通用接口**: 支持任意 LangGraph 应用
- **Interrupt 处理**: 自动映射到 Redis Streams
- **状态管理**: 完整的任务状态持久化
- **错误恢复**: 自动重试和故障恢复

### 实时通信
- **Server-Sent Events**: 替代 WebSocket，更稳定
- **Redis Streams**: 高性能事件流处理
- **多客户端支持**: 支持多个前端同时连接

### 任务管理
- **异步执行**: Celery 分布式任务队列
- **任务持久化**: Redis 状态存储
- **进度跟踪**: 实时进度更新
- **会话恢复**: 支持断线重连

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

### Docker 部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

### 生产部署
1. 配置 Nginx 反向代理
2. 设置 SSL 证书
3. 配置 Redis 集群
4. 部署 Celery Workers
5. 启动监控服务

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
- **Redis 连接失败**: 检查 Redis 服务状态
- **Celery Worker 无响应**: 重启 Worker 进程
- **SSL 证书错误**: 检查证书配置和有效期

### 调试模式
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG

# 启动调试模式
uvicorn backend.app.main:app --reload --log-level debug
```

---

**注意**: 这是一个生产级的 LangGraph 集成方案，适合需要高可靠性和可扩展性的应用场景。
