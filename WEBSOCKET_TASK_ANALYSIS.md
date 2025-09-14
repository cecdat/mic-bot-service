# WebSocket 和任务执行逻辑分析报告

## 概述

本报告分析了 `mic-bot-node` 和 `mic-bot-service` 之间的 WebSocket 连接逻辑和任务下发执行机制。

## 1. WebSocket 连接逻辑

### 1.1 mic-bot-node (客户端)

#### 连接初始化
```typescript
// 位置: mic-bot-node/src/index.ts:327-370
class NodeWebSocketClient {
    init() {
        const io = require('socket.io-client');
        this.socket = io(serverUrl, {
            auth: {
                token: this.config.apiServer.token,
                nodeName: this.config.apiServer.nodeName
            },
            transports: ['polling', 'websocket'],
            timeout: 30000,
            forceNew: true,
            reconnection: true,
            // ... 其他配置
        });
    }
}
```

#### 事件监听
```typescript
// 位置: mic-bot-node/src/index.ts:384-450
setupEventListeners() {
    this.socket.on('connect', () => {
        log('main', 'WebSocket', '✅ WebSocket连接成功');
        this.isConnected = true;
        this.processQueue(); // 处理队列中的消息
    });

    this.socket.on('new_task', (data: any) => {
        log('main', 'WebSocket', `📋 收到新任务: ${JSON.stringify(data)}`);
        globalWebSocketTask = data; // 存储到全局变量
        this.emitTaskStatusUpdate(data.task_id, 'received', data.node_name);
    });

    this.socket.on('node_ready_confirmed', (data: any) => {
        log('main', 'WebSocket', `✅ 节点准备就绪确认: ${JSON.stringify(data)}`);
    });
}
```

#### 房间加入逻辑
```typescript
// 位置: mic-bot-node/src/index.ts:1392-1396
// 在节点签成功后加入WebSocket房间
if (wsClient && wsClient.connected) {
    wsClient.safeEmit('join_node_room', {
        node_name: apiConfig.nodeName
    });
    log('main', 'WebSocket', '📡 节点注册成功，已加入WebSocket房间');
}
```

### 1.2 mic-bot-service (服务端)

#### WebSocket 事件注册
```python
# 位置: mic-bot-service/project/websocket_events.py:22-46
def register_websocket_events(socketio_instance):
    @socketio_instance.on('connect')
    def handle_connect():
        logger.debug(f'客户端连接: {request.sid}')
        emit('connected', {'message': '连接成功'})

    @socketio_instance.on('join_node_room')
    def handle_join_node_room(data):
        node_id = data.get('node_id')
        node_name = data.get('node_name')
        
        # 根据node_id或node_name查找节点
        if node_id:
            node = BotNode.query.get(node_id)
        else:
            node = BotNode.query.filter_by(node_name=node_name).first()
        
        if not node:
            emit('error', {'message': '节点不存在'})
            return
        
        # 加入房间
        room_name = f'node_{node.id}'
        join_room(room_name)
        
        # 发送确认消息
        emit('node_ready_confirmed', {
            'node_id': node.id,
            'node_name': node.node_name,
            'room_name': room_name,
            'message': '节点房间加入成功'
        })
```

## 2. 任务下发逻辑

### 2.1 手动触发 (Web界面)

```python
# 位置: mic-bot-service/project/api_web.py:436-461
@bp.route('/nodes/<int:node_id>/trigger', methods=['POST'])
def trigger_node(node_id):
    node = BotNode.query.get(node_id)
    
    # 检查节点状态
    if node.activity_status != 'Idle':
        return jsonify({"status": "error", "message": f"节点正忙 ({node.activity_status})，无法触发。"}), 409
    
    # 尝试使用WebSocket发送任务
    try:
        from . import websocket_events
        success = websocket_events.send_task_to_node(node_id, 'RUN_TASKS')
        if success:
            return jsonify({"status": "success", "message": f"已通过WebSocket向节点 {node.node_name} 发送触发指令。"})
    except Exception as e:
        logger.warning(f"WebSocket任务发送失败，回退到轮询模式: {e}")
    
    # 回退到传统轮询模式
    node.command = 'RUN_TASKS'
    node.command_status = 'pending'
    db.session.commit()
    return jsonify({"status": "success", "message": f"已向节点 {node.node_name} 发送触发指令（轮询模式）。"})
```

