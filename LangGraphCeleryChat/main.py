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
from redis import asyncio as aioredis
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



async def _process_stream_chunk(chunk, task_id):
    """处理流式输出的单个 chunk - 提取的公共函数"""
    try:
        event_data = None

        if isinstance(chunk, (list, tuple)) and len(chunk) == 2:
            stream_type, data = chunk

            if stream_type == "updates" and isinstance(data, dict):
                # 处理更新事件
                step_name = list(data.keys())[0] if data else "unknown"
                step_data = data.get(step_name, {})

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

            elif stream_type == "custom" and isinstance(data, dict):
                # 处理自定义事件 - 特别处理包含复杂内容的事件
                event_data = {
                    "type": "custom_event",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                    "step": data.get("step", "unknown"),
                    "status": data.get("status", ""),
                    "progress": data.get("progress", 0)
                }

                # 如果有 current_content，特别处理
                if "current_content" in data:
                    current_content = data["current_content"]
                    if isinstance(current_content, dict):
                        # 提取关键信息用于前端显示
                        content_summary = {
                            "title": current_content.get("title", ""),
                            "sections_count": len(current_content.get("sections", [])),
                            "has_content": bool(current_content)
                        }

                        # 如果有章节，提取章节标题
                        if "sections" in current_content:
                            sections = current_content["sections"]
                            if isinstance(sections, list) and sections:
                                content_summary["section_titles"] = [
                                    section.get("title", "") for section in sections[:5]  # 只取前5个
                                ]

                        event_data["content_summary"] = content_summary
                        event_data["full_content"] = current_content  # 保留完整内容
                    else:
                        event_data["current_content"] = current_content

                # 添加其他字段
                for key, value in data.items():
                    if key not in ["step", "status", "progress", "current_content"]:
                        event_data[key] = value
            else:
                # 其他类型的输出
                event_data = {
                    "type": "raw_output",
                    "task_id": task_id,
                    "stream_type": stream_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
        else:
            # 非元组格式的输出
            event_data = {
                "type": "raw_output",
                "task_id": task_id,
                "data": chunk,
                "timestamp": datetime.now().isoformat()
            }

        # 写入事件流
        if event_data:
            redis_client.xadd(
                f"events:{task_id}",
                {
                    "timestamp": str(time.time()),
                    "data": json.dumps(event_data, default=str, ensure_ascii=False)
                }
            )

        return event_data

    except Exception as e:
        logger.error(f"处理流式输出失败: {e}")
        return None

def _check_for_interruption(chunk, task_id):
    """检查是否有中断请求 - 提取的公共函数"""
    if isinstance(chunk, tuple) and len(chunk) == 2:
        stream_type, data = chunk
        if stream_type == "updates" and isinstance(data, dict) and "__interrupt__" in data:
            interrupt_info = data["__interrupt__"]

            # 更新任务状态为暂停
            redis_client.hset(f"task:{task_id}", "status", "paused")

            # 发送中断事件 - 提取真实的中断信息
            interrupt_event = {
                "type": "interrupt_request",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }

            # 提取中断信息 - 处理 Interrupt 对象
            interrupt_data = None

            # 处理 tuple 格式的中断信息
            if isinstance(interrupt_info, tuple) and len(interrupt_info) > 0:
                # interrupt_info 是 tuple，第一个元素是 Interrupt 对象
                interrupt_obj = interrupt_info[0]
                if hasattr(interrupt_obj, 'value'):
                    interrupt_data = interrupt_obj.value
                else:
                    interrupt_data = {"message": str(interrupt_obj)}

            elif hasattr(interrupt_info, 'value'):
                # 这是一个直接的 Interrupt 对象，提取其 value
                interrupt_data = interrupt_info.value
            elif isinstance(interrupt_info, dict):
                # 这是一个普通字典
                interrupt_data = interrupt_info
            else:
                # 其他类型，转换为字符串
                interrupt_data = {"message": str(interrupt_info)}

            # 从中断数据中提取具体内容
            if isinstance(interrupt_data, dict):
                interrupt_event.update({
                    "interrupt_type": interrupt_data.get("type", "confirmation"),
                    "title": interrupt_data.get("type", "需要确认"),
                    "message": interrupt_data.get("message", "请确认是否继续"),
                    "instructions": interrupt_data.get("instructions", ""),
                    "interrupt_data": interrupt_data  # 保留完整的中断数据（已经是可序列化的）
                })
            else:
                # 回退到默认值
                interrupt_event.update({
                    "interrupt_type": "confirmation",
                    "title": "需要确认",
                    "message": str(interrupt_data) if interrupt_data else "请确认是否继续",
                    "instructions": "请回复 'yes' 或 'no'",
                    "interrupt_data": {"raw": str(interrupt_data)}
                })

            try:
                json_data = json.dumps(interrupt_event, ensure_ascii=False)


                redis_client.xadd(
                    f"events:{task_id}",
                    {
                        "timestamp": str(time.time()),
                        "data": json_data
                    }
                )
            except Exception as e:
                logger.error(f"发送中断事件失败: {e}")

            return True
    return False

@celery_app.task(bind=True)
def execute_writing_task(self, user_id: str, session_id: str, task_id: str, config_data: Dict[str, Any]):
    """执行写作任务 - 重构简化版"""

    async def run_workflow():
        try:
            # 更新任务状态
            redis_client.hset(f"task:{task_id}", "status", "running")

            # 按照官方示例使用 AsyncRedisSaver
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from graph.graph import create_writing_assistant_graph

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
                "messages": [],
                "checkpointer": None
            }

            config = cast(RunnableConfig, {"configurable": {"thread_id": task_id}})
            logger.info(f"开始执行任务: {task_id}, 主题: {config_data.get('topic')}")

            final_result = None
            interrupted = False
            # 使用官方推荐的 AsyncRedisSaver 方式
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver

            async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
                await checkpointer.asetup()

                # 创建并编译图 - 强制重新创建
                workflow = create_writing_assistant_graph()
                graph = workflow.compile(checkpointer=checkpointer)
                logger.info(f"图编译完成，节点数: {len(workflow.nodes)}")

                # 异步流式执行
                async for chunk in graph.astream(initial_state, config, stream_mode=["updates", "custom"]):
                    # 处理输出
                    await _process_stream_chunk(chunk, task_id)

                    # 检查中断
                    if _check_for_interruption(chunk, task_id):
                        interrupted = True
                        return {"interrupted": True, "task_id": task_id}

                    final_result = chunk

            # 任务完成处理
            return await _handle_task_completion(task_id, final_result, interrupted)

        except Exception as e:
            return await _handle_task_failure(task_id, e)

    return asyncio.run(run_workflow())

