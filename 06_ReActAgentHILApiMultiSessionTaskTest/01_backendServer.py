import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import time
from fastapi import FastAPI, HTTPException
from typing import Dict
import uuid
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
import uvicorn
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from utils.config import Config
from utils.tasks import celery_app, invoke_agent_task, resume_agent_task
from utils.models import AgentRequest, InterruptResponse, SystemInfoResponse, LongMemRequest
from utils.models import SessionInfoResponse, TaskInfoResponse, ActiveSessionInfoResponse, SessionStatusResponse
from utils.redis import get_session_manager



# Author:@南哥AGI研习社 (B站 or YouTube 搜索“南哥AGI研习社”)


# 设置日志基本配置，级别为DEBUG或INFO
logger = logging.getLogger(__name__)
# 设置日志器级别为DEBUG
logger.setLevel(logging.DEBUG)
logger.handlers = []  # 清空默认处理器
# 使用ConcurrentRotatingFileHandler
handler = ConcurrentRotatingFileHandler(
    # 日志文件
    Config.LOG_FILE,
    # 日志文件最大允许大小为5MB，达到上限后触发轮转
    maxBytes=Config.MAX_BYTES,
    # 在轮转时，最多保留3个历史日志文件
    backupCount=Config.BACKUP_COUNT
)
# 设置处理器级别为DEBUG
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)


# 指定用户写入长期记忆内容
async def write_long_term_info(user_id: str, memory_info: str):
    """
    指定用户写入长期记忆内容

    Args:
        user_id: 用户的唯一标识
        memory_info: 要保存的记忆内容

    Returns:
        Dict[str, Any]: 包含成功状态和存储记忆ID的结果
    """
    try:
        # 生成命名空间和唯一记忆ID
        namespace = ("memories", user_id)
        memory_id = str(uuid.uuid4())
        # 存储数据到指定命名空间
        result = await app.state.store.aput(
            namespace=namespace,
            key=memory_id,
            value={"data": memory_info}
        )
        # 记录存储成功的日志
        logger.info(f"成功为用户ID: {user_id} 存储记忆，记忆ID: {memory_id}")
        # 返回存储成功的响应
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "记忆存储成功"
        }

    except Exception as e:
        # 处理其他未预期的错误
        logger.error(f"存储用户ID: {user_id} 的记忆时发生意外错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"存储记忆失败: {str(e)}"
        )


