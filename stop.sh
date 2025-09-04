#!/bin/bash

# 停止 mic-bot-service 脚本

echo "停止 mic-bot-service..."

# 停止并删除容器
echo "停止容器..."
docker stop api postgres-db-service 2>/dev/null || true
docker rm api postgres-db-service 2>/dev/null || true

# 删除网络
echo "清理网络..."
docker network rm app-network 2>/dev/null || true

echo "停止完成！"
