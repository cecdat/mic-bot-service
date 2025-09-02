# 推送功能问题排查指南

## 问题描述
推送管理功能没有执行推送，需要排查可能的原因。

## 排查步骤

### 1. 检查服务状态
```bash
# 检查服务是否运行
docker-compose ps

# 如果服务未运行，启动服务
docker-compose up -d
```

### 2. 检查推送配置
```bash
# 运行诊断脚本
python diagnose_push.py
```

### 3. 手动检查数据库
```bash
# 连接数据库
docker-compose exec db psql -U user -d rewards_db

# 查看推送配置
SELECT * FROM push_configs;

# 查看启用的推送配置
SELECT * FROM push_configs WHERE status = 1;
```

### 4. 检查推送配置字段
确保推送配置表中的字段名称正确：
- `notify_on_node_online`
- `notify_on_node_offline` 
- `notify_on_account_error`
- `notify_on_verification_code`
- `status`

### 5. 测试推送功能
```bash
# 运行测试脚本
python test_push.py
```

## 常见问题及解决方案

### 问题1: 没有配置推送URL
**症状**: 推送配置页面为空
**解决方案**: 
1. 在推送配置页面添加Bark URL
2. 确保URL格式正确：`https://api.day.app/YOUR_KEY/`
3. 开启需要的事件订阅开关

### 问题2: Bark URL格式错误
**症状**: 推送发送失败
**解决方案**:
1. 确保URL以 `https://api.day.app/` 开头
2. 确保URL以 `/` 结尾
3. 验证Bark Key是否正确

### 问题3: 事件订阅未开启
**症状**: 配置了URL但没有收到推送
**解决方案**:
1. 检查推送配置页面的事件开关
2. 确保对应的事件类型已开启
3. 确保配置状态为启用（status=1）

### 问题4: 数据库连接问题
**症状**: 推送配置查询失败
**解决方案**:
1. 检查数据库服务是否正常运行
2. 检查数据库连接配置
3. 查看应用日志中的错误信息

### 问题5: 网络连接问题
**症状**: 无法访问Bark API
**解决方案**:
1. 检查网络连接
2. 检查防火墙设置
3. 验证Bark服务是否可用

## 推送事件类型

### 1. 节点上线 (node_online)
- **触发条件**: 节点首次上线或重新上线
- **推送内容**: 节点名称和IP地址

### 2. 节点离线 (node_offline)
- **触发条件**: 节点心跳超时
- **推送内容**: 节点名称和离线时间

### 3. 账户异常 (account_error)
- **触发条件**: 账户登录失败或状态异常
- **推送内容**: 账户邮箱、节点名称、错误详情

### 4. 验证码提醒 (verification_code)
- **触发条件**: 需要输入验证码
- **推送内容**: 账户邮箱、验证码信息

## 调试方法

### 1. 查看应用日志
```bash
# 查看容器日志
docker-compose logs api

# 实时查看日志
docker-compose logs -f api
```

### 2. 手动测试推送
```bash
# 使用curl测试推送
curl -X POST http://localhost:2002/bot_api/test_push \
  -H "Content-Type: application/json" \
  -d '{"event_type":"node_online","title":"测试","body":"测试内容"}'
```

### 3. 检查推送配置API
```bash
# 获取推送配置
curl http://localhost:2002/web_api/push_configs

# 添加推送配置
curl -X POST http://localhost:2002/web_api/push_configs \
  -H "Content-Type: application/json" \
  -d '{"url":"https://api.day.app/test/","notify_on_node_online":true}'
```

## 推送配置示例

### 正确的Bark URL格式
```
https://api.day.app/YOUR_BARK_KEY/
```

### 推送配置JSON示例
```json
{
  "url": "https://api.day.app/YOUR_BARK_KEY/",
  "notify_on_node_online": true,
  "notify_on_node_offline": true,
  "notify_on_account_error": true,
  "notify_on_verification_code": true
}
```

## 验证步骤

### 1. 配置验证
1. 在推送配置页面添加Bark URL
2. 开启需要的事件订阅
3. 保存配置

### 2. 功能验证
1. 触发相应事件（如节点上线）
2. 检查是否收到推送
3. 查看应用日志确认推送发送

### 3. 错误排查
1. 运行诊断脚本
2. 检查应用日志
3. 验证Bark URL可访问性

## 联系支持

如果按照以上步骤仍然无法解决问题，请提供以下信息：
1. 应用日志
2. 推送配置截图
3. 诊断脚本输出
4. 错误信息详情
