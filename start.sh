#!/bin/bash

# 设置宿主机主机名
export HOST_HOSTNAME=$(hostname)

echo "设置 HOST_HOSTNAME 为: $HOST_HOSTNAME"

dos2unix ./init/init.sh
# 启动 Docker Compose
docker-compose up -d --build
