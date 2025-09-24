# 搜索任务交叉执行功能

## 功能概述

搜索任务交叉执行功能允许节点按照账户轮询的方式执行搜索任务，而不是传统的按账户顺序执行。这个功能可以提高任务执行的均衡性，减少单个账户的负载，并提高整体执行效率。

## 功能特点

### 传统顺序执行模式
- **执行方式**：A账户全部任务 → B账户全部任务 → C账户全部任务
- **优点**：逻辑简单，易于理解
- **缺点**：单个账户负载集中，可能导致某些账户执行时间过长

### 交叉执行模式
- **执行方式**：A账户搜索1次 → B账户搜索1次 → C账户搜索1次 → A账户搜索1次...
- **优点**：负载均衡，减少单账户压力，提高整体效率
- **缺点**：逻辑相对复杂，需要更多的状态管理

## 技术实现

### 1. 数据库模型更新

#### BotNode 模型新增字段
```python
class BotNode(db.Model):
    # ... 现有字段 ...
    search_cross_execution = db.Column(db.Boolean, default=False)  # 搜索任务交叉执行开关
```

#### 数据库迁移脚本
```sql
-- 升级数据库到版本 2.12
ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;
UPDATE db_version SET version = '2.12', updated_at = NOW() WHERE id = 1;
```

### 2. 前端界面更新

#### 节点管理页面新增配置项
```html
<!-- 搜索任务交叉执行配置 -->
<div class="layui-form-item" style="margin-bottom: 15px;">
    <label class="layui-form-label" style="width: 80px; white-space: nowrap;">搜索执行</label>
    <div class="layui-input-block" style="margin-left: 90px;">
        <input type="checkbox" name="search_cross_execution" lay-skin="switch" lay-text="交叉执行|顺序执行" title="搜索任务交叉执行">
        <div class="layui-form-mid layui-word-aux" style="margin-left: 10px; font-size: 12px; color: #999;">
            开启后，搜索任务将按账户轮询执行（A→B→C→A...），否则按账户顺序执行（A全部→B全部→C全部）
        </div>
    </div>
</div>
```

### 3. 后端API更新

#### 节点配置API
```python
@bp.route('/get_config', methods=['GET'])
@bot_api_required
def get_node_config():
    node = g.node
    config_data = {
        "cron_schedule": node.cron_schedule,
        "min_sleep_minutes": node.min_sleep_minutes,
        "max_sleep_minutes": node.max_sleep_minutes,
        "clusters": node.clusters,
        "search_delay_min": node.search_delay_min,
        "search_delay_max": node.search_delay_max,
        "search_cross_execution": node.search_cross_execution  # 新增字段
    }
    return jsonify(config_data)
```

#### 节点管理API
```python
# 创建节点时包含新字段
new_node = BotNode(
    # ... 其他字段 ...
    search_cross_execution=data.get('search_cross_execution', False)
)

# 更新节点时包含新字段
node.search_cross_execution = data.get('search_cross_execution', node.search_cross_execution)
```

### 4. 节点端执行逻辑

#### 执行模式选择
```typescript
// 检查是否启用搜索任务交叉执行
const searchCrossExecution = (config as any).search_cross_execution || false;

if (searchCrossExecution) {
    log('main', '主流程', '🔄 启用搜索任务交叉执行模式');
    await executeTasksWithCrossExecution(accounts, config);
} else {
    log('main', '主流程', '📋 使用传统顺序执行模式');
    await executeTasksSequentially(accounts, config);
}
```

#### 交叉执行核心逻辑
```typescript
async function executeTasksWithCrossExecution(accounts: Account[], config: Config) {
    // 第一阶段：桌面端交叉执行
    await executeCrossSearchTasks(accounts, config, 'desktop', accountPointsData);
    
    // 第二阶段：移动端交叉执行
    await executeCrossSearchTasks(accounts, config, 'mobile', accountPointsData);
}

async function executeCrossSearchTasks(accounts, config, taskType, accountPointsData) {
    const maxRounds = 10; // 最大轮数，防止无限循环
    let currentRound = 0;
    let allCompleted = false;
    
    while (currentRound < maxRounds && !allCompleted && !shouldStopTask) {
        currentRound++;
        
        for (const account of accounts) {
            // 执行单个账户的搜索任务
            await runTasksForAccounts([account], config, taskType);
            
            // 添加轮次间延迟
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
}
```

## 执行流程对比

### 传统顺序执行流程
```
账户A: 桌面端全部任务 → 移动端全部任务
账户B: 桌面端全部任务 → 移动端全部任务  
账户C: 桌面端全部任务 → 移动端全部任务
```

