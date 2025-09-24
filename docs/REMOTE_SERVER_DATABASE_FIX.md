# 远程服务器数据库修复指南

## 问题描述

在远程服务器上部署 mic-bot-service 时，出现以下错误：
```
column bot_nodes.search_cross_execution does not exist
```

这是因为数据库升级脚本虽然执行了，但是 `search_cross_execution` 字段没有被正确添加到数据库中。

## 修复步骤

### 方法1：使用修复脚本（推荐）

1. **上传修复脚本到服务器**
   ```bash
   # 将 fix_search_cross_execution_field.sql 上传到服务器的 /app/sql/ 目录
   ```

2. **连接到数据库容器**
   ```bash
   # 进入 mic-bot-service 目录
   cd /path/to/mic-bot-service
   
   # 连接到数据库容器
   docker-compose exec db psql -U user -d rewards_db
   ```

3. **执行修复脚本**
   ```sql
   -- 在 psql 中执行
   \i /app/sql/fix_search_cross_execution_field.sql
   ```

4. **验证修复结果**
   ```sql
   -- 检查字段是否存在
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'bot_nodes' 
   AND column_name = 'search_cross_execution';
   
   -- 检查数据库版本
   SELECT version FROM db_version WHERE id = 1;
   ```

### 方法2：手动执行 SQL 命令

1. **连接到数据库容器**
   ```bash
   docker-compose exec db psql -U user -d rewards_db
   ```

2. **手动添加字段**
   ```sql
   -- 添加字段
   ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;
   
   -- 更新数据库版本
   UPDATE db_version SET version = '2.12' WHERE id = 1;
   ```

3. **验证修复**
   ```sql
   -- 检查字段
   \d bot_nodes
   
   -- 检查版本
   SELECT version FROM db_version WHERE id = 1;
   ```

### 方法3：使用 Docker 命令直接执行

```bash
# 直接执行修复脚本
docker-compose exec db psql -U user -d rewards_db -f /app/sql/fix_search_cross_execution_field.sql

# 或者执行单个命令
docker-compose exec db psql -U user -d rewards_db -c "ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;"
docker-compose exec db psql -U user -d rewards_db -c "UPDATE db_version SET version = '2.12' WHERE id = 1;"
```

## 验证修复

### 1. 检查字段是否存在
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'bot_nodes' 
AND column_name = 'search_cross_execution';
```

**期望结果：**
```
      column_name       
------------------------
 search_cross_execution
(1 row)
```

### 2. 检查数据库版本
```sql
SELECT version FROM db_version WHERE id = 1;
```

**期望结果：**
```
 version 
---------
 2.12
(1 row)
```

### 3. 检查表结构
```sql
\d bot_nodes
```

**期望结果：** 应该能看到 `search_cross_execution` 字段

## 重启服务

修复完成后，重启 mic-bot-service：

```bash
# 重启 API 服务
docker-compose restart api

# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs api --tail=20
```

## 故障排除

### 问题1：无法连接到数据库
```bash
# 检查数据库容器是否运行
docker-compose ps

# 启动数据库容器
docker-compose up -d db

# 等待数据库启动完成
docker-compose logs db --tail=10
```

### 问题2：权限问题
```bash
# 检查数据库用户权限
docker-compose exec db psql -U user -d rewards_db -c "\du"
```

### 问题3：字段已存在但服务仍报错
```bash
# 重启所有服务
docker-compose down
docker-compose up -d

# 或者只重启 API 服务
docker-compose restart api
```

## 预防措施

为了避免类似问题，建议：

1. **定期备份数据库**
   ```bash
   docker-compose exec db pg_dump -U user rewards_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **验证升级脚本执行结果**
   ```bash
   # 检查数据库版本
   docker-compose exec db psql -U user -d rewards_db -c "SELECT version FROM db_version WHERE id = 1;"
   
   # 检查表结构
   docker-compose exec db psql -U user -d rewards_db -c "\d bot_nodes"
   ```

3. **监控服务启动日志**
   ```bash
   docker-compose logs api --tail=50
   ```

## 联系支持

如果修复过程中遇到问题，请提供以下信息：

1. 错误日志
2. 数据库版本信息
3. 表结构信息
4. 服务状态信息

---

*修复指南版本: 1.0*
*创建日期: 2024-12-19*
*最后更新: 2024-12-19*
