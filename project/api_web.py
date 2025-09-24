from flask import Blueprint, request, jsonify, session, current_app, g
from .db import db
from .models import Account, BotAccount, BotNode, PushConfig, WebUser, AccountPointsHistory, NodeRestartHistory
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

def safe_isoformat(dt):
    """安全地将datetime对象转换为ISO格式字符串，确保包含时区信息"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

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

def calculate_next_run_time(cron_schedule):
    """根据cron表达式计算下次执行时间"""
    if not cron_schedule:
        return None
    
    try:
        # 解析cron表达式 (分钟 小时 日 月 星期)
        cron_parts = cron_schedule.strip().split()
        if len(cron_parts) != 5:
            return None
        
        minute_part, hour_part, day_part, month_part, weekday_part = cron_parts
        
        # 获取当前时间（UTC）
        now = datetime.now(timezone.utc)
        
        # 解析小时和分钟
        hours = []
        minutes = []
        
        # 解析小时
        if hour_part == '*':
            hours = list(range(24))
        else:
            for part in hour_part.split(','):
                try:
                    hours.append(int(part))
                except ValueError:
                    continue
        
        # 解析分钟
        if minute_part == '*':
            minutes = list(range(60))
        else:
            for part in minute_part.split(','):
                try:
                    minutes.append(int(part))
                except ValueError:
                    continue
        
        # 确保小时和分钟值在有效范围内
        hours = [h for h in hours if 0 <= h <= 23]
        minutes = [m for m in minutes if 0 <= m <= 59]
        
        if not hours or not minutes:
            return None
        
        # 查找下一个执行时间
        for day_offset in range(8):  # 最多查找8天
            target_date = now.date() + timedelta(days=day_offset)
            
            for hour in sorted(hours):
                for minute in sorted(minutes):
                    next_time = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute)).replace(tzinfo=timezone.utc)
                    
                    # 如果是今天，需要确保时间还没过
                    if day_offset == 0 and next_time <= now:
                        continue
                    
                    return next_time
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"计算下次执行时间失败: {e}")
        return None

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
                if account.desktop_gain and account.desktop_gain > 0:
                    desktop_status = 'online'
                else:
                    desktop_status = 'offline'
                
                if account.mobile_gain and account.mobile_gain > 0:
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
    try:
        if request.method == 'GET':
            # 获取所有节点，按节点名称排序
            nodes = BotNode.query.order_by(BotNode.node_name.asc()).all()
            node_data = []
            
            for node in nodes:
                try:
                    # 使用智能状态推断
                    inferred_status = get_inferred_status(node)
                    
                    # 计算下次执行时间
                    next_run_time = calculate_next_run_time(node.cron_schedule)
                    
                    node_data.append({
                        'id': node.id,
                        'node_name': node.node_name,
                        'status': 'Online' if node.status == 1 else 'Offline',
                        'activity_status': inferred_status,
                        'ip_address': node.ip_address,
                        'last_seen': safe_isoformat(node.last_seen),
                        'status_updated_at': safe_isoformat(node.status_updated_at),
                        'account_count_total': BotAccount.query.filter_by(assigned_node_id=node.id).count(),
                        'next_run_time': safe_isoformat(next_run_time),
                        'cron_schedule': node.cron_schedule,
                        'min_sleep_minutes': node.min_sleep_minutes,
                        'max_sleep_minutes': node.max_sleep_minutes,
                        'clusters': node.clusters,
                        'search_delay_min': node.search_delay_min,
                        'search_delay_max': node.search_delay_max,
                        'search_cross_execution': getattr(node, 'search_cross_execution', False),
                        'created_at': None
                    })
                except Exception as e:
                    print(f"处理节点 {node.id} 时出错: {e}")
                    # 继续处理其他节点
                    continue
            
            return jsonify({
                "code": 0,
                "msg": "success", 
                "count": len(node_data),
                "data": node_data
            })
        
        elif request.method == 'POST':
            try:
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
                
                # 处理交叉执行开关的布尔值转换
                search_cross_execution_value = data.get('search_cross_execution', False)
                if isinstance(search_cross_execution_value, str):
                    search_cross_execution_bool = search_cross_execution_value == 'on'
                else:
                    search_cross_execution_bool = bool(search_cross_execution_value)
                
                # 创建节点
                new_node = BotNode(
                    node_name=node_name,
                    api_token_hash=generate_password_hash(api_token),
                    status=0,  # 默认离线
                    activity_status='Idle',
                    cron_schedule=data.get('cron_schedule', '10 9,13,19 * * *'),
                    min_sleep_minutes=data.get('min_sleep_minutes', 5),
                    max_sleep_minutes=data.get('max_sleep_minutes', 20),
                    clusters=data.get('clusters', 1),
                    search_delay_min=data.get('search_delay_min', '30s'),
                    search_delay_max=data.get('search_delay_max', '2min'),
                    search_cross_execution=search_cross_execution_bool
                )
                
                db.session.add(new_node)
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': '节点创建成功',
                    'node_id': new_node.id,
                    'api_token': api_token
                })
            except Exception as e:
                db.session.rollback()
                print(f"创建节点失败: {e}")
                return jsonify({'error': f'创建节点失败: {str(e)}'}), 500
        
        elif request.method == 'PUT':
            try:
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
                
                # 更新节点配置
                node.node_name = node_name
                node.cron_schedule = data.get('cron_schedule', node.cron_schedule)
                node.min_sleep_minutes = data.get('min_sleep_minutes', node.min_sleep_minutes)
                node.max_sleep_minutes = data.get('max_sleep_minutes', node.max_sleep_minutes)
                node.clusters = data.get('clusters', node.clusters)
                node.search_delay_min = data.get('search_delay_min', node.search_delay_min)
                node.search_delay_max = data.get('search_delay_max', node.search_delay_max)
                # 处理交叉执行开关的布尔值转换
                search_cross_execution_value = data.get('search_cross_execution', getattr(node, 'search_cross_execution', False))
                if isinstance(search_cross_execution_value, str):
                    node.search_cross_execution = search_cross_execution_value == 'on'
                else:
                    node.search_cross_execution = bool(search_cross_execution_value)
                
                db.session.commit()
                
                return jsonify({'status': 'success', 'message': '节点更新成功'})
            except Exception as e:
                db.session.rollback()
                print(f"更新节点失败: {e}")
                return jsonify({'error': f'更新节点失败: {str(e)}'}), 500
    
    except Exception as e:
        print(f"manage_nodes 请求出错: {e}")
        return jsonify({
            "code": 1,
            "msg": f"请求处理失败: {str(e)}",
            "count": 0,
            "data": []
        }), 500


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
        node.command = 'RUN_TASKS'
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
        node.command = 'STOP_TASKS'
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

@bp.route('/nodes/<int:node_id>/restart', methods=['POST'])
@web_login_required
def restart_node(node_id):
    """重启节点服务"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 检查节点是否在线
        if node.status != 1:
            return jsonify({'error': '节点不在线，无法重启'}), 400
        
        # 记录重启开始时间
        restart_start_time = datetime.now(timezone.utc)
        
        # 设置重启命令
        node.command_status = 'pending'
        node.command = 'RESTART_SERVICE'
        node.command_updated_at = restart_start_time
        node.command_data = json.dumps({
            'restart_time': safe_isoformat(restart_start_time),
            'restart_reason': 'manual_restart',
            'restart_by': g.user.username if hasattr(g, 'user') else 'unknown'
        })
        
        # 创建重启历史记录（如果表存在）
        try:
            restart_record = NodeRestartHistory(
                node_id=node_id,
                restart_time=restart_start_time,
                restart_reason='manual_restart',
                restarted_by=g.user.username if hasattr(g, 'user') else 'unknown',
                status='pending',
                notes=f'管理员手动重启节点 {node.node_name}'
            )
            db.session.add(restart_record)
            db.session.commit()
        except Exception as history_error:
            # 如果历史记录表不存在，记录警告但继续执行重启
            current_app.logger.warning(f"无法创建重启历史记录: {history_error}")
            # 回滚历史记录相关的操作，但保持节点命令设置
            db.session.rollback()
            # 重新设置节点命令（因为rollback会撤销之前的操作）
            node.command_status = 'pending'
            node.command = 'RESTART_SERVICE'
            node.command_updated_at = restart_start_time
            node.command_data = json.dumps({
                'restart_time': safe_isoformat(restart_start_time),
                'restart_reason': 'manual_restart',
                'restart_by': g.user.username if hasattr(g, 'user') else 'unknown'
            })
            db.session.commit()
        
        # 记录重启日志
        current_app.logger.info(f"管理员 {g.user.username if hasattr(g, 'user') else 'unknown'} 重启节点 {node.node_name} (ID: {node_id})")
        
        # 触发推送通知
        try:
            from .push import trigger_push_notification
            trigger_push_notification(
                'system_alert', 
                f"🔄 节点重启", 
                f"节点 {node.node_name} 正在重启服务\n⏰ 重启时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n👤 操作人: {g.user.username if hasattr(g, 'user') else 'unknown'}"
            )
        except Exception as push_error:
            current_app.logger.warning(f"重启推送通知失败: {push_error}")
        
        return jsonify({
            'status': 'success', 
            'message': '重启命令已下发',
            'restart_time': datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        current_app.logger.error(f"重启节点失败: {e}")
        return jsonify({'error': '重启节点失败'}), 500

@bp.route('/nodes/<int:node_id>', methods=['GET'])
@web_login_required
def get_node_detail(node_id):
    """获取节点详情"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 获取节点分配的账户数量
        account_count = BotAccount.query.filter_by(assigned_node_id=node_id, is_enabled=True).count()
        
        node_data = {
            'id': node.id,
            'node_name': node.node_name,
            'status': 'Online' if node.status == 1 else 'Offline',
            'activity_status': node.activity_status,
            'last_seen': safe_isoformat(node.last_seen),
            'ip_address': node.ip_address,
            'account_count': account_count,
            'command': node.command,
            'command_status': node.command_status,
            'command_updated_at': safe_isoformat(node.command_updated_at),
            'created_at': safe_isoformat(node.created_at) if hasattr(node, 'created_at') else None
        }
        
        return jsonify({'status': 'success', 'data': node_data})
    
    except Exception as e:
        current_app.logger.error(f"获取节点详情失败: {e}")
        return jsonify({'error': '获取节点详情失败'}), 500

@bp.route('/nodes/<int:node_id>/restart-history', methods=['GET'])
@web_login_required
def get_node_restart_history(node_id):
    """获取节点重启历史记录"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({'error': '节点不存在'}), 404
        
        # 检查 node_restart_history 表是否存在
        try:
            # 获取重启历史记录
            history_records = NodeRestartHistory.query.filter_by(node_id=node_id)\
                .order_by(NodeRestartHistory.restart_time.desc())\
                .limit(20).all()
            
            history_data = [record.to_dict() for record in history_records]
        except Exception as table_error:
            # 如果表不存在，返回空数据
            current_app.logger.warning(f"node_restart_history 表不存在或查询失败: {table_error}")
            history_data = []
        
        return jsonify({
            'status': 'success', 
            'data': {
                'node_id': node_id,
                'node_name': node.node_name,
                'restart_history': history_data
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"获取节点重启历史失败: {e}")
        return jsonify({'error': '获取节点重启历史失败'}), 500

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
        # 将token进行hash处理后存储到数据库
        node.api_token_hash = generate_password_hash(new_token)
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
        
        node_name = node.node_name
        
        # 检查是否有账户分配到此节点，如果有则将其设为未分配
        assigned_accounts = BotAccount.query.filter_by(assigned_node_id=node_id).all()
        account_count = len(assigned_accounts)
        
        if account_count > 0:
            # 将账户的assigned_node_id设为None（未分配状态）
            for account in assigned_accounts:
                account.assigned_node_id = None
            current_app.logger.info(f'已将节点 {node_name} 下的 {account_count} 个账户设为未分配状态')
        
        # 清理节点的所有任务（调度器任务和数据库任务）
        try:
            scheduler.clear_node_tasks(node_id)
            current_app.logger.info(f'已清理节点 {node_name} 的所有任务')
        except Exception as clear_error:
            current_app.logger.warning(f'清理节点 {node_name} 任务时出错: {clear_error}')
            # 继续执行删除操作，不因为任务清理失败而阻止节点删除
        
        # 删除节点
        db.session.delete(node)
        db.session.commit()
        
        message = f'节点 {node_name} 删除成功'
        if account_count > 0:
            message += f'，已将 {account_count} 个账户设为未分配状态'
        
        current_app.logger.info(message)
        return jsonify({'status': 'success', 'message': message})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除节点失败: {e}")
        return jsonify({'error': f'删除节点失败: {str(e)}'}), 500

@bp.route('/accounts', methods=['GET'])
@web_login_required
def get_accounts():
    """获取所有账户列表（用于账户分析页面）"""
    try:
        # 获取所有账户，按邮箱排序
        accounts = db.session.query(
            BotAccount,
            Account,
            BotNode
        ).outerjoin(
            Account, BotAccount.id == Account.bot_account_id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        ).order_by(BotAccount.email.asc()).all()
        
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
                'created_at': safe_isoformat(bot_account.created_at)
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
        # 获取查询参数
        node_id = request.args.get('node_id', type=int)
        status = request.args.get('status')
        email = request.args.get('email')
        
        # 构建查询
        query = db.session.query(
            BotAccount,
            Account,
            BotNode
        ).outerjoin(
            Account, BotAccount.id == Account.bot_account_id
        ).outerjoin(
            BotNode, BotAccount.assigned_node_id == BotNode.id
        )
        
        # 应用过滤条件
        if node_id:
            query = query.filter(BotAccount.assigned_node_id == node_id)
        
        if status:
            if status == 'enabled':
                query = query.filter(BotAccount.is_enabled == True)
            elif status == 'disabled':
                query = query.filter(BotAccount.is_enabled == False)
        
        if email:
            query = query.filter(BotAccount.email.contains(email))
        
        accounts = query.order_by(BotAccount.email.asc()).all()
        
        account_data = []
        for bot_account, account, node in accounts:
            # 构建监控数据对象
            monitoring_data = {
                'total_points': account.total_points if account else 0,
                'daily_gain': account.daily_gain if account else 0,
                'desktop_gain': account.desktop_gain if account else 0,
                'mobile_gain': account.mobile_gain if account else 0,
                'last_updated': safe_isoformat(account.last_updated) if account else None,
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
                'created_at': safe_isoformat(bot_account.created_at)
            })
        
        return jsonify({
            "code": 0,
            "msg": "success",
            "count": len(account_data),
            "data": account_data
        })
    
    elif request.method == 'POST':
        # 创建新账户或更新现有账户
        data = request.get_json()
        account_id = data.get('id')
        email = data.get('email')
        password = data.get('password')
        auxiliary_email = data.get('auxiliary_email')
        assigned_node_id = data.get('assigned_node_id')
        user_agent_id = data.get('user_agent_id')
        proxy = data.get('proxy', {})
        user_agents = data.get('userAgents', {})
        hot_search_endpoints = data.get('hotSearchEndpoints', [])
        
        if not email:
            return jsonify({'status': 'error', 'message': '邮箱不能为空'}), 400
        
        # 对于编辑操作，密码可以为空（表示不修改密码）
        # 对于新增操作，密码不能为空
        if not account_id and not password:
            return jsonify({'status': 'error', 'message': '新增账户时密码不能为空'}), 400
        
        try:
            if account_id:
                # 更新现有账户
                account = BotAccount.query.get(account_id)
                if not account:
                    return jsonify({'status': 'error', 'message': '账户不存在'}), 404
                
                # 检查邮箱是否被其他账户使用
                existing_account = BotAccount.query.filter(BotAccount.email == email, BotAccount.id != account_id).first()
                if existing_account:
                    return jsonify({'status': 'error', 'message': '邮箱已被其他账户使用'}), 400
                
                # 更新账户信息
                account.email = email
                # 只有在密码不为空时才更新密码（编辑时密码可以为空表示不修改）
                if password:
                    account.password = password
                account.auxiliary_email = auxiliary_email
                account.assigned_node_id = assigned_node_id
                account.proxy = json.dumps(proxy) if proxy else None
                account.user_agents = json.dumps(user_agents) if user_agents else None
                account.hot_search_endpoints = json.dumps(hot_search_endpoints) if hot_search_endpoints else None
                
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': '账户更新成功',
                    'account_id': account.id
                })
            else:
                # 创建新账户
                # 检查邮箱是否已存在
                existing_account = BotAccount.query.filter_by(email=email).first()
                if existing_account:
                    return jsonify({'status': 'error', 'message': '邮箱已存在'}), 400
                
                # 创建账户
                new_account = BotAccount(
                    email=email,
                    password=password,
                    auxiliary_email=auxiliary_email,
                    assigned_node_id=assigned_node_id,
                    proxy=json.dumps(proxy) if proxy else None,
                    user_agents=json.dumps(user_agents) if user_agents else None,
                    hot_search_endpoints=json.dumps(hot_search_endpoints) if hot_search_endpoints else None,
                    is_enabled=True
                )
                
                db.session.add(new_account)
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': '账户创建成功',
                    'account_id': new_account.id
                })
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"保存账户失败: {e}")
            return jsonify({'status': 'error', 'message': f'保存失败: {str(e)}'}), 500

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
            'status': 'success',
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
            'auxiliary_email': account.auxiliary_email,
            'assigned_node_id': account.assigned_node_id,
            'node_name': node.node_name if node else '未分配',
            'is_enabled': account.is_enabled,
            'proxy': account.proxy,
            'user_agents': account.user_agents,
            'hot_search_endpoints': account.hot_search_endpoints,
            'user_agent_id': getattr(account, 'user_agent_id', None),  # 如果字段不存在则返回None
            'total_points': points_data.total_points if points_data else 0,
            'daily_gain': points_data.daily_gain if points_data else 0,
            'desktop_gain': points_data.desktop_gain if points_data else 0,
            'mobile_gain': points_data.mobile_gain if points_data else 0,
            'last_updated': points_data.last_updated if points_data else None,
            'created_at': safe_isoformat(account.created_at)
        }
        
        return jsonify({
            'status': 'success',
            'data': account_data
        })
    
    elif request.method == 'DELETE':
        # 删除账户
        try:
            account = BotAccount.query.get(account_id)
            if not account:
                return jsonify({'status': 'error', 'message': '账户不存在'}), 404
            
            # 删除账户（相关数据会通过外键约束自动删除）
            # accounts, account_points_history, tasks 表的数据会通过 ON DELETE CASCADE 自动删除
            # user_agents 表的 used_by_account_id 会通过 ON DELETE SET NULL 自动设置为 NULL
            db.session.delete(account)
            db.session.commit()
            
            current_app.logger.info(f'账户 {account_id} 删除成功')
            return jsonify({'status': 'success', 'message': '账户删除成功'})
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除账户失败: {e}")
            return jsonify({'status': 'error', 'message': f'删除账户失败: {str(e)}'}), 500

