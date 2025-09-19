from flask import Blueprint, request, jsonify, session, current_app
from .db import db
from .models import Account, BotAccount, BotNode, PushConfig, WebUser, AccountPointsHistory
from .auth import web_login_required
from . import scheduler
from .bing_wallpaper import bing_wallpaper
from datetime import datetime, timedelta, timezone
import json
import secrets
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('api_web')

# 简单的内存缓存
_cache = {}
_cache_timeout = 30  # 30秒缓存过期

def get_cached_data(key):
    """获取缓存数据"""
    if key in _cache:
        data, timestamp = _cache[key]
        if time.time() - timestamp < _cache_timeout:
            return data
        else:
            del _cache[key]
    return None

def set_cached_data(key, data):
    """设置缓存数据"""
    _cache[key] = (data, time.time())

def clear_cache():
    """清理过期缓存"""
    current_time = time.time()
    expired_keys = [k for k, (_, timestamp) in _cache.items() if current_time - timestamp >= _cache_timeout]
    for key in expired_keys:
        del _cache[key]

def get_inferred_status(node):
    """智能推断节点状态，误差不超过30秒"""
    now = datetime.now(timezone.utc)
    
    # 如果节点离线，直接返回Idle
    if node.status != 1:
        return 'Idle'
    
    # 如果状态更新时间在30秒内，直接返回当前状态
    if node.status_updated_at:
        # 确保时间对象都是timezone-aware
        status_time = node.status_updated_at
        if status_time.tzinfo is None:
            # 如果是naive datetime，假设为UTC
            status_time = status_time.replace(tzinfo=timezone.utc)
        
        time_diff = (now - status_time).total_seconds()
        if time_diff <= 30:
            return node.activity_status
    
    # 如果最后心跳时间在30秒内，且状态为Running，保持Running
    if node.last_seen:
        # 确保时间对象都是timezone-aware
        last_seen = node.last_seen
        if last_seen.tzinfo is None:
            # 如果是naive datetime，假设为UTC
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        
        heartbeat_diff = (now - last_seen).total_seconds()
        if heartbeat_diff <= 30 and node.activity_status == 'Running':
            return 'Running'
    
    # 如果最后心跳时间超过30秒，推断为Idle
    if node.last_seen:
        # 确保时间对象都是timezone-aware
        last_seen = node.last_seen
        if last_seen.tzinfo is None:
            # 如果是naive datetime，假设为UTC
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        
        heartbeat_diff = (now - last_seen).total_seconds()
        if heartbeat_diff > 30:
            return 'Idle'
    
    # 默认返回当前状态
    return node.activity_status

bp = Blueprint('api_web', __name__, url_prefix='/web_api')

@bp.route('/login', methods=['POST'])
def web_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = WebUser.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': '登录成功'})
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@bp.route('/get_points', methods=['GET'])
@web_login_required
def get_points():
    """获取所有账户的积分数据"""
    try:
        # 检查缓存
        cache_key = 'points_data'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # 获取所有账户数据
        accounts = db.session.query(
            BotAccount,
            Account,
            BotNode
        ).outerjoin(
            Account, BotAccount.id == Account.bot_account_id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).all()
        
        points_data = []
        for bot_account, account, node in accounts:
            # 获取账户状态
            desktop_status = 'unknown'
            mobile_status = 'unknown'
            
            if account:
                # 检查状态是否过期（超过5分钟）
                now = datetime.now(timezone.utc)
                is_stale = False
                
                if account.last_updated:
                    last_updated = account.last_updated
                    if isinstance(last_updated, str):
                        try:
                            last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        except:
                            last_updated = None
                    
                    if last_updated:
                        if last_updated.tzinfo is None:
                            last_updated = last_updated.replace(tzinfo=timezone.utc)
                        
                        time_diff = (now - last_updated).total_seconds()
                        if time_diff > 300:  # 5分钟
                            is_stale = True
                
                # 根据积分数据推断状态
                if account.desktop_points and account.desktop_points > 0:
                    desktop_status = 'online'
                else:
                    desktop_status = 'offline'
                
                if account.mobile_points and account.mobile_points > 0:
                    mobile_status = 'online'
                else:
                    mobile_status = 'offline'
            
            points_data.append({
                'id': bot_account.id,
                'email': bot_account.email,
                'node_name': node.node_name if node else '未分配',
                'total_points': account.total_points if account else 0,
                'daily_gain': account.daily_gain if account else 0,
                'desktop_gain': account.desktop_gain if account else 0,
                'mobile_gain': account.mobile_gain if account else 0,
                'last_updated': account.last_updated if account else None,
                'is_stale': is_stale,
                'desktop_status': desktop_status,
                'mobile_status': mobile_status
            })
        
        # 缓存数据
        set_cached_data(cache_key, points_data)
        
        return jsonify(points_data)
    
    except Exception as e:
        current_app.logger.error(f"获取积分数据失败: {e}")
        return jsonify({'error': '获取积分数据失败'}), 500

