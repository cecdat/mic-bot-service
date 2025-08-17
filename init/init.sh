#!/bin/bash

# 数据库初始化脚本
# 此脚本会在容器启动时自动执行

# 等待数据库服务就绪
echo "等待数据库服务就绪..."
# 使用Python检查数据库连接并输出错误信息
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

# 检查数据库是否已初始化（通过检查db_version表是否存在）
echo "检查数据库是否已初始化..."
TABLE_EXISTS=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'db_version');")

if [[ $TABLE_EXISTS == *"t"* ]]; then
    echo "数据库已初始化，跳过base.sql执行"
else
    # 执行数据库初始化（使用合并后的base.sql脚本）
    echo "应用数据库初始化脚本base.sql..."
    # 调试信息：检查psql命令是否存在
    which psql || echo "psql命令不存在"
    # 打印环境变量
    echo "POSTGRES_USER: ${POSTGRES_USER}"
    echo "POSTGRES_DB: ${POSTGRES_DB}"
    echo "DATABASE_URL: ${DATABASE_URL}"
    # 列出sql目录下的文件，确认base.sql存在
    ls -la sql/
    # 尝试使用绝对路径执行psql，并输出详细错误信息
    echo "开始执行base.sql脚本..."
    PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -v ON_ERROR_STOP=1 -f sql/base.sql 2>&1 || {
        echo "使用绝对路径执行psql失败"
        exit 1
    }

    echo "数据库初始化成功"
fi

echo "数据库初始化成功"

# 检查数据库版本
echo "查询当前数据库版本..."
# 查询当前数据库版本...
# 尝试使用绝对路径执行psql查询，提供密码
CURRENT_VERSION=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;")
echo "当前数据库版本: ${CURRENT_VERSION}"

# 检查是否需要应用升级脚本
# 简化版本检查，避免使用bc命令
if [[ "$CURRENT_VERSION" == *"1.0"* ]] || [[ -z "$CURRENT_VERSION" ]]; then
    echo "发现数据库版本需要升级，应用升级脚本upgrade_db.sql..."
    PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f sql/upgrade_db.sql
    
    # 记录升级版本
    echo "记录升级后的数据库版本..."
    PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "INSERT INTO db_version (version, description) VALUES ('1.1', '增加桌面和移动端收益字段，以及节点活动状态相关字段');"
fi

# 启动应用
echo "初始化完成，启动应用..."
# 启动应用
flask run --host=0.0.0.0