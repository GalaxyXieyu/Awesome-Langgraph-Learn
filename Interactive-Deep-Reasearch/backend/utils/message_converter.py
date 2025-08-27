"""
消息格式转换工具 - 超简化版
就是 graph 的 chunk 转化一层到 redis
"""

import json
import time
from typing import Any


def process_chunk(chunk: Any, task_id: str, redis_client, processor=None):
    """
    超简化版：graph chunk 转化一层到 redis - 只保留核心数据
    """
    try:
        # 1. 处理 ('custom', ...) 格式 - 解包双层嵌套
        if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == 'custom':
            data = chunk[1]

            # 解包双层嵌套: ('custom', ('custom', {...})) -> {...}
            if isinstance(data, tuple) and len(data) == 2 and data[0] == 'custom':
                data = data[1]

            if isinstance(data, dict):
                # 简化数据：只保留核心字段
                core_data = {
                    "message_type": data.get('message_type', 'unknown'),
                    "content": data.get('content', ''),
                    "node": data.get('node', 'unknown'),
                    "task_id": task_id
                }

                # 简单转换：interrupt_request -> interrupt
                if core_data['message_type'] == 'interrupt_request':
                    core_data['message_type'] = 'interrupt'

                # 保留一些有用的字段
                if 'progress' in data:
                    core_data['progress'] = data['progress']
                if 'action' in data:
                    core_data['action'] = data['action']
                if 'args' in data:
                    core_data['args'] = data['args']

                redis_client.xadd(
                    f"events:{task_id}",
                    {"timestamp": str(time.time()), "data": json.dumps(core_data, ensure_ascii=False)}
                )
                return True

        # 2. 处理 AIMessageChunk - 只保留内容
        if isinstance(chunk, tuple) and len(chunk) == 2:
            chunk_type, chunk_data = chunk
            if chunk_type == 'messages' and isinstance(chunk_data, tuple) and len(chunk_data) == 2:
                message_obj, metadata = chunk_data
                if hasattr(message_obj, 'content') and message_obj.content:
                    content = str(message_obj.content).strip()
                    if content:
                        # 从metadata中提取节点信息
                        node = metadata.get('langgraph_node', 'ai_generator') if metadata else 'ai_generator'

                        core_data = {
                            "message_type": "content",
                            "content": content,
                            "node": node,
                            "task_id": task_id
                        }
                        redis_client.xadd(
                            f"events:{task_id}",
                            {"timestamp": str(time.time()), "data": json.dumps(core_data, ensure_ascii=False)}
                        )
                        return True

        return False

    except Exception as e:
        # 简化错误处理
        error_data = {
            "message_type": "error",
            "content": f"处理错误: {str(e)}",
            "node": "error",
            "task_id": task_id
        }
        redis_client.xadd(
            f"events:{task_id}",
            {"timestamp": str(time.time()), "data": json.dumps(error_data, ensure_ascii=False)}
        )
        return False
