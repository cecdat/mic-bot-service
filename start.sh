#!/bin/bash

# 简化的启动脚本，避免Docker Compose复杂性问题

echo "启动 mic-bot-service..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误：Docker未运行，请先启动Docker"
    exit 1
fi

# 停止并删除现有容器
echo "清理现有容器..."
docker stop api postgres-db-service 2>/dev/null || true
docker rm api postgres-db-service 2>/dev/null || true

# 创建网络
echo "创建Docker网络..."
docker network create app-network 2>/dev/null || true

# 启动数据库
echo "启动PostgreSQL数据库..."
docker run -d \
    --name postgres-db-service \
    --network app-network \
    -e POSTGRES_DB=rewards_db \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e TZ=Asia/Shanghai \
    -e POSTGRES_INITDB_ARGS="--encoding=UTF-8" \
    -v $(pwd)/data:/var/lib/postgresql/data \
    -p 5432:5432 \
    --restart unless-stopped \
    postgres:16

# 等待数据库启动
echo "等待数据库启动..."
sleep 10

# 构建API镜像
echo "构建API镜像..."
docker build -t mic-bot-api .

# 启动API容器
echo "启动API容器..."
docker run -d \
    --name api \
    --network app-network \
    -e FLASK_APP=run \
    -e FLASK_ENV=production \
    -e TZ=Asia/Shanghai \
    -e DATABASE_URL=postgresql://user:password@postgres-db-service:5432/rewards_db \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=rewards_db \
    -v $(pwd)/run.py:/app/run.py:ro \
    -v $(pwd)/project:/app/project:ro \
    -v $(pwd)/init:/app/init:ro \
    -v $(pwd)/instance:/app/instance \
    -v $(pwd)/sql:/app/sql:ro \
    -p 2003:5000 \
    --restart unless-stopped \
    --entrypoint python \
    mic-bot-api /app/init/init.py

echo "启动完成！"
echo "API服务地址：http://localhost:2003"
echo "数据库端口：5432"

# 显示容器状态
echo "容器状态："
docker ps
