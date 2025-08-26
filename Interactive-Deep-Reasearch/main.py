"""FastAPI and Celery service for the Interactive Deep Research graph.
Provides asynchronous task execution with Redis checkpoint storage and
both API and terminal interfaces.
"""
import argparse
import asyncio
import json
import os
import uuid
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
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
    """Select Redis or Postgres checkpointer based on environment."""
    if PG_URL:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        return AsyncPostgresSaver.from_conn_string(PG_URL)
    else:
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver

        return AsyncRedisSaver.from_conn_string(REDIS_URL)


# ---------------------------------------------------------------------------
# Celery task that executes the research graph asynchronously
# ---------------------------------------------------------------------------
@celery_app.task(name="run_research_task")
def run_research_task(user_id: str, topic: str, task_id: str) -> Dict[str, Any]:
    """Execute the deep research graph and store progress in Redis streams."""

    async def _runner() -> Dict[str, Any]:
        workflow = create_deep_research_graph()
        async with get_checkpointer() as checkpointer:
            await checkpointer.asetup()
            graph = workflow.compile(checkpointer=checkpointer)

            state = create_simple_state(topic, user_id=user_id)
            state["session_id"] = task_id
            config = RunnableConfig(configurable={"thread_id": task_id})

            async for chunk in graph.astream(state, config, stream_mode=["updates", "messages"]):
                data = chunk[1] if isinstance(chunk, (list, tuple)) and len(chunk) == 2 and chunk[0] == "custom" else chunk
                redis_client.xadd(
                    f"events:{task_id}", {"data": json.dumps(data, ensure_ascii=False)}
                )
            redis_client.hset(f"task:{task_id}", "status", "completed")
        return {"status": "completed"}

    return asyncio.run(_runner())


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(title="Interactive Deep Research")


class CreateTask(BaseModel):
    topic: str
    user_id: str = "user"


@app.post("/research/tasks")
async def create_task(req: CreateTask):
    task_id = f"task_{uuid.uuid4().hex[:8]}"
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
    async def event_stream():
        last_id = "0-0"
        while True:
            status = redis_client.hget(f"task:{task_id}", "status")
            if status in {"completed", "canceled"}:
                break
            results = redis_client.xread({f"events:{task_id}": last_id}, block=1000, count=1)
            if not results:
                continue
            _, messages = results[0]
            for _id, fields in messages:
                last_id = _id
                yield f"data: {fields['data']}\n\n"
        yield f"data: {json.dumps({'status': status})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
        async with get_checkpointer() as checkpointer:
            await checkpointer.asetup()
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
    parser = argparse.ArgumentParser(description="Run deep research from terminal")
    parser.add_argument("topic", help="research topic")
    parser.add_argument("--user", default="cli", help="user id")
    args = parser.parse_args()
    run_from_terminal(args.topic, args.user)
