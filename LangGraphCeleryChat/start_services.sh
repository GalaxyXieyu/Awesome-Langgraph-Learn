#!/bin/bash

# LangGraph Celery Chat 服务启动脚本

echo "🚀 启动 LangGraph Celery Chat 服务"
echo "=================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查 Redis 服务
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis 未安装"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 加载环境变量
if [ -f .env ]; then
    echo "📄 加载环境变量..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env 文件不存在，使用默认配置"
fi

# 启动 Redis (如果未运行)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔴 启动 Redis 服务..."
    redis-server --daemonize yes --logfile logs/redis.log
    sleep 2
else
    echo "✅ Redis 服务已运行"
fi

# 检查 Redis 连接
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis 连接正常"
else
    echo "❌ Redis 连接失败"
    exit 1
fi

# 安装依赖
echo "📦 检查 Python 依赖..."
pip install -r requirements.txt

# 启动 Celery Worker
echo "👷 启动 Celery Worker..."
celery -A backend.celery_app worker --loglevel=info --logfile=logs/celery_worker.log --detach

# 启动 Celery Flower (监控)
echo "🌸 启动 Celery Flower 监控..."
celery -A backend.celery_app flower --port=5555 --logfile=logs/celery_flower.log &

# 等待服务启动
sleep 3

# 启动 FastAPI 服务
echo "🌐 启动 FastAPI 服务..."
echo "API 地址: http://localhost:8000"
echo "Flower 监控: http://localhost:5555"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 启动 FastAPI
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

echo ""
echo "🛑 正在停止服务..."

# 停止 Celery 进程
pkill -f "celery.*worker"
pkill -f "celery.*flower"

echo "✅ 服务已停止"
