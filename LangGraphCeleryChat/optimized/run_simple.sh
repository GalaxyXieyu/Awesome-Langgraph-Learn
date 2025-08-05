#!/bin/bash

echo "🚀 启动 WebSocket + LangGraph 简化版"
echo "=============================================="
echo "支持真正的中断处理和用户交互"

# 清理旧的worker进程
echo "🧹 清理旧的Celery Worker进程..."
pkill -f "celery.*websocket_simple" 2>/dev/null || true

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

# 启动Celery Worker (后台运行)
echo "🔄 启动简化版 Celery Worker..."
python3 -m celery -A websocket_simple.celery_app worker --loglevel=info --detach --pidfile=/tmp/celery_simple.pid

# 等待Celery启动
sleep 3

# 检查Celery是否启动成功
if pgrep -f "celery.*websocket_simple" > /dev/null; then
    echo "✅ 简化版 Celery Worker 启动成功"
else
    echo "❌ 简化版 Celery Worker 启动失败"
    exit 1
fi

# 启动WebSocket服务
echo "🌐 启动 WebSocket + LangGraph 简化版服务..."
echo "📱 访问地址: http://localhost:8005"
echo "🧠 支持真正的中断处理和用户交互"
echo "⚡ 支持高并发连接"
echo ""
echo "按 Ctrl+C 停止服务"

# 设置退出处理
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    pkill -f "celery.*websocket_simple" 2>/dev/null || true
    rm -f /tmp/celery_simple.pid
    echo "✅ 服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

python3 websocket_simple.py
