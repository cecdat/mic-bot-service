#!/bin/bash

# Docker 构建脚本 - 处理网络超时问题

echo "🚀 开始构建 mic-bot-service Docker 镜像..."

# 设置构建参数
IMAGE_NAME="mic-bot-service"
TAG="latest"

# 清理旧的构建缓存（可选）
echo "🧹 清理 Docker 构建缓存..."
docker builder prune -f

# 尝试构建，如果失败则使用备用方法
echo "📦 尝试构建 Docker 镜像..."

if docker build -t ${IMAGE_NAME}:${TAG} .; then
    echo "✅ Docker 镜像构建成功！"
    echo "📋 镜像信息："
    docker images | grep ${IMAGE_NAME}
else
    echo "❌ 标准构建失败，尝试使用优化版本..."
    
    # 使用优化的 Dockerfile
    if docker build -f Dockerfile.optimized -t ${IMAGE_NAME}:${TAG} .; then
        echo "✅ 使用优化版本构建成功！"
    else
        echo "❌ 优化版本也失败，尝试使用备用版本..."
        
        # 使用备用 Dockerfile
        if docker build -f Dockerfile.backup -t ${IMAGE_NAME}:${TAG} .; then
            echo "✅ 使用备用版本构建成功！"
        else
            echo "❌ 所有构建方法都失败了！"
            echo "💡 建议："
            echo "1. 检查网络连接"
            echo "2. 尝试使用 VPN"
            echo "3. 手动修改 Dockerfile 中的镜像源"
            echo "4. 使用 docker build --network=host 参数"
            exit 1
        fi
    fi
fi

echo "🎉 构建完成！"
echo "🚀 启动命令："
echo "docker-compose up -d --build"
