#!/bin/bash

echo "🚀 启动 WebSocket + LangGraph 集成版"
echo "=============================================="
echo "这个脚本现在只启动 Celery Worker。"
echo "请打开另一个终端，运行 'python3 websocket_langgraph.py' 来启动FastAPI服务。"
echo ""

# 清理旧的worker进程
echo "🧹 清理旧的Celery Worker进程..."
pkill -f "celery.*websocket_langgraph" 2>/dev/null || true

# 检查Redis连接
echo "🔍 检查 Redis 连接..."
if ! python3 -c "import redis; redis.Redis.from_url('redis://default:mfzstl2v@dbconn.sealoshzh.site:41277').ping()"; then
    echo "❌ Redis 连接失败"
    exit 1
fi
echo "✅ Redis 连接正常"

# 检查LangGraph模块
echo "🧠 检查 LangGraph 模块..."
if ! python3 -c "from graph.graph import create_writing_assistant_graph; print('✅ LangGraph模块正常')"; then
    echo "❌ LangGraph 模块导入失败"
    exit 1
fi

# 启动Celery Worker (在前台运行，以便查看日志)
echo "🔄 启动 LangGraph Celery Worker (前台模式)..."
echo "日志将直接输出到此终端。按 Ctrl+C 停止。"
python3 -m celery -A websocket_langgraph.celery_app worker --loglevel=info

