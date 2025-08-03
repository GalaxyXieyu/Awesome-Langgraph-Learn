#!/usr/bin/env python3
"""
启动 FastAPI 服务的简化脚本
"""

import uvicorn
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动 LangGraph Celery Chat API 服务")
    print("=" * 50)
    
    try:
        # 启动 FastAPI 服务
        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
