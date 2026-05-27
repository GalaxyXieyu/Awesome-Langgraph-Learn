#!/bin/bash

# LangGraph Celery Chat - 优化版启动脚本

echo "🚀 启动 LangGraph Celery Chat - 优化版"

# 清理旧进程
pkill -f "celery.*main.celery_app"
pkill -f "uvicorn main:app"
echo "🧹 旧进程已清理"

# 检查 Redis 是否运行（跳过本地检查，使用远程 Redis）
echo "🔗 使用远程 Redis 服务"

# 启动 FastAPI 服务 (后台)
echo "🌐 启动 FastAPI 服务 (后台)..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi_server.log 2>&1 &
FASTAPI_PID=$!
sleep 2 # 等待服务启动

echo "✅ FastAPI 服务已在后台启动 (PID: $FASTAPI_PID)"
echo "📱 API 地址: http://localhost:8000"
echo "📋 API 文档: http://localhost:8000/docs"
echo ""

# 启动 Celery Worker (前台)
echo "🔄 启动 Celery Worker (前台)..."
echo "Worker 的日志将直接输出到此终端。按 Ctrl+C 停止所有服务。"

# 定义清理函数
cleanup() {
    echo "🛑 正在停止服务..."
    kill $FASTAPI_PID
    pkill -f "celery.*main.celery_app"
    echo "✅ 所有服务已停止。"
    exit 0
}

# 捕获 Ctrl+C 信号
trap cleanup SIGINT

python3 -m celery -A main.celery_app worker --loglevel=info

# 如果worker退出，也执行清理
cleanup
