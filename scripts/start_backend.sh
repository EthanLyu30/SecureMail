#!/bin/bash
# 启动后端服务 - 开发模式

cd /home/exam/backend

# 启动服务（使用 SQLite，无须数据库配置）
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload