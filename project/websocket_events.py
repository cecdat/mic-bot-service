"""
WebSocket事件处理器
处理实时状态同步和节点管理
"""
from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request, session
from .auth import web_login_required
from .models import BotNode
from .db import db
from datetime import datetime
import logging
import json

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
    
    @socketio.on('node_ready')
    def handle_node_ready(data):
        """节点准备就绪，可以接收任务"""
        node_name = data.get('node_name')
        if not node_name:
            emit('error', {'message': '节点名称不能为空'})
            return
        
        # 查找节点
        node = BotNode.query.filter_by(node_name=node_name).first()
        if not node:
            emit('error', {'message': '节点不存在'})
            return
        
        # 更新节点状态
        node.activity_status = 'Idle'
        node.status_updated_at = datetime.utcnow()
        db.session.commit()
        
        # 加入节点房间
        room_name = f'node_{node.id}'
        join_room(room_name)
        
        logger.info(f'节点 {node_name} 准备就绪，已加入房间 {room_name}')
        
        # 发送确认消息
        emit('node_ready_confirmed', {
            'node_id': node.id,
            'node_name': node_name,
            'message': '节点已准备就绪'
        })
        
        # 检查是否有待执行的任务
        check_and_send_pending_tasks(node)
    
    @socketio.on('task_status_update')
    def handle_task_status_update(data):
        """处理任务状态更新"""
        task_id = data.get('task_id')
        status = data.get('status')
        node_name = data.get('node_name')
        
        if not all([task_id, status, node_name]):
            emit('error', {'message': '任务ID、状态和节点名称不能为空'})
            return
        
        # 查找节点
        node = BotNode.query.filter_by(node_name=node_name).first()
        if not node:
            emit('error', {'message': '节点不存在'})
            return
        
        # 更新任务状态
        node.command_status = status
        if status == 'executed':
            node.command = None
            node.command_data = None
        db.session.commit()
        
        logger.info(f'任务 {task_id} 状态更新为 {status} (节点: {node_name})')
        
        # 广播任务状态更新
        socketio.emit('task_status_broadcast', {
            'task_id': task_id,
            'status': status,
            'node_id': node.id,
            'node_name': node_name,
            'timestamp': datetime.utcnow().isoformat()
        }, room='all_nodes')
    
    @socketio.on('task_completed')
    def handle_task_completed(data):
        """处理任务完成通知"""
        task_id = data.get('task_id')
        node_name = data.get('node_name')
        result = data.get('result', {})
        
        if not all([task_id, node_name]):
            emit('error', {'message': '任务ID和节点名称不能为空'})
            return
        
        # 查找节点
        node = BotNode.query.filter_by(node_name=node_name).first()
        if not node:
            emit('error', {'message': '节点不存在'})
            return
        
        # 更新节点状态
        node.activity_status = 'Idle'
        node.command_status = 'completed'
        node.command = None
        node.command_data = None
        node.status_updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'任务 {task_id} 已完成 (节点: {node_name})')
        
        # 广播任务完成
        socketio.emit('task_completed_broadcast', {
            'task_id': task_id,
            'node_id': node.id,
            'node_name': node_name,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }, room='all_nodes')
        
        # 检查是否有新的待执行任务
        check_and_send_pending_tasks(node)

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

def check_and_send_pending_tasks(node):
    """检查并发送待执行的任务"""
    if not hasattr(socketio, 'emit'):
        return
    
    # 检查节点是否有待执行的任务
    if node.command and node.command_status == 'pending':
        task_data = {
            'task_id': f"task_{node.id}_{int(datetime.utcnow().timestamp())}",
            'command': node.command,
            'command_data': json.loads(node.command_data) if node.command_data else {},
            'node_id': node.id,
            'node_name': node.node_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 发送任务到节点
        socketio.emit('new_task', task_data, room=f'node_{node.id}')
        
        # 更新任务状态为已发送
        node.command_status = 'sent'
        db.session.commit()
        
        logger.info(f'已向节点 {node.node_name} 发送任务: {node.command}')

def send_task_to_node(node_id, command, command_data=None):
    """向特定节点发送任务"""
    if not hasattr(socketio, 'emit'):
        return False
    
    node = BotNode.query.get(node_id)
    if not node:
        return False
    
    # 检查节点是否在线且空闲
    if node.activity_status != 'Idle':
        logger.warning(f'节点 {node.node_name} 当前状态为 {node.activity_status}，无法接收新任务')
        return False
    
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
    node.command_status = 'pending'
    db.session.commit()
    
    # 发送任务到节点
    socketio.emit('new_task', task_data, room=f'node_{node_id}')
    
    # 更新任务状态为已发送
    node.command_status = 'sent'
    db.session.commit()
    
    logger.info(f'已向节点 {node.node_name} 发送任务: {command}')
    return True

def broadcast_task_status(task_id, status, node_id, node_name, result=None):
    """广播任务状态更新"""
    if not hasattr(socketio, 'emit'):
        return
    
    data = {
        'task_id': task_id,
        'status': status,
        'node_id': node_id,
        'node_name': node_name,
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # 广播到所有节点房间
    socketio.emit('task_status_broadcast', data, room='all_nodes')
    
    logger.info(f'广播任务状态: {task_id} -> {status} (节点: {node_name})')
