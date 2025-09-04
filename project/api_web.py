from flask import Blueprint, request, jsonify, session, current_app
from .db import db
from .models import Account, BotAccount, BotNode, PushConfig, WebUser
from .auth import web_login_required
from . import scheduler
from .bing_wallpaper import bing_wallpaper
from datetime import datetime, timedelta, timezone
import json
import secrets
import os

def get_inferred_status(node):
    """智能推断节点状态，误差不超过30秒"""
    now = datetime.now(timezone.utc)
    
    # 如果节点离线，直接返回Idle
    if node.status != 1:
        return 'Idle'
    
    # 如果状态更新时间在30秒内，直接返回当前状态
    if node.status_updated_at:
        time_diff = (now - node.status_updated_at).total_seconds()
        if time_diff <= 30:
            return node.activity_status
    
    # 如果最后心跳时间在30秒内，且状态为Running，保持Running
    if node.last_seen:
        heartbeat_diff = (now - node.last_seen).total_seconds()
        if heartbeat_diff <= 30 and node.activity_status == 'Running':
            return 'Running'
    
    # 如果最后心跳时间超过30秒，推断为Idle
    if node.last_seen:
        heartbeat_diff = (now - node.last_seen).total_seconds()
        if heartbeat_diff > 30:
            return 'Idle'
    
    # 默认返回当前状态
    return node.activity_status
from werkzeug.security import generate_password_hash, check_password_hash
import time
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
    import time
    start_time = time.time()
    
    # [核心修改] 增加 filter 参数
    show_all = request.args.get('filter', 'all') == 'all'
    
    query = db.session.query(Account, BotAccount.email, BotNode.node_name)\
        .outerjoin(BotAccount, Account.bot_account_id == BotAccount.id)\
        .outerjoin(BotNode, BotAccount.assigned_node_id == BotNode.id)\
        .order_by(Account.last_updated.desc())
    
    today_str = datetime.now(timezone.utc).date().isoformat()

    if not show_all:
        # 仅查询当天的数据
        query = query.filter(db.func.date(Account.last_updated) == today_str)
        
    results = query.all()

    # 如果没有结果且不是查询所有数据，则尝试查询所有数据
    if not results and not show_all:
        query = db.session.query(Account, BotAccount.email, BotNode.node_name)\
            .outerjoin(BotAccount, Account.bot_account_id == Account.id)\
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
            try:
                # 确保last_updated是字符串类型
                last_updated_str = str(acc_dict['last_updated'])
                last_updated_date_str = datetime.fromisoformat(last_updated_str).date().isoformat()
                acc_dict['is_stale'] = last_updated_date_str != today_str
            except (TypeError, ValueError):
                # 如果转换失败，标记为stale
                acc_dict['is_stale'] = True
        else:
            acc_dict['is_stale'] = True
        points_data.append(acc_dict)
    
    # 记录查询时间
    query_time = time.time() - start_time
    if query_time > 1.0:  # 如果查询时间超过1秒，记录警告
        print(f"警告: get_points查询耗时 {query_time:.2f}秒，返回 {len(points_data)} 条记录")
    
    return jsonify(points_data)