@bp.route('/nodes', methods=['GET', 'POST', 'PUT'])
@web_login_required
def manage_nodes():
    if request.method == 'GET':
        # 获取所有节点
        nodes = BotNode.query.all()
        node_data = []
        
        for node in nodes:
            # 使用智能状态推断
            inferred_status = get_inferred_status(node)
            
            node_data.append({
                'id': node.id,
                'node_name': node.node_name,
                'status': 'Online' if node.status == 1 else 'Offline',
                'activity_status': inferred_status,
                'ip_address': node.ip_address,
                'last_seen': node.last_seen.isoformat() if node.last_seen else None,
                'status_updated_at': node.status_updated_at.isoformat() if node.status_updated_at else None,
                'account_count_total': BotAccount.query.filter_by(assigned_node_id=node.id).count(),
                'next_run_time': None,  # 暂时设为None，后续可以根据cron_schedule计算
                'created_at': None
            })
        
        return jsonify({
            "code": 0,
            "msg": "success", 
            "count": len(node_data),
            "data": node_data
        })
    
    elif request.method == 'POST':
        # 创建新节点
        data = request.get_json()
        node_name = data.get('node_name')
        
        if not node_name:
            return jsonify({'error': '节点名称不能为空'}), 400
        
        # 检查节点名称是否已存在
        existing_node = BotNode.query.filter_by(node_name=node_name).first()
        if existing_node:
            return jsonify({'error': '节点名称已存在'}), 400
        
        # 生成API Token
        api_token = secrets.token_urlsafe(32)
        
        # 创建节点
        new_node = BotNode(
            node_name=node_name,
            api_token_hash=api_token,
            status=0,  # 默认离线
            activity_status='Idle'
        )
        
        db.session.add(new_node)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '节点创建成功',
            'node_id': new_node.id,
            'api_token': api_token
        })
    
    elif request.method == 'PUT':
        # 更新节点信息
        data = request.get_json()
        node_id = data.get('id')
        node_name = data.get('node_name')
        
        if not node_id or not node_name:
            return jsonify({'error': '节点ID和名称不能为空'}), 400
        
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 检查节点名称是否已被其他节点使用
        existing_node = BotNode.query.filter(BotNode.node_name == node_name, BotNode.id != node_id).first()
        if existing_node:
            return jsonify({'error': '节点名称已被其他节点使用'}), 400
        
        node.node_name = node_name
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '节点更新成功'})

@bp.route('/logs/receive', methods=['POST'])
@web_login_required
def receive_logs():
    """接收节点日志"""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        logs = data.get('logs', [])
        
        if not node_id:
            return jsonify({'error': '节点ID不能为空'}), 400
        
        # 这里可以添加日志存储逻辑
        # 目前只是简单记录
        current_app.logger.info(f"收到节点 {node_id} 的 {len(logs)} 条日志")
        
        return jsonify({'success': True, 'message': '日志接收成功'})
    
    except Exception as e:
        current_app.logger.error(f"接收日志失败: {e}")
        return jsonify({'error': '接收日志失败'}), 500

