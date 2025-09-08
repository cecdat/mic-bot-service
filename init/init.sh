#!/bin/bash

echo "等待数据库服务就绪..."
while true; do
    if python -c "
import psycopg2
try:
    conn = psycopg2.connect(host='db', user='user', password='password', dbname='rewards_db')
    print('成功连接到数据库')
    conn.close()
    exit(0)
except Exception as e:
    print(f'连接数据库失败: {e}')
    exit(1)
"; then
        break
    fi
    sleep 1
done

echo "数据库服务已就绪，开始初始化..."

# 检查数据库是否已初始化
echo "检查数据库是否已初始化..."
TABLE_EXISTS=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'db_version');")

if [[ $TABLE_EXISTS == *"t"* ]]; then
    echo "数据库已初始化，跳过base.sql执行"
else
    echo "应用数据库初始化脚本base.sql..."
    PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -v ON_ERROR_STOP=1 -f sql/base.sql 2>&1 || {
        echo "执行base.sql失败"
        exit 1
    }
    echo "数据库初始化成功"
fi

echo "数据库初始化完成"

# 检查是否需要执行数据库升级
echo "=========================================="
echo "开始数据库升级检查..."
echo "=========================================="

# 检查数据库版本，只有在需要时才执行升级
echo "检查数据库版本..."
CURRENT_VERSION=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;" 2>/dev/null | xargs)

if [ -z "$CURRENT_VERSION" ]; then
    echo "❌ 无法获取数据库版本，跳过升级"
else
    echo "当前数据库版本: $CURRENT_VERSION"
    
    # 检查是否有新的升级脚本
    LATEST_SCRIPT_VERSION=""
    if [ -d "/app/sql" ]; then
        LATEST_SCRIPT_VERSION=$(ls /app/sql/upgrade_db_v*.sql 2>/dev/null | sed 's/.*upgrade_db_v\([0-9.]*\)\.sql/\1/' | sort -V | tail -1)
    fi
    
    if [ -z "$LATEST_SCRIPT_VERSION" ]; then
        echo "❌ 未找到升级脚本，跳过升级"
    elif [ "$CURRENT_VERSION" = "$LATEST_SCRIPT_VERSION" ]; then
        echo "✅ 数据库已是最新版本 ($CURRENT_VERSION)，跳过升级"
    else
        echo "🔄 发现新版本 ($LATEST_SCRIPT_VERSION)，开始升级..."
        
        # 使用Python数据库升级模块
        echo "使用Python数据库升级模块..."
        
        # 检查Python文件是否存在
        if [ ! -f "/app/init/upgrade_db.py" ]; then
            echo "❌ 升级脚本文件不存在: /app/init/upgrade_db.py"
            exit 1
        fi
        
        echo "🐍 执行Python升级脚本..."
        cd /app && python init/upgrade_db.py
        UPGRADE_EXIT_CODE=$?
        
        if [ $UPGRADE_EXIT_CODE -ne 0 ]; then
            echo "❌ 数据库升级失败，退出码: $UPGRADE_EXIT_CODE"
            exit 1
        else
            echo "✅ 数据库升级完成"
        fi
    fi
fi

echo "数据库初始化脚本执行完成"

# 启动Flask应用
echo "初始化完成，启动Flask应用..."

if [[ "${FLASK_ENV}" == "production" ]]; then
    echo "使用生产环境启动 (gunicorn)..."
    exec gunicorn --config config/gunicorn_eventlet.conf.py run:app
else
    echo "使用开发环境启动 (flask run)..."
    exec flask run --host=0.0.0.0 --port=5000
fi
