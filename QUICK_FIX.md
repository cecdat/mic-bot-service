# 快速修复指南

## 问题
mic-bot-service 启动时报错：`column bot_nodes.search_cross_execution does not exist`

## 快速修复方法

### 方法1：使用自动修复脚本（推荐）

**Linux/macOS 服务器：**
```bash
# 进入 mic-bot-service 目录
cd /path/to/mic-bot-service

# 给脚本执行权限
chmod +x scripts/fix_database.sh

# 执行修复脚本
./scripts/fix_database.sh
```

**Windows 服务器：**
```cmd
# 进入 mic-bot-service 目录
cd C:\path\to\mic-bot-service

# 执行修复脚本
scripts\fix_database.bat
```

### 方法2：手动执行命令

```bash
# 1. 添加缺失的字段
docker-compose exec db psql -U user -d rewards_db -c "ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;"

# 2. 更新数据库版本
docker-compose exec db psql -U user -d rewards_db -c "UPDATE db_version SET version = '2.12' WHERE id = 1;"

# 3. 重启服务
docker-compose restart api
```

### 方法3：使用修复脚本文件

```bash
# 执行修复脚本
docker-compose exec db psql -U user -d rewards_db -f /app/sql/fix_search_cross_execution_field.sql

# 重启服务
docker-compose restart api
```

## 验证修复

```bash
# 检查字段是否存在
docker-compose exec db psql -U user -d rewards_db -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'bot_nodes' AND column_name = 'search_cross_execution';"

# 检查数据库版本
docker-compose exec db psql -U user -d rewards_db -c "SELECT version FROM db_version WHERE id = 1;"

# 检查服务状态
docker-compose ps
```

## 预期结果

- 字段检查应该返回：`search_cross_execution`
- 版本检查应该返回：`2.12`
- 服务状态应该显示：`Up`

修复完成后，您就可以正常使用搜索任务交叉执行功能了！
