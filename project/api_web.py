from flask import Blueprint, request, jsonify, session
from .db import db
from .models import Account, BotAccount, BotNode, PushConfig, WebUser
from .auth import web_login_required
import datetime
import json
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('api_web', __name__, url_prefix='/web_api')

@bp.route('/login', methods=['POST'])
def web_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = WebUser.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session.clear()
        session['user_id'] = user.id
        return jsonify({"status": "success", "token": os.environ.get('ADMIN_PASS', 'password')})

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@bp.route('/get_points', methods=['GET'])
@web_login_required
def get_points():
    # [核心修改] 增加 filter 参数
    show_all = request.args.get('filter', 'all') == 'all'
    
    query = db.session.query(Account, BotAccount.email, BotNode.node_name)\
        .outerjoin(BotAccount, Account.bot_account_id == BotAccount.id)\
        .outerjoin(BotNode, BotAccount.assigned_node_id == BotNode.id)\
        .order_by(Account.last_updated.desc())
    
    today_str = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    if not show_all:
        # 仅查询当天的数据
        query = query.filter(db.func.date(Account.last_updated) == today_str)
        
    results = query.all()

    # 如果没有结果且不是查询所有数据，则尝试查询所有数据
    if not results and not show_all:
        query = db.session.query(Account, BotAccount.email, BotNode.node_name)\
            .outerjoin(BotAccount, Account.bot_account_id == BotAccount.id)\
            .outerjoin(BotNode, BotAccount.assigned_node_id == BotNode.id)\
            .order_by(Account.last_updated.desc())
        results = query.all()
    
    points_data = []
    
    for account, email, node_name in results:
        acc_dict = {c.name: getattr(account, c.name) for c in account.__table__.columns}
        acc_dict['email'] = email or "未知账户 (孤立数据)"
        acc_dict['node_name'] = node_name or None

        if acc_dict.get('status_details'):
            acc_dict['status_details'] = json.loads(acc_dict['status_details'])
        else:
            acc_dict['status_details'] = {}
            
        if acc_dict.get('last_updated'):
            last_updated_date_str = datetime.datetime.fromisoformat(acc_dict['last_updated']).date().isoformat()
            acc_dict['is_stale'] = last_updated_date_str != today_str
        else:
            acc_dict['is_stale'] = True
        points_data.append(acc_dict)
    return jsonify(points_data)

@bp.route('/nodes', methods=['GET', 'POST', 'PUT'])
@web_login_required
def manage_nodes():
    if request.method == 'GET':
        nodes = BotNode.query.order_by(BotNode.node_name).all()
        nodes_data = []
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        for node in nodes:
            node_dict = {
                "id": node.id, "node_name": node.node_name, "last_seen": node.last_seen,
                "heartbeat_timeout": node.heartbeat_timeout, "ip_address": node.ip_address,
                "cron_schedule": node.cron_schedule, "min_sleep_minutes": node.min_sleep_minutes,
                "max_sleep_minutes": node.max_sleep_minutes, "clusters": node.clusters,
                "search_delay_min": node.search_delay_min, "search_delay_max": node.search_delay_max,
                "activity_status": node.activity_status
            }
            if node.last_seen:
                last_seen_dt = datetime.datetime.fromisoformat(node.last_seen)
                timeout = node.heartbeat_timeout or 600
                node_dict['status'] = 'Online' if (now_utc - last_seen_dt).total_seconds() <= timeout else 'Offline'
            else:
                node_dict['status'] = 'Never Seen'
            
            # [核心修正] 在这里计算并添加统计数据到字典中
            total_count = node.accounts.count()
            # 这是一个简化的状态统计，更精确的统计可能需要更复杂的查询
            normal_count = Account.query.join(BotAccount).filter(BotAccount.assigned_node_id == node.id, Account.status_details.like('%"status": true%')).count()
            abnormal_count = total_count - normal_count

            node_dict['account_count_total'] = total_count
            node_dict['account_count_normal'] = normal_count
            node_dict['account_count_abnormal'] = abnormal_count
            
            nodes_data.append(node_dict)
        return jsonify(nodes_data)

    if request.method == 'POST' or request.method == 'PUT':
        data = request.get_json()
        
        if request.method == 'POST':
            node_name = data.get('node_name')
            if not node_name: return jsonify({"status": "error", "message": "节点名称为必填项"}), 400
            if BotNode.query.filter_by(node_name=node_name).first():
                return jsonify({"status": "error", "message": "该节点名称已存在"}), 409
            
            new_token = secrets.token_hex(24)
            token_hash = generate_password_hash(new_token)
            node = BotNode(node_name=node_name, api_token_hash=token_hash)
            db.session.add(node)
        else: # PUT
            node_id = data.get('id')
            node = BotNode.query.get(node_id)
            if not node: return jsonify({"status": "error", "message": "未找到该节点"}), 404
            node.node_name = data.get('node_name', node.node_name)

        node.cron_schedule = data.get('cron_schedule', node.cron_schedule)
        node.min_sleep_minutes = data.get('min_sleep_minutes', node.min_sleep_minutes)
        node.max_sleep_minutes = data.get('max_sleep_minutes', node.max_sleep_minutes)
        node.clusters = data.get('clusters', node.clusters)
        node.search_delay_min = data.get('search_delay_min', node.search_delay_min)
        node.search_delay_max = data.get('search_delay_max', node.search_delay_max)
        
        db.session.commit()
        
        if request.method == 'POST':
            return jsonify({"status": "success", "node_name": node.node_name, "api_token": new_token})
        else:
            return jsonify({"status": "success", "message": "节点配置已更新。"})

