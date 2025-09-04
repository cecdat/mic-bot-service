from flask import Blueprint, request, jsonify, g
from .db import db
# [CORE FIX] Import the 'BotNode' model along with the others
from .models import Account, BotAccount, BotNode, Task
from .auth import bot_api_required
from .push import trigger_push_notification
from .scheduler import reset_node_tasks
from datetime import datetime, timezone
import json
import time
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('api_bot')

bp = Blueprint('api_bot', __name__, url_prefix='/bot_api')

@bp.route('/checkin', methods=['POST'])
@bot_api_required
def node_checkin():
    data = request.get_json()
    node = g.node 
    
    # 使用节点发送的UTC时间戳，如果没有则使用服务器本地时间
    node_timestamp = data.get('timestamp')
    if node_timestamp:
        try:
            timestamp = datetime.fromisoformat(node_timestamp)
            # 确保timestamp带有时区信息
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except ValueError:
            timestamp = datetime.now(timezone.utc)
    else:
        timestamp = datetime.now(timezone.utc)
    
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        is_coming_online = node.status != 1 or not node.last_seen
        
        node.status = 1
        node.last_seen = timestamp
        node.ip_address = ip_address
        
        # 处理bot_status参数
        if 'bot_status' in data:
            bot_status = data.get('bot_status')
            if bot_status in ['Running', 'Idle']:
                # 检查是否从非Running状态变为Running状态
                is_running = node.activity_status != 'Running' and bot_status == 'Running'
                node.activity_status = bot_status
                
                # 如果变为Running状态，重置任务
                if is_running:
                    logger.info(f'节点 {node.node_name} 状态变为Running，重置任务')
                    reset_node_tasks(node.id)
                
        if 'heartbeat_timeout' in data:
            node.heartbeat_timeout = data.get('heartbeat_timeout')
        db.session.commit()

        if is_coming_online:
            trigger_push_notification('node_online', f"节点上线: {node.node_name}", f"IP: {ip_address}")

        return jsonify({"status": "success", "message": f"Node {node.node_name} checked in."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/update_task_status', methods=['POST'])
@bot_api_required
def update_task_status():
    data = request.get_json()
    node = g.node
    
    # 验证请求数据
    if not data or 'task_id' not in data or 'status' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    task_id = data.get('task_id')
    new_status = data.get('status')
    result = data.get('result')
    error_message = data.get('error_message')
    
    # 检查任务是否存在且属于该节点
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': f'任务 {task_id} 不存在'}), 404
    
    if task.node_id != node.id:
        return jsonify({'success': False, 'message': f'任务 {task_id} 不属于当前节点'}), 403
    
    # 更新任务状态
    try:
        from .scheduler import update_task_status as update_task
        success = update_task(task_id, new_status, result, error_message)
        
        if success:
            return jsonify({'success': True, 'message': f'任务 {task_id} 状态已更新为 {new_status}'})
        else:
            return jsonify({'success': False, 'message': f'更新任务 {task_id} 状态失败'}), 500
    except Exception as e:
        logger.error(f'节点 {node.node_name} 更新任务 {task_id} 状态时发生错误: {str(e)}')
        return jsonify({'success': False, 'message': f'服务器内部错误: {str(e)}'}), 500

        if is_coming_online:
            trigger_push_notification('node_online', f"节点上线: {node.node_name}", f"IP: {ip_address}")

        return jsonify({"status": "success", "message": f"Node {node.node_name} checked in."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

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

@bp.route('/confirm_command', methods=['POST'])
@bot_api_required
def confirm_command():
    node = g.node
    data = request.get_json()
    command = data.get('command')
    
    try:
        node_fresh = BotNode.query.get(node.id)
        if node_fresh and node_fresh.command == command:
            # Clear command and update status
            node_fresh.command = None
            node_fresh.command_status = 'executed'
            db.session.commit()
            return jsonify({"status": "success", "message": "Command confirmed"})
        return jsonify({"status": "error", "message": "No pending command to confirm"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/update_activity', methods=['POST'])
@bot_api_required
def update_activity():
    data = request.get_json()
    status = data.get('activity_status')
    if status not in ['Running', 'Idle']:
        return jsonify({"status": "error", "message": "Invalid activity status"}), 400
    
    node = g.node
    node.activity_status = status
    
    # 记录状态更新时间
    if 'timestamp' in data:
        try:
            from datetime import datetime
            node.status_updated_at = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except:
            node.status_updated_at = datetime.utcnow()
    else:
        node.status_updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({"status": "success", "message": f"Activity status updated to {status}"})

@bp.route('/sync_status', methods=['POST'])
@bot_api_required
def sync_status():
    """精准状态同步接口"""
    data = request.get_json()
    status = data.get('activity_status')
    if status not in ['Running', 'Idle']:
        return jsonify({"status": "error", "message": "Invalid activity status"}), 400
    
    node = g.node
    node.activity_status = status
    
    # 记录状态更新时间
    if 'timestamp' in data:
        try:
            from datetime import datetime
            node.status_updated_at = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except:
            node.status_updated_at = datetime.utcnow()
    else:
        node.status_updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({"status": "success", "message": f"Status synced to {status}"})

@bp.route('/get_config', methods=['GET'])
@bot_api_required
def get_node_config():
    node = g.node
    config_data = {
        "cron_schedule": node.cron_schedule,
        "min_sleep_minutes": node.min_sleep_minutes,
        "max_sleep_minutes": node.max_sleep_minutes,
        "clusters": node.clusters,
        "search_delay_min": node.search_delay_min,
        "search_delay_max": node.search_delay_max,
        # 日志推送配置
        "log_push_enabled": node.log_push_enabled,
        "log_push_interval": node.log_push_interval
    }
    return jsonify(config_data)

@bp.route('/accounts', methods=['GET'])
@bot_api_required
def get_assigned_accounts():
    node = g.node
    accounts = BotAccount.query.filter_by(assigned_node_id=node.id, is_enabled=True).all()
    
    accounts_data = []
    for acc in accounts:
        accounts_data.append({
            "email": acc.email, "password": acc.password,
            "auxiliary_email": acc.auxiliary_email,
            "proxy": json.loads(acc.proxy or '{}'),
            "userAgents": json.loads(acc.user_agents or '{}'),
            "hotSearchEndpoints": json.loads(acc.hot_search_endpoints or '[]')
        })
    return jsonify(accounts_data)

@bp.route('/update_login_status', methods=['POST'])
@bot_api_required
def update_login_status():
    data = request.get_json()
    email = data.get('email')
    platform_type = data.get('type')
    if not all([email, platform_type]): return jsonify({"status": "error", "message": "Missing email or type"}), 400
        
    try:
        bot_account = BotAccount.query.filter_by(email=email).first()
        if not bot_account: return jsonify({"status": "error", "message": "Account not found"}), 404
        
        account = bot_account.monitoring_data
        if not account:
            account = Account(bot_account_id=bot_account.id)
            db.session.add(account)

        current_status = json.loads(account.status_details) if account.status_details else {}
        current_status[platform_type] = {
            "status": data.get('status'), "code": data.get('code'), "message": data.get('message')
        }
        
        account.status_details = json.dumps(current_status)
        # 修复时间戳处理：使用正确的timezone.utc语法
        account.last_updated = datetime.now(timezone.utc).isoformat()
        account.node_name = g.node.node_name

        db.session.commit()

        if data.get('status') is False:
            trigger_push_notification(
                'account_error', 
                f"账户异常: {email}", 
                f"节点: {g.node.node_name}, 平台: {data.get('type')}, 详情: {data.get('message')}"
            )

        return jsonify({"status": "success", "message": "Login status updated."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/update_points', methods=['POST'])
@bot_api_required
def update_points():
    data = request.get_json()
    email = data.get('email')
    if not data or not email: return jsonify({"status": "error", "message": "Invalid data"}), 400
        
    try:
        bot_account = BotAccount.query.filter_by(email=email).first()
        if not bot_account: return jsonify({"status": "error", "message": "Account not found"}), 404
        
        account = bot_account.monitoring_data
        if not account:
            account = Account(bot_account_id=bot_account.id)
            db.session.add(account)

        account.total_points = data.get('total_points')
        account.daily_gain = data.get('daily_gain')
        account.desktop_gain = data.get('desktop_gain', 0)
        account.mobile_gain = data.get('mobile_gain', 0)
        # 修复时间戳处理：使用正确的datetime.now()和timezone.utc语法
        account.last_updated = datetime.now(timezone.utc).isoformat()
        account.node_name = g.node.node_name

        db.session.commit()
        return jsonify({"status": "success", "message": "Points updated."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/report_task_completion', methods=['POST'])
@bot_api_required
def report_task_completion():
    data = request.get_json()
    task_id = data.get('task_id')
    status = data.get('status')
    error_message = data.get('error_message')
    
    if not all([task_id, status]):
        return jsonify({"status": "error", "message": "Missing task_id or status"}), 400
        
    try:
        # 查找对应的任务
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"status": "error", "message": "Task not found"}), 404
        
        # 更新任务状态
        task.status = status
        if status == 'completed':
            task.completed_at = datetime.now(timezone.utc)
        elif status == 'failed':
            task.error_message = error_message
            task.completed_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'任务 {task_id} 状态已更新为: {status}')
        return jsonify({"status": "success", "message": "Task completion reported"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/test_push', methods=['POST'])
def test_push():
    """测试推送功能"""
    data = request.get_json()
    event_type = data.get('event_type')
    title = data.get('title')
    body = data.get('body')
    
    if not all([event_type, title, body]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    
    try:
        from .push import trigger_push_notification
        trigger_push_notification(event_type, title, body)
        return jsonify({"status": "success", "message": f"Push notification sent for {event_type}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500