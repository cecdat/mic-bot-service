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

# 全局socketio实例
socketio = None

def register_websocket_events(socketio_instance):
    """注册WebSocket事件处理器"""
    global socketio
    socketio = socketio_instance
    
    @socketio_instance.on('connect')
    def handle_connect():
        """客户端连接时触发"""
        logger.debug(f'客户端连接: {request.sid}')
        emit('connected', {'message': '连接成功'})
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """客户端断开连接时触发"""
        try:
            logger.debug(f'客户端断开连接: {request.sid}')
        except Exception as e:
            logger.warning(f'处理断开连接时出错: {e}')
    
    @socketio_instance.on('ping')
    def handle_ping(data=None):
        """处理ping心跳"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})
        logger.debug(f'收到ping心跳: {request.sid}')
    
    @socketio_instance.on('join_node_room')
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
    
    @socketio_instance.on('leave_node_room')
    def handle_leave_node_room(data):
        """离开节点房间"""
        node_id = data.get('node_id')
        if node_id:
            room_name = f'node_{node_id}'
            leave_room(room_name)
            logger.info(f'客户端 {request.sid} 离开节点房间: {room_name}')
    
    @socketio_instance.on('join_all_nodes_room')
    def handle_join_all_nodes_room(data=None):
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
    
    @socketio_instance.on('leave_all_nodes_room')
    def handle_leave_all_nodes_room(data=None):
        """离开所有节点房间"""
        leave_room('all_nodes')
        logger.info(f'客户端 {request.sid} 离开所有节点房间')
    
    @socketio_instance.on('request_node_status')
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
    
    @socketio_instance.on('node_ready')
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
        
        # 更新节点状态（不强制设置为Idle，保持当前状态）
        # 只更新状态更新时间，不改变activity_status
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
    
    @socketio_instance.on('task_status_update')
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
    
    @socketio_instance.on('task_completed')
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
        
        # 发送任务完成推送通知
        try:
            from .push import trigger_push_notification
            # 获取执行的账户数量和积分信息
            account_count = result.get('account_count', 0)
            total_points = result.get('total_points', 0)
            accounts = result.get('accounts', [])
            
            # 构建账户列表信息
            account_list = []
            for account in accounts:
                email = account.get('email', '')
                points_gained = account.get('points_gained', 0)
                final_points = account.get('final_points', 0)
                account_list.append(f"{email}(+{points_gained}积分)")
            
            # 构建推送内容
            if account_count > 0:
                content = f'节点 {node_name} 任务执行完成\n\n'
                content += f'共执行 {account_count} 个账户\n'
                content += f'总获得积分: {total_points}\n\n'
                content += '账户详情:\n' + '\n'.join(account_list)
            else:
                content = f'节点 {node_name} 任务执行完成，共执行{account_count}个账户'
            
            trigger_push_notification('task_finish', f'**节点任务执行完成**', content)
        except Exception as push_error:
            logger.warning(f'发送任务完成推送失败: {push_error}')
        
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
    if not hasattr(socketio, 'emit') or socketio is None:
        return
    
    try:
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
        
        logger.debug(f'广播节点状态更新: 节点{node_id} -> {activity_status}')  # 减少日志输出
    except Exception as e:
        logger.warning(f'广播节点状态更新失败: {e}')

def broadcast_node_heartbeat(node_id, last_seen):
    """广播节点心跳更新"""
    if not hasattr(socketio, 'emit') or socketio is None:
        return
    
    try:
        data = {
            'node_id': node_id,
            'last_seen': last_seen.isoformat() if last_seen else None,
            'timestamp': last_seen.isoformat() if last_seen else None
        }
        
        # 广播到特定节点房间
        socketio.emit('node_heartbeat_update', data, room=f'node_{node_id}')
        
        # 广播到所有节点房间
        socketio.emit('node_heartbeat_update', data, room='all_nodes')
    except Exception as e:
        logger.warning(f'广播节点心跳更新失败: {e}')

def check_and_send_pending_tasks(node):
    """检查并发送待执行的任务"""
    if not hasattr(socketio, 'emit') or socketio is None:
        return
    
    try:
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
    except Exception as e:
        logger.warning(f'发送待执行任务失败: {e}')

def send_task_to_node(node_id, command, command_data=None):
    """向特定节点发送任务"""
    if not hasattr(socketio, 'emit') or socketio is None:
        return False
    
    try:
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
    except Exception as e:
        logger.warning(f'发送任务到节点失败: {e}')
        return False

def broadcast_task_status(task_id, status, node_id, node_name, result=None):
    """广播任务状态更新"""
    if not hasattr(socketio, 'emit') or socketio is None:
        return
    
    try:
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
    except Exception as e:
        logger.warning(f'广播任务状态失败: {e}')
