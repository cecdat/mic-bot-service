# WebSocket任务调度方案

## 概述

本方案通过WebSocket技术实现服务端主动推送任务，替代mic-bot-node的轮询机制，实现真正的实时任务调度。

## 技术架构

### 服务端 (mic-bot-service)
- **任务队列管理**: 基于WebSocket的任务分发
- **实时推送**: 任务创建时立即推送给节点
- **状态确认**: 节点接收任务后确认状态
- **降级支持**: WebSocket失败时回退到轮询

### 客户端 (mic-bot-node)
- **实时接收**: 通过WebSocket接收任务
- **状态反馈**: 实时反馈任务执行状态
- **混合模式**: WebSocket + HTTP双重保障

## 功能特性

### 1. 实时任务调度
- ✅ **毫秒级延迟**: 任务创建后立即推送
- ✅ **状态同步**: 实时反馈任务执行状态
- ✅ **自动重连**: 连接断开时自动重连

### 2. 任务生命周期管理
- ✅ **任务创建**: 服务端创建任务并推送
- ✅ **任务接收**: 节点接收并确认任务
- ✅ **任务执行**: 节点执行任务并反馈状态
- ✅ **任务完成**: 任务完成后通知服务端

### 3. 错误处理和降级
- ✅ **连接失败**: 自动降级到HTTP轮询
- ✅ **任务失败**: 错误状态反馈和处理
- ✅ **超时处理**: 任务执行超时处理

## 事件类型

### 服务端 -> 客户端
- `new_task`: 新任务推送
- `node_ready_confirmed`: 节点准备就绪确认
- `task_status_broadcast`: 任务状态广播
- `task_completed_broadcast`: 任务完成广播

### 客户端 -> 服务端
- `node_ready`: 节点准备就绪
- `task_status_update`: 任务状态更新
- `task_completed`: 任务完成通知
- `node_heartbeat`: 节点心跳

## 数据格式

### 任务数据
```json
{
  "task_id": "task_1_1704067200",
  "command": "RUN_TASKS",
  "command_data": {
    "task_type": "scheduled",
    "priority": "normal"
  },
  "node_id": 1,
  "node_name": "Node-1",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 状态更新数据
```json
{
  "task_id": "task_1_1704067200",
  "status": "executing",
  "node_name": "Node-1",
  "result": {
    "progress": 50,
    "message": "任务执行中..."
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 使用示例

### 服务端发送任务
```python
from . import websocket_events

# 发送任务到节点
success = websocket_events.send_task_to_node(
    node_id=1,
    command='RUN_TASKS',
    command_data={'task_type': 'scheduled'}
)

if success:
    print("任务已通过WebSocket发送")
else:
    print("任务发送失败，已回退到轮询模式")
```

### 客户端接收任务
```javascript
// 在mic-bot-node中
const wsClient = new WebSocketClient(config);
wsClient.init();

// 监听新任务
wsClient.socket.on('new_task', (data) => {
    console.log('收到新任务:', data);
    // 执行任务逻辑
    executeTask(data);
});
```

## 性能优化

### 1. 连接管理
- **连接池**: 复用WebSocket连接
- **心跳检测**: 定期检测连接状态
- **自动重连**: 连接断开时自动重连

### 2. 任务管理
- **任务队列**: 本地任务队列管理
- **优先级**: 支持任务优先级
- **并发控制**: 控制同时执行的任务数量

### 3. 状态同步
- **增量更新**: 只同步变化的状态
- **批量更新**: 支持批量状态更新
- **缓存机制**: 本地状态缓存

## 故障排除

### 1. 连接问题
- 检查WebSocket服务是否启动
- 确认端口和路径配置正确
- 查看浏览器控制台错误信息

### 2. 任务不执行
- 检查节点是否在线
- 确认任务格式正确
- 查看服务端日志

### 3. 状态不同步
- 检查WebSocket连接状态
- 确认事件监听器正确
- 查看网络延迟

## 监控和调试

### 1. 服务端监控
```python
# 查看连接状态
print(f"WebSocket连接数: {len(socketio.server.manager.rooms)}")

# 查看任务队列
print(f"待执行任务数: {len(pending_tasks)}")
```

### 2. 客户端调试
```javascript
// 查看连接状态
console.log('WebSocket连接状态:', wsClient.isConnected);

// 查看任务队列
console.log('待执行任务:', wsClient.taskQueue);
```

## 配置选项

### 服务端配置
```python
# WebSocket配置
SOCKETIO_ASYNC_MODE = 'threading'
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
SOCKETIO_LOGGER = True
```

### 客户端配置
```javascript
// WebSocket配置
const config = {
    apiServer: {
        enabled: true,
        updateUrl: "https://bot.237890.xyz/",
        token: "your-token",
        nodeName: "Node-1"
    },
    websocket: {
        enabled: true,
        reconnectAttempts: 5,
        reconnectInterval: 5000
    }
};
```

## 版本兼容性

- **Flask-SocketIO**: >= 5.3.6
- **python-socketio**: >= 5.9.0
- **Socket.IO客户端**: >= 4.7.2
- **Node.js**: >= 14.0.0

## 安全考虑

- **认证机制**: 基于API Token认证
- **房间隔离**: 按节点ID隔离连接
- **任务验证**: 验证任务来源和格式
- **错误处理**: 避免敏感信息泄露

## 部署建议

### 1. 生产环境
- 使用反向代理（Nginx）
- 启用SSL/TLS加密
- 配置负载均衡
- 监控连接状态

### 2. 开发环境
- 启用调试日志
- 使用本地WebSocket服务
- 配置开发工具
- 测试连接稳定性

## 迁移指南

### 从轮询模式迁移
1. 安装WebSocket依赖
2. 更新配置文件
3. 重启服务
4. 验证功能正常

### 回退到轮询模式
1. 禁用WebSocket配置
2. 重启服务
3. 确认轮询功能正常