async def _handle_task_completion(task_id: str, final_result, interrupted: bool):
    """处理任务完成 - 提取的公共函数"""
    if not interrupted and final_result:
        # 提取结果
        result_data = {}
        if isinstance(final_result, tuple) and len(final_result) == 2:
            _, data = final_result
            if isinstance(data, dict):
                # 查找文章生成节点的结果
                for value in data.values():
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

    return {"completed": False}

async def _handle_task_failure(task_id: str, error: Exception):
    """处理任务失败 - 提取的公共函数"""
    logger.error(f"任务执行失败: {task_id}, 错误: {error}")
    redis_client.hset(f"task:{task_id}", mapping={
        "status": "failed",
        "error": str(error)
    })

    # 发送失败事件到事件流
    failure_event = {
        "type": "task_failed",
        "task_id": task_id,
        "status": "failed",
        "error": str(error),
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

    raise error


@celery_app.task(bind=True)
def resume_writing_task(self, user_id: str, session_id: str, task_id: str, user_response: str):
    """恢复写作任务 - 参考 ReActAgentsTest 的简单实现"""
    
    async def resume_workflow():
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from graph.graph import create_writing_assistant_graph
            # 更新任务状态为运行中
            redis_client.hset(f"task:{task_id}", "status", "running")     
            config = cast(RunnableConfig, {"configurable": {"thread_id": task_id}})
            # 使用与 execute_writing_task 相同的 AsyncRedisSaver 模式
            from langgraph.types import Command
            interrupted = False
            # 使用官方推荐的 AsyncRedisSaver
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver

            async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
                await checkpointer.asetup()

                # 创建并编译图 - 强制重新创建
                workflow = create_writing_assistant_graph()
                graph = workflow.compile(checkpointer=checkpointer)

                async for chunk in graph.astream(Command(resume=user_response), config, stream_mode=["updates", "custom"]):
                    print("--------------------------------")
                    print("恢复任务收到 chunk", chunk)
                    print("--------------------------------")
                    # 简单记录 chunk 内容
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        stream_type, data = chunk
                        logger.info(f"  流类型: {stream_type}")
                        if isinstance(data, dict):
                            logger.info(f"  数据键: {list(data.keys())}")
                            if stream_type == "updates":
                                # 记录节点执行
                                node_names = [k for k in data.keys() if k != "__interrupt__"]
                                if node_names:
                                    logger.info(f"  执行节点: {node_names}")

                    # 写入事件流
                    redis_client.xadd(
                        f"events:{task_id}",
                        {
                            "timestamp": str(time.time()),
                            "data": json.dumps(chunk, default=str, ensure_ascii=False)
                        }
                    )

                    # # 检查中断 - 使用统一的中断处理函数
                    is_interrupt = _check_for_interruption(chunk, task_id)
                    if is_interrupt:
                        interrupted = True
                        return {"interrupted": True, "task_id": task_id}

            # 处理完成结果
                logger.info(f"🔍 恢复任务结束检查: interrupted={interrupted}, chunk_count={chunk_count}")

                if not interrupted:
                    logger.info("✅ 任务未中断，开始处理完成结果")
                    result_data = {}

                    # 如果没有处理任何 chunks，尝试获取当前状态
                    if chunk_count == 0:
                        logger.info("⚠️ 没有处理任何 chunks，检查当前图状态...")
                        try:
                            # 获取当前状态
                            current_state = await checkpointer.aget_tuple(config)
                            if current_state and hasattr(current_state, 'checkpoint') and current_state.checkpoint:
                                state_data = current_state.checkpoint.get('channel_values', {})
                                logger.info(f"📊 从 checkpoint 获取状态键: {list(state_data.keys())}")

                                # 提取结果数据
                                result_data = {
                                    "outline": state_data.get("outline"),
                                    "article": state_data.get("article"),
                                    "search_results": state_data.get("search_results", []),
                                    "topic": state_data.get("topic"),
                                    "enhancement_suggestions": state_data.get("enhancement_suggestions", [])
                                }

                                # 检查是否真的完成了
                                if result_data.get("article"):
                                    logger.info("✅ 找到生成的文章，任务确实完成")
                                else:
                                    logger.warning("⚠️ 没有找到生成的文章，任务可能未完全完成")
                            else:
                                logger.warning("⚠️ 无法获取 checkpoint 状态")
                        except Exception as e:
                            logger.error(f"获取 checkpoint 状态失败: {e}")

                    redis_client.hset(f"task:{task_id}", mapping={
                        "status": "completed",
                        "result": json.dumps(result_data, default=str, ensure_ascii=False)
                    })

                    logger.info(f"📋 任务完成，结果数据键: {list(result_data.keys())}")
                    if result_data.get("article"):
                        article_length = len(result_data["article"]) if isinstance(result_data["article"], str) else 0
                        logger.info(f"✅ 文章生成成功，长度: {article_length} 字符")
                    else:
                        logger.warning("⚠️ 任务完成但没有生成文章")

                    logger.info(f"🎯 返回 completed=True，result 键: {list(result_data.keys())}")
                    return {"completed": True, "result": result_data}
                else:
                    logger.info(f"🔄 任务被中断，返回 interrupted=True")

        except Exception as e:
            redis_client.hset(f"task:{task_id}", mapping={"status": "failed", "error": str(e)})
            raise
    
    return asyncio.run(resume_workflow())

# ============================================================================
# FastAPI 应用
# ============================================================================

app = FastAPI(
    title="LangGraph-Celery-Redis-Stream",
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