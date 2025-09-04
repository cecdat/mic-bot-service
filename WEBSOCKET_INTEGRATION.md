# WebSocket实时状态同步方案

## 概述

本方案通过WebSocket技术实现mic-bot-service和mic-bot-node之间的实时状态同步，将状态显示延迟从30秒降低到毫秒级。

## 技术架构

### 服务端 (mic-bot-service)
- **Flask-SocketIO**: 提供WebSocket支持
- **房间管理**: 按节点ID分组管理连接
- **事件广播**: 实时推送状态变化和心跳更新

### 客户端 (前端)
- **Socket.IO客户端**: 自动重连和降级支持
- **状态同步**: 实时更新表格显示
- **错误处理**: 连接失败时自动降级到HTTP轮询

### 节点端 (mic-bot-node, 可选)
- **WebSocket客户端**: 可选的实时状态推送
- **混合模式**: WebSocket + HTTP双重保障

## 功能特性

### 1. 实时状态同步
- ✅ **毫秒级延迟**: 状态变化立即推送
- ✅ **自动重连**: 连接断开时自动重连
- ✅ **降级支持**: WebSocket失败时回退到HTTP轮询

### 2. 房间管理
- ✅ **节点房间**: 按节点ID分组管理连接
- ✅ **全局房间**: 监听所有节点状态变化
- ✅ **动态加入/离开**: 根据需要动态管理房间

### 3. 事件类型
- ✅ **状态更新**: `node_status_update`
- ✅ **心跳更新**: `node_heartbeat_update`
- ✅ **连接管理**: `connect`, `disconnect`, `error`

## 安装和配置

### 1. 安装依赖
```bash
pip install Flask-SocketIO==5.3.6 python-socketio==5.9.0
```

### 2. 启动服务
```bash
python run.py
```

### 3. 前端集成
```html
<!-- 引入Socket.IO客户端 -->
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script src="/static/websocket-client.js"></script>
```

## API接口

### WebSocket事件

#### 客户端 -> 服务端
- `join_node_room`: 加入特定节点房间
- `leave_node_room`: 离开特定节点房间
- `join_all_nodes_room`: 加入所有节点房间
- `leave_all_nodes_room`: 离开所有节点房间
- `request_node_status`: 请求特定节点状态

#### 服务端 -> 客户端
- `node_status_update`: 节点状态更新
- `node_heartbeat_update`: 节点心跳更新
- `connected`: 连接成功确认
- `error`: 错误信息

### 数据格式

#### 状态更新数据
```json
{
  "node_id": 1,
  "activity_status": "Running",
  "status_updated_at": "2024-01-01T12:00:00Z",
  "last_seen": "2024-01-01T12:00:00Z",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 心跳更新数据
```json
{
  "node_id": 1,
  "last_seen": "2024-01-01T12:00:00Z",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 使用示例

### 前端JavaScript
```javascript
// 初始化WebSocket连接
window.wsManager.init();

// 监听特定节点状态变化
window.wsManager.onStatusUpdate(nodeId, (data) => {
    console.log('节点状态更新:', data);
});

// 监听特定节点心跳变化
window.wsManager.onHeartbeatUpdate(nodeId, (data) => {
    console.log('节点心跳更新:', data);
});
```

### 服务端Python
```python
# 广播状态更新
from . import websocket_events
websocket_events.broadcast_node_status_update(
    node_id, 
    status, 
    status_updated_at, 
    last_seen
)

# 广播心跳更新
websocket_events.broadcast_node_heartbeat(node_id, last_seen)
```

## 性能优化

### 1. 连接管理
- **自动重连**: 最多重试5次，间隔5秒
- **心跳检测**: 30秒间隔检测连接状态
- **优雅降级**: 连接失败时自动切换到HTTP轮询

### 2. 内存优化
- **事件清理**: 页面卸载时自动清理连接
- **回调管理**: 使用Map管理回调函数
- **定时器清理**: 避免内存泄漏

### 3. 网络优化
- **事件去重**: 避免重复发送相同状态
- **批量更新**: 支持批量状态更新
- **压缩传输**: Socket.IO自动压缩数据

## 故障排除

### 1. 连接问题
- 检查防火墙设置
- 确认端口5000可访问
- 查看浏览器控制台错误信息

### 2. 状态不同步
- 检查WebSocket连接状态
- 查看服务端日志
- 确认房间加入成功

### 3. 性能问题
- 检查连接数量
- 监控内存使用
- 查看网络延迟

## 监控和调试

### 1. 客户端调试
```javascript
// 查看连接状态
console.log('WebSocket连接状态:', window.wsManager.isConnected);

// 查看注册的回调
console.log('状态回调:', window.wsManager.statusCallbacks);
console.log('心跳回调:', window.wsManager.heartbeatCallbacks);
```

### 2. 服务端监控
- 查看Flask-SocketIO日志
- 监控连接数量
- 检查事件广播频率

## 版本兼容性

- **Flask-SocketIO**: >= 5.3.6
- **python-socketio**: >= 5.9.0
- **Socket.IO客户端**: >= 4.7.2
- **浏览器支持**: 现代浏览器（IE11+）

## 安全考虑

- **CORS配置**: 允许跨域连接
- **认证机制**: 基于API Token认证
- **房间隔离**: 按节点ID隔离连接
- **错误处理**: 避免敏感信息泄露
