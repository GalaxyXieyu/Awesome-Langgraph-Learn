"""
流式事件处理工具
处理Redis流的SSE事件生成
"""

import json
from typing import AsyncGenerator


async def generate_stream_events(task_id: str, redis_client) -> AsyncGenerator[str, None]:
    """
    生成SSE流式事件 - 从Redis流读取并转换为SSE格式
    
    Args:
        task_id: 任务ID
        redis_client: Redis客户端
        
    Yields:
        str: SSE格式的事件数据
    """
    stream_name = f"events:{task_id}"
    last_id = "0"

    # 立即发送连接确认
    yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id})}\n\n"

    try:
        # 检查流是否存在
        exists = redis_client.exists(stream_name)
        if exists:
            # 读取所有现有消息
            all_messages = redis_client.xrange(stream_name)
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

        # 监听新消息
        timeout_count = 0
        while timeout_count < 120:  # 2分钟超时
            try:
                # 检查任务状态
                status = redis_client.hget(f"task:{task_id}", "status")
                if status in {"completed", "canceled", "failed"}:
                    yield f"data: {json.dumps({'type': 'task_status', 'status': status})}\n\n"
                    break

                # 读取新消息
                results = redis_client.xread({stream_name: last_id}, block=1000, count=10)

                if results:
                    timeout_count = 0  # 重置超时计数
                    _, messages = results[0]
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

            except Exception as e:
                timeout_count += 1
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
