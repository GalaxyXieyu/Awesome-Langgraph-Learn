# LangGraph Celery Chat - 优化版

基于 ReActAgentsTest 参考代码的简洁实现，总代码量 < 500 行。

## 核心优势

- **单文件架构**: 只有一个 `main.py` 文件（400+ 行）
- **直接调用**: FastAPI → Celery → LangGraph，无中间层
- **保持核心功能**: 你的 `graph.py` 和 `tools.py` 完全不变
- **简化状态管理**: Redis 存基础状态，LangGraph 管理 checkpoint

## 项目结构

```
optimized/
├── main.py           # 唯一的主文件（FastAPI + Celery + 任务）
├── graph/           # 你的核心代码（不变）
│   ├── graph.py     # 复制自原项目
│   └── tools.py     # 复制自原项目
├── requirements.txt # 依赖列表
└── README.md       # 说明文档
```

## 快速启动

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   python install_deps.py  # 安装测试依赖
   ```

2. **一键启动**
   ```bash
   ./run.sh
   ```

   或手动启动：
   ```bash
   # 启动 Celery Worker
   celery -A main.celery_app worker --loglevel=info
   
   # 启动 FastAPI 服务
   python main.py
   ```

## 测试接口

### 快速测试
```bash
python quick_test.py
```

### 完整测试（包含中断流程）
```bash
python test_api.py
```

这个测试会：
1. 创建写作任务
2. 监控事件流
3. 等待 LangGraph 中断
4. 模拟用户确认
5. 恢复任务执行
6. 验证最终结果

## API 接口

### 创建任务
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "user123",
       "topic": "人工智能的发展趋势",
       "max_words": 2000,
       "style": "professional",
       "language": "zh"
     }'
```

### 查看任务状态
```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}"
```

### 恢复中断任务
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/resume" \
     -H "Content-Type: application/json" \
     -d '{"response": "yes", "approved": true}'
```

### 实时事件流
```bash
curl "http://localhost:8000/api/v1/events/{task_id}"
```

## 与原版本对比

| 项目 | 原版本 | 优化版本 |
|------|--------|----------|
| 总文件数 | 20+ | 4 |
| 总代码行数 | 2000+ | 400+ |
| 核心文件 | main.py (759行) + tasks.py (341行) + adapter.py (705行) | main.py (400行) |
| 状态管理 | 3套系统 | 2套系统 |
| 中间层 | WorkflowAdapter + CeleryStreamWriter + InterruptManager | 无 |

## 配置说明

所有配置都在 `main.py` 顶部：

```python
# Redis 配置
REDIS_URL = "redis://localhost:6379/0"

# Celery 配置
celery_app = Celery("writing_tasks", broker=REDIS_URL, backend=REDIS_URL)
```

## 核心设计思路

1. **去掉 WorkflowAdapter**: 直接在 Celery 任务中调用 LangGraph
2. **简化流式输出**: 直接写入 Redis Streams，无复杂封装
3. **统一 ID 管理**: task_id 即是 thread_id，避免映射混乱
4. **保持兼容性**: API 接口与原版本完全兼容

这就是"少即是多"的典型例子！