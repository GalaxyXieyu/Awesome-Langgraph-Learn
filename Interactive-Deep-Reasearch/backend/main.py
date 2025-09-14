"""FastAPI and Celery service for the Interactive Deep Research graph.
Provides asynchronous task execution with Redis checkpoint storage and
both API and terminal interfaces.

🎯 简化版架构 (2024年12月更新):
- 使用新的4个核心消息类型: processing, content, thinking, interrupt
- 兼容旧格式消息，自动转换为新格式
- 基于 writer/WriterDocs.md 的最新简化设计
"""
import asyncio
import json
import os
import uuid
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery import Celery
import redis
from langchain_core.runnables import RunnableConfig

from graph import create_deep_research_graph
from state import create_simple_state
from utils import process_chunk, generate_stream_events

# ---------------------------------------------------------------------------
# Redis & Celery configuration
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
PG_URL = os.environ.get("PG_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
celery_app = Celery("deep_research", broker=REDIS_URL, backend=REDIS_URL)


def get_checkpointer():
    """
    获取 checkpoint saver

    根据环境配置选择使用 PostgreSQL 或内存存储
    """
    # 检查是否启用 PostgreSQL checkpoint
    use_postgres = os.environ.get("USE_POSTGRES_CHECKPOINT", "false").lower() == "true"

    # 如果有 PG_URL 且启用了 PostgreSQL checkpoint，则使用 PostgreSQL
    if use_postgres and PG_URL:
        try:
            from config.checkpoint import ResearchPostgresSaver
            print("🔗 使用 PostgreSQL checkpoint saver")
            print(f"🔗 数据库: {PG_URL.split('@')[1] if '@' in PG_URL else 'unknown'}")
            checkpointer = ResearchPostgresSaver(PG_URL)
            checkpointer.setup()  # 创建表结构
            return checkpointer
        except Exception as e:
            print(f"❌ PostgreSQL checkpoint saver 初始化失败: {e}")
            print("🔄 回退到内存存储")
    elif PG_URL:
        print("💡 检测到 PG_URL 配置，但未启用 PostgreSQL checkpoint")
        print("💡 要启用请设置: USE_POSTGRES_CHECKPOINT=true")

    # 默认使用内存存储
    print("💾 使用内存 checkpoint saver")
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()


# ---------------------------------------------------------------------------
# Celery task that executes the research graph asynchronously
# ---------------------------------------------------------------------------
@celery_app.task(name="run_research_task")
def run_research_task(task_data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """Execute the deep research graph and store progress in Redis streams."""

    async def _runner() -> Dict[str, Any]:
        workflow = create_deep_research_graph()
        checkpointer = get_checkpointer()
        graph = workflow.compile(checkpointer=checkpointer)

        # 从 task_data 提取必要信息
        user_id = task_data.get("user_id", "user")
        topic = task_data.get("topic", "")
        mode = task_data.get("mode", "copilot")
        
        # 创建状态时传递 mode 参数
        state = create_simple_state(topic, user_id=user_id, mode=mode)
        state["session_id"] = task_id
        config = RunnableConfig(configurable={"thread_id": task_id})

        # 使用writer/core.py的简化版标准化处理器
        from writer.core import AgentWorkflowProcessor, create_stream_writer
        from writer.config import get_writer_config

        # 创建简化版消息处理器 - 支持新的4个核心消息类型
        config_obj = get_writer_config()
        writer = create_stream_writer("research_task", "main", config=config_obj)
        processor = AgentWorkflowProcessor(writer, config=config_obj)

        async for chunk in graph.astream(state, config, stream_mode=["custom", "updates", "messages"]):
            # 超简化：graph chunk 转化一层到 redis
            process_chunk(chunk, task_id, redis_client, processor)
        redis_client.hset(f"task:{task_id}", "status", "completed")
        return {"status": "completed"}

    return asyncio.run(_runner())

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(title="Interactive Deep Research")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateTask(BaseModel):
    topic: str
    user_id: str = "user"
    mode: str = "copilot"
    report_type: str = "comprehensive"
    target_audience: str = "general"
    depth_level: str = "moderate"
    max_sections: int = 5
    target_length: int = 1000
    language: str = "zh"
    style: str = "professional"

@app.post("/research/tasks")
async def create_task(req: CreateTask):
    task_id = uuid.uuid4().hex[:8]  # 移除task_前缀
    # 传递完整的请求数据到 Celery 任务
    result = run_research_task.apply_async(args=[req.dict(), task_id])
    redis_client.hset(
        f"task:{task_id}",
        mapping={
            "status": "pending",
            "topic": req.topic,
            "user_id": req.user_id,
            "mode": req.mode,
            "report_type": req.report_type,
            "celery_id": result.id,
        },
    )
    return {"task_id": task_id}


@app.get("/research/tasks/{task_id}")
async def get_task(task_id: str):
    data = redis_client.hgetall(f"task:{task_id}")
    if not data:
        raise HTTPException(status_code=404, detail="task not found")
    return data


@app.get("/research/tasks/{task_id}/stream")
async def stream_task(task_id: str):
    """事件流 - 使用抽取的流式处理函数"""
    return StreamingResponse(
        generate_stream_events(task_id, redis_client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.post("/research/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    data = redis_client.hgetall(f"task:{task_id}")
    if not data:
        raise HTTPException(status_code=404, detail="task not found")
    celery_id = data.get("celery_id")
    if celery_id:
        celery_app.control.revoke(celery_id, terminate=True)
    redis_client.hset(f"task:{task_id}", "status", "canceled")
    redis_client.xadd(f"events:{task_id}", {"data": json.dumps({"status": "canceled"})})
    return {"status": "canceled"}


# ---------------------------------------------------------------------------
# Terminal usage
# ---------------------------------------------------------------------------
def stop(topic: str, user_id: str = "cli") -> None:
    """Run the research graph and print events to stdout - 支持简化版消息格式."""

    async def _run() -> None:
        workflow = create_deep_research_graph()
        checkpointer = get_checkpointer()
        graph = workflow.compile(checkpointer=checkpointer)
        state = create_simple_state(topic, user_id=user_id)

        # 使用简化版处理器
        from writer.core import AgentWorkflowProcessor, create_stream_writer
        from writer.config import get_writer_config

        config_obj = get_writer_config()
        writer = create_stream_writer("terminal", "cli", config=config_obj)
        processor = AgentWorkflowProcessor(writer, config=config_obj)

        try:
            async for chunk in graph.astream(state, stream_mode=["custom", "updates", "messages"]):
                # 超简化：直接处理chunk输出到终端
                if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "custom":
                    data = chunk[1]
                    # 简单转换
                    if data.get('message_type') == 'interrupt_request':
                        data['message_type'] = 'interrupt'
                    print(json.dumps(data, ensure_ascii=False))
                else:
                    # 使用processor处理其他格式
                    result = processor.process_chunk(chunk)
                    if 'flat_data' in result:
                        print(json.dumps(result['flat_data'], ensure_ascii=False))
        except KeyboardInterrupt:
            pass
    asyncio.run(_run())


if __name__ == "__main__":
    import uvicorn
    print("🚀 启动智能报告生成器后端服务...")
    print("📊 API文档: http://localhost:8000/docs")
    print("🔗 前端地址: http://localhost:3000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
