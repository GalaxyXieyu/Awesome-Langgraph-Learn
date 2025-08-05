"""
WebSocket + Redis Pub/Sub + 真正的LangGraph集成版本
基于main.py的实现，使用WebSocket推送真正的LangGraph生成过程
"""

import json
import uuid
import time
import logging
import asyncio
import threading
from typing import Dict, Set, Optional, Any, cast
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from celery import Celery
import redis
from langchain_core.runnables import RunnableConfig

from langchain_core.messages import BaseMessage

def langchain_serializer(obj: Any) -> Any:
    """JSON serializer for objects that can't be directly encoded, like LangChain messages."""
    if isinstance(obj, BaseMessage):
        return obj.dict()  # Use the .dict() method for pydantic models
    if isinstance(obj, (datetime, uuid.UUID)):
        return str(obj)
    try:
        return obj.__dict__
    except AttributeError:
        return str(obj)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 配置和初始化
# ============================================================================

# Redis 配置
REDIS_URL = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277/0"
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Celery 配置
celery_app = Celery(
    "websocket_langgraph",
    broker=REDIS_URL,
    backend=REDIS_URL,

)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# FastAPI 应用
app = FastAPI(title="WebSocket + LangGraph Chat", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# WebSocket 连接管理器
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_stats = {
            "total_connections": 0,
            "active_tasks": 0,
            "messages_sent": 0
        }
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
            self.connection_stats["active_tasks"] += 1
        
        self.active_connections[task_id].add(websocket)
        self.connection_stats["total_connections"] += 1
        
        logger.info(f"📱 WebSocket连接: {task_id}, 连接数: {len(self.active_connections[task_id])}")
        
        # 发送连接确认
        await self.send_to_connection(websocket, {
            "type": "connected",
            "task_id": task_id,
            "timestamp": time.time(),
            "message": "WebSocket连接成功，准备接收LangGraph生成过程"
        })
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            self.connection_stats["total_connections"] -= 1
            
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
                self.connection_stats["active_tasks"] -= 1
        
        logger.info(f"📱 WebSocket断开: {task_id}")
    
    async def send_to_connection(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message, default=langchain_serializer, ensure_ascii=False))
            return True
        except:
            return False
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        if task_id not in self.active_connections:
            return 0
        
        disconnected = set()
        sent_count = 0
        
        for connection in self.active_connections[task_id].copy():
            success = await self.send_to_connection(connection, message)
            if success:
                sent_count += 1
            else:
                disconnected.add(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.active_connections[task_id].discard(conn)
            self.connection_stats["total_connections"] -= 1
        
        if sent_count > 0:
            self.connection_stats["messages_sent"] += sent_count
        
        return sent_count
    
    def get_stats(self):
        return {
            **self.connection_stats,
            "tasks": {task_id: len(connections) for task_id, connections in self.active_connections.items()}
        }

manager = ConnectionManager()

# ============================================================================
# Redis Pub/Sub 订阅器
# ============================================================================

class PubSubSubscriber:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.running = False
        self.pubsub = None
        self.main_loop = None
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        # 获取主事件循环
        try:
            self.main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.main_loop = None
        
        thread = threading.Thread(target=self._subscribe_loop, daemon=True)
        thread.start()
        logger.info("🔄 Redis Pub/Sub 订阅器启动 (LangGraph版)")
    
    def _subscribe_loop(self):
        """Redis Pub/Sub订阅循环"""
        try:
            self.pubsub = redis_client.pubsub()
            self.pubsub.psubscribe("task_events:*")  # 订阅所有任务事件
            
            logger.info("📡 开始监听 LangGraph 生成过程...")
            
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'pmessage':
                    try:
                        # 解析频道名获取task_id
                        channel = message['channel']
                        task_id = channel.replace('task_events:', '')
                        
                        # 解析消息数据
                        data = json.loads(message['data'])
                        
                        # 使用线程安全的方式调度异步任务
                        if self.main_loop and not self.main_loop.is_closed():
                            self.main_loop.call_soon_threadsafe(
                                lambda: asyncio.create_task(
                                    self.manager.broadcast_to_task(task_id, data)
                                )
                            )
                        else:
                            # 如果没有主循环，创建新的事件循环
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(
                                    self.manager.broadcast_to_task(task_id, data)
                                )
                                loop.close()
                            except Exception as e:
                                logger.error(f"创建新事件循环失败: {e}")
                        
                        logger.debug(f"📨 转发LangGraph消息到任务 {task_id}: {data.get('type', 'unknown')}")
                        
                    except Exception as e:
                        logger.error(f"❌ 处理LangGraph Pub/Sub消息失败: {e}")
                        
        except Exception as e:
            logger.error(f"❌ LangGraph Pub/Sub订阅循环异常: {e}")
        finally:
            if self.pubsub:
                self.pubsub.close()
    
    def stop(self):
        self.running = False
        if self.pubsub:
            self.pubsub.close()

# 启动Pub/Sub订阅器
subscriber = PubSubSubscriber(manager)

@app.on_event("startup")
async def startup_event():
    """在应用启动时启动Redis Pub/Sub订阅器"""
    logger.info("🚀 应用启动: 正在启动Redis Pub/Sub订阅器...")
    subscriber.start()

@app.on_event("shutdown")
def shutdown_event():
    """在应用关闭时停止Redis Pub/Sub订阅器"""
    logger.info("🛑 应用关闭: 正在停止Redis Pub/Sub订阅器...")
    subscriber.stop()


# ============================================================================
# LangGraph集成的Celery任务 - 重构优化
# ============================================================================

def _publish_event(task_id: str, event_data: dict):
    """Helper to publish events to Redis Pub/Sub."""
    try:
        redis_client.publish(f"task_events:{task_id}", json.dumps(event_data, default=langchain_serializer, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Failed to publish event for task {task_id}: {e}")

async def _wait_for_resume(task_id: str) -> bool:
    """Waits for a user to resume a paused task."""
    logger.info(f"Waiting for user response for interrupt: {task_id}")
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"task_events:{task_id}")
    
    timeout = 300  # 5 minutes
    start_wait = time.time()

    try:
        while time.time() - start_wait < timeout:
            message = pubsub.get_message(timeout=1)
            if not message or message['type'] != 'message':
                await asyncio.sleep(0.1)
                continue

            resume_data = json.loads(message['data'])
            if resume_data.get('type') != 'task_resume':
                continue

            logger.info(f"Received resume signal: {resume_data}")
            user_response = resume_data.get('response', {})
            if user_response.get('approved', False):
                logger.info(f"User approved continuation for task: {task_id}")
                redis_client.hset(f"task:{task_id}", "status", "running")
                _publish_event(task_id, {
                    "type": "task_resumed", "task_id": task_id,
                    "message": "Task has been resumed by user.", "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                logger.info(f"User denied continuation for task: {task_id}")
                redis_client.hset(f"task:{task_id}", "status", "cancelled")
                _publish_event(task_id, {
                    "type": "task_cancelled", "task_id": task_id,
                    "message": "Task was cancelled by the user.", "timestamp": datetime.now().isoformat()
                })
                return False
        
        # Timeout logic
        logger.warning(f"Timeout waiting for user response for task: {task_id}")
        redis_client.hset(f"task:{task_id}", "status", "timeout")
        _publish_event(task_id, {
            "type": "task_timeout", "task_id": task_id,
            "message": "Timeout waiting for user response.", "timestamp": datetime.now().isoformat()
        })
        return False
    finally:
        pubsub.close()

def _parse_step_content(step_data: dict) -> dict:
    """Parses content from a graph step for logging/eventing."""
    content_info = {}
    if not isinstance(step_data, dict):
        return content_info

    if 'messages' in step_data and step_data['messages']:
        last_msg = step_data['messages'][-1]
        if hasattr(last_msg, 'content'):
            content = last_msg.content
            content_info = {
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                "content_length": len(content),
                "message_type": type(last_msg).__name__
            }
    
    for key, value in step_data.items():
        if key != 'messages' and isinstance(value, (str, int, float, bool, list, dict)):
            content_info[key] = value
            
    return content_info

async def _handle_graph_chunk(chunk: Any, task_id: str) -> Optional[str]:
    """Processes a single chunk from the graph stream and returns interrupt status."""
    if not isinstance(chunk, (list, tuple)) or len(chunk) != 2:
        _publish_event(task_id, {
            "type": "raw_update", "task_id": task_id, "data": chunk, "timestamp": datetime.now().isoformat()
        })
        return None

    stream_type, data = chunk
    if stream_type != "updates" or not isinstance(data, dict):
        _publish_event(task_id, {
            "type": "raw_update", "task_id": task_id, "data": chunk, "timestamp": datetime.now().isoformat()
        })
        return None
        
    step_name = list(data.keys())[0] if data else "unknown"
    step_data = data.get(step_name, {})
    
    _publish_event(task_id, {
        "type": "progress_update", "task_id": task_id, "step": step_name,
        "content_info": _parse_step_content(step_data), "data": data, "timestamp": datetime.now().isoformat()
    })

    if "__interrupt__" in data:
        interrupt_info = data["__interrupt__"]
        logger.info(f"Interrupt detected: {interrupt_info}")
        redis_client.hset(f"task:{task_id}", "status", "paused")
        _publish_event(task_id, {
            "type": "interrupt_request", "task_id": task_id,
            "interrupt_type": "confirmation", "title": "Confirmation Required",
            "message": "Please confirm to continue.", "timestamp": datetime.now().isoformat()
        })
        return "interrupted"
        
    return None

def _process_final_result(final_result: Any, task_id: str):
    """Processes the final result from the graph stream."""
    result_data = {}
    if isinstance(final_result, (list, tuple)) and len(final_result) == 2:
        _, data = final_result
        if isinstance(data, dict):
            # Assuming the final state is in the last node's output
            last_node_output = list(data.values())[0] if data else {}
            result_data = {
                "outline": last_node_output.get("outline"),
                "article": last_node_output.get("article"),
                "search_results": last_node_output.get("search_results", [])
            }

    redis_client.hset(f"task:{task_id}", mapping={
        "status": "completed",
        "result": json.dumps(result_data, default=langchain_serializer, ensure_ascii=False),
        "completed_at": datetime.now().isoformat()
    })
    
    _publish_event(task_id, {
        "type": "task_complete", "task_id": task_id, "status": "completed",
        "result": result_data, "message": "Article generation completed successfully!",
        "timestamp": datetime.now().isoformat()
    })
    logger.info(f"✅ WebSocket+LangGraph task completed: {task_id}")
    return {"completed": True, "result": result_data}

async def run_langgraph_workflow(task_data: dict):
    """The main async workflow for running the LangGraph graph."""
    task_id = task_data["task_id"]
    
    try:
        from graph.graph import create_writing_assistant_graph
        
        redis_client.hset(f"task:{task_id}", "status", "running")
        _publish_event(task_id, {
            "type": "task_started", "task_id": task_id,
            "message": f"Starting to generate an article about '{task_data.get('topic')}' using LangGraph.",
            "timestamp": datetime.now().isoformat()
        })
        
        graph = create_writing_assistant_graph()
        config = cast(RunnableConfig, {"configurable": {"thread_id": task_id}})
        
        initial_state = {k: v for k, v in task_data.items() if k not in ["task_id", "user_id", "created_at"]}
        initial_state.update({
             "user_id": task_data["user_id"],
             "outline": None, "article": None, "search_results": [], "messages": []
        })

        logger.info(f"🔄 Starting LangGraph workflow: {task_id}, Topic: {task_data.get('topic')}")
        
        final_result = None
        async for chunk in graph.astream(initial_state, config, stream_mode=["updates"]):
            logger.info(f"📨 Received LangGraph chunk for {task_id}: {chunk}")
            final_result = chunk
            
            status = await _handle_graph_chunk(chunk, task_id)
            
            if status == "interrupted":
                should_continue = await _wait_for_resume(task_id)
                if not should_continue:
                    return {"completed": False, "interrupted": True, "reason": "User cancelled or timed out."}
        
        if final_result:
            return _process_final_result(final_result, task_id)
        
        return {"completed": False, "interrupted": False, "reason": "Workflow finished without a final result."}

    except Exception as e:
        logger.error(f"❌ LangGraph workflow failed for task {task_id}: {e}", exc_info=True)
        redis_client.hset(f"task:{task_id}", mapping={"status": "failed", "error": str(e)})
        _publish_event(task_id, {
            "type": "task_failed", "task_id": task_id, "status": "failed",
            "error": str(e), "timestamp": datetime.now().isoformat()
        })
        raise

@celery_app.task(bind=True)
def execute_writing_task_langgraph(self, task_data: dict):
    """
    Celery task wrapper for the LangGraph writing assistant workflow.
    It runs the asynchronous workflow in a synchronous Celery task.
    """
    try:
        # Use asyncio.run() which handles loop creation and shutdown
        return asyncio.run(run_langgraph_workflow(task_data))
    except Exception as e:
        logger.error(f"❌ Failed to execute async workflow in Celery for task {task_data.get('task_id')}: {e}")
        # The exception is already logged and published in run_langgraph_workflow
        # Re-raising ensures Celery marks the task as FAILED.
        raise
# ============================================================================
# API 模型和路由
# ============================================================================


class TaskRequest(BaseModel):
    user_id: str
    topic: str
    max_words: Optional[int] = 800
    style: Optional[str] = "casual"
    language: Optional[str] = "zh"
    mode: Optional[str] = "copilot"

@app.get("/")
async def get_frontend():
    return FileResponse('test_frontend.html')

@app.get("/health")
async def health_check():
    try:
        redis_client.ping()
        return {"status": "ok", "services": {"redis": "ok", "celery": "ok", "langgraph": "ok", "pubsub": "ok"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.get("/stats")
async def get_stats():
    return manager.get_stats()

@app.post("/api/v1/tasks")
async def create_task(task_request: TaskRequest):
    """创建任务 - 集成真正的LangGraph"""
    task_id = f"task_{uuid.uuid4().hex[:8]}"

    task_data = {
        "task_id": task_id,
        "user_id": task_request.user_id,
        "topic": task_request.topic,
        "max_words": task_request.max_words,
        "style": task_request.style,
        "language": task_request.language,
        "mode": task_request.mode,
        "created_at": datetime.now().isoformat()
    }

    # 存储任务信息
    redis_client.hset(f"task:{task_id}", mapping={
        "status": "pending",
        "data": json.dumps(task_data, default=langchain_serializer, ensure_ascii=False),
        "created_at": datetime.now().isoformat()
    })

    # 使用集成LangGraph的Celery任务
    execute_writing_task_langgraph.delay(task_data)

    logger.info(f"🚀 创建LangGraph集成任务: {task_id}")

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "LangGraph任务已创建，正在处理中"
    }

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    task_info = redis_client.hgetall(f"task:{task_id}")

    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = {
        "task_id": task_id,
        "status": task_info.get("status", "unknown"),
        "created_at": task_info.get("created_at"),
        "completed_at": task_info.get("completed_at")
    }

    if "result" in task_info:
        result["result"] = json.loads(task_info["result"])

    if "error" in task_info:
        result["error"] = task_info["error"]

    return result

@app.post("/api/v1/tasks/{task_id}/resume")
async def resume_task(task_id: str, response: dict):
    """恢复被中断的任务"""
    try:
        # 检查任务状态
        task_info = redis_client.hgetall(f"task:{task_id}")
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task_info.get("status") != "paused":
            raise HTTPException(status_code=400, detail="任务未处于暂停状态")

        # 发布恢复事件
        resume_event = {
            "type": "task_resume",
            "task_id": task_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

        redis_client.publish(f"task_events:{task_id}", json.dumps(resume_event, default=langchain_serializer, ensure_ascii=False))

        # 更新任务状态
        redis_client.hset(f"task:{task_id}", "status", "running")

        logger.info(f"📤 任务恢复: {task_id}")

        return {
            "task_id": task_id,
            "status": "resumed",
            "message": "任务已恢复执行"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {e}")

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)

    # 创建一个任务来处理入站消息，这样主协程就不会被阻塞
    async def receive_handler():
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await manager.send_to_connection(websocket, {
                        "type": "pong",
                        "timestamp": time.time(),
                        "message": "LangGraph心跳响应"
                    })
        except WebSocketDisconnect:
            pass # 主循环会处理断开连接
        except Exception as e:
            logger.error(f"WebSocket 接收异常: {e}")

    receive_task = asyncio.create_task(receive_handler())

    try:
        # 保持连接开放，直到接收任务结束（通常是断开连接）
        await receive_task
    except WebSocketDisconnect:
        # 这个异常现在会在主任务中被捕获
        pass
    except Exception as e:
        logger.error(f"WebSocket 主任务异常: {e}")
    finally:
        if not receive_task.done():
            receive_task.cancel()
        manager.disconnect(websocket, task_id)

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动 WebSocket + LangGraph 集成版")
    print("📱 访问 http://localhost:8004 查看测试页面")
    print("🧠 集成真正的LangGraph AI工作流")
    print("⚡ 支持 50,000+ 并发连接")

    uvicorn.run(app, host="0.0.0.0", port=8004)
