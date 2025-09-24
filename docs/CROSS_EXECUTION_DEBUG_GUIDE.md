# 交叉执行配置调试指南

## 问题现象

mic-bot-node 日志显示：
```
[2025/9/23 10:18:21] [PID: 1] [LOG] 主进程 [主流程] 📋 配置未启用交叉执行，使用顺序执行模式
[2025/9/23 10:18:21] [PID: 1] [LOG] 主流程] 📋 使用传统顺序执行模式
```

## 调试步骤

### 1. 检查数据库配置

#### 方法一：通过 Docker 命令检查
```bash
# 进入数据库容器
docker-compose exec postgres-db-service psql -U mic_bot_user -d mic_bot_service

# 检查表结构
\d bot_nodes

# 查询节点配置
SELECT id, name, search_cross_execution, status FROM bot_nodes;

# 检查数据库版本
SELECT version FROM db_version WHERE id = 1;
```

#### 方法二：通过 Python 脚本检查
```bash
# 运行检查脚本
cd mic-bot-service
python scripts/check_cross_execution.py
```

### 2. 检查前端配置

#### 登录管理界面
1. 打开浏览器访问 mic-bot-service 管理界面
2. 进入"节点管理"页面
3. 找到对应的节点
4. 检查"交叉运行"开关是否已开启
5. 如果未开启，请开启并保存

### 3. 检查 API 配置传递

#### 查看 mic-bot-service 日志
```bash
# 查看 mic-bot-service 日志
docker-compose logs mic-bot-service | grep -i "cross\|交叉"

# 查看节点配置 API 调用
docker-compose logs mic-bot-service | grep -i "config\|配置"
```

#### 手动测试 API
```bash
# 获取节点配置（需要替换实际的 API token）
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     http://localhost:5000/bot_api/config
```

### 4. 检查节点配置加载

#### 查看 mic-bot-node 启动日志
```bash
# 查看节点启动日志
docker-compose logs mic-bot-node | grep -i "交叉执行\|cross"

# 查看配置加载日志
docker-compose logs mic-bot-node | grep -i "配置\|config"
```

#### 预期的正确日志
```
[LOG] 主进程 [启动] 🔄 交叉执行配置: 已启用
[LOG] 主进程 [主流程] ✅ 满足交叉执行条件：X 个有效账户，启用交叉执行模式
```

#### 错误的日志
```
[LOG] 主进程 [启动] 🔄 交叉执行配置: 未启用
[LOG] 主进程 [主流程] 📋 配置未启用交叉执行，使用顺序执行模式
```

### 5. 重启服务验证

#### 重启 mic-bot-service
```bash
# 重启服务
docker-compose restart mic-bot-service

# 查看重启日志
docker-compose logs -f mic-bot-service
```

#### 重启 mic-bot-node
```bash
# 重启节点
docker-compose restart mic-bot-node

# 查看重启日志
docker-compose logs -f mic-bot-node
```

## 常见问题和解决方案

### 问题1：数据库字段不存在
**现象**：数据库查询报错 `column "search_cross_execution" does not exist`

**解决方案**：
```bash
# 执行数据库升级脚本
docker-compose exec postgres-db-service psql -U mic_bot_user -d mic_bot_service -f /docker-entrypoint-initdb.d/upgrade_db_v2.12.sql
```

### 问题2：前端开关未保存
**现象**：前端显示开关已开启，但数据库中没有更新

**解决方案**：
1. 确保点击"保存"按钮
2. 检查浏览器控制台是否有错误
3. 查看 mic-bot-service 日志中的保存操作

### 问题3：配置未传递到节点
**现象**：数据库配置正确，但节点日志显示未启用

**解决方案**：
1. 重启 mic-bot-service
2. 重启 mic-bot-node
3. 检查 API token 是否正确
4. 检查网络连接

### 问题4：节点配置加载失败
**现象**：节点启动时配置加载失败

**解决方案**：
1. 检查 mic-bot-service 是否正常运行
2. 检查 API 接口是否可访问
3. 检查节点配置中的服务地址是否正确

## 验证交叉执行是否工作

### 检查执行日志
当交叉执行正常工作时，应该看到以下日志：

```
[LOG] 主进程 [主流程] 🔄 启用搜索任务交叉执行模式
[LOG] 主进程 [主流程] 🖥️ 开始桌面端交叉执行（包含登录流程）...
[LOG] 主进程 [主流程] 🔄 开始第 1 轮 desktop 交叉执行（包含登录流程）
[LOG] 主进程 [主流程] [账户A] 开始第 1 轮 desktop 任务（包含登录流程）
[LOG] 主进程 [主流程] [账户B] 开始第 1 轮 desktop 任务（包含登录流程）
```

### 检查任务执行顺序
- **顺序执行**：A全部任务 → B全部任务 → C全部任务
- **交叉执行**：A一轮 → B一轮 → C一轮 → A二轮 → B二轮 → C二轮

## 快速诊断命令

```bash
# 一键检查所有配置
echo "=== 检查数据库配置 ==="
docker-compose exec postgres-db-service psql -U mic_bot_user -d mic_bot_service -c "SELECT id, name, search_cross_execution FROM bot_nodes;"

echo "=== 检查服务状态 ==="
docker-compose ps

echo "=== 检查最近日志 ==="
docker-compose logs --tail=50 mic-bot-service | grep -i "cross\|交叉"
docker-compose logs --tail=50 mic-bot-node | grep -i "交叉执行\|cross"
```

## 联系支持

如果按照以上步骤仍然无法解决问题，请提供以下信息：

1. 数据库配置查询结果
2. mic-bot-service 相关日志
3. mic-bot-node 启动日志
4. 前端管理界面的截图
5. 具体的错误信息

---

*调试指南版本: 1.0*
*创建日期: 2024-12-19*
*最后更新: 2024-12-19*
