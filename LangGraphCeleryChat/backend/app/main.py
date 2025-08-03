"""
FastAPI 主应用
基于 Celery + Redis 的 LangGraph 写作助手 API
"""

import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from ..models.schemas import (
    CreateTaskRequest, CreateTaskResponse, TaskStatusResponse,
    InterruptResponseRequest, SessionInfo, ErrorResponse,
    WritingTaskConfig, WritingMode, WritingStyle, TaskStatus
)
from ..celery_app.tasks import execute_writing_task, resume_writing_task, cancel_writing_task
from ..utils.config import get_config
from ..utils.redis_client import get_redis_client
from ..utils.session_manager import get_session_manager
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
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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


# ============================================================================
# 任务管理 API
# ============================================================================

@app.post("/api/v1/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    """创建写作任务"""
    try:
        # 生成任务和会话 ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        session_id = f"session_{request.user_id}_{int(datetime.now().timestamp())}"

        # 立即创建任务状态记录
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
                "created_at": datetime.now().isoformat()
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
            config_data=request.config.model_dump()
        )

        logger.info(f"创建写作任务: {task_id}, Celery任务: {celery_task.id}")

        return CreateTaskResponse(
            task_id=task_id,
            session_id=session_id,
            status=TaskStatus.PENDING,
            message="任务已创建，正在处理中"
        )
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # 启动恢复任务
        celery_task = resume_writing_task.delay(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            user_response=request.model_dump()
        )
        
        logger.info(f"恢复写作任务: {task_id}, Celery任务: {celery_task.id}")
        
        return {"message": "任务已恢复", "task_id": task_id, "celery_task_id": celery_task.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


# ============================================================================
# 事件流 API (Server-Sent Events)
# ============================================================================

@app.get("/api/v1/events/{session_id}")
async def get_event_stream(session_id: str):
    """获取会话事件流 (Server-Sent Events)"""
    
    async def event_generator():
        """事件生成器"""
        redis_client = get_redis_client()
        stream_name = f"task_events:{session_id}"
        last_id = "0"
        
        try:
            while True:
                # 读取新事件
                events = redis_client.xread({stream_name: last_id}, count=10, block=1000)
                
                if events:
                    for stream, messages in events:
                        for message_id, fields in messages:
                            # 格式化为 SSE 格式
                            event_data = {
                                "id": message_id,
                                "event_type": fields.get("event_type", "unknown"),
                                "task_id": fields.get("task_id", ""),
                                "timestamp": fields.get("timestamp", ""),
                                "data": json.loads(fields.get("data", "{}"))
                            }
                            
                            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                            last_id = message_id
                else:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except Exception as e:
            logger.error(f"事件流错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
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
    """任务进度流式接口"""
    async def progress_generator():
        redis_client = get_redis_client()
        stream_name = f"stream:{task_id}"
        last_id = "0"

        try:
            while True:
                # 从 Redis 流中读取进度更新
                try:
                    events = redis_client.client.xread({stream_name: last_id}, count=10, block=1000)
                except Exception:
                    events = []

                if events:
                    for stream, messages in events:
                        for message_id, fields in messages:
                            # 解码字节数据
                            data = fields.get(b"data", b"").decode() if isinstance(fields.get(b"data", b""), bytes) else fields.get("data", "")
                            timestamp = fields.get(b"timestamp", b"").decode() if isinstance(fields.get(b"timestamp", b""), bytes) else fields.get("timestamp", "")

                            event_data = {
                                "id": message_id.decode() if isinstance(message_id, bytes) else message_id,
                                "timestamp": timestamp,
                                "task_id": task_id,
                                "data": data
                            }

                            yield f"data: {json.dumps(event_data)}\n\n"
                            last_id = message_id
                else:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"

        except Exception as e:
            logger.error(f"任务流式错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        progress_generator(),
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