@bp.route('/nodes/<int:node_id>/trigger', methods=['POST'])
@web_login_required
def trigger_node(node_id):
    """触发节点执行任务"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        if node.status != 1:
            return jsonify({'error': '节点离线，无法执行任务'}), 400
        
        # 设置任务状态为待执行
        node.command_status = 'pending'
        node.command = 'run_tasks'
        node.command_updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '任务已下发'})
    
    except Exception as e:
        current_app.logger.error(f"触发节点失败: {e}")
        return jsonify({'error': '触发节点失败'}), 500

@bp.route('/nodes/<int:node_id>/stop', methods=['POST'])
@web_login_required
def stop_node(node_id):
    """停止节点任务"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 设置停止命令
        node.command_status = 'pending'
        node.command = 'stop_tasks'
        node.command_updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '停止命令已下发'})
    
    except Exception as e:
        current_app.logger.error(f"停止节点失败: {e}")
        return jsonify({'error': '停止节点失败'}), 500

@bp.route('/nodes/<int:node_id>/reset', methods=['POST'])
@web_login_required
def reset_node(node_id):
    """重置节点任务"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 重置节点状态
        node.command_status = 'idle'
        node.command = None
        node.activity_status = 'Idle'
        node.status_updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '节点已重置'})
    
    except Exception as e:
        current_app.logger.error(f"重置节点失败: {e}")
        return jsonify({'error': '重置节点失败'}), 500

@bp.route('/nodes/<int:node_id>/regenerate-token', methods=['POST'])
@web_login_required
def regenerate_token(node_id):
    """重新生成节点API Token"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 生成新的API Token
        new_token = secrets.token_urlsafe(32)
        node.api_token = new_token
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Token重新生成成功',
            'token': new_token
        })
        
    except Exception as e:
        current_app.logger.error(f"重新生成Token失败: {e}")
        return jsonify({'error': '重新生成Token失败'}), 500

