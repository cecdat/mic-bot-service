#!/bin/bash

# 远程服务器数据库修复脚本
# 用于修复 search_cross_execution 字段缺失问题

echo "🔧 开始修复数据库字段缺失问题..."

# 检查 Docker Compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 命令未找到，请确保 Docker 已正确安装"
    exit 1
fi

# 检查数据库容器是否运行
echo "📋 检查数据库容器状态..."
if ! docker-compose ps db | grep -q "Up"; then
    echo "⚠️  数据库容器未运行，正在启动..."
    docker-compose up -d db
    
    # 等待数据库启动
    echo "⏳ 等待数据库启动完成..."
    sleep 10
fi

# 检查字段是否存在
echo "🔍 检查 search_cross_execution 字段是否存在..."
FIELD_EXISTS=$(docker-compose exec -T db psql -U user -d rewards_db -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bot_nodes' AND column_name = 'search_cross_execution';" 2>/dev/null | tr -d ' \n')

if [ "$FIELD_EXISTS" = "1" ]; then
    echo "✅ search_cross_execution 字段已存在，无需修复"
else
    echo "❌ search_cross_execution 字段不存在，开始修复..."
    
    # 添加字段
    echo "🔧 添加 search_cross_execution 字段..."
    if docker-compose exec -T db psql -U user -d rewards_db -c "ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;" 2>/dev/null; then
        echo "✅ 字段添加成功"
    else
        echo "❌ 字段添加失败"
        exit 1
    fi
    
    # 更新数据库版本
    echo "🔧 更新数据库版本到 2.12..."
    if docker-compose exec -T db psql -U user -d rewards_db -c "UPDATE db_version SET version = '2.12' WHERE id = 1;" 2>/dev/null; then
        echo "✅ 数据库版本更新成功"
    else
        echo "❌ 数据库版本更新失败"
        exit 1
    fi
fi

# 验证修复结果
echo "🔍 验证修复结果..."

# 检查字段
FIELD_CHECK=$(docker-compose exec -T db psql -U user -d rewards_db -t -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'bot_nodes' AND column_name = 'search_cross_execution';" 2>/dev/null | tr -d ' \n')

if [ "$FIELD_CHECK" = "search_cross_execution" ]; then
    echo "✅ 字段验证成功"
else
    echo "❌ 字段验证失败"
    exit 1
fi

# 检查版本
VERSION_CHECK=$(docker-compose exec -T db psql -U user -d rewards_db -t -c "SELECT version FROM db_version WHERE id = 1;" 2>/dev/null | tr -d ' \n')

if [ "$VERSION_CHECK" = "2.12" ]; then
    echo "✅ 版本验证成功"
else
    echo "❌ 版本验证失败，当前版本: $VERSION_CHECK"
fi

# 重启 API 服务
echo "🔄 重启 API 服务..."
if docker-compose restart api; then
    echo "✅ API 服务重启成功"
else
    echo "❌ API 服务重启失败"
    exit 1
fi

# 等待服务启动
echo "⏳ 等待服务启动完成..."
sleep 5

# 检查服务状态
echo "📋 检查服务状态..."
if docker-compose ps api | grep -q "Up"; then
    echo "✅ API 服务运行正常"
else
    echo "❌ API 服务启动失败"
    echo "📋 查看服务日志："
    docker-compose logs api --tail=20
    exit 1
fi

echo ""
echo "🎉 数据库修复完成！"
echo "📊 修复结果："
echo "   ✅ search_cross_execution 字段已添加"
echo "   ✅ 数据库版本已更新到 2.12"
echo "   ✅ API 服务已重启并运行正常"
echo ""
echo "💡 您现在可以正常使用搜索任务交叉执行功能了！"
