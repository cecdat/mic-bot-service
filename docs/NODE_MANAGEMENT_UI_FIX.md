# 节点管理页面UI修复说明

## 问题描述

mic-bot-service 节点管理页面存在两个问题：

1. **UI显示问题**：交叉执行开关的 `title` 属性显示"搜索任务交叉执行"文字，导致开关被拉得太长
2. **保存报错**：交叉执行开关修改保存时报错，接口返回500错误

## 问题分析

### 问题1：UI显示问题
- **原因**：LayUI 的 `lay-skin="switch"` 组件在设置了 `title` 属性时，会在开关内显示文字
- **影响**：开关被拉得太长，影响页面美观

### 问题2：保存报错问题
- **原因**：可能是数据库字段 `search_cross_execution` 不存在或数据库版本问题
- **影响**：无法保存交叉执行配置，功能不可用

## 修复方案

### 1. 修复UI显示问题

**修复前：**
```html
<input type="checkbox" name="search_cross_execution" lay-skin="switch" title="搜索任务交叉执行">
```

**修复后：**
```html
<input type="checkbox" name="search_cross_execution" lay-skin="switch">
```

**修复说明：**
- 移除了 `title` 属性，避免在开关内显示文字
- 保留了开关功能，通过注释说明用途

### 2. 修复保存报错问题

#### 检查数据库状态
创建了检查脚本来诊断数据库问题：

```bash
# 检查数据库状态
python /app/scripts/check_database.py
```

#### 修复数据库字段
如果字段不存在，使用修复脚本：

```bash
# 修复数据库字段
python /app/scripts/fix_search_cross_execution.py
```

#### 手动SQL修复
如果脚本无法运行，可以手动执行SQL：

```sql
-- 检查字段是否存在
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'bot_nodes' 
    AND column_name = 'search_cross_execution'
);

-- 如果字段不存在，添加字段
ALTER TABLE bot_nodes 
ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;

-- 更新数据库版本
UPDATE db_version SET version = '2.12' WHERE id = 1;
```

## 修复效果

### 预期改善
1. **UI优化**：交叉执行开关不再显示内部文字，界面更美观
2. **功能恢复**：交叉执行开关可以正常保存和修改
3. **错误消除**：不再出现500错误

### 修复后的UI效果

**修复前：**
```
[交叉运行] [搜索任务交叉执行] 开启后，搜索任务将按账户轮询执行...
```

**修复后：**
```
[交叉运行] [开关] 开启后，搜索任务将按账户轮询执行...
```

## 测试验证

### 测试场景
1. **UI测试**：验证交叉执行开关显示正常
2. **功能测试**：测试开关的开启/关闭功能
3. **保存测试**：验证配置能够正常保存
4. **API测试**：测试PUT接口是否正常响应

### 验证命令
```bash
# 检查数据库状态
docker-compose exec api python /app/scripts/check_database.py

# 修复数据库字段（如果需要）
docker-compose exec api python /app/scripts/fix_search_cross_execution.py

# 重启服务
docker-compose restart mic-bot-service

# 测试API接口
curl -X PUT http://localhost:5000/web_api/nodes \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "node_name": "test", "search_cross_execution": true}'
```

## 相关文件

### 修改文件
- `mic-bot-service/project/templates/nodes.html` - 修复UI显示问题

### 新增文件
- `mic-bot-service/scripts/check_database.py` - 数据库状态检查脚本
- `mic-bot-service/scripts/fix_search_cross_execution.py` - 数据库字段修复脚本

### 相关文件
- `mic-bot-service/project/api_web.py` - API处理逻辑
- `mic-bot-service/project/models.py` - 数据库模型
- `mic-bot-service/sql/upgrade_db_v2.12.sql` - 数据库升级脚本

## 注意事项

1. **数据库备份**：在执行修复脚本前，建议备份数据库
2. **服务重启**：修复后需要重启 mic-bot-service 服务
3. **版本检查**：确保数据库版本正确更新到 2.12

## 故障排除

### 如果修复后仍有问题

1. **检查数据库连接**：
   ```bash
   docker-compose exec postgres-db-service psql -U postgres -d mic_bot_db -c "\d bot_nodes"
   ```

2. **检查服务日志**：
   ```bash
   docker-compose logs mic-bot-service
   ```

3. **手动验证字段**：
   ```sql
   SELECT column_name, data_type, column_default 
   FROM information_schema.columns 
   WHERE table_name = 'bot_nodes' 
   AND column_name = 'search_cross_execution';
   ```

## 回滚方案

如果修复后出现问题，可以回滚：

```bash
# 回滚UI修改
git checkout HEAD~1 -- mic-bot-service/project/templates/nodes.html

# 回滚数据库字段（如果需要）
ALTER TABLE bot_nodes DROP COLUMN IF EXISTS search_cross_execution;
```

---

*修复说明版本: 1.0*
*创建日期: 2024-12-19*
*最后更新: 2024-12-19*
