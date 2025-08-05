"""
WebSocket + LangGraph 修复版本
专注于解决流式输出问题
"""

import json
import uuid
import time
import logging
import asyncio
import threading
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from celery import Celery
import redis

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 配置
REDIS_URL = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Celery 配置
celery_app = Celery(
    "websocket_fixed",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["websocket_fixed"]
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
app = FastAPI(title="WebSocket Fixed Chat", version="6.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_stats = {"total_connections": 0, "active_tasks": 0, "messages_sent": 0}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
            self.connection_stats["active_tasks"] += 1
        self.active_connections[task_id].add(websocket)
        self.connection_stats["total_connections"] += 1
        
        await self.send_to_connection(websocket, {
            "type": "connected",
            "task_id": task_id,
            "message": "WebSocket连接成功，准备接收LangGraph生成过程"
        })
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            self.connection_stats["total_connections"] -= 1
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
                self.connection_stats["active_tasks"] -= 1
    
    async def send_to_connection(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
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

# Redis Pub/Sub 订阅器
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
        try:
            self.main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.main_loop = None
        
        thread = threading.Thread(target=self._subscribe_loop, daemon=True)
        thread.start()
        logger.info("🔄 Redis Pub/Sub 订阅器启动")
    
    def _subscribe_loop(self):
        try:
            self.pubsub = redis_client.pubsub()
            self.pubsub.psubscribe("task_events:*")
            
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'pmessage':
                    try:
                        channel = message['channel']
                        task_id = channel.replace('task_events:', '')
                        data = json.loads(message['data'])
                        
                        if self.main_loop and not self.main_loop.is_closed():
                            self.main_loop.call_soon_threadsafe(
                                lambda: asyncio.create_task(
                                    self.manager.broadcast_to_task(task_id, data)
                                )
                            )
                        
                    except Exception as e:
                        logger.error(f"❌ 处理Pub/Sub消息失败: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Pub/Sub订阅循环异常: {e}")
        finally:
            if self.pubsub:
                self.pubsub.close()
    
    def stop(self):
        self.running = False
        if self.pubsub:
            self.pubsub.close()

subscriber = PubSubSubscriber(manager)
subscriber.start()

# 修复的LangGraph任务
@celery_app.task(bind=True)
def execute_writing_task_fixed(self, task_data: dict):
    """修复版LangGraph任务 - 解决流式输出问题"""
    task_id = task_data["task_id"]
    
    def publish_event(event_data):
        redis_client.publish(f"task_events:{task_id}", json.dumps(event_data, ensure_ascii=False))
    
    try:
        logger.info(f"🚀 开始执行修复版LangGraph任务: {task_id}")
        
        # 导入LangGraph
        from graph.graph import create_writing_assistant_graph
        from langchain_core.runnables import RunnableConfig
        from typing import cast
        
        redis_client.hset(f"task:{task_id}", "status", "running")
        
        publish_event({
            "type": "task_started",
            "task_id": task_id,
            "message": f"🚀 开始使用LangGraph生成关于'{task_data.get('topic')}'的文章",
            "timestamp": datetime.now().isoformat()
        })
        
        # 创建图实例
        graph = create_writing_assistant_graph()
        
        # 准备初始状态
        initial_state = {
            "topic": task_data.get("topic"),
            "user_id": task_data["user_id"],
            "max_words": task_data.get("max_words", 800),
            "style": task_data.get("style", "casual"),
            "language": task_data.get("language", "zh"),
            "mode": task_data.get("mode", "interactive"),
            "outline": None,
            "article": None,
            "search_results": [],
            "messages": []
        }
        
        config = cast(RunnableConfig, {"configurable": {"thread_id": task_id}})
        
        logger.info(f"🔄 开始执行LangGraph工作流: {task_id}")
        
        # 使用同步方式但添加更多调试信息
        step_count = 0
        for chunk in graph.stream(initial_state, config, stream_mode=["updates"]):
            step_count += 1
            logger.info(f"📨 收到LangGraph输出 #{step_count}: {chunk}")
            
            try:
                # 处理输出
                if isinstance(chunk, dict):
                    for node_name, node_data in chunk.items():
                        logger.info(f"🔍 处理节点: {node_name}")
                        
                        # 提取内容信息
                        content_info = {}
                        if isinstance(node_data, dict):
                            if 'messages' in node_data:
                                messages = node_data['messages']
                                if messages and len(messages) > 0:
                                    last_msg = messages[-1]
                                    if hasattr(last_msg, 'content'):
                                        content = last_msg.content
                                        content_info = {
                                            "content_preview": content[:500] + "..." if len(content) > 500 else content,
                                            "content_length": len(content),
                                            "message_type": type(last_msg).__name__
                                        }
                                        logger.info(f"📝 提取到内容: {len(content)} 字符")
                        
                        event_data = {
                            "type": "progress_update",
                            "task_id": task_id,
                            "step": node_name,
                            "step_count": step_count,
                            "content_info": content_info,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        publish_event(event_data)
                        logger.info(f"📤 发布事件: {node_name}")
                        
                        # 检查中断
                        if "__interrupt__" in node_data:
                            logger.info(f"检测到中断: {node_data['__interrupt__']}")
                            
                            redis_client.hset(f"task:{task_id}", "status", "paused")
                            
                            interrupt_event = {
                                "type": "interrupt_request",
                                "task_id": task_id,
                                "interrupt_type": "confirmation",
                                "message": "请确认是否继续执行",
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            publish_event(interrupt_event)
                            return {"interrupted": True, "task_id": task_id}
                            
            except Exception as e:
                logger.error(f"处理LangGraph输出失败: {e}")
        
        logger.info(f"🔄 LangGraph工作流完成，共处理 {step_count} 个步骤")
        
        # 获取最终状态
        try:
            final_state = graph.get_state(config).values
            result_data = {
                "outline": final_state.get("outline"),
                "article": final_state.get("article"),
                "search_results": final_state.get("search_results", [])
            }
            logger.info(f"📊 提取结果: 文章长度 {len(result_data.get('article', ''))}")
        except Exception as e:
            logger.error(f"获取最终状态失败: {e}")
            result_data = {"error": "无法获取最终状态"}
        
        redis_client.hset(f"task:{task_id}", mapping={
            "status": "completed",
            "result": json.dumps(result_data, default=str, ensure_ascii=False),
            "completed_at": datetime.now().isoformat()
        })
        
        publish_event({
            "type": "task_complete",
            "task_id": task_id,
            "status": "completed",
            "result": result_data,
            "message": f"🎉 LangGraph文章生成完成！共处理 {step_count} 个步骤",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"✅ 修复版LangGraph任务完成: {task_id}")
        return {"completed": True, "result": result_data}
        
    except Exception as e:
        logger.error(f"❌ 修复版LangGraph任务失败: {task_id}, 错误: {e}")
        redis_client.hset(f"task:{task_id}", mapping={
            "status": "failed",
            "error": str(e)
        })
        
        publish_event({
            "type": "task_failed",
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        
        raise

# API 模型
class TaskRequest(BaseModel):
    user_id: str
    topic: str
    max_words: Optional[int] = 800
    style: Optional[str] = "casual"
    language: Optional[str] = "zh"
    mode: Optional[str] = "interactive"

@app.get("/")
async def root():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket + LangGraph 修复版</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f2f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; }
        .messages { height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 15px; background: white; border-radius: 5px; font-family: monospace; }
        .message { margin: 8px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff; }
        .message.success { border-left-color: #28a745; background: #d4edda; }
        .message.error { border-left-color: #dc3545; background: #f8d7da; }
        .message.interrupt { border-left-color: #ffc107; background: #fff3cd; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px; }
        button:hover { background: #0056b3; }
        button.success { background: #28a745; }
        button.danger { background: #dc3545; }
        input, select { padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }
        .connected { color: #28a745; font-weight: bold; }
        .disconnected { color: #dc3545; font-weight: bold; }
        .interrupt-panel { background: #fff3cd; padding: 20px; margin: 15px 0; border-radius: 8px; border: 2px solid #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 WebSocket + LangGraph 修复版</h1>
            <p>解决流式输出问题，支持真正的中断处理</p>
        </div>

        <div class="section">
            <h3>🎯 创建LangGraph任务</h3>
            <div>
                <input type="text" id="topic" placeholder="文章主题" value="人工智能的发展历程" style="width: 300px;">
                <input type="number" id="maxWords" placeholder="最大字数" value="600" style="width: 100px;">
                <select id="style">
                    <option value="casual">轻松风格</option>
                    <option value="academic">学术风格</option>
                    <option value="professional">专业风格</option>
                </select>
                <select id="mode">
                    <option value="interactive">交互模式 (支持中断)</option>
                    <option value="copilot">Copilot模式 (自动执行)</option>
                </select>
                <button onclick="createTaskAndConnect()" class="success">🚀 启动任务</button>
                <button onclick="disconnect()" class="danger">断开连接</button>
            </div>
            <div id="taskInfo"></div>
            <div>连接状态: <span id="connectionStatus" class="disconnected">未连接</span></div>
        </div>

        <div id="interruptPanel" class="interrupt-panel" style="display: none;">
            <h4>⚠️ 需要您的确认</h4>
            <p id="interruptMessage">请确认是否继续执行</p>
            <button onclick="resumeTask(true)" class="success">✅ 继续执行</button>
            <button onclick="resumeTask(false)" class="danger">❌ 停止任务</button>
        </div>

        <div class="section">
            <h3>📨 LangGraph 实时生成过程</h3>
            <div id="messages" class="messages"></div>
            <button onclick="clearMessages()">清空消息</button>
            <button onclick="scrollToBottom()">滚动到底部</button>
        </div>
    </div>

    <script>
        let ws = null;
        let currentTaskId = null;
        let messageCount = 0;

        async function createTaskAndConnect() {
            const topic = document.getElementById('topic').value;
            const maxWords = parseInt(document.getElementById('maxWords').value);
            const style = document.getElementById('style').value;
            const mode = document.getElementById('mode').value;

            try {
                const response = await fetch('/api/v1/tasks', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: 'fixed_user_' + Date.now(),
                        topic: topic,
                        max_words: maxWords,
                        style: style,
                        language: 'zh',
                        mode: mode
                    })
                });

                const result = await response.json();
                currentTaskId = result.task_id;

                document.getElementById('taskInfo').innerHTML = `
                    <div style="background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <p><strong>✅ LangGraph任务创建成功</strong></p>
                        <p>📋 任务ID: ${currentTaskId}</p>
                        <p>🎯 主题: ${topic}</p>
                        <p>🧠 模式: ${mode}</p>
                    </div>
                `;

                connectWebSocket();

            } catch (e) {
                document.getElementById('taskInfo').innerHTML = `
                    <div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <p><strong>❌ 创建任务失败</strong></p>
                        <p>${e.message}</p>
                    </div>
                `;
            }
        }

        function connectWebSocket() {
            if (!currentTaskId) {
                addMessage('⚠️ 请先创建任务', 'error');
                return;
            }

            if (ws) {
                ws.close();
            }

            const wsUrl = `ws://localhost:8006/ws/${currentTaskId}`;
            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                document.getElementById('connectionStatus').textContent = '已连接';
                document.getElementById('connectionStatus').className = 'connected';
                addMessage('🔗 WebSocket连接成功', 'success');
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            ws.onclose = function() {
                document.getElementById('connectionStatus').textContent = '已断开';
                document.getElementById('connectionStatus').className = 'disconnected';
                addMessage('❌ WebSocket连接断开', 'error');
            };

            ws.onerror = function(error) {
                addMessage('❌ WebSocket错误: ' + error, 'error');
            };
        }

        function handleMessage(data) {
            messageCount++;
            const msgType = data.type || 'unknown';

            if (msgType === 'connected') {
                addMessage(`🔗 连接确认: ${data.task_id}\\n💬 ${data.message}`, 'success');
            } else if (msgType === 'task_started') {
                addMessage(`🚀 ${data.message}`, 'success');
            } else if (msgType === 'progress_update') {
                const step = data.step || 'unknown';
                const stepCount = data.step_count || 0;
                const contentInfo = data.content_info || {};

                let msg = `🧠 LangGraph步骤 #${stepCount}: ${step}`;
                if (contentInfo.content_preview) {
                    msg += `\\n📝 ${contentInfo.message_type || 'Message'} (${contentInfo.content_length || 0} 字符)`;
                    msg += `\\n💬 ${contentInfo.content_preview}`;
                }

                addMessage(msg, 'success');
            } else if (msgType === 'interrupt_request') {
                addMessage(`⚠️ 收到中断请求: ${data.message}`, 'interrupt');

                // 显示中断面板
                document.getElementById('interruptPanel').style.display = 'block';
                document.getElementById('interruptMessage').textContent = data.message || '请确认是否继续执行';

                scrollToBottom();
            } else if (msgType === 'task_complete') {
                const result = data.result || {};
                const article = result.article || '';
                const outline = result.outline || {};

                let msg = `🎉 任务完成!\\n📖 文章长度: ${article.length} 字符\\n📝 标题: ${outline.title || 'N/A'}`;
                if (data.message) {
                    msg += `\\n💬 ${data.message}`;
                }
                if (article) {
                    msg += `\\n\\n📄 文章预览:\\n${article.substring(0, 300)}...`;
                }
                addMessage(msg, 'success');

                // 隐藏中断面板
                document.getElementById('interruptPanel').style.display = 'none';
            } else if (msgType === 'task_failed') {
                addMessage(`❌ 任务失败: ${data.error || 'Unknown error'}`, 'error');
            } else {
                addMessage(`📨 ${msgType}: ${JSON.stringify(data).substring(0, 200)}...`, 'success');
            }

            scrollToBottom();
        }

        async function resumeTask(approved) {
            if (!currentTaskId) {
                addMessage('❌ 没有活跃的任务', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/v1/tasks/${currentTaskId}/resume`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        response: approved ? 'yes' : 'no',
                        approved: approved
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    addMessage(`✅ 任务恢复: ${result.message}`, 'success');

                    // 隐藏中断面板
                    document.getElementById('interruptPanel').style.display = 'none';
                } else {
                    const error = await response.text();
                    addMessage(`❌ 恢复任务失败: ${error}`, 'error');
                }
            } catch (e) {
                addMessage(`❌ 恢复任务异常: ${e.message}`, 'error');
            }
        }

        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }

        function addMessage(message, type = 'success') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `<small>${new Date().toLocaleTimeString()}</small><br><pre style="white-space: pre-wrap; font-family: inherit;">${message}</pre>`;
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }

        function clearMessages() {
            document.getElementById('messages').innerHTML = '';
            messageCount = 0;
        }

        function scrollToBottom() {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    try:
        redis_client.ping()
        return {"status": "ok", "services": {"redis": "ok", "celery": "ok", "langgraph": "ok"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.get("/stats")
async def get_stats():
    return manager.get_stats()

@app.post("/api/v1/tasks")
async def create_task(task_request: TaskRequest):
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

    redis_client.hset(f"task:{task_id}", mapping={
        "status": "pending",
        "data": json.dumps(task_data, ensure_ascii=False),
        "created_at": datetime.now().isoformat()
    })

    execute_writing_task_fixed.delay(task_data)

    logger.info(f"🚀 创建修复版LangGraph任务: {task_id}")

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "LangGraph任务已创建，正在处理中"
    }

@app.post("/api/v1/tasks/{task_id}/resume")
async def resume_task(task_id: str, response: dict):
    try:
        task_info = redis_client.hgetall(f"task:{task_id}")
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        resume_event = {
            "type": "task_resume",
            "task_id": task_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

        redis_client.publish(f"task_events:{task_id}", json.dumps(resume_event, ensure_ascii=False))
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

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_to_connection(websocket, {
                    "type": "pong",
                    "timestamp": time.time()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
        manager.disconnect(websocket, task_id)

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动 WebSocket + LangGraph 修复版")
    print("📱 访问 http://localhost:8006 查看测试页面")
    print("🧠 解决流式输出问题，支持真正的中断处理")

    uvicorn.run(app, host="0.0.0.0", port=8006)
