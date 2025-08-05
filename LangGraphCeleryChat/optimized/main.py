"""
LangGraph Celery Chat - 优化简化版
参考 ReActAgentsTest 的简洁实现，保持核心 graph 代码不变
总代码量 < 500 行
"""

import json
import uuid
import time
import logging
import asyncio
from typing import Dict, Any, Optional, cast
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from celery import Celery
import redis
import aioredis
from langchain_core.runnables import RunnableConfig

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 配置和初始化
# ============================================================================

# Redis 配置
REDIS_URL = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# 异步Redis客户端 (用于事件流)
async_redis_client = None

async def get_async_redis():
    """获取异步Redis客户端"""
    global async_redis_client
    if async_redis_client is None:
        async_redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return async_redis_client

# Celery 配置
celery_app = Celery(
    "writing_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["main"]  # 包含当前模块
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)

# ============================================================================
# 请求模型
# ============================================================================

class TaskRequest(BaseModel):
    user_id: str
    topic: str
    max_words: int = 2000
    style: str = "professional"
    language: str = "zh"
    mode: str = "interactive"

class ResumeRequest(BaseModel):
    response: str = "yes"
    approved: bool = True

# ============================================================================
# Celery 任务
# ============================================================================

@celery_app.task(bind=True)
def execute_writing_task(self, user_id: str, session_id: str, task_id: str, config_data: Dict[str, Any]):
    """执行写作任务 - 直接调用 LangGraph"""
    
    async def run_workflow():
        try:
            # 导入你的核心 graph (保持不变)
            from graph.graph import create_writing_assistant_graph
            
            # 更新任务状态
            redis_client.hset(f"task:{task_id}", "status", "running")
            
            # 创建图实例
            graph = create_writing_assistant_graph()
            
            # 准备初始状态
            initial_state = {
                "topic": config_data.get("topic"),
                "user_id": user_id,
                "max_words": config_data.get("max_words", 2000),
                "style": config_data.get("style", "professional"),
                "language": config_data.get("language", "zh"),
                "mode": config_data.get("mode", "interactive"),
                "outline": None,
                "article": None,
                "search_results": [],
                "messages": []
            }
            
            # 执行工作流 - 直接使用 LangGraph
            config = cast(RunnableConfig, {"configurable": {"thread_id": task_id}})
            
            logger.info(f"开始执行任务: {task_id}, 主题: {config_data.get('topic')}")
            
            final_result = None
            interrupted = False
            
            # 流式执行并处理输出
            async for chunk in graph.astream(initial_state, config, stream_mode=["updates"]):
                logger.info(f"收到输出: {chunk}")
                
                # 写入事件流 - 增强版本，显示详细生成过程
                try:
                    # 将LangGraph输出转换为标准事件格式
                    if isinstance(chunk, (list, tuple)) and len(chunk) == 2:
                        stream_type, data = chunk
                        if stream_type == "updates" and isinstance(data, dict):
                            # 提取节点名称作为步骤信息
                            step_name = list(data.keys())[0] if data else "unknown"
                            step_data = data.get(step_name, {})

                            # 提取详细内容
                            content_info = {}
                            if isinstance(step_data, dict):
                                # 提取消息内容
                                if 'messages' in step_data:
                                    messages = step_data['messages']
                                    if messages and len(messages) > 0:
                                        last_msg = messages[-1]
                                        if hasattr(last_msg, 'content'):
                                            content = last_msg.content
                                            content_info = {
                                                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                                                "content_length": len(content),
                                                "message_type": type(last_msg).__name__
                                            }

                                # 提取其他有用信息
                                for key, value in step_data.items():
                                    if key != 'messages' and isinstance(value, (str, int, float, bool)):
                                        content_info[key] = value

                            event_data = {
                                "type": "progress_update",
                                "task_id": task_id,
                                "step": step_name,
                                "content_info": content_info,
                                "data": data,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            event_data = {
                                "type": "raw_update",
                                "task_id": task_id,
                                "data": chunk,
                                "timestamp": datetime.now().isoformat()
                            }
                    else:
                        event_data = {
                            "type": "raw_update",
                            "task_id": task_id,
                            "data": chunk,
                            "timestamp": datetime.now().isoformat()
                        }

                    redis_client.xadd(
                        f"events:{task_id}",
                        {
                            "timestamp": str(time.time()),
                            "data": json.dumps(event_data, default=str, ensure_ascii=False)
                        }
                    )
                except Exception as e:
                    logger.error(f"写入事件流失败: {e}")
                
                # 检查中断
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    stream_type, data = chunk
                    if stream_type == "updates" and "__interrupt__" in data:
                        interrupted = True
                        interrupt_info = data["__interrupt__"]
                        logger.info(f"检测到中断: {interrupt_info}")
                        
                        # 更新任务状态为暂停
                        redis_client.hset(f"task:{task_id}", "status", "paused")
                        
                        # 发送中断事件
                        interrupt_event = {
                            "type": "interrupt_request",
                            "task_id": task_id,
                            "interrupt_type": "confirmation",
                            "title": "需要确认",
                            "message": "请确认是否继续",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        redis_client.xadd(
                            f"events:{task_id}",
                            {
                                "timestamp": str(time.time()),
                                "data": json.dumps(interrupt_event, ensure_ascii=False)
                            }
                        )
                        return {"interrupted": True, "task_id": task_id}
                
                final_result = chunk
            
            # 任务完成
            if not interrupted and final_result:
                # 提取结果
                result_data = {}
                if isinstance(final_result, tuple) and len(final_result) == 2:
                    _, data = final_result
                    if isinstance(data, dict):
                        # 查找文章生成节点的结果
                        for key, value in data.items():
                            if isinstance(value, dict):
                                result_data.update({
                                    "outline": value.get("outline"),
                                    "article": value.get("article"),
                                    "search_results": value.get("search_results", [])
                                })
                                break
                
                # 更新任务状态为完成
                redis_client.hset(f"task:{task_id}", mapping={
                    "status": "completed",
                    "result": json.dumps(result_data, default=str, ensure_ascii=False),
                    "completed_at": datetime.now().isoformat()
                })

                # 发送完成事件到事件流
                completion_event = {
                    "type": "task_complete",
                    "task_id": task_id,
                    "status": "completed",
                    "result": result_data,
                    "timestamp": datetime.now().isoformat()
                }

                try:
                    redis_client.xadd(
                        f"events:{task_id}",
                        {
                            "timestamp": str(time.time()),
                            "data": json.dumps(completion_event, default=str, ensure_ascii=False)
                        }
                    )
                except Exception as e:
                    logger.error(f"发送完成事件失败: {e}")

                logger.info(f"任务完成: {task_id}")
                return {"completed": True, "result": result_data}
            
        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            redis_client.hset(f"task:{task_id}", mapping={
                "status": "failed",
                "error": str(e)
            })

            # 发送失败事件到事件流
            failure_event = {
                "type": "task_failed",
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

            try:
                redis_client.xadd(
                    f"events:{task_id}",
                    {
                        "timestamp": str(time.time()),
                        "data": json.dumps(failure_event, default=str, ensure_ascii=False)
                    }
                )
            except Exception as xe:
                logger.error(f"发送失败事件失败: {xe}")

            raise
    
    return asyncio.run(run_workflow())


@celery_app.task(bind=True)
def resume_writing_task(self, user_id: str, session_id: str, task_id: str, user_response: str):
    """恢复写作任务 - 参考 ReActAgentsTest 的简单实现"""
    
    async def resume_workflow():
        try:
            from graph.graph import create_writing_assistant_graph
            
            # 更新任务状态为运行中
            redis_client.hset(f"task:{task_id}", "status", "running")
            
            # 创建图实例
            graph = create_writing_assistant_graph()
            config = cast(RunnableConfig, {"configurable": {"thread_id": task_id}})
            
            logger.info(f"恢复任务: {task_id}, 用户响应: {user_response}")
            
            # 简单的恢复调用 - 参考 ReActAgentsTest
            class Command:
                def __init__(self, resume=None):
                    self.resume = resume
            
            # 执行恢复
            final_result = None
            interrupted = False
            
            async for chunk in graph.astream(Command(resume=user_response), config, stream_mode=["updates"]):
                # 写入事件流
                redis_client.xadd(
                    f"events:{task_id}",
                    {
                        "timestamp": str(time.time()),
                        "data": json.dumps(chunk, default=str, ensure_ascii=False)
                    }
                )
                
                # 检查中断
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    stream_type, data = chunk
                    if stream_type == "updates" and "__interrupt__" in data:
                        interrupted = True
                        redis_client.hset(f"task:{task_id}", "status", "paused")
                        return {"interrupted": True, "task_id": task_id}
                
                final_result = chunk
            
            # 处理完成结果
            if not interrupted:
                result_data = {}
                if isinstance(final_result, tuple) and len(final_result) == 2:
                    _, data = final_result
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, dict):
                                result_data.update({
                                    "outline": value.get("outline"),
                                    "article": value.get("article"),
                                    "search_results": value.get("search_results", [])
                                })
                                break
                
                redis_client.hset(f"task:{task_id}", mapping={
                    "status": "completed", 
                    "result": json.dumps(result_data, default=str, ensure_ascii=False)
                })
                
                return {"completed": True, "result": result_data}
                
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            redis_client.hset(f"task:{task_id}", mapping={"status": "failed", "error": str(e)})
            raise
    
    return asyncio.run(resume_workflow())

# ============================================================================
# FastAPI 应用
# ============================================================================

app = FastAPI(
    title="LangGraph Celery Chat - 优化版",
    version="1.0.0",
    description="简化版实现，保持核心功能"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "LangGraph Celery Chat - 优化版", "status": "running"}

@app.get("/health")
async def health():
    redis_status = "ok" if redis_client.ping() else "error"
    return {"status": "ok", "services": {"redis": redis_status, "celery": "ok"}}

# ============================================================================
# 核心 API
# ============================================================================

@app.post("/api/v1/tasks")
async def create_task(request: TaskRequest):
    """创建任务 - 参考 ReActAgentsTest"""
    try:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        session_id = f"session_{request.user_id}_{int(time.time())}"
        
        # 存储任务信息
        task_data = {
            "task_id": task_id,
            "session_id": session_id,
            "user_id": request.user_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "config": json.dumps(request.model_dump())
        }
        
        redis_client.hset(f"task:{task_id}", mapping=task_data)
        redis_client.expire(f"task:{task_id}", 3600)
        
        # 启动 Celery 任务
        celery_task = execute_writing_task.delay(
            user_id=request.user_id,
            session_id=session_id,
            task_id=task_id,
            config_data=request.model_dump()
        )
        
        logger.info(f"创建任务: {task_id}")
        
        return {
            "task_id": task_id,
            "session_id": session_id,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 解析 JSON 字段
        if "config" in task_data:
            task_data["config"] = json.loads(task_data["config"])
        if "result" in task_data:
            task_data["result"] = json.loads(task_data["result"])
            
        return task_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/{task_id}/resume")
async def resume_task(task_id: str, request: ResumeRequest):
    """恢复任务"""
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        status = task_data.get("status")
        if status not in ["paused"]:
            raise HTTPException(status_code=400, detail=f"任务状态 {status} 不支持恢复")
        
        # 启动恢复任务
        celery_task = resume_writing_task.delay(
            user_id=task_data.get("user_id"),
            session_id=task_data.get("session_id"),
            task_id=task_id,
            user_response=request.response
        )
        
        return {"message": "任务已恢复", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/events/{task_id}")
async def get_event_stream(task_id: str):
    """事件流 - 真正的异步版本 (aioredis)"""

    async def event_generator():
        stream_name = f"events:{task_id}"
        last_id = "0"

        # 获取异步Redis客户端
        async_redis = await get_async_redis()

        # 立即发送连接确认
        yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id})}\n\n"

        try:
            # 异步检查Redis连接
            await async_redis.ping()
            yield f"data: {json.dumps({'type': 'debug', 'message': 'Redis连接正常'})}\n\n"

            # 异步检查流是否存在
            exists = await async_redis.exists(stream_name)
            yield f"data: {json.dumps({'type': 'debug', 'message': f'流存在: {exists}'})}\n\n"

            if exists:
                # 异步获取流长度
                length = await async_redis.xlen(stream_name)
                yield f"data: {json.dumps({'type': 'debug', 'message': f'流长度: {length}'})}\n\n"

                # 异步读取所有现有消息
                all_messages = await async_redis.xrange(stream_name)
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

            # 异步监听新消息
            timeout_count = 0
            while timeout_count < 120:  # 增加到120次 (2分钟)
                # 真正的异步xread - 不会阻塞事件循环！
                try:
                    events = await async_redis.xread({stream_name: last_id}, count=10, block=1000)

                    if events:
                        timeout_count = 0  # 重置超时计数
                        for stream, messages in events:
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

                except asyncio.TimeoutError:
                    timeout_count += 1
                    yield f"data: {json.dumps({'type': 'heartbeat', 'count': timeout_count})}\n\n"

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)