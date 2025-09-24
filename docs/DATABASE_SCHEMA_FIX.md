# 数据库模型定义修复说明

## 问题描述

mic-bot-service 启动时出现数据库错误：
```
psycopg2.errors.UndefinedColumn: column bot_nodes.search_split_enabled does not exist
```

## 问题分析

### 根本原因
1. **数据库升级脚本**：`upgrade_db_v2.12.sql` 删除了 `log_push_enabled` 和 `log_push_interval` 字段
2. **模型定义不匹配**：`models.py` 中的 `BotNode` 模型仍然包含 `search_split_*` 字段
3. **数据库结构**：实际数据库中没有这些字段，但模型定义中仍然存在
4. **SQLAlchemy 查询失败**：启动时查询 `BotNode.query.all()` 失败

### 错误流程
```
应用启动 → 初始化调度器 → 查询所有节点 → SQLAlchemy 生成SQL → 查询不存在的字段 → 数据库错误
```

## 修复方案

### 1. 移除模型中的不存在的字段

**修复前**：
```python
class BotNode(db.Model):
    # ... 其他字段 ...
    search_delay_min = db.Column(db.String(10), default='30s')
    search_delay_max = db.Column(db.String(10), default='2min')
    # 搜索任务拆分配置
    search_split_enabled = db.Column(db.Boolean, default=False)
    search_split_count = db.Column(db.Integer, default=3)
    search_split_interval_min = db.Column(db.Integer, default=30)
    search_split_interval_max = db.Column(db.Integer, default=120)
```

**修复后**：
```python
class BotNode(db.Model):
    # ... 其他字段 ...
    search_delay_min = db.Column(db.String(10), default='30s')
    search_delay_max = db.Column(db.String(10), default='2min')
```

### 2. 更新API中的字段引用

**修复的API端点**：
- **节点列表API** (`/web_api/nodes`) - 移除响应中的 `search_split_*` 字段
- **节点创建API** (`POST /web_api/nodes`) - 移除创建时的 `search_split_*` 字段
- **节点更新API** (`PUT /web_api/nodes/<id>`) - 移除更新时的 `search_split_*` 字段

**修复前**：
```python
node_data.append({
    # ... 其他字段 ...
    'search_split_enabled': node.search_split_enabled,
    'search_split_count': node.search_split_count,
    'search_split_interval_min': node.search_split_interval_min,
    'search_split_interval_max': node.search_split_interval_max,
})
```

**修复后**：
```python
node_data.append({
    # ... 其他字段 ...
    # 移除了 search_split_* 字段
})
```

### 3. 更新前端UI

**移除的UI元素**：
- 搜索任务拆分复选框
- 拆分次数输入框
- 拆分间隔时间输入框

**修复前**：
```html
<div class="layui-form-item">
    <label>搜索拆分</label>
    <input type="checkbox" name="search_split_enabled">
    <input type="number" name="search_split_count">
    <input type="number" name="search_split_interval_min">
    <input type="number" name="search_split_interval_max">
</div>
```

**修复后**：
```html
<!-- 完全移除了搜索拆分相关的UI元素 -->
```

### 4. 更新JavaScript逻辑

**移除的JavaScript代码**：
```javascript
"search_split_enabled": data ? data.search_split_enabled : false,
"search_split_count": data ? data.search_split_count : 3,
"search_split_interval_min": data ? data.search_split_interval_min : 30,
"search_split_interval_max": data ? data.search_split_interval_max : 120
```

## 修复效果

### 修复前的问题
- 应用启动失败
- 数据库查询错误
- 模型定义与数据库结构不匹配

### 修复后的效果
- 应用正常启动
- 数据库查询成功
- 模型定义与数据库结构一致
- 前端UI简化，移除不需要的功能

## 技术细节

### 数据库字段对比

**保留的字段**：
- `search_delay_min` - 搜索延迟最小值
- `search_delay_max` - 搜索延迟最大值

**移除的字段**：
- `search_split_enabled` - 搜索任务拆分启用状态
- `search_split_count` - 搜索任务拆分次数
- `search_split_interval_min` - 拆分间隔最小时间
- `search_split_interval_max` - 拆分间隔最大时间

### 兼容性考虑
- 保持现有功能不受影响
- 移除未使用的功能
- 确保API响应格式一致

### 错误处理
- 模型定义与数据库结构同步
- 避免查询不存在的字段
- 确保应用启动成功

## 部署说明

1. **更新代码**：
   ```bash
   # 在远程服务器上更新代码
   git pull origin main
   ```

2. **重启服务**：
   ```bash
   cd mic-bot-service
   docker-compose restart
   ```

3. **验证修复效果**：
   - 检查应用启动日志
   - 确认没有数据库错误
   - 验证节点管理功能正常

## 测试建议

1. **启动测试**：
   - 确认应用正常启动
   - 检查调度器初始化成功
   - 验证数据库连接正常

2. **功能测试**：
   - 测试节点列表显示
   - 验证节点创建功能
   - 检查节点更新功能

3. **UI测试**：
   - 确认前端页面正常加载
   - 验证节点管理界面
   - 检查表单提交功能

## 监控要点

1. **启动日志**：确认没有数据库错误
2. **功能完整性**：验证节点管理功能正常
3. **性能影响**：监控修复对性能的影响
4. **错误日志**：检查是否有新的错误

---

*修复完成时间: 2024-12-19*
*修复版本: v2.12*
*影响范围: 数据库模型定义、API响应、前端UI*
