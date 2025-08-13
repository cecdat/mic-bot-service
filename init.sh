#!/bin/bash

# 数据库初始化脚本
# 此脚本会在容器启动时自动执行

# 等待数据库服务就绪
echo "等待数据库服务就绪..."
# 使用Python检查数据库连接并输出错误信息
while true; do
    if python -c "import mysql.connector
try:
    conn = mysql.connector.connect(host='db', user='user', password='password', database='rewards_db')
    print('成功连接到数据库')
    conn.close()
    exit(0)
except Exception as e:
    print(f'连接数据库失败: {e}')
    exit(1)"; then
        break
    fi
    sleep 1
done

echo "数据库服务已就绪，开始初始化..."

# 确保版本表存在
echo "创建数据库版本表（如果不存在）..."
mysql -h db -uuser -ppassword rewards_db < create_version_table.sql

# 检查当前数据库版本
CURRENT_VERSION=$(mysql -h db -uuser -ppassword -e "USE rewards_db; SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;" | tail -1)
echo "当前数据库版本: ${CURRENT_VERSION:-未初始化}"

# 检查数据库是否已初始化
# 通过检查web_users表是否存在来判断
TABLE_EXISTS=$(mysql -h db -uuser -ppassword -e "USE rewards_db; SHOW TABLES LIKE 'web_users';" | wc -l)

if [ $TABLE_EXISTS -eq 0 ]; then
    echo "首次初始化数据库..."
    # 执行数据库初始化
    flask init-db
    
    # 记录初始版本
    echo "记录初始数据库版本..."
    mysql -h db -uuser -ppassword -e "USE rewards_db; INSERT INTO db_version (version, description) VALUES ('1.0', '初始数据库结构');"
    
    # 临时禁用自动创建管理员账号
    echo "临时禁用自动创建管理员账号，用于测试无平台用户场景。"
else
    echo "数据库已初始化，检查是否需要升级..."
    
    # 检查是否需要应用升级脚本
    # 这里可以添加版本检查逻辑，根据CURRENT_VERSION应用不同的升级脚本
    
    # 示例：如果当前版本小于1.1，则应用upgrade_db.sql
    if [[ -z "$CURRENT_VERSION" || $(echo "$CURRENT_VERSION < 1.1" | bc) -eq 1 ]]; then
        echo "发现数据库版本需要升级，应用升级脚本upgrade_db.sql..."
        mysql -h db -uuser -ppassword rewards_db < upgrade_db.sql
        
        # 记录升级版本
        echo "记录升级后的数据库版本..."
        mysql -h db -uuser -ppassword -e "USE rewards_db; INSERT INTO db_version (version, description) VALUES ('1.1', '增加桌面和移动端收益字段，以及节点活动状态相关字段');"
    fi
fi

echo "初始化完成，启动应用..."
# 启动应用
flask run --host=0.0.0.0