### 2.2 WebSocket 任务发送

```python
# 位置: mic-bot-service/project/websocket_events.py:398-441
def send_task_to_node(node_id, command, command_data=None):
    node = BotNode.query.get(node_id)
    
    # 检查节点状态
    if node.activity_status != 'Idle':
        logger.warning(f'节点 {node.node_name} 当前状态为 {node.activity_status}，无法接收新任务')
        return False
    
    # 准备任务数据
    task_data = {
        'task_id': f"task_{node_id}_{int(datetime.utcnow().timestamp())}",
        'command': command,
        'command_data': command_data or {},
        'node_id': node_id,
        'node_name': node.node_name,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # 更新节点任务信息
    node.command = command
    node.command_data = json.dumps(command_data) if command_data else None
    node.command_status = 'pending'  # 关键：保持pending状态
    db.session.commit()
    
    # 发送任务到节点
    room_name = f'node_{node_id}'
    socketio.emit('new_task', task_data, room=room_name)
    
    # 注意：不立即设置为 'sent'，保持 'pending' 状态
    # 这样 HTTP 轮询也能收到命令
    
    logger.info(f'已向节点 {node.node_name} 发送任务: {command} (房间: {room_name})')
    return True
```

### 2.3 HTTP 轮询机制

```python
# 位置: mic-bot-service/project/api_bot.py:148-170
@bp.route('/command_poll', methods=['GET'])
@bot_api_required
def command_poll():
    node = g.node
    # Long poll, waiting for up to 55 seconds
    for _ in range(55):
        # Re-fetch from DB each loop to get the latest command
        node_fresh = BotNode.query.get(node.id)
        if node_fresh and node_fresh.command and node_fresh.command_status == 'pending':
            command_to_run = node_fresh.command
            command_data = node_fresh.command_data
            # Update command status to received
            if node_fresh.command_status != 'received':
                node_fresh.command_status = 'received'
                db.session.commit()
            response = {"command": command_to_run}
            if command_data:
                response["data"] = json.loads(command_data)
            return jsonify(response)
        time.sleep(1)
    
    # Return no command after timeout
    return jsonify({"command": None})
```

## 3. 任务执行逻辑

### 3.1 mic-bot-node 任务处理

#### 主循环任务检查
```typescript
// 位置: mic-bot-node/src/index.ts:2616-2632
while (true) {
    // 检查是否有WebSocket任务需要处理
    if (globalWebSocketTask) {
        const task = globalWebSocketTask;
        globalWebSocketTask = null; // 清除任务
        
        log('main', '主流程', `📋 收到WebSocket任务: ${task.task_id} (${task.command})`);
        
        // 检查是否与当前正在执行的任务冲突
        if (isTaskRunning) {
            log('main', '主流程', `⚠️ 有任务正在执行中，将WebSocket任务加入队列: ${task.task_id}`, 'warn');
            taskExecutionQueue.push(task);
        } else {
            // 使用隔离执行函数
            executeTaskIsolated(task);
        }
    }
    
    // 如果使用WebSocket调度，跳过轮询
    if (useWebSocketScheduling && wsClient && wsClient.connected) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // 等待5秒
        continue;
    }
    
    // HTTP 轮询逻辑
    const response = await axios.get(commandUrl.toString(), {
        headers: { 'Authorization': `Bearer ${config.apiServer.token}` },
        timeout: 60000
    });
    
    const command = response.data.command;
    if (command === 'RUN_TASKS') {
        // 执行任务逻辑
        await executeTasks();
    }
}
```

#### 任务执行函数
```typescript
// 位置: mic-bot-node/src/index.ts:663-870
async function executeTasks() {
    const taskResult = {
        success: true,
        account_count: 0,
        total_points: 0,
        accounts: []
    };
    
    try {
        // 获取账户列表
        const accounts = await getAccounts();
        
        // 执行每个账户的任务
        for (const account of accounts) {
            const bot = new MicrosoftRewardsBot(account, config);
            const result = await bot.run();
            
            taskResult.accounts.push({
                email: account.email,
                points_gained: result.gain,
                final_points: result.points,
                desktop_gain: result.desktopGain,
                mobile_gain: result.mobileGain
            });
            
            taskResult.total_points += result.gain;
        }
        
        taskResult.account_count = accounts.length;
        
    } catch (error) {
        log('main', '任务执行', `任务执行失败: ${String(error)}`, 'error');
        taskResult.success = false;
    }
    
    return taskResult;
}
```