@bp.route('/nodes', methods=['GET', 'POST', 'PUT'])
@web_login_required
def manage_nodes():
    if request.method == 'GET':
        # 检查缓存
        cache_key = 'nodes_data'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # 优化查询：使用单次查询获取所有数据
        from sqlalchemy import func, case
        
        # 使用子查询优化账户统计
        account_stats = db.session.query(
            BotAccount.assigned_node_id,
            func.count(BotAccount.id).label('total_count'),
            func.sum(case(
                (Account.status_details.like('%"status": true%'), 1),
                else_=0
            )).label('normal_count')
        ).outerjoin(Account, BotAccount.id == Account.bot_account_id)\
         .group_by(BotAccount.assigned_node_id)\
         .subquery()
        
        # 获取所有节点和统计信息
        nodes_query = db.session.query(
            BotNode,
            func.coalesce(account_stats.c.total_count, 0).label('account_count_total'),
            func.coalesce(account_stats.c.normal_count, 0).label('account_count_normal')
        ).outerjoin(account_stats, BotNode.id == account_stats.c.assigned_node_id)\
         .order_by(BotNode.node_name)
        
        nodes_with_stats = nodes_query.all()
        
        nodes_data = []
        now_utc = datetime.now(timezone.utc)
        
        # 批量获取任务信息
        from .models import Task
        all_pending_tasks = Task.query.filter(
            Task.status == 'pending',
            Task.execution_time > now_utc
        ).all()
        
        # 创建任务映射
        tasks_by_node = {}
        for task in all_pending_tasks:
            if task.node_id not in tasks_by_node:
                tasks_by_node[task.node_id] = []
            tasks_by_node[task.node_id].append(task)
        
        for node, total_count, normal_count in nodes_with_stats:
            node_dict = {
                "id": node.id, "node_name": node.node_name, "last_seen": node.last_seen,
                "heartbeat_timeout": node.heartbeat_timeout, "ip_address": node.ip_address,
                "cron_schedule": node.cron_schedule, "min_sleep_minutes": node.min_sleep_minutes,
                "max_sleep_minutes": node.max_sleep_minutes, "clusters": node.clusters,
                "search_delay_min": node.search_delay_min, "search_delay_max": node.search_delay_max,
                "activity_status": get_inferred_status(node),
                "log_push_enabled": node.log_push_enabled,
                "log_push_interval": node.log_push_interval
            }
            
            if node.last_seen:
                last_seen_dt = node.last_seen
                if last_seen_dt.tzinfo is None:
                    last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
                timeout = node.heartbeat_timeout or 600
                node_dict['status'] = 'Online' if (now_utc - last_seen_dt).total_seconds() <= timeout else 'Offline'
            else:
                node_dict['status'] = 'Never Seen'
            
            # 使用预计算的统计数据
            node_dict['account_count_total'] = int(total_count or 0)
            node_dict['account_count_normal'] = int(normal_count or 0)
            node_dict['account_count_abnormal'] = int(total_count or 0) - int(normal_count or 0)

            # 获取下次执行时间（从预加载的任务中查找）
            try:
                node_tasks = tasks_by_node.get(node.id, [])
                if node_tasks:
                    # 找到最早的任务
                    next_task = min(node_tasks, key=lambda t: t.execution_time)
                    node_dict['next_run_time'] = next_task.execution_time.isoformat()
                else:
                    # 如果没有待执行任务，按原来的方式计算
                    if node.cron_schedule:
                        from apscheduler.triggers.cron import CronTrigger
                        import random
                        
                        trigger = CronTrigger.from_crontab(node.cron_schedule)
                        next_run_time = trigger.get_next_fire_time(None, now_utc)
                        
                        min_delay = node.min_sleep_minutes or 0
                        max_delay = node.max_sleep_minutes or 0
                        
                        if min_delay > 0 or max_delay > 0:
                            if min_delay > max_delay:
                                min_delay, max_delay = max_delay, min_delay
                            
                            delay_seconds = random.randint(min_delay * 60, max_delay * 60)
                            next_run_time = next_run_time + datetime.timedelta(seconds=delay_seconds)
                        
                        node_dict['next_run_time'] = next_run_time.isoformat()
                    else:
                        node_dict['next_run_time'] = None
            except Exception as e:
                node_dict['next_run_time'] = None
                print(f"获取节点 {node.node_name} 下次执行时间失败: {str(e)}")
            
            nodes_data.append(node_dict)
        
        # 缓存结果
        set_cached_data(cache_key, nodes_data)
        # 返回符合规范的格式，包含success状态码
        return jsonify(nodes_data)

    if request.method == 'POST' or request.method == 'PUT':
        # 清除相关缓存
        clear_cache()
        # 特别清理节点数据缓存
        if 'nodes_data' in _cache:
            del _cache['nodes_data']
        
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
            
            # 检查节点名字是否被修改，如果修改了需要验证是否重复
            new_node_name = data.get('node_name', node.node_name)
            if new_node_name != node.node_name:
                # 检查新名字是否已被其他节点使用
                existing_node = BotNode.query.filter(BotNode.node_name == new_node_name, BotNode.id != node_id).first()
                if existing_node:
                    return jsonify({"status": "error", "message": "该节点名称已存在"}), 409
                node.node_name = new_node_name

        node.cron_schedule = data.get('cron_schedule', node.cron_schedule)
        node.min_sleep_minutes = data.get('min_sleep_minutes', node.min_sleep_minutes)
        node.max_sleep_minutes = data.get('max_sleep_minutes', node.max_sleep_minutes)
        node.clusters = data.get('clusters', node.clusters)
        node.search_delay_min = data.get('search_delay_min', node.search_delay_min)
        node.search_delay_max = data.get('search_delay_max', node.search_delay_max)
        # 日志推送配置
        log_push_enabled_value = data.get('log_push_enabled', node.log_push_enabled)
        # 处理checkbox的值转换：'on' -> True, 其他 -> False
        node.log_push_enabled = log_push_enabled_value == 'on' if isinstance(log_push_enabled_value, str) else bool(log_push_enabled_value)
        node.log_push_interval = data.get('log_push_interval', node.log_push_interval)
        
        db.session.commit()
        
        # 更新定时任务
        scheduler.update_node_task(node.id, node.cron_schedule, node.node_name, node.min_sleep_minutes, node.max_sleep_minutes)
        
        if request.method == 'POST':
            return jsonify({"status": "success", "node_name": node.node_name, "api_token": new_token})
        else:
            return jsonify({"status": "success", "message": "节点配置已更新。"})

