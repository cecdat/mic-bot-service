"""
WebSocket事件处理器
处理实时状态同步和节点管理
"""
from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request, session
from .auth import web_login_required
from .models import BotNode
from .db import db
import logging

logger = logging.getLogger(__name__)

def register_websocket_events(socketio):
    """注册WebSocket事件处理器"""
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接时触发"""
        logger.info(f'客户端连接: {request.sid}')
        emit('connected', {'message': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接时触发"""
        logger.info(f'客户端断开连接: {request.sid}')
    
    @socketio.on('join_node_room')
    def handle_join_node_room(data):
        """加入节点房间，接收特定节点的状态更新"""
        node_id = data.get('node_id')
        if not node_id:
            emit('error', {'message': '节点ID不能为空'})
            return
        
        # 验证节点是否存在
        node = BotNode.query.get(node_id)
        if not node:
            emit('error', {'message': '节点不存在'})
            return
        
        # 加入房间
        room_name = f'node_{node_id}'
        join_room(room_name)
        logger.info(f'客户端 {request.sid} 加入节点房间: {room_name}')
        
        # 发送当前节点状态
        emit('node_status_update', {
            'node_id': node_id,
            'activity_status': node.activity_status,
            'status_updated_at': node.status_updated_at.isoformat() if node.status_updated_at else None,
            'last_seen': node.last_seen.isoformat() if node.last_seen else None
        })
    
    @socketio.on('leave_node_room')
    def handle_leave_node_room(data):
        """离开节点房间"""
        node_id = data.get('node_id')
        if node_id:
            room_name = f'node_{node_id}'
            leave_room(room_name)
            logger.info(f'客户端 {request.sid} 离开节点房间: {room_name}')
    
    @socketio.on('join_all_nodes_room')
    def handle_join_all_nodes_room():
        """加入所有节点房间，接收所有节点的状态更新"""
        join_room('all_nodes')
        logger.info(f'客户端 {request.sid} 加入所有节点房间')
        
        # 发送所有节点的当前状态
        nodes = BotNode.query.all()
        for node in nodes:
            emit('node_status_update', {
                'node_id': node.id,
                'activity_status': node.activity_status,
                'status_updated_at': node.status_updated_at.isoformat() if node.status_updated_at else None,
                'last_seen': node.last_seen.isoformat() if node.last_seen else None
            })
    
    @socketio.on('leave_all_nodes_room')
    def handle_leave_all_nodes_room():
        """离开所有节点房间"""
        leave_room('all_nodes')
        logger.info(f'客户端 {request.sid} 离开所有节点房间')
    
    @socketio.on('request_node_status')
    def handle_request_node_status(data):
        """请求特定节点的状态"""
        node_id = data.get('node_id')
        if not node_id:
            emit('error', {'message': '节点ID不能为空'})
            return
        
        node = BotNode.query.get(node_id)
        if not node:
            emit('error', {'message': '节点不存在'})
            return
        
        emit('node_status_response', {
            'node_id': node_id,
            'activity_status': node.activity_status,
            'status_updated_at': node.status_updated_at.isoformat() if node.status_updated_at else None,
            'last_seen': node.last_seen.isoformat() if node.last_seen else None
        })

def broadcast_node_status_update(node_id, activity_status, status_updated_at=None, last_seen=None):
    """广播节点状态更新到所有相关房间"""
    if not hasattr(socketio, 'emit'):
        return
    
    data = {
        'node_id': node_id,
        'activity_status': activity_status,
        'status_updated_at': status_updated_at.isoformat() if status_updated_at else None,
        'last_seen': last_seen.isoformat() if last_seen else None,
        'timestamp': status_updated_at.isoformat() if status_updated_at else None
    }
    
    # 广播到特定节点房间
    socketio.emit('node_status_update', data, room=f'node_{node_id}')
    
    # 广播到所有节点房间
    socketio.emit('node_status_update', data, room='all_nodes')
    
    logger.info(f'广播节点状态更新: 节点{node_id} -> {activity_status}')

def broadcast_node_heartbeat(node_id, last_seen):
    """广播节点心跳更新"""
    if not hasattr(socketio, 'emit'):
        return
    
    data = {
        'node_id': node_id,
        'last_seen': last_seen.isoformat() if last_seen else None,
        'timestamp': last_seen.isoformat() if last_seen else None
    }
    
    # 广播到特定节点房间
    socketio.emit('node_heartbeat_update', data, room=f'node_{node_id}')
    
    # 广播到所有节点房间
    socketio.emit('node_heartbeat_update', data, room='all_nodes')