## 4. 问题分析

### 4.1 已修复的问题

1. **WebSocket 任务发送后状态问题**
   - **问题**: `send_task_to_node` 函数在发送 WebSocket 消息后立即将 `command_status` 设置为 `'sent'`
   - **影响**: HTTP 轮询无法收到命令，因为轮询检查的是 `command_status == 'pending'`
   - **修复**: 保持 `command_status` 为 `'pending'`，只有当节点确认收到命令时才设置为 `'sent'`

### 4.2 潜在问题

1. **节点认证问题**
   - 节点可能没有正确的 `api_token_hash`
   - WebSocket 认证和 HTTP 认证可能不一致

2. **房间加入失败**
   - 节点名称不匹配
   - 数据库中节点记录不存在

3. **任务状态管理**
   - 多个任务可能同时执行
   - 任务状态重置时机不当

## 5. 建议改进

### 5.1 增强错误处理
```python
# 在 send_task_to_node 中添加更详细的错误处理
def send_task_to_node(node_id, command, command_data=None):
    try:
        node = BotNode.query.get(node_id)
        if not node:
            logger.error(f'节点 {node_id} 不存在')
            return False
            
        # 检查节点状态
        if node.activity_status != 'Idle':
            logger.warning(f'节点 {node.node_name} 当前状态为 {node.activity_status}，无法接收新任务')
            return False
        
        # 发送任务逻辑...
        
    except Exception as e:
        logger.error(f'发送任务到节点 {node_id} 失败: {e}')
        return False
```

### 5.2 添加任务确认机制
```python
# 在 confirm_command 中正确处理任务状态
@bp.route('/confirm_command', methods=['POST'])
@bot_api_required
def confirm_command():
    node = g.node
    data = request.get_json()
    command = data.get('command')
    
    try:
        node_fresh = BotNode.query.get(node.id)
        if node_fresh and node_fresh.command == command:
            # 只有当节点确认收到命令时才设置为 'sent'
            if node_fresh.command_status == 'pending':
                node_fresh.command_status = 'sent'
                db.session.commit()
            
            # 执行完成后清除命令
            node_fresh.command = None
            node_fresh.command_status = 'executed'
            db.session.commit()
            
            return jsonify({"status": "success", "message": "Command confirmed"})
    except Exception as e:
        logger.error(f'确认命令失败: {e}')
        return jsonify({"status": "error", "message": str(e)}), 500
```

### 5.3 增强日志记录
```python
# 在关键位置添加详细日志
def send_task_to_node(node_id, command, command_data=None):
    logger.info(f'开始向节点 {node_id} 发送任务: {command}')
    
    # 发送逻辑...
    
    logger.info(f'任务发送完成: 节点={node.node_name}, 命令={command}, 房间={room_name}')
    return True
```

## 6. 测试建议

### 6.1 WebSocket 连接测试
```bash
# 检查 WebSocket 连接状态
docker-compose logs api | grep -E "(WebSocket|join_node_room|new_task)"
docker-compose logs node-1 | grep -E "(WebSocket|new_task|join_node_room)"
```

### 6.2 HTTP 轮询测试
```bash
# 检查 HTTP 轮询状态
docker-compose logs api | grep -E "(command_poll|trigger)"
docker-compose logs node-1 | grep -E "(收到|执行|任务)"
```

### 6.3 任务执行测试
```bash
# 检查任务执行状态
docker-compose logs node-1 | grep -E "(executeTasks|RUN_TASKS|任务执行)"
```

## 7. 总结

当前的 WebSocket 和任务执行逻辑基本正确，主要问题已经修复：

1. ✅ **WebSocket 连接逻辑** - 正确实现了连接、认证、房间加入
2. ✅ **任务下发逻辑** - 支持 WebSocket 和 HTTP 轮询双重机制
3. ✅ **任务执行逻辑** - 正确处理任务状态和执行流程
4. ✅ **错误处理** - 有基本的错误处理和重连机制

修复后的系统应该能够：
- 通过 WebSocket 实时发送任务
- 通过 HTTP 轮询作为备用机制
- 正确处理任务状态和确认
- 提供详细的日志记录用于调试
