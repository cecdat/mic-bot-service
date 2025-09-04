/**
 * WebSocket客户端管理器
 * 处理实时状态同步和连接管理
 */
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000; // 5秒
        this.heartbeatInterval = 30000; // 30秒心跳
        this.heartbeatTimer = null;
        this.statusCallbacks = new Map();
        this.heartbeatCallbacks = new Map();
    }

    /**
     * 初始化WebSocket连接
     */
    init() {
        try {
            this.socket = io();
            this.setupEventListeners();
            this.startHeartbeat();
            console.log('🔌 WebSocket客户端初始化完成');
        } catch (error) {
            console.error('❌ WebSocket初始化失败:', error);
            this.fallbackToPolling();
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        this.socket.on('connect', () => {
            console.log('✅ WebSocket连接成功');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.joinAllNodesRoom();
        });

        this.socket.on('disconnect', () => {
            console.log('❌ WebSocket连接断开');
            this.isConnected = false;
            this.scheduleReconnect();
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ WebSocket连接错误:', error);
            this.scheduleReconnect();
        });

        this.socket.on('node_status_update', (data) => {
            console.log('📊 收到节点状态更新:', data);
            this.handleStatusUpdate(data);
        });

        this.socket.on('node_heartbeat_update', (data) => {
            console.log('💓 收到节点心跳更新:', data);
            this.handleHeartbeatUpdate(data);
        });

        this.socket.on('error', (error) => {
            console.error('❌ WebSocket错误:', error);
        });
    }

    /**
     * 加入所有节点房间
     */
    joinAllNodesRoom() {
        if (this.socket && this.isConnected) {
            this.socket.emit('join_all_nodes_room');
            console.log('🏠 已加入所有节点房间');
        }
    }

    /**
     * 加入特定节点房间
     */
    joinNodeRoom(nodeId) {
        if (this.socket && this.isConnected) {
            this.socket.emit('join_node_room', { node_id: nodeId });
            console.log(`🏠 已加入节点房间: ${nodeId}`);
        }
    }

    /**
     * 离开特定节点房间
     */
    leaveNodeRoom(nodeId) {
        if (this.socket && this.isConnected) {
            this.socket.emit('leave_node_room', { node_id: nodeId });
            console.log(`🚪 已离开节点房间: ${nodeId}`);
        }
    }

    /**
     * 处理状态更新
     */
    handleStatusUpdate(data) {
        const { node_id, activity_status, status_updated_at, last_seen } = data;
        
        // 更新表格中的状态显示
        this.updateNodeStatusInTable(node_id, activity_status, status_updated_at, last_seen);
        
        // 触发回调函数
        if (this.statusCallbacks.has(node_id)) {
            this.statusCallbacks.get(node_id)(data);
        }
    }

    /**
     * 处理心跳更新
     */
    handleHeartbeatUpdate(data) {
        const { node_id, last_seen } = data;
        
        // 更新表格中的心跳时间
        this.updateNodeHeartbeatInTable(node_id, last_seen);
        
        // 触发回调函数
        if (this.heartbeatCallbacks.has(node_id)) {
            this.heartbeatCallbacks.get(node_id)(data);
        }
    }

    /**
     * 更新表格中的节点状态
     */
    updateNodeStatusInTable(nodeId, activityStatus, statusUpdatedAt, lastSeen) {
        // 查找表格中的对应行
        const table = layui.table;
        if (window.tableIns) {
            const data = window.tableIns.config.data;
            const index = data.findIndex(item => item.id == nodeId);
            
            if (index !== -1) {
                // 更新数据
                data[index].activity_status = activityStatus;
                data[index].status_updated_at = statusUpdatedAt;
                data[index].last_seen = lastSeen;
                
                // 重新渲染表格
                window.tableIns.reload({
                    data: data,
                    page: { curr: window.tableIns.config.page.curr }
                });
                
                console.log(`📊 已更新节点 ${nodeId} 状态为: ${activityStatus}`);
            }
        }
    }

    /**
     * 更新表格中的节点心跳
     */
    updateNodeHeartbeatInTable(nodeId, lastSeen) {
        const table = layui.table;
        if (window.tableIns) {
            const data = window.tableIns.config.data;
            const index = data.findIndex(item => item.id == nodeId);
            
            if (index !== -1) {
                // 更新数据
                data[index].last_seen = lastSeen;
                
                // 重新渲染表格
                window.tableIns.reload({
                    data: data,
                    page: { curr: window.tableIns.config.page.curr }
                });
                
                console.log(`💓 已更新节点 ${nodeId} 心跳时间`);
            }
        }
    }

    /**
     * 注册状态更新回调
     */
    onStatusUpdate(nodeId, callback) {
        this.statusCallbacks.set(nodeId, callback);
    }

    /**
     * 注册心跳更新回调
     */
    onHeartbeatUpdate(nodeId, callback) {
        this.heartbeatCallbacks.set(nodeId, callback);
    }

    /**
     * 开始心跳检测
     */
    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            if (this.socket && this.isConnected) {
                this.socket.emit('ping');
            }
        }, this.heartbeatInterval);
    }

    /**
     * 停止心跳检测
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * 安排重连
     */
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.init();
            }, this.reconnectInterval);
        } else {
            console.log('❌ 达到最大重连次数，切换到轮询模式');
            this.fallbackToPolling();
        }
    }

    /**
     * 降级到轮询模式
     */
    fallbackToPolling() {
        console.log('🔄 切换到HTTP轮询模式');
        // 这里可以启动定时轮询
        this.startPolling();
    }

    /**
     * 启动轮询
     */
    startPolling() {
        // 每30秒轮询一次状态
        setInterval(() => {
            if (window.tableIns) {
                window.tableIns.reload();
            }
        }, 30000);
    }

    /**
     * 销毁连接
     */
    destroy() {
        this.stopHeartbeat();
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isConnected = false;
        console.log('🔌 WebSocket连接已销毁');
    }
}

// 创建全局WebSocket管理器实例
window.wsManager = new WebSocketManager();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.wsManager.init();
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    window.wsManager.destroy();
});
