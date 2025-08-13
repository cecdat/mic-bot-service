from flask import Blueprint, request, jsonify, g
from .db import db
# [CORE FIX] Import the 'BotNode' model along with the others
from .models import Account, BotAccount, BotNode
from .auth import bot_api_required
from .push import trigger_push_notification
import datetime
import json
import time

bp = Blueprint('api_bot', __name__, url_prefix='/bot_api')

@bp.route('/checkin', methods=['POST'])
@bot_api_required
def node_checkin():
    data = request.get_json()
    node = g.node 
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
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
                node.activity_status = bot_status
                
        if 'heartbeat_timeout' in data:
            node.heartbeat_timeout = data.get('heartbeat_timeout')
        db.session.commit()

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
            # Update command status to received
            if node_fresh.command_status != 'received':
                node_fresh.command_status = 'received'
                db.session.commit()
            return jsonify({"command": command_to_run})
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
    db.session.commit()
    return jsonify({"status": "success", "message": f"Activity status updated to {status}"})

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
        "search_delay_max": node.search_delay_max
    }
    return jsonify(config_data)

@bp.route('/accounts', methods=['GET'])
@bot_api_required
def get_assigned_accounts():
    node = g.node
    accounts = BotAccount.query.filter_by(assigned_node_id=node.id, status=1).all()
    
    accounts_data = []
    for acc in accounts:
        accounts_data.append({
            "email": acc.email, "password": acc.password,
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
        account.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
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
        account.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
        account.node_name = g.node.node_name

        db.session.commit()
        return jsonify({"status": "success", "message": "Points updated."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500