# 生命周期函数 app应用初始化函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期函数，用于初始化和清理资源
    """
    try:
        # 实例化异步Redis会话管理器
        app.state.session_manager = get_session_manager()
        logger.info("Redis初始化成功")

        # 创建数据库连接池
        app.state.pool = AsyncConnectionPool(
            conninfo=Config.DB_URI,
            min_size=Config.MIN_SIZE,
            max_size=Config.MAX_SIZE,
            kwargs={"autocommit": True, "prepare_threshold": 0}
        )
        await app.state.pool.open()  # 显式打开连接池
        logger.info("数据库连接池初始化成功")
        # 短期记忆 初始化checkpointer
        app.state.checkpointer = AsyncPostgresSaver(app.state.pool)
        # await app.state.checkpointer.setup()
        logger.info("短期记忆存储Checkpointer初始化成功")
        # 长期记忆 初始化store
        app.state.store = AsyncPostgresStore(app.state.pool)
        # await app.state.store.setup()
        logger.info("长期记忆存储Store初始化成功")
        yield

    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        raise RuntimeError(f"服务初始化失败: {str(e)}")

    finally:
        # 清理资源
        await app.state.session_manager.close()
        if hasattr(app.state, 'pool') and app.state.pool:
            await app.state.pool.close()
            logger.info("数据库连接池已关闭")
        logger.info("关闭服务并完成资源清理")

# 实例化app 并使用生命周期上下文管理器进行app初始化
app = FastAPI(
    title="Agent智能体后端API接口服务(异步任务调度)",
    description="基于LangGraph提供AI Agent服务",
    lifespan=lifespan
)

# API接口:异步运行智能体并返回任务ID
@app.post("/agent/invoke", response_model=dict)
async def invoke_agent(request: AgentRequest):
    logger.info(f"调用/agent/invoke接口，运行智能体并返回任务ID，接受到前端用户请求:{request}")
    # 获取用户请求中的user_id、session_id和task_id
    user_id = request.user_id
    session_id = request.session_id
    task_id = request.task_id

    # 检查指定用户ID的指定session_id的指定task_id是否存在
    exists = await app.state.session_manager.session_task_id_exists(user_id, session_id, task_id)
    # 若不存在，则创建新会话
    if not exists:
        await app.state.session_manager.create_session(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            status="idle",
            last_updated=time.time(),
            ttl=Config.TTL
        )

    # 使用delay()调用任务 将任务发送到消息队列以便由Worker进程异步执行
    task = invoke_agent_task.delay(
        user_id=user_id,
        session_id=session_id,
        task_id=task_id,
        query=request.query,
        system_prompt=request.system_message or "你会使用工具来帮助用户。如果工具使用被拒绝，请提示用户。"
    )

    # 设置任务状态为等待并绑定用户和会话
    await app.state.session_manager.set_task_status(
        task_id=task_id,
        status="pending",
        user_id=user_id,
        session_id=session_id
    )

    # 立即返回用户ID、会话ID和任务ID
    logger.info(f"返回当前用户ID {user_id} 会话ID {session_id} 和任务ID {task_id}")
    return {"user_id": user_id, "session_id": session_id, "task_id": task_id}

# API接口:提交异步恢复被中断的智能体运行返回任务ID
@app.post("/agent/resume", response_model=dict)
async def resume_agent(response: InterruptResponse):
    logger.info(f"调用/agent/resume接口，恢复被中断的智能体运行并等待运行完成或再次中断，接受到前端用户请求:{response}")
    # 获取用户中断请求中的user_id、session_id和task_id
    user_id = response.user_id
    session_id = response.session_id
    task_id = response.task_id

    # 检查指定用户ID的指定session_id的指定task_id是否存在
    exists = await app.state.session_manager.session_task_id_exists(user_id, session_id, task_id)
    # 若不存在 则抛出异常
    if not exists:
        logger.error(f"status_code=404,用户会话任务 {user_id}:{session_id}:{task_id} 不存在")
        raise HTTPException(status_code=404, detail=f"用户会话任务 {user_id}:{session_id}:{task_id} 不存在")

    # 获取指定用户当前会话和任务ID的对应的状态数据
    session = await app.state.session_manager.get_session_by_task(user_id, session_id, task_id)
    # 检查会话状态是否为中断 若不是中断则抛出异常
    status = session.get("status")
    if status != "interrupted":
        logger.error(f"status_code=400,用户会话任务 {user_id}:{session_id}:{task_id} 当前状态为 {status}，无法恢复非中断状态的会话")
        raise HTTPException(status_code=400, detail=f"用户会话任务 {user_id}:{session_id}:{task_id} 当前状态为 {status}，无法恢复非中断状态的会话")

    # 更新会话状态
    await app.state.session_manager.update_session(
        user_id=user_id,
        session_id=session_id,
        task_id=task_id,
        status="running",
        last_query=None,
        last_response=None,
        last_updated=time.time(),
        ttl=Config.TTL
    )

    # 构造响应数据
    command_data = {
        "type": response.response_type
    }
    # 如果提供了参数，添加到响应数据中
    if response.args:
        command_data["args"] = response.args

    # 使用delay()调用任务 将任务发送到消息队列以便由Worker进程异步执行
    task = resume_agent_task.delay(
        user_id=user_id,
        session_id=session_id,
        task_id=task_id,
        command_data=command_data
    )

    # 设置任务状态为等待并绑定用户和会话
    await app.state.session_manager.set_task_status(
        task_id=task_id,
        status="pending",
        user_id=user_id,
        session_id=session_id
    )

    # 立即返回用户ID、会话ID和任务ID
    logger.info(f"返回当前用户ID {user_id} 会话ID {session_id} 和任务ID {task_id}")
    return {"user_id": user_id, "session_id": session_id, "task_id": task_id}

# API接口:获取当前系统内全部的会话状态信息
@app.get("/system/info", response_model=SystemInfoResponse)
async def get_system_info():
    logger.info(f"调用/system/info接口，获取当前系统内全部的会话状态信息")
    # 构造SystemInfoResponse对象
    response = SystemInfoResponse(
        # 获取系统内所有用户下的所有会话的总数
        sessions_count=await app.state.session_manager.get_session_count(),
        # 获取系统内所有用户下的所有session_id
        active_users=await app.state.session_manager.get_all_users_session_ids()
    )
    logger.info(f"返回当前系统内全部的会话状态信息:{response}")
    return response

# API接口:获取指定用户ID的最近一次修改的会话ID
@app.get("/agent/active/sessionid/{user_id}", response_model=ActiveSessionInfoResponse)
async def get_agent_active_sessionid(user_id: str):
    logger.info(f"调用/agent/active/sessionid/接口，获取指定用户当前最近一次更新的会话ID，接受到前端用户请求:{user_id}")
    # 判断当前用户是否存在
    exists = await app.state.session_manager.user_id_exists(user_id)
    # 若用户不存在 构造ActiveSessionInfoResponse对象
    if not exists:
        logger.warning(f"用户 {user_id} 的会话不存在，将会新建会话")
        return ActiveSessionInfoResponse(
            active_session_id=""
        )
    # 若会话存在 构造ActiveSessionInfoResponse对象
    # 获取指定用户ID的最近一次修改的会话ID
    response = ActiveSessionInfoResponse(
        active_session_id=await app.state.session_manager.get_user_active_session_id(user_id)
    )
    logger.info(f"返回当前用户ID的最近一次修改的会话ID:{response}")
    return response

# API接口:获取指定用户ID的所有session_id
@app.get("/agent/sessionids/{user_id}", response_model=SessionInfoResponse)
async def get_agent_sessionids(user_id: str):
    logger.info(f"调用/agent/sessionids/接口，获取指定用户ID的所有session_id，接受到前端用户请求:{user_id}")
    # 检查指定用户ID是否存在
    exists = await app.state.session_manager.user_id_exists(user_id)
    # 若不存在 构造SessionInfoResponse对象
    if not exists:
        logger.warning(f"用户 {user_id} 的会话不存在")
        return SessionInfoResponse(
            session_ids=[]
        )
    # 若存在 构造SessionInfoResponse对象
    # 获取指定用户ID的所有session_id
    response = SessionInfoResponse(
        session_ids=await app.state.session_manager.get_all_session_ids(user_id)
    )

    logger.info(f"返回当前用户ID的所有session_id:{response}")
    return response

# API接口:获取指定用户ID和会话ID下所有任务的ID和状态值
@app.get("/agent/tasks/{user_id}/{session_id}", response_model=TaskInfoResponse)
async def get_agent_task_ids(user_id: str, session_id: str):
    logger.info(f"调用/agent/tasks接口，获取指定用户ID和会话ID下所有任务的ID和状态值，接受到前端用户请求:{user_id} {session_id}")
    # 检查指定用户ID的指定session_id是否存在
    exists = await app.state.session_manager.session_id_exists(user_id, session_id)
    # 若不存在 构造TaskInfoResponse对象
    if not exists:
        logger.warning(f"用户 {user_id} 的会话 {session_id} 不存在")
        return TaskInfoResponse(
            task_ids=[]
        )
    # 若存在 构造TaskInfoResponse对象
    # 获取指定用户ID和会话ID下所有任务的ID和状态值
    response = TaskInfoResponse(
        task_ids=await app.state.session_manager.get_task_status(user_id, session_id)
    )

    logger.info(f"返回当用户ID的指定会话ID的所有task_id:{response}")
    return response

# API接口:获取指定用户当前会话和任务ID的对应的状态数据
@app.get("/agent/status/{user_id}/{session_id}/{task_id}", response_model=SessionStatusResponse)
async def get_agent_status(user_id: str, session_id: str, task_id: str):
    logger.info(f"调用/agent/status/接口，获取指定用户当前会话和任务ID的对应的状态数据，接受到前端用户请求:{user_id}:{session_id}:{task_id}")
    # 检查指定用户ID的指定session_id的指定task_id是否存在
    exists = await app.state.session_manager.session_task_id_exists(user_id, session_id, task_id)
    # 若不存在 构造SessionStatusResponse对象
    if not exists:
        logger.warning(f"用户 {user_id}:{session_id}:{task_id} 的会话不存在")
        return SessionStatusResponse(
            user_id=user_id,
            session_id=session_id,
            task_id=task_id,
            status="not_found",
            message=f"用户 {user_id}:{session_id}:{task_id} 的会话不存在"
        )
    # 若存在 构造SessionStatusResponse对象
    # 获取指定用户当前会话和任务ID的对应的状态数据
    session = await app.state.session_manager.get_session_by_task(user_id, session_id, task_id)
    response = SessionStatusResponse(
        user_id=user_id,
        session_id=session_id,
        task_id=task_id,
        status=session.get("status"),
        last_query=session.get("last_query"),
        last_updated=session.get("last_updated"),
        last_response=session.get("last_response")
    )
    logger.info(f"返回当前用户当前会话和任务ID的对应的状态数据:{response}")
    return response

# API接口:写入指定用户的长期记忆
@app.post("/agent/write/longterm")
async def write_long_term(request: LongMemRequest):
    logger.info(f"调用/agent/write/long_term接口，写入指定用户的长期记忆，接受到前端用户请求:{request}")
    # 获取用户请求中的user_id、memory_info
    user_id = request.user_id
    memory_info = request.memory_info
    # 检查指定用户ID是否存在
    exists = await app.state.session_manager.user_id_exists(user_id)
    # 如果不存在 则抛出异常
    if not exists:
        logger.error(f"status_code=404,用户 {user_id} 不存在")
        raise HTTPException(status_code=404, detail=f"用户会话 {user_id} 不存在")
    # 若存在 则写入指定用户长期记忆内容
    result = await write_long_term_info(user_id, memory_info)
    # 检查返回结果是否成功
    if result.get("success", False):
        # 构造成功响应
        return {
            "status": "success",
            "memory_id": result.get("memory_id"),
            "message": result.get("message", "记忆存储成功")
        }
    else:
        # 处理非成功返回结果
        raise HTTPException(
            status_code=500,
            detail="记忆存储失败，返回结果未包含成功状态"
        )

# API接口:删除指定用户指定会话
@app.delete("/agent/session/{user_id}/{session_id}")
async def delete_agent_session(user_id: str, session_id: str):
    logger.info(f"调用/agent/session/接口，删除指定用户当前会话，接受到前端用户请求:{user_id}:{session_id}")
    # 检查指定用户ID的指定session_id是否存在
    exists = await app.state.session_manager.session_id_exists(user_id, session_id)
    # 如果不存在 则抛出异常
    if not exists:
        logger.error(f"status_code=404,用户 {user_id}:{session_id} 的会话不存在")
        raise HTTPException(status_code=404, detail=f"用户 {user_id}:{session_id} 的会话不存在")

    # 如果存在 则删除会话
    await app.state.session_manager.delete_session(user_id, session_id)
    response = {
        "status": "success",
        "message": f"用户 {user_id}:{session_id} 的会话已删除"
    }
    logger.info(f"用户会话已经删除:{response}")
    return response

# API接口:删除指定用户指定会话的指定任务
@app.delete("/agent/task/{user_id}/{session_id}/{task_id}")
async def delete_agent_task(user_id: str, session_id: str, task_id: str):
    logger.info(f"调用/agent/task/接口，删除指定用户指定会话的指定任务，接受到前端用户请求:{user_id}:{session_id}:{task_id}")
    # 检查指定用户ID的指定session_id的指定task_id是否存在
    exists = await app.state.session_manager.session_task_id_exists(user_id, session_id, task_id)
    # 如果不存在 则抛出异常
    if not exists:
        logger.error(f"status_code=404,用户 {user_id}:{session_id}:{task_id} 的任务不存在")
        raise HTTPException(status_code=404, detail=f"用户 {user_id}:{session_id}:{task_id} 的任务不存在")

    # 如果存在 则删除任务
    await app.state.session_manager.delete_session(user_id, session_id, task_id)
    response = {
        "status": "success",
        "message": f"用户 {user_id}:{session_id}:{task_id} 的任务已删除"
    }
    logger.info(f"用户任务已经删除:{response}")
    return response



# 启动服务器
if __name__ == "__main__":
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
