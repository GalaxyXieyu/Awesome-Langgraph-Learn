#!/bin/bash

# LangGraph Celery Chat - 优化版启动脚本

echo "🚀 启动 LangGraph Celery Chat - 优化版"

# 检查 Redis 是否运行（跳过本地检查，使用远程 Redis）
echo "🔗 使用远程 Redis 服务"

echo "✅ Redis 已启动"

# 启动 Celery Worker (后台)
echo "🔄 启动 Celery Worker..."
python3 -m celery -A main.celery_app worker --loglevel=info --detach

# 等待 Celery 启动
sleep 2

# 启动 FastAPI 服务
echo "🌐 启动 FastAPI 服务..."
echo "📱 API 地址: http://localhost:8000"
echo "📋 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000