@bp.route('/nodes/<int:node_id>', methods=['DELETE'])
@web_login_required
def delete_node(node_id):
    """删除节点"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 检查是否有账户分配到此节点
        account_count = BotAccount.query.filter_by(assigned_node_id=node_id).count()
        if account_count > 0:
            return jsonify({'error': f'该节点下还有 {account_count} 个账户，无法删除'}), 400
        
        db.session.delete(node)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '节点删除成功'})
    
    except Exception as e:
        current_app.logger.error(f"删除节点失败: {e}")
        return jsonify({'error': '删除节点失败'}), 500

@bp.route('/accounts', methods=['GET'])
@web_login_required
def get_accounts():
    """获取所有账户列表（用于账户分析页面）"""
    try:
        # 获取所有账户
        accounts = db.session.query(
            BotAccount,
            Account,
            BotNode
        ).outerjoin(
            Account, BotAccount.id == Account.bot_account_id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).all()
        
        account_data = []
        for bot_account, account, node in accounts:
            account_data.append({
                'id': bot_account.id,
                'email': bot_account.email,
                'node_name': node.node_name if node else '未分配',
                'total_points': account.total_points if account else 0,
                'daily_gain': account.daily_gain if account else 0,
                'desktop_gain': account.desktop_gain if account else 0,
                'mobile_gain': account.mobile_gain if account else 0,
                'last_updated': account.last_updated if account else None,
                'is_enabled': bot_account.is_enabled,
                'created_at': bot_account.created_at.isoformat() if bot_account.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': account_data
        })
            
    except Exception as e:
        current_app.logger.error(f"获取账户列表失败: {e}")
        return jsonify({'success': False, 'message': '获取账户列表失败'}), 500

@bp.route('/bot_accounts', methods=['GET', 'POST'])
@web_login_required
def manage_bot_accounts():
    if request.method == 'GET':
        # 获取所有账户
        accounts = db.session.query(
            BotAccount,
            Account,
            BotNode
        ).outerjoin(
            Account, BotAccount.id == Account.bot_account_id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).all()
        
        account_data = []
        for bot_account, account, node in accounts:
            # 构建监控数据对象
            monitoring_data = {
                'total_points': account.total_points if account else 0,
                'daily_gain': account.daily_gain if account else 0,
                'desktop_gain': account.desktop_gain if account else 0,
                'mobile_gain': account.mobile_gain if account else 0,
                'last_updated': account.last_updated.isoformat() if account and account.last_updated else None,
                'status_details': account.status_details if account else None
            }
            
            account_data.append({
                'id': bot_account.id,
                'email': bot_account.email,
                'password': bot_account.password,
                'assigned_node_id': bot_account.assigned_node_id,
                'assigned_node_name': node.node_name if node else '未分配',
                'is_enabled': bot_account.is_enabled,
                'monitoring_data': monitoring_data,  # 包装监控数据
                'created_at': bot_account.created_at.isoformat() if bot_account.created_at else None
            })
        
        return jsonify({
            "code": 0,
            "msg": "success",
            "count": len(account_data),
            "data": account_data
        })
    
    elif request.method == 'POST':
        # 创建新账户
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        assigned_node_id = data.get('assigned_node_id')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 检查邮箱是否已存在
        existing_account = BotAccount.query.filter_by(email=email).first()
        if existing_account:
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 创建账户
        new_account = BotAccount(
            email=email,
            password=password,
            assigned_node_id=assigned_node_id,
            is_enabled=True
        )
        
        db.session.add(new_account)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '账户创建成功',
            'account_id': new_account.id
        })

@bp.route('/bot_accounts/<int:account_id>/toggle', methods=['POST'])
@web_login_required
def toggle_account(account_id):
    """切换账户激活状态"""
    try:
        account = BotAccount.query.get(account_id)
        if not account:
            return jsonify({'error': '账户不存在'}), 404
        
        account.is_enabled = not account.is_enabled
        db.session.commit()
        
        status = '激活' if account.is_enabled else '停用'
        return jsonify({
            'success': True,
            'message': f'账户已{status}',
            'is_enabled': account.is_enabled
        })
    
    except Exception as e:
        current_app.logger.error(f"切换账户状态失败: {e}")
        return jsonify({'error': '切换账户状态失败'}), 500

@bp.route('/bot_accounts/<int:account_id>', methods=['GET', 'DELETE'])
@web_login_required
def manage_single_account(account_id):
    if request.method == 'GET':
        # 获取单个账户详情
        account = BotAccount.query.get(account_id)
        if not account:
            return jsonify({'error': '账户不存在'}), 404
        
        # 获取关联的积分数据
        points_data = Account.query.filter_by(bot_account_id=account_id).first()
            
        # 获取分配的节点信息
        node = BotNode.query.get(account.assigned_node_id) if account.assigned_node_id else None
            
        account_data = {
            'id': account.id,
            'email': account.email,
            'password': account.password,
            'assigned_node_id': account.assigned_node_id,
            'node_name': node.node_name if node else '未分配',
            'is_enabled': account.is_enabled,
            'total_points': points_data.total_points if points_data else 0,
            'daily_gain': points_data.daily_gain if points_data else 0,
            'desktop_points': points_data.desktop_points if points_data else 0,
            'mobile_points': points_data.mobile_points if points_data else 0,
            'desktop_gain': points_data.desktop_gain if points_data else 0,
            'mobile_gain': points_data.mobile_gain if points_data else 0,
            'last_updated': points_data.last_updated if points_data else None,
            'created_at': account.created_at.isoformat() if account.created_at else None
        }
        
        return jsonify(account_data)
    
    elif request.method == 'DELETE':
        # 删除账户
        try:
            account = BotAccount.query.get(account_id)
            if not account:
                return jsonify({'error': '账户不存在'}), 404
            
            # 删除关联的积分数据
            points_data = Account.query.filter_by(bot_account_id=account_id).first()
            if points_data:
                db.session.delete(points_data)
                
            db.session.delete(account)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': '账户删除成功'})
        
        except Exception as e:
            current_app.logger.error(f"删除账户失败: {e}")
            return jsonify({'error': '删除账户失败'}), 500

@bp.route('/bot_accounts/batch_delete', methods=['POST'])
@web_login_required
def batch_delete_accounts():
    """批量删除账户"""
    try:
        data = request.get_json()
        account_ids = data.get('ids', [])
        
        if not account_ids:
            return jsonify({'error': '请选择要删除的账户'}), 400
        
        deleted_count = 0
        for account_id in account_ids:
            account = BotAccount.query.get(account_id)
            if account:
                # 删除关联的积分数据
                points_data = Account.query.filter_by(bot_account_id=account_id).first()
                if points_data:
                    db.session.delete(points_data)
                
                db.session.delete(account)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f'成功删除 {deleted_count} 个账户'
        })
    
    except Exception as e:
        current_app.logger.error(f"批量删除账户失败: {e}")
        db.session.rollback()
        return jsonify({'error': '批量删除账户失败'}), 500

@bp.route('/push_configs', methods=['GET', 'POST'])
@web_login_required
def manage_push_configs():
    if request.method == 'GET':
        # 获取所有推送配置
        configs = PushConfig.query.all()
        config_data = []
        
        for config in configs:
            config_data.append({
                'id': config.id,
                'name': config.name,
                'channel': config.channel,
                'is_enabled': config.is_enabled,
                'config_data': json.loads(config.config_data) if config.config_data else {},
                'created_at': config.created_at.isoformat() if config.created_at else None
            })
        
        return jsonify(config_data)
    
    elif request.method == 'POST':
        # 创建新推送配置
        data = request.get_json()
        name = data.get('name')
        channel = data.get('channel')
        config_data = data.get('config_data', {})
        
        if not name or not channel:
            return jsonify({'error': '配置名称和渠道不能为空'}), 400
        
        # 检查配置名称是否已存在
        existing_config = PushConfig.query.filter_by(name=name).first()
        if existing_config:
            return jsonify({'error': '配置名称已存在'}), 400
        
        # 创建配置
        new_config = PushConfig(
            name=name,
            channel=channel,
            config_data=json.dumps(config_data),
            is_enabled=True
        )
        
        db.session.add(new_config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '推送配置创建成功',
            'config_id': new_config.id
        })

@bp.route('/push_configs/<int:config_id>', methods=['DELETE'])
@web_login_required
def delete_push_config(config_id):
    """删除推送配置"""
    try:
        config = PushConfig.query.get(config_id)
        if not config:
            return jsonify({'error': '推送配置不存在'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '推送配置删除成功'})
    
    except Exception as e:
        current_app.logger.error(f"删除推送配置失败: {e}")
        return jsonify({'error': '删除推送配置失败'}), 500

@bp.route('/nodes/<int:node_id>/logs', methods=['GET'])
@web_login_required
def get_node_logs(node_id):
    """获取节点日志"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 这里可以添加从数据库或文件系统读取日志的逻辑
        # 目前返回空日志
        logs = []
        
        return jsonify({
            'success': True,
            'logs': logs,
            'node_name': node.node_name
        })
        
    except Exception as e:
        current_app.logger.error(f"获取节点日志失败: {e}")
        return jsonify({'error': '获取节点日志失败'}), 500

