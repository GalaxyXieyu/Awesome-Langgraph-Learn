"""
简化版 FastAPI 主应用
基于 ReActAgentsTest 参考代码的简洁实现
总行数目标: < 200 行
"""

import json
import uuid
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel

# 简化导入
from ..celery_app.tasks_simple import execute_writing_task, resume_writing_task
from ..utils.redis_simple import get_redis_client

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 简化的请求模型
class TaskRequest(BaseModel):
    user_id: str
    topic: str
    max_words: int = 2000
    style: str = "professional"
    language: str = "zh"

class ResumeRequest(BaseModel):
    task_id: str
    response: str = "yes"

# Redis 客户端
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redis_client
    logger.info("启动 LangGraph Celery Chat API (简化版)")
    
    # 初始化 Redis
    redis_client = get_redis_client()
    if redis_client.ping():
        logger.info("✅ Redis 连接成功")
    else:
        logger.error("❌ Redis 连接失败")
    
    yield
    
    logger.info("关闭应用")
    if redis_client:
        redis_client.close()

# 创建 FastAPI 应用
app = FastAPI(
    title="LangGraph Celery Chat (简化版)",
    version="1.0.0",
    description="参考 ReActAgentsTest 的简洁实现",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "LangGraph Celery Chat (简化版)", "status": "running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    redis_status = "ok" if redis_client and redis_client.ping() else "error"
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "services": {"redis": redis_status, "celery": "ok"}
    }

# ============================================================================
# 核心 API - 参考 ReActAgentsTest 的简洁设计
# ============================================================================

@app.post("/api/v1/tasks")
async def create_task(request: TaskRequest):
    """创建写作任务 - 直接参考 ReActAgentsTest 的实现"""
    try:
        # 生成任务 ID (参考 ReActAgentsTest)
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        session_id = f"session_{request.user_id}_{int(time.time())}"
        
        # 创建任务状态记录 (简化版)
        task_data = {
            "task_id": task_id,
            "session_id": session_id,
            "user_id": request.user_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "config": request.model_dump()
        }
        
        # 存储到 Redis (参考 ReActAgentsTest 的 session_manager)
        redis_client.hset(f"task:{task_id}", task_data)
        redis_client.expire(f"task:{task_id}", 3600)  # 1小时过期
        
        # 启动 Celery 任务 (直接参考 ReActAgentsTest)
        celery_task = execute_writing_task.delay(
            user_id=request.user_id,
            session_id=session_id,
            task_id=task_id,
            config_data=request.model_dump()
        )
        
        logger.info(f"创建任务: {task_id}, Celery: {celery_task.id}")
        
        return {
            "task_id": task_id,
            "session_id": session_id,
            "status": "pending",
            "message": "任务已创建"
        }
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态 - 直接从 Redis 读取"""
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
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/{task_id}/resume")
async def resume_task(task_id: str, request: ResumeRequest):
    """恢复任务 - 参考 ReActAgentsTest 的简单实现"""
    try:
        # 检查任务是否存在
        task_data = redis_client.hgetall(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        user_id = task_data.get("user_id")
        session_id = task_data.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(status_code=400, detail="任务信息不完整")
        
        # 检查任务状态
        status = task_data.get("status")
        if status not in ["paused", "interrupted"]:
            raise HTTPException(
                status_code=400, 
                detail=f"任务状态 {status} 不支持恢复"
            )
        
        # 启动恢复任务 (直接参考 ReActAgentsTest)
        celery_task = resume_writing_task.delay(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            user_response=request.response
        )
        
        logger.info(f"恢复任务: {task_id}, Celery: {celery_task.id}")
        
        return {
            "message": "任务已恢复",
            "task_id": task_id,
            "celery_task_id": celery_task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 更新状态为已取消
        redis_client.hset(f"task:{task_id}", "status", "cancelled")
        
        return {"message": "任务已取消", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# 事件流 API - 简化版 SSE
# ============================================================================

@app.get("/api/v1/events/{task_id}")
async def get_event_stream(task_id: str):
    """获取任务事件流 - 简化的 SSE 实现"""
    
    async def event_generator():
        """简化的事件生成器"""
        stream_name = f"events:{task_id}"
        last_id = "0"
        
        # 发送连接确认
        yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id})}\n\n"
        
        try:
            while True:
                # 从 Redis Streams 读取事件
                events = redis_client.xread({stream_name: last_id}, count=10, block=1000)
                
                if events:
                    for stream, messages in events:
                        for message_id, fields in messages:
                            try:
                                # 发送事件数据
                                event_data = {
                                    "id": message_id,
                                    "task_id": task_id,
                                    "timestamp": fields.get("timestamp", ""),
                                    "data": json.loads(fields.get("data", "{}"))
                                }
                                
                                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                last_id = message_id
                                
                            except Exception as e:
                                logger.error(f"解析事件失败: {e}")
                                continue
                else:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
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
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)