### 交叉执行流程
```
第1轮桌面端: A搜索1次 → B搜索1次 → C搜索1次
第2轮桌面端: A搜索1次 → B搜索1次 → C搜索1次
...
桌面端完成

第1轮移动端: A搜索1次 → B搜索1次 → C搜索1次
第2轮移动端: A搜索1次 → B搜索1次 → C搜索1次
...
移动端完成
```

## 配置说明

### 节点配置参数
- **参数名称**: `search_cross_execution`
- **数据类型**: Boolean
- **默认值**: `false`
- **说明**: 控制是否启用搜索任务交叉执行模式

### 配置方式
1. **创建节点时配置**: 在节点管理页面创建新节点时设置
2. **编辑节点配置**: 在节点管理页面编辑现有节点配置
3. **API配置**: 通过API接口动态更新配置

## 使用场景

### 适合交叉执行的场景
- **多账户节点**: 节点分配了多个账户（3个以上）
- **搜索任务密集**: 搜索任务较多，需要均衡负载
- **网络环境稳定**: 网络连接稳定，适合频繁切换账户
- **追求效率**: 希望提高整体任务执行效率

### 适合顺序执行的场景
- **单账户节点**: 节点只分配了1-2个账户
- **网络不稳定**: 网络连接不稳定，频繁切换可能导致问题
- **调试模式**: 需要详细跟踪单个账户的执行过程
- **特殊需求**: 有特殊的账户执行顺序要求

## 性能优化

### 轮次间延迟
- **延迟时间**: 2秒
- **目的**: 避免过于频繁的账户切换
- **可配置**: 未来可考虑将延迟时间设为可配置参数

### 最大轮数限制
- **限制值**: 10轮
- **目的**: 防止无限循环，避免系统资源耗尽
- **机制**: 达到最大轮数后自动停止执行

### 失败任务重试
- **重试机制**: 每轮执行后检查失败任务
- **重试策略**: 失败的任务会在下一轮继续尝试
- **完成条件**: 所有任务成功或达到最大轮数

## 监控和日志

### 关键日志信息
```
[LOG] 主流程 🔄 启用搜索任务交叉执行模式
[LOG] 主流程 🖥️ 开始桌面端交叉执行...
[LOG] 主流程 🔄 开始第 1 轮 desktop 交叉执行
[LOG] 主流程 [account@example.com] 开始第 1 轮 desktop 搜索任务
[LOG] 主流程 [account@example.com] 第 1 轮 desktop 搜索任务完成
[LOG] 主流程 第 1 轮 desktop 交叉执行完成，所有任务成功
[LOG] 主流程 📱 开始移动端交叉执行...
```

### 状态监控
- **执行模式**: 显示当前使用的执行模式（交叉/顺序）
- **轮次进度**: 显示当前执行轮次和总轮次
- **账户状态**: 显示每个账户的执行状态
- **失败统计**: 统计失败任务数量和重试次数

## 部署说明

### 数据库升级
```bash
# 执行数据库升级脚本
psql -d mic_bot_db -f sql/upgrade_db_v2.12.sql
```

### 服务重启
```bash
# 重启 mic-bot-service
docker-compose restart mic-bot-service

# 重启 mic-bot-node
docker-compose restart mic-bot-node
```

### 配置验证
1. 访问节点管理页面
2. 创建或编辑节点配置
3. 确认"搜索执行"开关可用
4. 保存配置并验证

## 注意事项

### 兼容性
- **向后兼容**: 现有节点默认使用顺序执行模式
- **配置迁移**: 现有节点配置不受影响
- **API兼容**: 所有现有API接口保持兼容

### 性能考虑
- **内存使用**: 交叉执行模式需要更多内存来管理状态
- **CPU负载**: 频繁的账户切换可能增加CPU负载
- **网络开销**: 账户切换可能增加网络请求

### 故障处理
- **异常恢复**: 单个账户失败不影响其他账户
- **超时处理**: 设置合理的超时时间避免长时间阻塞
- **资源清理**: 确保异常情况下正确清理资源

## 未来扩展

### 可配置参数
- **轮次间延迟**: 允许用户配置轮次间的延迟时间
- **最大轮数**: 允许用户配置最大执行轮数
- **失败重试策略**: 提供更多的重试策略选项

### 高级功能
- **智能调度**: 根据账户历史表现智能调整执行顺序
- **负载均衡**: 根据账户负载动态调整任务分配
- **性能监控**: 提供详细的性能监控和分析

---

*功能版本: 2.12*
*创建日期: 2024-12-19*
*最后更新: 2024-12-19*