@bp.route('/nodes/<int:node_id>/logs/clear', methods=['POST'])
@web_login_required
def clear_node_logs(node_id):
    """清空节点日志"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 这里可以添加清空日志的逻辑
        # 目前只是简单返回成功
        
        return jsonify({'status': 'success', 'message': '日志已清空'})
        
    except Exception as e:
        current_app.logger.error(f"清空节点日志失败: {e}")
        return jsonify({'error': '清空节点日志失败'}), 500

@bp.route('/mobile/get_points', methods=['GET'])
def mobile_get_points():
    """移动端获取积分数据（免登录）"""
    try:
        # 检查缓存
        cache_key = 'mobile_points_data'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # 获取所有节点和账户数据
        nodes = BotNode.query.filter_by(status=1).all()  # 只获取在线节点
        node_data = []
        
        for node in nodes:
            # 获取该节点下的账户
            accounts = db.session.query(
                BotAccount,
                Account
            ).outerjoin(
                Account, BotAccount.id == Account.bot_account_id
            ).filter(
                BotAccount.assigned_node_id == node.id,
                BotAccount.is_enabled == True
            ).all()
            
            account_data = []
            total_points = 0
            
            for bot_account, account in accounts:
                if account:
                    total_points += account.total_points or 0
                    account_data.append({
                        'email': bot_account.email,
                        'total_points': account.total_points or 0,
                        'daily_gain': account.daily_gain or 0,
                        'desktop_points': account.desktop_points or 0,
                        'mobile_points': account.mobile_points or 0
                    })
            
            if account_data:  # 只显示有账户的节点
                node_data.append({
                    'node_name': node.node_name,
                    'account_count': len(account_data),
                    'total_points': total_points,
                    'accounts': account_data
                })
        
        # 缓存数据
        set_cached_data(cache_key, node_data)
        
        return jsonify(node_data)
    
    except Exception as e:
        current_app.logger.error(f"获取移动端积分数据失败: {e}")
        return jsonify({'error': '获取积分数据失败'}), 500

@bp.route('/wallpaper', methods=['GET'])
def get_wallpaper():
    """获取Bing每日壁纸URL"""
    try:
        wallpaper_url = bing_wallpaper.get_wallpaper_url()
        return jsonify({
            "success": True,
            "url": wallpaper_url
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/points_history', methods=['GET'])
@web_login_required
def get_points_history():
    """获取积分历史记录"""
    try:
        # 获取查询参数
        days = int(request.args.get('days', 7))  # 默认查询7天
        account_id = request.args.get('account_id', type=int)
        
        # 计算查询日期范围
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days-1)
        
        # 构建查询
        query = db.session.query(
            AccountPointsHistory,
            BotAccount.email,
            BotNode.node_name
        ).join(
            BotAccount, AccountPointsHistory.bot_account_id == BotAccount.id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).filter(
            AccountPointsHistory.record_date >= start_date,
            AccountPointsHistory.record_date <= end_date
        ).order_by(
            AccountPointsHistory.record_date.desc(),
            BotAccount.email
        )
        
        # 如果指定了账户ID，则过滤
        if account_id:
            query = query.filter(AccountPointsHistory.bot_account_id == account_id)
        
        results = query.all()
        
        # 组织数据
        history_data = []
        for result in results:
            history, email, node_name = result
            history_data.append({
                'id': history.id,
                'email': email,
                'node_name': node_name or '未分配',
                'total_points': history.total_points,
                'daily_gain': history.daily_gain,
                'desktop_gain': history.desktop_gain,
                'mobile_gain': history.mobile_gain,
                'record_date': history.record_date.isoformat(),
                'created_at': history.created_at.isoformat() if history.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': history_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取积分历史失败: {str(e)}'
        }), 500

@bp.route('/points_analysis', methods=['GET'])
@web_login_required
def get_points_analysis():
    """获取积分分析数据，用于图表显示"""
    try:
        # 获取查询参数
        days = int(request.args.get('days', 7))  # 默认查询7天
        
        # 计算查询日期范围
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days-1)
        
        # 获取所有账户的历史数据
        results = db.session.query(
            AccountPointsHistory,
            BotAccount.email,
            BotNode.node_name
        ).join(
            BotAccount, AccountPointsHistory.bot_account_id == BotAccount.id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).filter(
            AccountPointsHistory.record_date >= start_date,
            AccountPointsHistory.record_date <= end_date
        ).order_by(
            AccountPointsHistory.record_date,
            BotAccount.email
        ).all()
        
        # 按日期组织数据
        daily_data = {}
        for result in results:
            history, email, node_name = result
            date_str = history.record_date.isoformat()
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'total_points': 0,
                    'total_daily_gain': 0,
                    'total_desktop_gain': 0,
                    'total_mobile_gain': 0,
                    'account_count': 0
                }
            
            daily_data[date_str]['total_points'] += history.total_points
            daily_data[date_str]['total_daily_gain'] += history.daily_gain
            daily_data[date_str]['total_desktop_gain'] += history.desktop_gain
            daily_data[date_str]['total_mobile_gain'] += history.mobile_gain
            daily_data[date_str]['account_count'] += 1
        
        # 转换为列表并排序
        daily_chart = sorted(daily_data.values(), key=lambda x: x['date'])
        
        # 计算总统计
        total_stats = {
            'total_points': sum(item['total_points'] for item in daily_chart),
            'avg_daily_gain': sum(item['total_daily_gain'] for item in daily_chart) / len(daily_chart) if daily_chart else 0,
            'total_desktop_gain': sum(item['total_desktop_gain'] for item in daily_chart),
            'total_mobile_gain': sum(item['total_mobile_gain'] for item in daily_chart)
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'daily_chart': daily_chart,
                'total_stats': total_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取积分分析失败: {str(e)}'
        }), 500

@bp.route('/account_analysis/<int:account_id>', methods=['GET'])
@web_login_required
def get_account_analysis(account_id):
    """获取指定账户的积分分析数据"""
    try:
        # 获取查询参数
        days = int(request.args.get('days', 7))  # 默认查询7天
        
        # 计算查询日期范围
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days-1)
        
        # 获取指定账户的历史数据
        results = db.session.query(
            AccountPointsHistory,
            BotAccount.email,
            BotNode.node_name
        ).join(
            BotAccount, AccountPointsHistory.bot_account_id == BotAccount.id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).filter(
            AccountPointsHistory.bot_account_id == account_id,
            AccountPointsHistory.record_date >= start_date,
            AccountPointsHistory.record_date <= end_date
        ).order_by(
            AccountPointsHistory.record_date
        ).all()
        
        if not results:
            return jsonify({
                'success': False,
                'message': '该账户暂无历史数据'
            }), 404
        
        # 组织图表数据
        chart_data = {
            'labels': [],
            'total_points': [],
            'daily_gains': [],
            'desktop_gains': [],
            'mobile_gains': []
        }
        
        # 统计数据
        stats = {
            'total_points': 0,
            'max_points': 0,
            'min_points': float('inf'),
            'avg_daily_gain': 0,
            'max_daily_gain': 0,
            'min_daily_gain': float('inf'),
            'total_desktop_gain': 0,
            'avg_desktop_gain': 0,
            'total_mobile_gain': 0,
            'avg_mobile_gain': 0,
            'desktop_ratio': 0,
            'mobile_ratio': 0
        }
        
        daily_gains = []
        desktop_gains = []
        mobile_gains = []
        
        for result in results:
            history, email, node_name = result
            
            # 图表数据
            date_str = history.record_date.strftime('%m/%d')
            chart_data['labels'].append(date_str)
            chart_data['total_points'].append(history.total_points)
            chart_data['daily_gains'].append(history.daily_gain)
            chart_data['desktop_gains'].append(history.desktop_gain)
            chart_data['mobile_gains'].append(history.mobile_gain)
            
            # 统计数据
            stats['total_points'] = history.total_points  # 最新记录的总积分
            stats['max_points'] = max(stats['max_points'], history.total_points)
            stats['min_points'] = min(stats['min_points'], history.total_points)
            
            daily_gains.append(history.daily_gain)
            desktop_gains.append(history.desktop_gain)
            mobile_gains.append(history.mobile_gain)
        
        # 计算统计指标
        if daily_gains:
            stats['avg_daily_gain'] = sum(daily_gains) / len(daily_gains)
            stats['max_daily_gain'] = max(daily_gains)
            stats['min_daily_gain'] = min(daily_gains)
        
        if desktop_gains:
            stats['total_desktop_gain'] = sum(desktop_gains)
            stats['avg_desktop_gain'] = sum(desktop_gains) / len(desktop_gains)
        
        if mobile_gains:
            stats['total_mobile_gain'] = sum(mobile_gains)
            stats['avg_mobile_gain'] = sum(mobile_gains) / len(mobile_gains)
        
        # 计算占比
        total_gain = stats['total_desktop_gain'] + stats['total_mobile_gain']
        if total_gain > 0:
            stats['desktop_ratio'] = round((stats['total_desktop_gain'] / total_gain) * 100, 1)
            stats['mobile_ratio'] = round((stats['total_mobile_gain'] / total_gain) * 100, 1)
        
        # 处理最小值
        if stats['min_points'] == float('inf'):
            stats['min_points'] = 0
        if stats['min_daily_gain'] == float('inf'):
            stats['min_daily_gain'] = 0
        
        return jsonify({
            'success': True,
            'data': {
                'account_info': {
                    'id': account_id,
                    'email': results[0][1],  # email
                    'node_name': results[0][2]  # node_name
                },
                'chart_data': chart_data,
                'stats': stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取账户分析失败: {str(e)}'
        }), 500