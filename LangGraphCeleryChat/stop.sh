#!/bin/bash

echo "🛑 停止 LangGraph Celery Chat 服务"
echo "=================================="

# 停止所有相关进程
echo "🔍 查找并停止相关进程..."

# 停止 FastAPI/Uvicorn 进程
echo "📱 停止 FastAPI 服务..."
pkill -f "uvicorn.*main:app" && echo "✅ FastAPI 服务已停止" || echo "ℹ️  没有找到 FastAPI 进程"

# 停止 Celery Worker 进程
echo "🔄 停止 Celery Worker..."
pkill -f "celery.*worker" && echo "✅ Celery Worker 已停止" || echo "ℹ️  没有找到 Celery Worker 进程"

# 停止所有包含 main.py 的 Python 进程（更精确的匹配）
echo "🐍 停止相关 Python 进程..."
pkill -f "python.*main" && echo "✅ 相关 Python 进程已停止" || echo "ℹ️  没有找到相关 Python 进程"

# 等待进程完全停止
echo "⏳ 等待进程完全停止..."
sleep 3

# 检查是否还有残留进程
echo "🔍 检查残留进程..."
REMAINING_PROCESSES=$(ps aux | grep -E "(uvicorn|celery|main)" | grep -v grep | grep -v stop.sh)

if [ -n "$REMAINING_PROCESSES" ]; then
    echo "⚠️  发现残留进程:"
    echo "$REMAINING_PROCESSES"
    echo ""
    echo "🔨 强制停止残留进程..."
    
    # 强制停止残留的 uvicorn 进程
    pkill -9 -f "uvicorn.*main:app" 2>/dev/null
    
    # 强制停止残留的 celery 进程
    pkill -9 -f "celery.*worker" 2>/dev/null
    
    # 强制停止残留的 python main 进程
    pkill -9 -f "python.*main" 2>/dev/null
    
    sleep 2
    echo "✅ 强制停止完成"
else
    echo "✅ 没有残留进程"
fi

# 最终检查
echo ""
echo "🔍 最终检查..."
FINAL_CHECK=$(ps aux | grep -E "(uvicorn|celery)" | grep -v grep | grep -v stop.sh)

if [ -n "$FINAL_CHECK" ]; then
    echo "❌ 仍有进程在运行:"
    echo "$FINAL_CHECK"
    echo ""
    echo "💡 你可能需要手动停止这些进程"
else
    echo "✅ 所有服务已成功停止"
fi

# 检查端口占用
echo ""
echo "🔍 检查端口占用情况..."
PORT_8000=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PORT_8000" ]; then
    echo "⚠️  端口 8000 仍被占用，进程ID: $PORT_8000"
    echo "🔨 尝试释放端口..."
    kill -9 $PORT_8000 2>/dev/null && echo "✅ 端口 8000 已释放" || echo "❌ 无法释放端口 8000"
else
    echo "✅ 端口 8000 已释放"
fi

echo ""
echo "🎉 停止脚本执行完成！"
echo "💡 现在可以运行 ./run.sh 重新启动服务"
