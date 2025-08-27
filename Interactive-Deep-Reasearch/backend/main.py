"""FastAPI and Celery service for the Interactive Deep Research graph.
Provides asynchronous task execution with Redis checkpoint storage and
both API and terminal interfaces.
"""
import argparse
import asyncio
import json
import os
import time
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

# ---------------------------------------------------------------------------
# Redis & Celery configuration
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
PG_URL = os.environ.get("PG_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
celery_app = Celery("deep_research", broker=REDIS_URL, backend=REDIS_URL)


def get_checkpointer():
    """Use memory checkpointer for simplicity."""
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()


def convert_chunk_to_message(chunk, task_id):
    """将其他类型的chunk转换为消息格式"""
    current_time = time.time()

    # 处理messages格式 ('messages', (AIMessageChunk, metadata))
    if isinstance(chunk, tuple) and len(chunk) == 2:
        chunk_type, chunk_data = chunk

        if chunk_type == 'messages' and isinstance(chunk_data, tuple) and len(chunk_data) == 2:
            message_obj, metadata = chunk_data

            # 检查是否是AIMessageChunk
            if hasattr(message_obj, '__class__') and type(message_obj).__name__ == "AIMessageChunk":
                if hasattr(message_obj, 'content') and message_obj.content:
                    content = str(message_obj.content)
                    if content and content.strip():
                        return {
                            "message_type": "content_streaming",
                            "content": content,
                            "node": "ai_generator",
                            "timestamp": current_time,
                            "task_id": task_id,
                            "length": len(content),
                            "chunk_index": 0
                        }

    # 处理子图格式 (('subgraph_id',), 'messages'/'updates', data)
    if isinstance(chunk, tuple) and len(chunk) == 3:
        subgraph_ids, chunk_type, chunk_data = chunk

        # 提取agent名称
        agent_name = "unknown"
        if isinstance(subgraph_ids, tuple) and subgraph_ids:
            for subgraph_id in subgraph_ids:
                if isinstance(subgraph_id, str) and ':' in subgraph_id:
                    parts = subgraph_id.split(':')
                    if len(parts) >= 2:
                        potential_agent = parts[0]
                        if potential_agent in ['research', 'writing', 'content_creation', 'tools', 'intelligent_supervisor', 'outline_generation']:
                            agent_name = potential_agent
                            break

        if chunk_type == 'messages' and isinstance(chunk_data, tuple) and len(chunk_data) == 2:
            message_obj, metadata = chunk_data

            if hasattr(message_obj, '__class__') and type(message_obj).__name__ == "AIMessageChunk":
                if hasattr(message_obj, 'content') and message_obj.content:
                    content = str(message_obj.content)
                    if content and content.strip():
                        return {
                            "message_type": "content_streaming",
                            "content": content,
                            "node": agent_name,
                            "agent": agent_name,
                            "timestamp": current_time,
                            "task_id": task_id,
                            "length": len(content),
                            "chunk_index": 0
                        }

    # 默认返回None，表示无法处理
    return None

# ---------------------------------------------------------------------------
# Celery task that executes the research graph asynchronously
# ---------------------------------------------------------------------------
@celery_app.task(name="run_research_task")
def run_research_task(user_id: str, topic: str, task_id: str) -> Dict[str, Any]:
    """Execute the deep research graph and store progress in Redis streams."""

    async def _runner() -> Dict[str, Any]:
        workflow = create_deep_research_graph()
        checkpointer = get_checkpointer()
        graph = workflow.compile(checkpointer=checkpointer)

        state = create_simple_state(topic, user_id=user_id)
        state["session_id"] = task_id
        config = RunnableConfig(configurable={"thread_id": task_id})

        # 使用writer/core.py的标准化处理器
        from writer.core import AgentWorkflowProcessor, create_stream_writer
        from writer.config import get_writer_config

        # 创建消息处理器
        config_obj = get_writer_config()
        writer = create_stream_writer("research_task", "main", config=config_obj)
        processor = AgentWorkflowProcessor(writer, config=config_obj)

        async for chunk in graph.astream(state, config, stream_mode=["custom", "updates", "messages"]):
            try:
                # 处理('custom', {...})格式的数据
                if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == 'custom':
                    # 直接提取custom数据（这就是标准格式）
                    message_data = chunk[1]
                    if isinstance(message_data, dict):
                        message_data['task_id'] = task_id

                        # 写入Redis流
                        redis_client.xadd(
                            f"events:{task_id}",
                            {
                                "timestamp": str(time.time()),
                                "data": json.dumps(message_data, default=str, ensure_ascii=False)
                            }
                        )
                        continue

                # 使用标准化处理器处理其他格式的chunk
                result = processor.process_chunk(chunk)

                # 检查是否有扁平化数据（标准消息）
                if 'flat_data' in result:
                    flat_data = result['flat_data']
                    flat_data['task_id'] = task_id

                    # 写入Redis流
                    redis_client.xadd(
                        f"events:{task_id}",
                        {
                            "timestamp": str(time.time()),
                            "data": json.dumps(flat_data, default=str, ensure_ascii=False)
                        }
                    )

                # 检查是否处理了中断
                elif result.get('interrupt_processed'):
                    interrupt_message = {
                        "message_type": "interrupt_request",
                        "content": f"等待用户确认操作: {result.get('action', 'unknown')}",
                        "node": "interrupt_handler",
                        "timestamp": time.time(),
                        "task_id": task_id,
                        "interrupt_id": result.get('interrupt_id'),
                        "action": result.get('action'),
                        "args": result.get('args', {})
                    }

                    redis_client.xadd(
                        f"events:{task_id}",
                        {
                            "timestamp": str(time.time()),
                            "data": json.dumps(interrupt_message, default=str, ensure_ascii=False)
                        }
                    )

                # 处理其他类型的chunk（如AIMessageChunk）
                else:
                    processed_message = convert_chunk_to_message(chunk, task_id)
                    if processed_message:
                        redis_client.xadd(
                            f"events:{task_id}",
                            {
                                "timestamp": str(time.time()),
                                "data": json.dumps(processed_message, default=str, ensure_ascii=False)
                            }
                        )

            except Exception as e:
                # 发送错误消息
                error_message = {
                    "message_type": "error",
                    "content": f"处理消息时出错: {str(e)}",
                    "node": "error_handler",
                    "timestamp": time.time(),
                    "task_id": task_id,
                    "error_type": "ChunkProcessingError"
                }

                redis_client.xadd(
                    f"events:{task_id}",
                    {
                        "timestamp": str(time.time()),
                        "data": json.dumps(error_message, default=str, ensure_ascii=False)
                    }
                )
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


@app.post("/research/tasks")
async def create_task(req: CreateTask):
    task_id = uuid.uuid4().hex[:8]  # 移除task_前缀
    result = run_research_task.apply_async(args=[req.user_id, req.topic, task_id])
    redis_client.hset(
        f"task:{task_id}",
        mapping={
            "status": "pending",
            "topic": req.topic,
            "user_id": req.user_id,
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
    """事件流 - 基于参考实现的异步版本"""
    async def event_generator():
        stream_name = f"events:{task_id}"
        last_id = "0"

        # 立即发送连接确认
        yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id})}\n\n"

        try:
            # 检查流是否存在
            exists = redis_client.exists(stream_name)
            if exists:
                # 读取所有现有消息
                all_messages = redis_client.xrange(stream_name)
                for message_id, fields in all_messages:
                    try:
                        event_data = {
                            "id": message_id,
                            "timestamp": fields.get("timestamp"),
                            "data": json.loads(fields.get("data", "{}"))
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                        last_id = message_id
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'解析消息失败: {e}'})}\n\n"

            # 监听新消息
            timeout_count = 0
            while timeout_count < 120:  # 2分钟超时
                try:
                    # 检查任务状态
                    status = redis_client.hget(f"task:{task_id}", "status")
                    if status in {"completed", "canceled", "failed"}:
                        yield f"data: {json.dumps({'type': 'task_status', 'status': status})}\n\n"
                        break

                    # 读取新消息
                    results = redis_client.xread({stream_name: last_id}, block=1000, count=10)

                    if results:
                        timeout_count = 0  # 重置超时计数
                        _, messages = results[0]
                        for message_id, fields in messages:
                            try:
                                event_data = {
                                    "id": message_id,
                                    "timestamp": fields.get("timestamp"),
                                    "data": json.loads(fields.get("data", "{}"))
                                }
                                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                last_id = message_id
                            except Exception as e:
                                yield f"data: {json.dumps({'type': 'error', 'message': f'解析新消息失败: {e}'})}\n\n"
                    else:
                        timeout_count += 1
                        yield f"data: {json.dumps({'type': 'heartbeat', 'count': timeout_count})}\n\n"

                except Exception as e:
                    timeout_count += 1
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
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
def run_from_terminal(topic: str, user_id: str = "cli") -> None:
    """Run the research graph and print events to stdout."""

    async def _run() -> None:
        workflow = create_deep_research_graph()
        checkpointer = get_checkpointer()
        graph = workflow.compile(checkpointer=checkpointer)
        state = create_simple_state(topic, user_id=user_id)
        try:
            async for chunk in graph.astream(state, stream_mode=["updates", "messages"]):
                data = chunk[1] if isinstance(chunk, (list, tuple)) and len(chunk) == 2 and chunk[0] == "custom" else chunk
                print(json.dumps(data, ensure_ascii=False))
        except KeyboardInterrupt:
            pass
    asyncio.run(_run())


if __name__ == "__main__":
    import uvicorn
    print("🚀 启动智能报告生成器后端服务...")
    print("📊 API文档: http://localhost:8000/docs")
    print("🔗 前端地址: http://localhost:3000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