@bp.route('/nodes/<int:node_id>/trigger', methods=['POST'])
@web_login_required
def trigger_node(node_id):
    node = BotNode.query.get(node_id)
    if not node:
        return jsonify({"status": "error", "message": "未找到该节点"}), 404

    if node.activity_status != 'Idle':
        return jsonify({"status": "error", "message": f"节点正忙 ({node.activity_status})，无法触发。"}), 409
        
    node.command = 'RUN_TASKS'
    db.session.commit()
    return jsonify({"status": "success", "message": f"已向节点 {node.node_name} 发送触发指令。"})

@bp.route('/nodes/<int:node_id>/stop', methods=['POST'])
@web_login_required
def stop_node(node_id):
    node = BotNode.query.get(node_id)
    if not node: return jsonify({"status": "error", "message": "未找到该节点"}), 404
    
    if node.activity_status != 'Running':
        return jsonify({"status": "error", "message": "节点当前未在运行任务，无法停止。"}), 409
        
    node.command = 'STOP_TASKS'
    db.session.commit()
    return jsonify({"status": "success", "message": f"已向节点 {node.node_name} 发送停止指令。"})

@bp.route('/nodes/<int:node_id>', methods=['DELETE'])
@web_login_required
def delete_node(node_id):
    try:
        node = BotNode.query.get(node_id)
        if not node: return jsonify({"status": "error", "message": "未找到该节点"}), 404
        
        # 获取关联的账户数量
        associated_accounts_count = node.accounts.count()
        
        # 如果有关联的账户，将它们设置为未分配状态
        if associated_accounts_count > 0:
            for account in node.accounts:
                account.assigned_node_id = None
            db.session.commit()
        
        # 删除节点
        node_name = node.node_name
        db.session.delete(node)
        db.session.commit()
        
        if associated_accounts_count > 0:
            return jsonify({"status": "success", "message": f"节点 {node_name} 已删除，{associated_accounts_count} 个关联账户已设置为未分配状态。"})
        else:
            return jsonify({"status": "success", "message": f"节点 {node_name} 已删除。"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500



@bp.route('/bot_accounts', methods=['GET', 'POST'])
@web_login_required
def manage_bot_accounts():
    if request.method == 'GET':
        accounts = BotAccount.query.order_by(BotAccount.email).all()
        accounts_data = []
        for acc in accounts:
            monitoring_data = acc.monitoring_data
            acc_dict = {
                "id": acc.id, "email": acc.email, "password": acc.password,
                "proxy": json.loads(acc.proxy or '{}'),
                "userAgents": json.loads(acc.user_agents or '{}'),
                "hotSearchEndpoints": json.loads(acc.hot_search_endpoints or '[]'),
                "assigned_node_id": acc.assigned_node_id,
                "assigned_node_name": acc.node.node_name if acc.node else None,
                "monitoring_data": {
                    "status_details": json.loads(monitoring_data.status_details) if monitoring_data and monitoring_data.status_details else {},
                    "last_updated": monitoring_data.last_updated if monitoring_data else None,
                    "total_points": monitoring_data.total_points if monitoring_data else 'N/A',
                    "daily_gain": monitoring_data.daily_gain if monitoring_data else 'N/A',
                    "desktop_gain": monitoring_data.desktop_gain if monitoring_data else 'N/A',
                    "mobile_gain": monitoring_data.mobile_gain if monitoring_data else 'N/A'
                }
            }
            accounts_data.append(acc_dict)
        return jsonify(accounts_data)

    if request.method == 'POST':
            data = request.get_json()
            email = data.get('email')
            try:
                account = BotAccount.query.filter_by(email=email).first()
                if not account:
                    account = BotAccount(email=email)
                    db.session.add(account)
                    # 创建对应的Account记录
                    new_account = Account(bot_account_id=account.id, total_points=0, daily_gain=0)
                    db.session.add(new_account)

                account.password = data.get('password')
                account.proxy = json.dumps(data.get('proxy', {}))
                account.user_agents = json.dumps(data.get('userAgents', {}))
                account.hot_search_endpoints = json.dumps(data.get('hotSearchEndpoints', []))
                account.assigned_node_id = data.get('assigned_node_id')
                
                db.session.commit()
                return jsonify({"status": "success", "message": "Account saved."})
            except Exception as e:
                db.session.rollback()
                return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/bot_accounts/<int:account_id>', methods=['DELETE'])
@web_login_required
def delete_bot_account(account_id):
    try:
        account = BotAccount.query.get(account_id)
        if account:
            db.session.delete(account)
            db.session.commit()
        return jsonify({"status": "success", "message": "Account deleted."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/push_configs', methods=['GET', 'POST'])
@web_login_required
def manage_push_configs():
    if request.method == 'GET':
        configs = PushConfig.query.all()
        return jsonify([{ "id": c.id, "url": c.url, "notify_on_node_online": c.notify_on_node_online, "notify_on_node_offline": c.notify_on_node_offline, "notify_on_account_error": c.notify_on_account_error } for c in configs])

    if request.method == 'POST':
        data = request.get_json()
        url = data.get('url')
        if not url: return jsonify({"status": "error", "message": "URL is required"}), 400
        
        config_id = data.get('id')
        if config_id:
            config = PushConfig.query.get(config_id)
        else:
            config = PushConfig()
            db.session.add(config)
        
        config.url = url
        config.notify_on_node_online = data.get('notify_on_node_online', False)
        config.notify_on_node_offline = data.get('notify_on_node_offline', False)
        config.notify_on_account_error = data.get('notify_on_account_error', False)
        
        db.session.commit()
        return jsonify({"status": "success"})

@bp.route('/push_configs/<int:config_id>', methods=['DELETE'])
@web_login_required
def delete_push_config(config_id):
    config = PushConfig.query.get(config_id)
    if config:
        db.session.delete(config)
        db.session.commit()
    return jsonify({"status": "success"})