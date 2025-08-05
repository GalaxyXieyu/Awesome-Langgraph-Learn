"""
FastAPI 主应用
基于 Celery + Redis 的 LangGraph 写作助手 API
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

# 抑制 asyncio 的 socket.send() 警告
logging.getLogger('asyncio').setLevel(logging.ERROR)

from ..models.schemas import (
    CreateTaskRequest, CreateTaskResponse, TaskStatusResponse,
    InterruptResponseRequest, SessionInfo, ErrorResponse,
    WritingTaskConfig, WritingMode, WritingStyle, TaskStatus,
    ConversationSummary, ResumeValidationResponse, ConversationContext
)
from ..celery_app.tasks import execute_writing_task, resume_writing_task, cancel_writing_task
from ..utils.config import get_config
from ..utils.redis_client import get_redis_client
from ..utils.session_manager import get_session_manager
from ..utils.conversation_service import get_conversation_service
from ..utils.logger import get_logger, setup_logging

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 获取配置
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动 LangGraph Celery Chat API")
    
    # 测试 Redis 连接
    redis_client = get_redis_client()
    if redis_client.ping():
        logger.info("✅ Redis 连接成功")
    else:
        logger.error("❌ Redis 连接失败")
    
    yield
    
    # 关闭时
    logger.info("关闭 LangGraph Celery Chat API")
    redis_client.close()


# 创建 FastAPI 应用
app = FastAPI(
    title=config.app_name,
    version=config.version,
    description="基于 Celery + Redis 的 LangGraph 写作助手 API",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=False,  # 设置为False以支持通配符
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "LangGraph Celery Chat API",
        "version": config.version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    redis_client = get_redis_client()
    redis_status = "ok" if redis_client.ping() else "error"
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": redis_status,
            "celery": "ok"  # 简化检查
        }
    }


# ============================================================================
# 会话管理 API
# ============================================================================

@app.post("/api/v1/sessions", response_model=SessionInfo)
async def create_session(user_id: str):
    """创建新会话"""
    try:
        session_manager = get_session_manager()
        session_id = await session_manager.create_session(user_id)
        
        return SessionInfo(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            active_tasks=[]
        )
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """获取会话信息"""
    try:
        session_manager = get_session_manager()
        session_data = await session_manager.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return SessionInfo(**session_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        session_manager = get_session_manager()
        success = await session_manager.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")

        return {"message": "会话已删除", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversations/{conversation_id}/summary", response_model=ConversationSummary)
async def get_conversation_summary(conversation_id: str):
    """获取会话摘要"""
    try:
        conversation_service = get_conversation_service()
        summary = await conversation_service.get_conversation_summary(conversation_id)

        if not summary:
            raise HTTPException(status_code=404, detail="会话不存在")

        return ConversationSummary(**summary)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conversation_service' in locals():
            await conversation_service.close()


@app.post("/api/v1/conversations/{conversation_id}/validate-resume", response_model=ResumeValidationResponse)
async def validate_resume_request(conversation_id: str, task_id: Optional[str] = None):
    """验证恢复请求"""
    try:
        conversation_service = get_conversation_service()
        is_valid, message = await conversation_service.validate_resume_request(conversation_id, task_id)

        # 获取额外信息
        conversation_exists = await conversation_service.check_conversation_exists(conversation_id)

        response = ResumeValidationResponse(
            is_valid=is_valid,
            message=message,
            conversation_exists=conversation_exists,
            can_resume=is_valid and conversation_exists
        )

        if not is_valid:
            response.suggested_action = "create_new" if not conversation_exists else "check_task_status"

        return response
    except Exception as e:
        logger.error(f"验证恢复请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conversation_service' in locals():
            await conversation_service.close()


# ============================================================================
# 任务管理 API
# ============================================================================

@app.post("/api/v1/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    """创建写作任务（支持会话恢复）"""
    try:
        # 使用会话服务判断是恢复还是创建
        conversation_service = get_conversation_service()
        session_id, is_resumed = await conversation_service.should_resume_or_create(
            request.conversation_id,
            request.user_id
        )

        # 生成任务 ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # 准备响应数据
        response_data = {
            "task_id": task_id,
            "session_id": session_id,
            "status": TaskStatus.PENDING,
            "is_resumed": is_resumed
        }

        # 如果是恢复模式，获取会话上下文
        if is_resumed:
            logger.info(f"🔄 恢复会话模式: {session_id}")
            context = await conversation_service.prepare_resume_context(session_id)
            response_data["conversation_context"] = context
            response_data["message"] = f"恢复会话成功，会话ID: {session_id}"
        else:
            logger.info(f"📝 创建新会话模式: {session_id}")
            response_data["message"] = f"创建新任务成功，会话ID: {session_id}"

        # 创建任务状态记录
        session_manager = get_session_manager()
        logger.info(f"正在创建任务状态记录: {task_id}")

        success = await session_manager.set_task_status(
            task_id=task_id,
            status="pending",
            user_id=request.user_id,
            session_id=session_id,
            metadata={
                "task_id": task_id,
                "session_id": session_id,
                "user_id": request.user_id,
                "config": request.config.model_dump(),
                "status": "pending",
                "current_step": "initializing",
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "is_resumed": is_resumed,
                "original_conversation_id": request.conversation_id
            }
        )

        if success:
            logger.info(f"✅ 任务状态记录创建成功: {task_id}")
        else:
            logger.error(f"❌ 任务状态记录创建失败: {task_id}")

        # 验证任务状态是否真的写入了
        verify_task = await session_manager.get_task_status(task_id)
        if verify_task:
            logger.info(f"✅ 验证成功，任务状态已写入: {task_id}")
        else:
            logger.error(f"❌ 验证失败，任务状态未写入: {task_id}")

        # 启动 Celery 任务
        celery_task = execute_writing_task.delay(
            user_id=request.user_id,
            session_id=session_id,
            task_id=task_id,
            config_data=request.config.model_dump(),
            is_resumed=is_resumed,
            original_conversation_id=request.conversation_id
        )

        logger.info(f"创建写作任务: {task_id}, Celery任务: {celery_task.id}")

        return CreateTaskResponse(**response_data)

    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 关闭会话服务连接
        if 'conversation_service' in locals():
            await conversation_service.close()


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        logger.info(f"🔍 查询任务状态: {task_id}")
        session_manager = get_session_manager()
        task_data = await session_manager.get_task_status(task_id)

        logger.info(f"📊 Redis 查询结果: {task_data}")

        if not task_data:
            logger.warning(f"❌ 任务不存在: {task_id}")
            raise HTTPException(status_code=404, detail="任务不存在")

        logger.info(f"✅ 找到任务数据: {task_id}")
        
        # 解析任务数据
        metadata = task_data.get("metadata", {})
        result = task_data.get("result", {})

        # 如果 result 是字符串，需要解析 JSON
        if isinstance(result, str):
            try:
                import json
                result = json.loads(result)
                logger.info(f"✅ 解析 result JSON 成功: {task_id}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ 解析 result JSON 失败: {task_id}, 错误: {e}")
                result = {}

        # 如果 metadata 是字符串，需要解析 JSON
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
                logger.info(f"✅ 解析 metadata JSON 成功: {task_id}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ 解析 metadata JSON 失败: {task_id}, 错误: {e}")
                metadata = {}
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_data.get("status", "unknown"),
            progress=metadata.get("progress", 0),
            current_step=metadata.get("current_step", "unknown"),
            outline=result.get("outline"),
            article=result.get("article"),
            search_results=result.get("search_results", []),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(task_data.get("updated_at", datetime.now().isoformat())),
            completed_at=datetime.fromisoformat(result.get("completed_at")) if result.get("completed_at") and isinstance(result.get("completed_at"), str) else None,
            word_count=result.get("word_count", 0),
            generation_time=result.get("generation_time"),
            error_message=task_data.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tasks/{task_id}/resume")
async def resume_task(task_id: str, request: InterruptResponseRequest):
    """恢复任务（响应用户交互）"""
    conversation_service = None
    try:
        # 获取任务信息
        session_manager = get_session_manager()
        task_data = await session_manager.get_task_status(task_id)

        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")

        user_id = task_data.get("user_id")
        session_id = task_data.get("session_id")

        if not user_id or not session_id:
            raise HTTPException(status_code=400, detail="任务信息不完整")

        # 使用会话服务验证恢复请求
        conversation_service = get_conversation_service()
        is_valid, validation_message = await conversation_service.validate_resume_request(session_id, task_id)

        if not is_valid:
            raise HTTPException(status_code=400, detail=f"恢复请求无效: {validation_message}")

        # 检查任务状态是否支持恢复
        task_status = task_data.get("status")
        if task_status not in ["paused", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态不支持恢复: {task_status}。只有暂停或失败的任务可以恢复。"
            )

        logger.info(f"🔄 恢复任务验证通过: {task_id}, 状态: {task_status}")

        # 启动恢复任务
        celery_task = resume_writing_task.delay(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            user_response=request.model_dump()
        )

        logger.info(f"恢复写作任务: {task_id}, Celery任务: {celery_task.id}")

        return {
            "message": "任务已恢复",
            "task_id": task_id,
            "celery_task_id": celery_task.id,
            "session_id": session_id,
            "previous_status": task_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conversation_service:
            await conversation_service.close()


@app.delete("/api/v1/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        # 获取任务信息
        session_manager = get_session_manager()
        task_data = await session_manager.get_task_status(task_id)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        user_id = task_data.get("user_id")
        session_id = task_data.get("session_id")
        
        # 启动取消任务
        celery_task = cancel_writing_task.delay(
            user_id=user_id or "unknown",
            session_id=session_id or "unknown",
            task_id=task_id
        )
        
        logger.info(f"取消写作任务: {task_id}, Celery任务: {celery_task.id}")
        
        return {"message": "任务已取消", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/{user_id}/tasks")
async def get_user_tasks(user_id: str):
    """获取用户的所有任务"""
    try:
        logger.info(f"获取用户任务列表: {user_id}")

        session_manager = get_session_manager()
        task_ids = await session_manager.get_user_tasks(user_id)

        # 获取每个任务的详细信息
        tasks = []
        for task_id in task_ids:
            task_data = await session_manager.get_task_status(task_id)
            if task_data:
                tasks.append(task_data)

        return {"status": "success", "tasks": tasks, "count": len(tasks)}

    except Exception as e:
        logger.error(f"获取用户任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 事件流 API (Server-Sent Events)
# ============================================================================

@app.get("/api/v1/events/{conversation_id}")
async def get_event_stream(conversation_id: str):
    """获取会话事件流 (Server-Sent Events) - 支持新的 WorkflowAdapter 格式"""
    logger.info(f"🔗 SSE连接请求: {conversation_id}")

    async def event_generator():
        """事件生成器 - 改进错误处理"""
        redis_client = get_redis_client()
        # 使用新的流名称格式
        stream_name = f"conversation_events:{conversation_id}"
        # 先发送一个测试事件
        yield f"data: {json.dumps({'type': 'connection_test', 'message': 'SSE连接成功', 'timestamp': datetime.now().isoformat()})}\n\n"

        # 使用 0 读取所有历史消息，然后切换到新消息
        last_id = "0"
        logger.info(f"📡 开始监听Redis流: {stream_name}")

        try:
            # 先读取所有历史消息
            try:
                events = redis_client.xread({stream_name: "0"}, count=100)
                if events:
                    logger.info(f"📨 发送历史事件: {len(events[0][1])} 个")
                    for stream, messages in events:
                        for message_id, fields in messages:
                            try:
                                # 解析新格式的数据
                                event_type = fields.get("event_type", "unknown")
                                timestamp = fields.get("timestamp", "")
                                data_str = fields.get("data", "{}")

                                # 解析 JSON 数据
                                data = json.loads(data_str) if isinstance(data_str, str) else data_str

                                # 格式化为 SSE 格式
                                event_data = {
                                    "id": message_id,
                                    "event_type": event_type,
                                    "conversation_id": conversation_id,
                                    "timestamp": timestamp,
                                    "step": data.get("step", "unknown"),
                                    "status": data.get("status", ""),
                                    "progress": data.get("progress", 0),
                                    "data": data
                                }

                                logger.info(f"📤 发送历史SSE事件: {message_id}, 类型: {event_type}")
                                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                last_id = message_id

                            except Exception as e:
                                logger.error(f"解析历史事件数据失败: {e}, fields: {fields}")
                                continue
                else:
                    logger.info("📭 没有历史事件")
            except Exception as e:
                logger.error(f"读取历史事件失败: {e}")

            # 现在监听新事件
            while True:
                try:
                    # 读取新事件
                    events = redis_client.xread({stream_name: last_id}, count=10, block=1000)

                    if events:
                        logger.info(f"📨 收到 {len(events)} 个流的事件")
                        for stream, messages in events:
                            logger.info(f"📋 处理流 {stream}, 消息数: {len(messages)}")
                            for message_id, fields in messages:
                                try:
                                    logger.debug(f"🔍 处理消息: {message_id}, 字段: {list(fields.keys())}")
                                    # 解析新格式的数据
                                    event_type = fields.get("event_type", "unknown")
                                    timestamp = fields.get("timestamp", "")
                                    data_str = fields.get("data", "{}")

                                    # 解析 JSON 数据
                                    data = json.loads(data_str) if isinstance(data_str, str) else data_str

                                    # 格式化为 SSE 格式
                                    event_data = {
                                        "id": message_id,
                                        "event_type": event_type,
                                        "conversation_id": conversation_id,
                                        "timestamp": timestamp,
                                        "step": data.get("step", "unknown"),
                                        "status": data.get("status", ""),
                                        "progress": data.get("progress", 0),
                                        "data": data
                                    }

                                    try:
                                        logger.info(f"📤 发送SSE事件: {message_id}, 类型: {event_type}")
                                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                        last_id = message_id
                                        logger.debug(f"✅ 更新last_id: {last_id}")
                                    except (ConnectionResetError, BrokenPipeError, OSError) as e:
                                        # 客户端断开连接，正常退出
                                        logger.info(f"客户端断开连接: {conversation_id}")
                                        return

                                except Exception as e:
                                    logger.error(f"解析事件数据失败: {e}, fields: {fields}")
                                    continue
                    else:
                        logger.debug(f"⏳ 没有新事件，继续等待...")
                        # 发送心跳
                        try:
                            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                        except (ConnectionResetError, BrokenPipeError, OSError) as e:
                            # 客户端断开连接，正常退出
                            logger.info(f"客户端断开连接（心跳）: {conversation_id}")
                            return

                except Exception as e:
                    logger.error(f"Redis 读取错误: {e}")
                    # 短暂等待后重试
                    import asyncio
                    await asyncio.sleep(1)
                    continue

        except Exception as e:
            logger.error(f"事件流严重错误: {e}")
            try:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            except:
                # 如果连接已断开，忽略发送错误
                pass

    async def safe_event_generator():
        """安全的事件生成器包装器"""
        try:
            async for chunk in event_generator():
                yield chunk
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            # 客户端断开连接，静默处理
            logger.debug(f"客户端断开连接: {conversation_id}")
            return
        except Exception as e:
            logger.error(f"事件流异常: {e}")
            return

    return StreamingResponse(
        safe_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.get("/api/v1/tasks/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """任务进度流式接口 - 兼容新的 conversation_events 格式"""
    async def progress_generator():
        # 获取任务信息以确定 conversation_id
        session_manager = get_session_manager()
        task_data = await session_manager.get_task_status(task_id)

        if not task_data:
            yield f"data: {json.dumps({'type': 'error', 'message': '任务不存在'})}\n\n"
            return

        # 确定 conversation_id
        metadata = task_data.get("metadata", {})
        original_conversation_id = metadata.get("original_conversation_id")
        session_id = task_data.get("session_id")
        conversation_id = original_conversation_id or session_id

        redis_client = get_redis_client()
        stream_name = f"conversation_events:{conversation_id}"
        last_id = "0"

        try:
            while True:
                try:
                    # 从 Redis 流中读取进度更新
                    events = redis_client.xread({stream_name: last_id}, count=10, block=1000)
                except Exception as e:
                    logger.error(f"Redis 读取错误: {e}")
                    events = []

                if events:
                    for stream, messages in events:
                        for message_id, fields in messages:
                            try:
                                # 解析新格式的数据
                                event_type = fields.get("event_type", "unknown")
                                timestamp = fields.get("timestamp", "")
                                data_str = fields.get("data", "{}")

                                # 解析 JSON 数据
                                data = json.loads(data_str) if isinstance(data_str, str) else data_str

                                event_data = {
                                    "id": message_id,
                                    "event_type": event_type,
                                    "timestamp": timestamp,
                                    "task_id": task_id,
                                    "conversation_id": conversation_id,
                                    "step": data.get("step", "unknown"),
                                    "status": data.get("status", ""),
                                    "progress": data.get("progress", 0),
                                    "data": data
                                }

                                try:
                                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                    last_id = message_id
                                except (ConnectionResetError, BrokenPipeError, OSError) as e:
                                    # 客户端断开连接，正常退出
                                    logger.info(f"客户端断开连接（任务流）: {task_id}")
                                    return

                            except Exception as e:
                                logger.error(f"解析任务进度数据失败: {e}, fields: {fields}")
                                continue
                else:
                    # 发送心跳
                    try:
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                    except (ConnectionResetError, BrokenPipeError, OSError) as e:
                        # 客户端断开连接，正常退出
                        logger.info(f"客户端断开连接（任务流心跳）: {task_id}")
                        return

        except Exception as e:
            logger.error(f"任务流式严重错误: {e}")
            try:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            except:
                # 如果连接已断开，忽略发送错误
                pass

    async def safe_progress_generator():
        """安全的进度生成器包装器"""
        try:
            async for chunk in progress_generator():
                yield chunk
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            # 客户端断开连接，静默处理
            logger.debug(f"客户端断开连接（任务流）: {task_id}")
            return
        except Exception as e:
            logger.error(f"任务流异常: {e}")
            return

    return StreamingResponse(
        safe_progress_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=config.debug)
