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
    """检查是否有中断请求 - 改进版本"""
    try:
        # 记录原始chunk用于调试
        logger.debug(f"检查中断 - chunk类型: {type(chunk)}, 内容: {chunk}")
        
        if isinstance(chunk, tuple) and len(chunk) == 2:
            stream_type, data = chunk
            logger.debug(f"流类型: {stream_type}, 数据类型: {type(data)}")
            
            # 检查是否是中断信号
            is_interrupt = False
            interrupt_info = None
            
            if stream_type == "updates" and isinstance(data, dict):
                # 方式1：检查 __interrupt__ 键
                if "__interrupt__" in data:
                    is_interrupt = True
                    interrupt_info = data["__interrupt__"]
                    logger.info(f"发现中断信号 (方式1): {interrupt_info}")
                
                # 方式2：检查是否有节点包含中断信息
                for node_name, node_data in data.items():
                    if isinstance(node_data, dict) and "interrupt" in str(node_data).lower():
                        is_interrupt = True
                        interrupt_info = node_data
                        logger.info(f"发现中断信号 (方式2) 在节点 {node_name}: {interrupt_info}")
                        break
            
            elif stream_type == "custom" and isinstance(data, dict):
                # 方式3：检查自定义事件中的中断
                if data.get("type") == "interrupt" or "interrupt" in data:
                    is_interrupt = True
                    interrupt_info = data
                    logger.info(f"发现中断信号 (方式3): {interrupt_info}")
            
            if not is_interrupt:
                # 方式4：检查整个chunk是否包含中断相关内容
                chunk_str = str(chunk).lower()
                if "interrupt" in chunk_str and ("confirmation" in chunk_str or "permission" in chunk_str):
                    is_interrupt = True
                    interrupt_info = {"raw_chunk": chunk}
                    logger.info(f"发现中断信号 (方式4): 在chunk字符串中检测到中断")
            
            if is_interrupt:
                # 更新任务状态为暂停
                redis_client.hset(f"task:{task_id}", "status", "paused")
                logger.info(f"任务 {task_id} 状态更新为 paused")

                # 构建中断事件
                interrupt_event = {
                    "type": "interrupt_request",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                    "detected_by": "improved_detection"
                }

                # 提取中断信息
                interrupt_data = _extract_interrupt_data(interrupt_info)
                interrupt_event.update(interrupt_data)

                # 发送中断事件
                try:
                    json_data = json.dumps(interrupt_event, ensure_ascii=False, default=str)
                    redis_client.xadd(
                        f"events:{task_id}",
                        {
                            "timestamp": str(time.time()),
                            "data": json_data
                        }
                    )
                    logger.info(f"中断事件已发送: {interrupt_event.get('interrupt_type', 'unknown')}")
                except Exception as e:
                    logger.error(f"发送中断事件失败: {e}")

                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查中断时发生错误: {e}")
        return False