@bp.route('/bot_accounts/batch_delete', methods=['POST'])
@web_login_required
def batch_delete_accounts():
    """批量删除账户"""
    try:
        data = request.get_json()
        account_ids = data.get('ids', [])
        
        if not account_ids:
            return jsonify({'status': 'error', 'message': '请选择要删除的账户'}), 400
        
        deleted_count = 0
        failed_accounts = []
        
        for account_id in account_ids:
            try:
                account = BotAccount.query.get(account_id)
                if account:
                    # 删除账户（相关数据会通过外键约束自动删除）
                    db.session.delete(account)
                    deleted_count += 1
                    current_app.logger.info(f'准备删除账户 {account_id}')
                else:
                    failed_accounts.append(f'账户 {account_id} 不存在')
            except Exception as e:
                failed_accounts.append(f'账户 {account_id} 删除失败: {str(e)}')
                current_app.logger.error(f'删除账户 {account_id} 时出错: {e}')
        
        db.session.commit()
        
        message = f'成功删除 {deleted_count} 个账户'
        if failed_accounts:
            message += f'，失败 {len(failed_accounts)} 个: {", ".join(failed_accounts)}'
        
        current_app.logger.info(f'批量删除完成: {message}')
        return jsonify({
            'status': 'success', 
            'message': message
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量删除账户失败: {e}")
        return jsonify({'status': 'error', 'message': f'批量删除账户失败: {str(e)}'}), 500

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
                'created_at': safe_isoformat(config.created_at)
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


@bp.route('/mobile/get_points', methods=['GET'])
def mobile_get_points():
    """移动端获取积分数据（免登录）"""
    try:
        # 检查缓存
        cache_key = 'mobile_points_data'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # 获取所有节点和账户数据，按节点名称排序
        nodes = BotNode.query.filter_by(status=1).order_by(BotNode.node_name.asc()).all()  # 只获取在线节点
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
                        'desktop_gain': account.desktop_gain or 0,
                        'mobile_gain': account.mobile_gain or 0
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
                'record_date': safe_isoformat(history.record_date),
                'created_at': safe_isoformat(history.created_at)
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
            date_str = safe_isoformat(history.record_date)
            
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