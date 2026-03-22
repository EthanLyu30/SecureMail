#!/bin/bash
# 启动 example.com 域名服务器

cd /home/exam/backend

# 设置域名环境变量
export DOMAIN_NAME="example.com"
export DOMAIN_ID=1
export SERVER_PORT=8001
export DATA_DIR="/home/exam/backend/data/example.com"

# 创建数据目录
mkdir -p "$DATA_DIR"

# 使用独立数据库
export DATABASE_URL="sqlite:///$DATA_DIR/mail.db"

echo "启动 example.com 邮件服务器..."
echo "端口: $SERVER_PORT"
echo "数据目录: $DATA_DIR"

python -c "from app.models import init_db; init_db()"

# 启动服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port $SERVER_PORT