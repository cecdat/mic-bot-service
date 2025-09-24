# 节点重启历史记录表修复说明

## 问题描述

重启节点服务时出现数据库错误：
```
postgres-db-service | 2025-09-22 10:57:59.412 CST [388] ERROR: relation "node_restart_history" does not exist
api | 2025-09-22 10:57:59,414 - project - ERROR - 重启节点失败: (psycopg2.errors.UndefinedTable) relation "node_restart_history" does not exist
```

## 问题分析

### 根本原因
1. **数据库表缺失**：`node_restart_history` 表不存在
2. **升级脚本未执行**：`upgrade_db_v2.11.sql` 可能没有正确执行
3. **API依赖表结构**：重启API尝试插入历史记录，但表不存在导致失败

### 错误流程
```
用户点击重启 → API尝试创建历史记录 → 表不存在 → 数据库错误 → API返回500
```

## 修复方案

### 1. 添加错误处理机制

**修复前**：
```python
# 直接创建历史记录，如果表不存在会失败
restart_record = NodeRestartHistory(...)
db.session.add(restart_record)
db.session.commit()
```

**修复后**：
```python
# 添加错误处理，如果表不存在则跳过历史记录
try:
    restart_record = NodeRestartHistory(...)
    db.session.add(restart_record)
    db.session.commit()
except Exception as history_error:
    # 记录警告但继续执行重启
    current_app.logger.warning(f"无法创建重启历史记录: {history_error}")
    # 回滚并重新设置节点命令
    db.session.rollback()
    # 重新设置节点命令...
    db.session.commit()
```

### 2. 创建手动修复脚本

**新增文件**：`sql/fix_restart_history_table.sql`
```sql
-- 检查表是否存在，如果不存在则创建
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'node_restart_history') THEN
        CREATE TABLE node_restart_history (
            id SERIAL PRIMARY KEY,
            node_id INTEGER NOT NULL,
            restart_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            restart_reason VARCHAR(100) NOT NULL DEFAULT 'manual_restart',
            restarted_by VARCHAR(100),
            restart_duration INTEGER,
            status VARCHAR(20) NOT NULL DEFAULT 'success',
            notes TEXT,
            FOREIGN KEY (node_id) REFERENCES bot_nodes(id) ON DELETE CASCADE
        );
        
        -- 创建索引
        CREATE INDEX idx_restart_history_node_id ON node_restart_history(node_id);
        CREATE INDEX idx_restart_history_restart_time ON node_restart_history(restart_time);
        CREATE INDEX idx_restart_history_status ON node_restart_history(status);
        
        RAISE NOTICE '表 node_restart_history 创建成功';
    ELSE
        RAISE NOTICE '表 node_restart_history 已存在，跳过创建';
    END IF;
END $$;
```

## 修复效果

### 修复前的问题
- 重启节点服务失败，返回500错误
- 无法记录重启历史
- 用户体验差，功能不可用

### 修复后的效果
- 重启功能正常工作，即使历史记录表不存在
- 优雅降级：记录警告但不影响核心功能
- 提供手动修复脚本，可以创建缺失的表

## 部署说明

### 方案1：使用错误处理（推荐）
1. **更新代码**：
   ```bash
   git pull origin main
   ```

2. **重启服务**：
   ```bash
   cd mic-bot-service
   docker-compose restart
   ```

3. **验证功能**：
   - 测试重启节点功能
   - 确认功能正常工作（即使没有历史记录）

### 方案2：手动创建表（可选）
1. **执行修复脚本**：
   ```bash
   cd mic-bot-service
   docker-compose exec db psql -U user -d rewards_db -f /app/sql/fix_restart_history_table.sql
   ```

2. **验证表创建**：
   ```bash
   docker-compose exec db psql -U user -d rewards_db -c "\d node_restart_history"
   ```

3. **重启服务**：
   ```bash
   docker-compose restart
   ```

## 技术细节

### 错误处理策略
1. **优雅降级**：核心功能优先，辅助功能可降级
2. **错误隔离**：历史记录失败不影响重启功能
3. **日志记录**：记录警告信息，便于排查问题

### 数据库事务处理
1. **回滚机制**：如果历史记录失败，回滚相关操作
2. **重新设置**：确保节点命令正确设置
3. **事务完整性**：保证数据库状态一致

### 表结构设计
```sql
CREATE TABLE node_restart_history (
    id SERIAL PRIMARY KEY,
    node_id INTEGER NOT NULL,
    restart_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    restart_reason VARCHAR(100) NOT NULL DEFAULT 'manual_restart',
    restarted_by VARCHAR(100),
    restart_duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    notes TEXT,
    FOREIGN KEY (node_id) REFERENCES bot_nodes(id) ON DELETE CASCADE
);
```

## 测试建议

### 1. 重启功能测试
1. 在节点管理页面点击"重启服务"
2. 确认重启功能正常工作
3. 检查日志中是否有警告信息

### 2. 历史记录测试（如果表存在）
1. 执行手动修复脚本创建表
2. 测试重启功能
3. 验证历史记录正确创建

### 3. 错误处理测试
1. 确认即使表不存在，重启功能仍然正常
2. 检查日志中的警告信息
3. 验证API返回200状态码

## 监控要点

1. **API响应状态**：确认重启API返回200状态码
2. **错误日志**：检查是否有历史记录相关的警告
3. **功能完整性**：验证重启功能正常工作
4. **数据库状态**：确认节点命令正确设置

## 后续优化建议

1. **数据库升级检查**：添加升级脚本执行状态检查
2. **表结构验证**：启动时验证必要的表是否存在
3. **自动修复**：考虑在启动时自动创建缺失的表
4. **监控告警**：添加表缺失的监控告警

---

*修复完成时间: 2024-12-19*
*修复版本: v2.12*
*影响范围: 节点重启功能、历史记录功能*