def _extract_interrupt_data(interrupt_info):
    """提取中断数据 - 分离的辅助函数"""
    interrupt_data = {
        "interrupt_type": "confirmation",
        "title": "需要确认",
        "message": "请确认是否继续",
        "instructions": "请回复 'yes' 或 'no'",
        "interrupt_data": {}
    }
    
    try:
        # 处理不同类型的中断信息
        if isinstance(interrupt_info, tuple) and len(interrupt_info) > 0:
            # interrupt_info 是 tuple，第一个元素是 Interrupt 对象
            interrupt_obj = interrupt_info[0]
            if hasattr(interrupt_obj, 'value'):
                raw_data = interrupt_obj.value
            else:
                raw_data = {"message": str(interrupt_obj)}

        elif hasattr(interrupt_info, 'value'):
            # 这是一个直接的 Interrupt 对象
            raw_data = interrupt_info.value
        elif isinstance(interrupt_info, dict):
            # 这是一个普通字典
            raw_data = interrupt_info
        else:
            # 其他类型，转换为字符串
            raw_data = {"raw": str(interrupt_info)}

        # 从原始数据中提取结构化信息
        if isinstance(raw_data, dict):
            interrupt_data.update({
                "interrupt_type": raw_data.get("type", "confirmation"),
                "title": raw_data.get("type", "需要确认"),
                "message": raw_data.get("message", "请确认是否继续"),
                "instructions": raw_data.get("instructions", "请回复 'yes' 或 'no'"),
                "interrupt_data": raw_data
            })
        else:
            interrupt_data.update({
                "message": str(raw_data) if raw_data else "请确认是否继续",
                "interrupt_data": {"raw": str(raw_data)}
            })
    
    except Exception as e:
        logger.error(f"提取中断数据失败: {e}")
        interrupt_data["interrupt_data"] = {"error": str(e), "raw": str(interrupt_info)}
    
    return interrupt_data

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
            # 使用官方推荐的 AsyncRedisSaver 方式 - 修复环境变量问题
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver
            import os
            
            # 确保环境变量设置
            REDIS_URL = "redis://default:mfzstl2v@dbconn.sealoshzh.site:41277"
            
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
            # 使用官方推荐的 AsyncRedisSaver - 修复环境变量问题
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver
            import os
            
            # 确保环境变量设置
            os.environ["REDIS_URL"] = REDIS_URL
            
            async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
                await checkpointer.asetup()

                # 创建并编译图 - 强制重新创建
                workflow = create_writing_assistant_graph()
                graph = workflow.compile(checkpointer=checkpointer)

                chunk_count = 0
                final_result = None
                
                # 先检查当前图状态
                try:
                    current_state = await checkpointer.aget_tuple(config)
                    if current_state:
                        logger.info(f"恢复前的图状态: {current_state.metadata if hasattr(current_state, 'metadata') else 'unknown'}")
                        
                        # 检查next节点
                        if hasattr(current_state, 'next') and current_state.next:
                            logger.info(f"🎯 恢复前的next节点: {current_state.next}")
                        else:
                            logger.warning("⚠️ 恢复前没有next节点，图可能已完成或出错")
                            
                        if hasattr(current_state, 'checkpoint') and current_state.checkpoint:
                            state_data = current_state.checkpoint.get('channel_values', {})
                            logger.info(f"恢复前的状态键: {list(state_data.keys())}")
                            
                            # 打印状态值概览
                            state_overview = {}
                            for key, value in state_data.items():
                                if value is not None:
                                    if isinstance(value, str):
                                        state_overview[key] = f"str({len(value)} chars)"
                                    elif isinstance(value, list):
                                        state_overview[key] = f"list({len(value)} items)"
                                    elif isinstance(value, dict):
                                        state_overview[key] = f"dict({len(value)} keys)"
                                    else:
                                        state_overview[key] = f"{type(value).__name__}"
                            logger.info(f"状态值概览: {state_overview}")
                    else:
                        logger.warning("恢复前无法获取图状态")
                except Exception as state_error:
                    logger.error(f"检查恢复前状态失败: {state_error}")

                async for chunk in graph.astream(Command(resume=user_response), config, stream_mode=["updates", "custom"]):
                    chunk_count += 1
                    logger.info(f"恢复任务收到 chunk #{chunk_count}: {type(chunk)}")
                    
                    # 处理流式输出
                    await _process_stream_chunk(chunk, task_id)
                    
                    # 记录 chunk 内容
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
                                    
                                # 保存最后的结果
                                for node_name in node_names:
                                    if node_name in data and isinstance(data[node_name], dict):
                                        final_result = (stream_type, data)

                    # 检查中断 - 使用统一的中断处理函数
                    is_interrupt = _check_for_interruption(chunk, task_id)
                    if is_interrupt:
                        interrupted = True
                        logger.info(f"检测到新的中断，chunk #{chunk_count}")
                        return {"interrupted": True, "task_id": task_id}

                logger.info(f"恢复任务处理完成，总共处理了 {chunk_count} 个chunks")
                
                # 如果没有处理任何chunks，说明可能已经完成或出错
                if chunk_count == 0:
                    logger.warning("⚠️ 没有处理任何chunks，可能图已经完成或发生错误")
                    # 尝试获取当前完整状态
                    try:
                        current_state = await checkpointer.aget_tuple(config)
                        if current_state and hasattr(current_state, 'checkpoint') and current_state.checkpoint:
                            state_data = current_state.checkpoint.get('channel_values', {})
                            logger.info(f"完成后状态键详情: {[(k, type(v)) for k, v in state_data.items()]}")
                            
                            # 检查是否真的完成了
                            if state_data.get('article'):
                                logger.info("✅ 发现文章内容，任务确实已完成")
                                final_result = ('completed', state_data)
                            elif state_data.get('outline'):
                                logger.warning("⚠️ 只有大纲，可能任务未完全完成")
                            else:
                                logger.error("❌ 没有找到任何有效内容")
                    except Exception as e:
                        logger.error(f"获取完成状态失败: {e}")

            # 处理完成结果 - 改进版
            logger.info(f"🔍 恢复任务结束检查: interrupted={interrupted}, final_result={bool(final_result)}")

            if not interrupted:
                logger.info("✅ 任务未中断，开始处理完成结果")
                result_data = {}

                # 方式1：从final_result获取结果
                if final_result:
                    logger.info("从final_result提取数据...")
                    try:
                        if isinstance(final_result, tuple) and len(final_result) == 2:
                            stream_type, data = final_result
                            if stream_type == 'completed' and isinstance(data, dict):
                                # 直接使用完成的状态数据
                                result_data = {
                                    "outline": data.get("outline"),
                                    "article": data.get("article"),
                                    "search_results": data.get("search_results", []),
                                    "topic": data.get("topic"),
                                    "enhancement_suggestions": data.get("enhancement_suggestions", [])
                                }
                                logger.info(f"从completed状态提取结果键: {[k for k, v in result_data.items() if v]}")
                            elif stream_type == 'updates' and isinstance(data, dict):
                                # 从更新中提取结果
                                for node_name, node_data in data.items():
                                    if isinstance(node_data, dict):
                                        result_data.update({
                                            "outline": node_data.get("outline") or result_data.get("outline"),
                                            "article": node_data.get("article") or result_data.get("article"),
                                            "search_results": node_data.get("search_results", result_data.get("search_results", [])),
                                            "topic": node_data.get("topic") or result_data.get("topic"),
                                            "enhancement_suggestions": node_data.get("enhancement_suggestions", result_data.get("enhancement_suggestions", []))
                                        })
                                logger.info(f"从updates提取结果键: {[k for k, v in result_data.items() if v]}")
                    except Exception as final_error:
                        logger.error(f"从final_result提取失败: {final_error}")

                # 方式2：从checkpointer获取状态
                if not any(result_data.values()):
                    logger.info("从final_result未获取到数据，尝试checkpoint...")
                    try:
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
                            logger.info(f"从checkpoint提取的结果键: {[k for k, v in result_data.items() if v]}")
                    except Exception as checkpoint_error:
                        logger.error(f"从checkpoint获取失败: {checkpoint_error}")

                # 方式3：从Redis获取历史结果
                if not any(result_data.values()):
                    logger.info("从checkpoint未获取到数据，尝试Redis...")
                    try:
                        task_result = redis_client.hget(f"task:{task_id}", "result")
                        if task_result:
                            existing_result = json.loads(task_result)
                            if existing_result and any(existing_result.values()):
                                result_data = existing_result
                                logger.info(f"从Redis获取的结果键: {[k for k, v in result_data.items() if v]}")
                    except Exception as redis_e:
                        logger.error(f"从Redis获取结果失败: {redis_e}")

                # 检查结果状态
                if result_data.get("article"):
                    logger.info("✅ 找到生成的文章，任务确实完成")
                elif result_data.get("outline"):
                    logger.info("✅ 找到大纲，但没有文章 - 任务可能未完全完成")
                else:
                    logger.warning("⚠️ 没有找到任何内容，任务可能失败或未完成")
                    # 创建默认结果
                    if not result_data:
                        result_data = {
                            "outline": None,
                            "article": None,
                            "search_results": [],
                            "topic": None,
                            "enhancement_suggestions": []
                        }

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