@bp.route('/logs/receive', methods=['POST'])
def receive_logs():
    """接收来自Node端的日志推送"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "无效的请求数据"}), 400
        
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({"status": "error", "message": "缺少认证token"}), 401
        
        # 查找对应的节点（使用check_password_hash进行认证）
        from werkzeug.security import check_password_hash
        nodes = BotNode.query.all()
        node = None
        for n in nodes:
            if check_password_hash(n.api_token_hash, token):
                node = n
                break
        
        if not node:
            return jsonify({"status": "error", "message": "无效的token"}), 401
        
        # 处理日志数据
        logs = data.get('logs', [])
        if not isinstance(logs, list):
            return jsonify({"status": "error", "message": "日志数据格式错误"}), 400
        
        # 存储日志到数据库
        from .models import NodeLog
        from datetime import datetime
        
        stored_count = 0
        for log_entry in logs:
            try:
                # 解析时间戳
                timestamp_str = log_entry.get('timestamp', '')
                if timestamp_str:
                    # 尝试解析ISO格式时间戳
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.utcnow()
                else:
                    timestamp = datetime.utcnow()
                
                # 创建日志记录
                node_log = NodeLog(
                    node_id=node.id,
                    node_name=node.node_name,
                    timestamp=timestamp,
                    level=log_entry.get('level', 'LOG'),
                    platform=log_entry.get('platform', ''),
                    title=log_entry.get('title', ''),
                    message=log_entry.get('message', ''),
                    pid=log_entry.get('pid', '')
                )
                db.session.add(node_log)
                stored_count += 1
                
            except Exception as e:
                print(f"存储日志条目失败: {e}")
                continue
        
        # 提交数据库事务
        db.session.commit()
        
        # 清理旧日志（保留最近1000条）
        try:
            from sqlalchemy import text
            db.session.execute(text("""
                DELETE FROM node_logs 
                WHERE node_id = :node_id 
                AND id NOT IN (
                    SELECT id FROM node_logs 
                    WHERE node_id = :node_id 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                )
            """), {'node_id': node.id})
            db.session.commit()
        except Exception as e:
            print(f"清理旧日志失败: {e}")
        
        return jsonify({"status": "success", "message": f"成功接收并存储 {stored_count} 条日志"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/nodes/<int:node_id>/trigger', methods=['POST'])
@web_login_required
def trigger_node(node_id):
    node = BotNode.query.get(node_id)
    if not node:
        return jsonify({"status": "error", "message": "未找到该节点"}), 404

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
    node.command_status = 'pending'  # 设置命令状态为待处理
    db.session.commit()
    return jsonify({"status": "success", "message": f"已向节点 {node.node_name} 发送触发指令（轮询模式）。"})

@bp.route('/nodes/<int:node_id>/stop', methods=['POST'])
@web_login_required
def stop_node(node_id):
    node = BotNode.query.get(node_id)
    if not node: return jsonify({"status": "error", "message": "未找到该节点"}), 404
    
    node.command = 'STOP_TASKS'
    node.command_status = 'pending'  # 设置命令状态为待处理
    db.session.commit()
    return jsonify({"status": "success", "message": f"已向节点 {node.node_name} 发送停止指令。"})

@bp.route('/nodes/<int:node_id>/reset', methods=['POST'])
@web_login_required
def reset_node_status(node_id):
    node = BotNode.query.get(node_id)
    if not node: return jsonify({"status": "error", "message": "未找到该节点"}), 404
    
    node.activity_status = 'Idle'
    db.session.commit()
    
    return jsonify({"status": "success", "message": f"节点 {node.node_name} 的Bot状态已重置为待机"})


@bp.route('/nodes/<int:node_id>/regenerate-token', methods=['POST'])
@web_login_required
def regenerate_node_token(node_id):
    """重新生成节点的API Token"""
    try:
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({"status": "error", "message": "节点不存在"}), 404
        
        # 生成新的API Token
        new_token = secrets.token_urlsafe(32)
        token_hash = generate_password_hash(new_token)
        
        # 更新数据库中的token hash
        node.api_token_hash = token_hash
        db.session.commit()
        
        logger.info(f"节点 {node.node_name} 的API Token已重新生成")
        
        return jsonify({
            "status": "success", 
            "message": f"节点 {node.node_name} 的API Token已重新生成",
            "token": new_token
        })
        
    except Exception as e:
        logger.error(f"重新生成API Token失败: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": f"重新生成API Token失败: {str(e)}"}), 500


@bp.route('/nodes/<int:node_id>', methods=['DELETE'])
@web_login_required
def delete_node(node_id):
    try:
        logger.info(f"开始删除节点，ID: {node_id}")
        
        node = BotNode.query.get(node_id)
        if not node:
            logger.warning(f"节点不存在，ID: {node_id}")
            return jsonify({"status": "error", "message": "节点不存在"}), 404
        
        node_name = node.node_name
        logger.info(f"开始删除节点: {node_name} (ID: {node_id})")
        
        # 第一步：清理节点任务（在删除节点前）
        try:
            from .scheduler import clear_node_tasks
            clear_node_tasks(node.id)
            logger.info(f"已清理节点 {node_name} 的任务")
        except Exception as task_error:
            logger.error(f"清理节点 {node_name} 任务时出错: {str(task_error)}")
            # 不阻止删除，继续执行
        
        # 第二步：清理验证码记录（有CASCADE约束，但为了安全先手动删除）
        try:
            from .models import VerificationCode
            verification_count = VerificationCode.query.filter_by(node_id=node.id).count()
            if verification_count > 0:
                VerificationCode.query.filter_by(node_id=node.id).delete()
                db.session.commit()
                logger.info(f"已删除节点 {node_name} 的 {verification_count} 条验证码记录")
        except Exception as verification_error:
            logger.error(f"删除节点 {node_name} 验证码记录时出错: {str(verification_error)}")
            db.session.rollback()
            # 不阻止删除，继续执行
        
        # 第三步：清理节点日志（有CASCADE约束，但为了安全先手动删除）
        try:
            from .models import NodeLog
            log_count = NodeLog.query.filter_by(node_id=node.id).count()
            if log_count > 0:
                NodeLog.query.filter_by(node_id=node.id).delete()
                db.session.commit()
                logger.info(f"已删除节点 {node_name} 的 {log_count} 条日志")
        except Exception as log_error:
            logger.error(f"删除节点 {node_name} 日志时出错: {str(log_error)}")
            db.session.rollback()
            # 不阻止删除，继续执行
        
        # 第四步：清理任务表（有CASCADE约束，但为了安全先手动删除）
        try:
            from .models import Task
            task_count = Task.query.filter_by(node_id=node.id).count()
            if task_count > 0:
                Task.query.filter_by(node_id=node.id).delete()
                db.session.commit()
                logger.info(f"已删除节点 {node_name} 的 {task_count} 个任务")
        except Exception as task_db_error:
            logger.error(f"删除节点 {node_name} 任务记录时出错: {str(task_db_error)}")
            db.session.rollback()
            # 不阻止删除，继续执行
        
        # 第五步：设置关联账户为未分配状态
        try:
            associated_accounts_count = node.accounts.count()
            logger.info(f"节点 {node_name} 关联了 {associated_accounts_count} 个账户")
            
            if associated_accounts_count > 0:
                for account in node.accounts:
                    account.assigned_node_id = None
                db.session.commit()
                logger.info(f"已将 {associated_accounts_count} 个账户设置为未分配状态")
        except Exception as account_error:
            logger.error(f"设置账户未分配状态时出错: {str(account_error)}")
            db.session.rollback()
            return jsonify({"status": "error", "message": f"处理关联账户时出错: {str(account_error)}"}), 500
        
        # 第六步：删除节点本身
        try:
            logger.info(f"准备删除节点 {node_name}")
            db.session.delete(node)
            db.session.commit()
            logger.info(f"节点 {node_name} 删除成功")
        except Exception as delete_error:
            logger.error(f"删除节点 {node_name} 时出错: {str(delete_error)}")
            import traceback
            logger.error(f"删除节点错误堆栈: {traceback.format_exc()}")
            db.session.rollback()
            return jsonify({"status": "error", "message": f"删除节点时出错: {str(delete_error)}"}), 500
        
        # 清理缓存
        clear_cache()
        # 特别清理节点数据缓存
        if 'nodes_data' in _cache:
            del _cache['nodes_data']
        # 强制清理所有缓存
        _cache.clear()
        
        # 返回成功消息
        if associated_accounts_count > 0:
            return jsonify({
                "status": "success", 
                "message": f"节点 {node_name} 已删除，{associated_accounts_count} 个关联账户已设置为未分配状态。"
            })
        else:
            return jsonify({
                "status": "success", 
                "message": f"节点 {node_name} 已删除。"
            })
            
    except Exception as e:
        logger.error(f"删除节点时发生未知错误: {str(e)}")
        import traceback
        logger.error(f"未知错误堆栈: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({"status": "error", "message": f"删除节点时发生未知错误: {str(e)}"}), 500



@bp.route('/bot_accounts', methods=['GET', 'POST'])
@web_login_required
def manage_bot_accounts():
    if request.method == 'GET':
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        
        # 获取筛选参数
        status_filter = request.args.get('status', '')
        node_id_filter = request.args.get('node_id', '')
        email_keyword = request.args.get('email', '')
        
        # 构建缓存键，包含分页和筛选参数
        cache_key = f'bot_accounts_data_{page}_{page_size}_{status_filter}_{node_id_filter}_{email_keyword}'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # 优化查询：使用预加载减少N+1查询
        from .models import UserAgent
        
        # 预加载所有User-Agent映射
        user_agents = {ua.used_by_account_id: ua.id for ua in UserAgent.query.filter(UserAgent.used_by_account_id.isnot(None)).all()}
        
        # 构建查询 - 安全处理 created_at 字段
        try:
            # 先检查 created_at 字段是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('bot_accounts')]
            has_created_at = 'created_at' in columns
            
            if has_created_at:
                # 字段存在，正常查询
                query = db.session.query(BotAccount, Account, BotNode.node_name)\
                    .outerjoin(Account, BotAccount.id == Account.bot_account_id)\
                    .outerjoin(BotNode, BotAccount.assigned_node_id == BotNode.id)
            else:
                # 字段不存在，使用基本查询
                print("Warning: created_at field not found, using basic query")
                query = db.session.query(BotAccount, Account, BotNode.node_name)\
                    .outerjoin(Account, BotAccount.id == Account.bot_account_id)\
                    .outerjoin(BotNode, BotAccount.assigned_node_id == BotNode.id)
        except Exception as e:
            print(f"Error checking created_at field: {e}")
            # 出错时使用基本查询
            query = db.session.query(BotAccount, Account, BotNode.node_name)\
                .outerjoin(Account, BotAccount.id == Account.bot_account_id)\
                .outerjoin(BotNode, BotAccount.assigned_node_id == BotNode.id)
        
        # 应用基本筛选条件
        if status_filter in ['enabled', 'disabled']:
            if status_filter == 'enabled':
                query = query.filter(BotAccount.is_enabled == True)
            elif status_filter == 'disabled':
                query = query.filter(BotAccount.is_enabled == False)
        
        if node_id_filter:
            query = query.filter(BotAccount.assigned_node_id == int(node_id_filter))
        
        if email_keyword:
            query = query.filter(BotAccount.email.contains(email_keyword))
        
        # 对于normal/error筛选，需要特殊处理
        if status_filter in ['normal', 'error']:
            # 先获取所有数据，然后在内存中筛选
            all_accounts = query.order_by(BotAccount.email).all()
            
            # 筛选数据
            filtered_accounts = []
            for acc, monitoring_data, node_name in all_accounts:
                user_agent_id = user_agents.get(acc.id)
                
                # 检查账户状态
                has_error = False
                if acc.is_enabled and monitoring_data and monitoring_data.status_details:
                    try:
                        status_details = json.loads(monitoring_data.status_details)
                        pc_status = status_details.get('pc', {}).get('status', False)
                        mobile_status = status_details.get('mobile', {}).get('status', False)
                        if not pc_status or not mobile_status:
                            has_error = True
                    except:
                        has_error = True
                elif acc.is_enabled:
                    has_error = True  # 启用但没有状态信息
                
                # 应用normal/error筛选
                if status_filter == 'normal':
                    # 正常：启用且没有错误
                    if acc.is_enabled and not has_error:
                        filtered_accounts.append((acc, monitoring_data, node_name, user_agent_id))
                elif status_filter == 'error':
                    # 异常：启用但有错误
                    if acc.is_enabled and has_error:
                        filtered_accounts.append((acc, monitoring_data, node_name, user_agent_id))
            
            # 计算分页
            total_count = len(filtered_accounts)
            offset = (page - 1) * page_size
            accounts = filtered_accounts[offset:offset + page_size]
            
        else:
            # 普通筛选，直接在数据库层面分页
            total_count = query.count()
            offset = (page - 1) * page_size
            accounts = query.order_by(BotAccount.email).offset(offset).limit(page_size).all()
            # 为普通查询添加user_agent_id
            accounts = [(acc, monitoring_data, node_name, user_agents.get(acc.id)) for acc, monitoring_data, node_name in accounts]
        
        accounts_data = []
        for acc, monitoring_data, node_name, user_agent_id in accounts:
            acc_dict = {
                "id": acc.id, "email": acc.email, "password": acc.password,
                "auxiliary_email": acc.auxiliary_email,
                "proxy": json.loads(acc.proxy or '{}'),
                "userAgents": json.loads(acc.user_agents or '{}'),
                "user_agent_id": user_agent_id,
                "hotSearchEndpoints": json.loads(acc.hot_search_endpoints or '[]'),
                "assigned_node_id": acc.assigned_node_id,
                "assigned_node_name": node_name,
                "is_enabled": acc.is_enabled,
                "created_at": acc.created_at.isoformat() if hasattr(acc, 'created_at') and acc.created_at else None,
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
        
        # 返回Layui表格期望的格式
        result = {
            "code": 0,
            "msg": "",
            "count": total_count,
            "data": accounts_data
        }
        
        # 缓存结果
        set_cached_data(cache_key, result)
        return jsonify(result)

    if request.method == 'POST':
            # 清除相关缓存
            clear_cache()
            
            data = request.get_json()
            email = data.get('email')
            try:
                account = BotAccount.query.filter_by(email=email).first()
                if not account:
                    account = BotAccount(email=email, is_enabled=True)
                    db.session.add(account)
                    db.session.flush()  # 刷新以获取id
                    # 创建对应的Account记录
                    new_account = Account(bot_account_id=account.id, total_points=0, daily_gain=0)
                    db.session.add(new_account)
                else:
                    db.session.add(account)

                # 处理密码字段：完全移除密码验证，允许空密码
                password = data.get('password')
                if password:  # 如果密码不为空，则更新密码
                    account.password = password
                # 完全移除密码验证，允许空密码
                
                account.auxiliary_email = data.get('auxiliary_email')
                account.proxy = json.dumps(data.get('proxy', {}))
                account.hot_search_endpoints = json.dumps(data.get('hotSearchEndpoints', []))
                account.assigned_node_id = data.get('assigned_node_id')
                
                # 处理User-Agent分配
                user_agent_id = data.get('user_agent_id')
                
                # 先释放当前账户使用的User-Agent
                from .models import UserAgent
                current_user_agent = UserAgent.query.filter_by(used_by_account_id=account.id).first()
                if current_user_agent:
                    current_user_agent.is_used = False
                    current_user_agent.used_by_account_id = None
                
                if user_agent_id and user_agent_id != 'custom':
                    # 如果选择了预定义的User-Agent
                    user_agent = UserAgent.query.get(user_agent_id)
                    if user_agent and not user_agent.is_used:
                        # 分配User-Agent给账户
                        user_agent.is_used = True
                        user_agent.used_by_account_id = account.id
                        # 设置账户的User-Agent
                        account.user_agents = json.dumps({
                            'desktop': user_agent.desktop_ua,
                            'mobile': user_agent.mobile_ua
                        })
                    else:
                        return jsonify({"status": "error", "message": "选择的User-Agent不可用或已被使用"}), 400
                else:
                    # 使用自定义User-Agent
                    account.user_agents = json.dumps(data.get('userAgents', {}))
                
                db.session.commit()
                return jsonify({"status": "success", "message": "Account saved."})
            except Exception as e:
                db.session.rollback()
                return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/bot_accounts/<int:account_id>/toggle', methods=['POST'])
@web_login_required
def toggle_bot_account(account_id):
    try:
        # 查找账户
        print(f"尝试切换账户状态，账户ID: {account_id}")
        account = BotAccount.query.get(account_id)
        if not account:
            print(f"未找到账户: {account_id}")
            return jsonify({"status": "error", "message": "未找到该账户"}), 404
        
        # 记录原始状态
        original_status = account.is_enabled
        print(f"账户 {account.email} (ID: {account_id}) 原始状态: {original_status}")
        
        # 切换状态
        account.is_enabled = not account.is_enabled
        status_text = "启用" if account.is_enabled else "禁用"
        print(f"账户状态切换为: {account.is_enabled}")
        
        # 提交更改
        db.session.commit()
        print(f"数据库更改已提交")
        
        # 验证更改是否生效
        updated_account = BotAccount.query.get(account_id)
        print(f"验证更改: 切换后状态为 {updated_account.is_enabled}")
        
        return jsonify({"status": "success", "message": f"账户已{status_text}", "is_enabled": updated_account.is_enabled})
    except Exception as e:
        db.session.rollback()
        print(f"切换账户状态时出错: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/bot_accounts/<int:account_id>', methods=['GET', 'DELETE'])
@web_login_required
def manage_single_bot_account(account_id):
    if request.method == 'GET':
        # 获取单个账户信息
        try:
            account = BotAccount.query.get(account_id)
            if not account:
                return jsonify({"status": "error", "message": "Account not found"}), 404
            
            # 获取关联的监控数据
            monitoring_data = None
            if hasattr(account, 'monitoring_data') and account.monitoring_data:
                monitoring_data = {
                    'total_points': account.monitoring_data.total_points,
                    'daily_gain': account.monitoring_data.daily_gain,
                    'desktop_gain': account.monitoring_data.desktop_gain,
                    'mobile_gain': account.monitoring_data.mobile_gain,
                    'last_updated': account.monitoring_data.last_updated.isoformat() if account.monitoring_data.last_updated else None,
                    'status_details': account.monitoring_data.status_details
                }
            
            # 获取分配的节点信息
            node_info = None
            if account.assigned_node_id:
                node = BotNode.query.get(account.assigned_node_id)
                if node:
                    node_info = {
                        'id': node.id,
                        'name': node.node_name
                    }
            
            account_data = {
                'id': account.id,
                'email': account.email,
                'password': account.password,
                'auxiliary_email': account.auxiliary_email,
                'proxy': account.proxy,
                'user_agents': account.user_agents,
                'hot_search_endpoints': account.hot_search_endpoints,
                'assigned_node_id': account.assigned_node_id,
                'status': account.status,
                'is_enabled': account.is_enabled,
                'monitoring_data': monitoring_data,
                'node_info': node_info
            }
            
            return jsonify({"status": "success", "data": account_data})
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    elif request.method == 'DELETE':
        # 删除账户
        try:
            account = BotAccount.query.get(account_id)
            if account:
                # 释放该账户使用的User-Agent
                from .models import UserAgent
                user_agent = UserAgent.query.filter_by(used_by_account_id=account.id).first()
                if user_agent:
                    user_agent.is_used = False
                    user_agent.used_by_account_id = None
                
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
        return jsonify([{ "id": c.id, "url": c.url, "notify_on_node_online": c.notify_on_node_online, "notify_on_node_offline": c.notify_on_node_offline, "notify_on_account_error": c.notify_on_account_error, "notify_on_verification_code": c.notify_on_verification_code } for c in configs])

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
        # 处理布尔值转换，确保正确转换为布尔类型
        config.notify_on_node_online = bool(data.get('notify_on_node_online', False))
        config.notify_on_node_offline = bool(data.get('notify_on_node_offline', False))
        config.notify_on_account_error = bool(data.get('notify_on_account_error', False))
        config.notify_on_verification_code = bool(data.get('notify_on_verification_code', False))
        
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

@bp.route('/nodes/<int:node_id>/logs', methods=['GET'])
@web_login_required
def get_node_logs(node_id):
    """获取指定节点的日志"""
    try:
        # 验证节点是否存在
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({"status": "error", "message": "未找到该节点"}), 404
        
        # 获取查询参数
        level = request.args.get('level', '')
        title = request.args.get('title', '')
        limit = int(request.args.get('limit', 100))
        
        # 构建查询
        from .models import NodeLog
        query = NodeLog.query.filter_by(node_id=node_id)
        
        if level:
            query = query.filter(NodeLog.level == level)
        
        if title:
            query = query.filter(NodeLog.title.contains(title))
        
        # 按时间倒序排列并限制数量
        logs = query.order_by(NodeLog.timestamp.desc()).limit(limit).all()
        
        # 转换为JSON格式
        logs_data = []
        for log_entry in logs:
            logs_data.append({
                'id': log_entry.id,
                'timestamp': log_entry.timestamp.isoformat(),
                'level': log_entry.level,
                'platform': log_entry.platform,
                'title': log_entry.title,
                'message': log_entry.message,
                'pid': log_entry.pid
            })
        
        return jsonify({
            "status": "success",
            "node_name": node.node_name,
            "logs": logs_data,
            "total": len(logs_data)
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/nodes/<int:node_id>/logs/clear', methods=['POST'])
@web_login_required
def clear_node_logs(node_id):
    """清空指定节点的日志"""
    try:
        # 验证节点是否存在
        node = BotNode.query.get(node_id)
        if not node:
            return jsonify({"status": "error", "message": "未找到该节点"}), 404
        
        # 删除该节点的所有日志
        from .models import NodeLog
        deleted_count = NodeLog.query.filter_by(node_id=node_id).delete()
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"已清空节点 {node.node_name} 的 {deleted_count} 条日志"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# 移动端积分数据接口（完全免登录，无需Token认证）
@bp.route('/mobile/get_points', methods=['GET'])
def mobile_get_points():
    # 直接获取所有账户的积分数据，无需Token认证，与账户管理页面保持一致
    accounts = BotAccount.query.order_by(BotAccount.email).all()
    points_data = []
    
    for acc in accounts:
        monitoring_data = acc.monitoring_data
        
        # 计算积分价值
        total_value = monitoring_data.total_points / 179.25 if monitoring_data and monitoring_data.total_points else 0
        daily_value = monitoring_data.daily_gain / 179.25 if monitoring_data and monitoring_data.daily_gain else 0
        
        # 检查数据是否过期（超过24小时）
        last_updated = None
        is_stale = False
        
        if monitoring_data and monitoring_data.last_updated:
            try:
                # 尝试处理字符串格式的时间
                if isinstance(monitoring_data.last_updated, str):
                    last_updated = datetime.fromisoformat(monitoring_data.last_updated.replace('Z', '+00:00'))
                # 尝试处理整数时间戳
                elif isinstance(monitoring_data.last_updated, (int, float)):
                    last_updated = datetime.fromtimestamp(monitoring_data.last_updated, tz=timezone.utc)
                # 如果已经是datetime对象
                elif isinstance(monitoring_data.last_updated, datetime):
                    last_updated = monitoring_data.last_updated
                
                if last_updated:
                    # 确保两个时间都是时区感知的
                    now_utc = datetime.now(timezone.utc)
                    if last_updated.tzinfo is None:
                        # 如果last_updated没有时区信息，假设为UTC
                        last_updated = last_updated.replace(tzinfo=timezone.utc)
                    time_diff = now_utc - last_updated
                    is_stale = time_diff.total_seconds() > 86400  # 24小时
            except Exception as e:
                # 如果时间解析失败，记录错误但不影响其他功能
                current_app.logger.warning(f"Failed to parse last_updated for account {acc.email}: {e}")
                is_stale = True  # 解析失败时标记为过期
        
        # 从status_details中解析状态信息，与账户管理页面保持一致
        status_details = {}
        if monitoring_data and monitoring_data.status_details:
            try:
                status_details = json.loads(monitoring_data.status_details)
            except:
                status_details = {}
        
        # 根据status_details和启用状态确定显示状态
        if not acc.is_enabled:
            desktop_status = '禁用'
            mobile_status = '禁用'
        else:
            # 优先使用monitoring_data.status_details中的真实状态
            # 从status_details中获取状态信息（注意：键名是'pc'而不是'desktop'）
            desktop_status_raw = status_details.get('pc', {}).get('status', False)
            mobile_status_raw = status_details.get('mobile', {}).get('status', False)
            
            # 解析桌面端状态
            if desktop_status_raw:
                desktop_status = '正常'
            else:
                # 检查具体的错误信息
                desktop_error = status_details.get('pc', {}).get('error', '')
                if '需要验证' in desktop_error:
                    desktop_status = '需要验证'
                elif '密码错误' in desktop_error:
                    desktop_status = '密码错误'
                elif '已锁定' in desktop_error:
                    desktop_status = '已锁定'
                elif '登录失败' in desktop_error:
                    desktop_status = '登录失败'
                else:
                    desktop_status = '异常'
            
            # 解析移动端状态
            if mobile_status_raw:
                mobile_status = '正常'
            else:
                # 检查具体的错误信息
                mobile_error = status_details.get('mobile', {}).get('error', '')
                if '需要验证' in mobile_error:
                    mobile_status = '需要验证'
                elif '密码错误' in mobile_error:
                    mobile_status = '密码错误'
                elif '已锁定' in mobile_error:
                    mobile_status = '已锁定'
                elif '登录失败' in mobile_error:
                    mobile_status = '登录失败'
                else:
                    mobile_status = '异常'
        
        points_data.append({
            'email': acc.email,
            'total_points': monitoring_data.total_points if monitoring_data else None,
            'daily_gain': monitoring_data.daily_gain if monitoring_data else None,
            'desktop_gain': monitoring_data.desktop_gain if monitoring_data else None,
            'mobile_gain': monitoring_data.mobile_gain if monitoring_data else None,
            'total_value': round(total_value, 2),
            'daily_value': round(daily_value, 2),
            'node_name': acc.node.node_name if acc.node else None,
            'last_updated': monitoring_data.last_updated if monitoring_data else None,
            'is_stale': is_stale,
            'desktop_status': desktop_status,
            'mobile_status': mobile_status
        })
    
    return jsonify(points_data)

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
            "message": f"获取壁纸失败: {str(e)}"
        }), 500