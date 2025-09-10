# 积分系统改进和历史数据功能

## 概述

本次更新主要解决了两个关键问题：
1. **积分计算问题**：修复了 mic-bot-node 中可能出现 0 积分上报的问题
2. **历史数据功能**：新增了 7 天积分历史记录功能

## 主要改进

### 1. 积分计算优化

#### 问题分析
- 积分获取时页面可能未完全加载
- 仪表板数据解析失败时没有重试机制
- 积分数据验证不足，可能出现异常值

#### 解决方案
- **增强 getDashboardData 函数**：
  - 添加页面加载等待机制
  - 实现重试逻辑（最多3次）
  - 增加数据完整性验证
  - 改进错误日志记录

- **积分计算重试机制**：
  - 桌面端和移动端积分获取都添加了重试
  - 每次重试间隔2秒
  - 详细的错误日志记录

- **数据验证**：
  - 验证积分数据合理性（不能为负数）
  - 异常数据自动修正为0
  - 增加警告日志

### 2. 历史数据功能

#### 数据库设计
```sql
-- 新增积分历史表
CREATE TABLE account_points_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bot_account_id INT NOT NULL,
    total_points INT NOT NULL,
    daily_gain INT NOT NULL,
    desktop_gain INT DEFAULT 0,
    mobile_gain INT DEFAULT 0,
    node_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 功能特性
- **自动记录**：每次积分变化时自动记录历史
- **智能清理**：自动清理7天前的历史数据
- **数据完整性**：只有积分真正变化时才记录
- **定时任务**：每天凌晨3点自动清理过期数据

#### API 接口
- `GET /web_api/points_history/<account_id>?days=N` - 获取历史数据
- 支持查询1-30天的历史记录
- 返回格式化的积分和美元价值数据

#### Web 界面
- 新增积分历史页面：`/points_history`
- 支持图表展示（ECharts）
- 表格形式展示详细数据
- 支持按账户和天数筛选

### 3. 系统稳定性提升

#### 错误处理
- 积分获取失败时的优雅降级
- 详细的错误日志和警告信息
- 异常数据自动修正

#### 性能优化
- 历史数据按需记录（只有变化时才记录）
- 异步清理过期数据，不阻塞主流程
- 数据库索引优化

## 文件变更

### mic-bot-service
- `sql/upgrade_db_v2.10.sql` - 数据库升级脚本
- `project/models.py` - 新增 AccountPointsHistory 模型
- `project/api_bot.py` - 改进积分更新逻辑
- `project/api_web.py` - 新增历史数据查询接口
- `project/scheduler.py` - 新增历史数据清理任务
- `project/templates/points_history.html` - 历史数据展示页面

### mic-bot-node
- `src/index.ts` - 改进积分计算和验证逻辑
- `src/browser/BrowserFunc.ts` - 增强 getDashboardData 函数

## 使用说明

### 1. 数据库升级
```bash
# 执行数据库升级脚本
mysql -u username -p database_name < sql/upgrade_db_v2.10.sql
```

### 2. 查看历史数据
- 访问 Web 界面：`http://your-server/points_history`
- 选择账户和查询天数
- 查看图表和表格数据

### 3. API 使用
```javascript
// 获取账户历史数据
fetch('/web_api/points_history/123?days=7')
  .then(response => response.json())
  .then(data => {
    console.log(data.data.history);
  });
```

## 监控和维护

### 日志监控
- 关注积分获取失败的警告日志
- 监控历史数据清理的执行情况
- 检查异常积分数据的修正记录

### 性能监控
- 历史数据表大小增长情况
- 积分更新接口响应时间
- 数据库查询性能

## 注意事项

1. **数据迁移**：现有系统升级后，历史数据从升级时开始记录
2. **存储空间**：历史数据会占用额外存储空间，系统会自动清理
3. **性能影响**：历史数据记录对性能影响很小，但建议定期监控
4. **兼容性**：新功能向后兼容，不影响现有功能

## 故障排除

### 积分获取失败
- 检查网络连接
- 查看浏览器日志
- 确认 Microsoft Rewards 页面可正常访问

### 历史数据问题
- 检查数据库连接
- 确认定时任务正常运行
- 查看清理任务执行日志

### 页面显示问题
- 清除浏览器缓存
- 检查 JavaScript 控制台错误
- 确认 ECharts 库加载正常
