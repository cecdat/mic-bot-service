#!/bin/bash

# 数据库初始化脚本
# 此脚本会在容器启动时自动执行

# 等待数据库服务就绪
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

echo "数据库初始化完成"

# 检查数据库版本
echo "查询当前数据库版本..."
CURRENT_VERSION=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;")
echo "当前数据库版本: ${CURRENT_VERSION}"

# 格式化当前版本号，移除空格和换行符
CURRENT_VERSION=$(echo "$CURRENT_VERSION" | tr -d ' \n')
# 如果当前版本为空，默认为0.0
if [[ -z "$CURRENT_VERSION" ]]; then
    CURRENT_VERSION="0.0"
fi

echo "当前数据库版本: $CURRENT_VERSION"

# 查找所有升级脚本并按版本号排序
UPGRADE_SCRIPTS=($(ls -1 sql/upgrade_db_v*.sql | sort -V))

# 遍历所有升级脚本
for SCRIPT in "${UPGRADE_SCRIPTS[@]}"; do
    # 提取脚本版本号
    SCRIPT_VERSION=$(echo "$SCRIPT" | sed -n 's/.*_v\([0-9]\.[0-9]\).*/\1/p')
    
    # 比较版本号
    if [[ "$SCRIPT_VERSION" > "$CURRENT_VERSION" ]]; then
        echo "发现需要应用的升级脚本: $SCRIPT (版本: $SCRIPT_VERSION)"
        
        # 执行升级脚本
        echo "应用升级脚本: $SCRIPT..."
        if PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -v ON_ERROR_STOP=1 -f "$SCRIPT"; then
            echo "升级脚本 $SCRIPT 应用成功"
            # 更新当前版本
            CURRENT_VERSION="$SCRIPT_VERSION"
        else
            echo "升级脚本 $SCRIPT 应用失败，终止升级过程"
            exit 1
        fi
    fi
done

if [[ "$CURRENT_VERSION" != "$(echo "${UPGRADE_SCRIPTS[-1]}" | sed -n 's/.*_v\([0-9]\.[0-9]\).*/\1/p')" ]] && [[ "${#UPGRADE_SCRIPTS[@]}" -gt 0 ]]; then
    echo "数据库已升级到最新版本: $CURRENT_VERSION"
fi

# 启动Flask应用
echo "初始化完成，启动Flask应用..."
flask run --host=0.0.0.0 --port=5000
