from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .db import db
from .models import BotNode, Task
import logging
import random
import json
from datetime import datetime, timedelta
from datetime import timezone

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('node_scheduler')

scheduler = None
app_instance = None  # 存储应用实例


def init_scheduler(app):
    """初始化定时任务调度器"""
    global scheduler, app_instance
    app_instance = app  # 保存应用实例
    
    # 如果调度器已存在且正在运行，先停止它
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info('调度器已停止')
    
    # 创建新的调度器
    scheduler = BackgroundScheduler()
    
    # 从数据库加载所有节点的定时任务
    with app.app_context():
        load_all_node_tasks()
        
        # 添加任务表扫描定时任务 (每5分钟执行一次，减少频率)
        scheduler.add_job(
            func=scan_task_table,
            trigger='interval',
            minutes=5,
            id='task_scanner',
            name='任务表扫描器',
            replace_existing=True,
            max_instances=1,  # 限制同时只能有一个实例运行
            misfire_grace_time=60  # 允许60秒的延迟执行
        )
        logger.info('已添加任务表扫描定时任务')
        
        # 添加日志清理定时任务 (每天凌晨2点执行)
        scheduler.add_job(
            func=cleanup_old_logs,
            trigger=CronTrigger(hour=2, minute=0),
            id='log_cleanup',
            name='日志清理任务',
            replace_existing=True
        )
        logger.info('已添加日志清理定时任务')
        
        # 添加每日任务重建定时任务 (每天凌晨1点执行)
        scheduler.add_job(
            func=recreate_daily_tasks,
            trigger=CronTrigger(hour=1, minute=0),
            id='daily_task_recreation',
            name='每日任务重建任务',
            replace_existing=True
        )
        logger.info('已添加每日任务重建定时任务')
        
        # 添加节点离线检测定时任务 (每3分钟执行一次，减少系统负载)
        scheduler.add_job(
            func=check_node_offline_status,
            trigger='interval',
            minutes=3,
            id='node_offline_checker',
            name='节点离线检测器',
            replace_existing=True,
            max_instances=1,  # 限制同时只能有一个实例运行
            misfire_grace_time=30  # 允许30秒的延迟执行
        )
        logger.info('已添加节点离线检测定时任务')
    
    # 启动调度器
    scheduler.start()
    logger.info('调度器已启动')



def load_all_node_tasks():
    """加载所有节点的定时任务"""
    nodes = BotNode.query.all()
    for node in nodes:
        if node.cron_schedule:
            # 清除旧任务
            clear_node_tasks(node.id)
            # 创建新任务
            create_node_tasks(node.id, node.cron_schedule, node.node_name, 
                             node.min_sleep_minutes, node.max_sleep_minutes)
        else:
            logger.info(f'节点 {node.node_name} 没有设置cron调度，跳过')



def clear_node_tasks(node_id):
    """清除节点的所有任务"""
    try:
        # 删除调度器中的任务
        job_id = f'node_{node_id}_task'
        if scheduler and scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f'已移除节点 {node_id} 的调度任务')

        # 注意：数据库中的任务会通过外键约束的 CASCADE 自动删除
        # 这里不需要手动删除，避免与外键约束冲突
        logger.info(f'节点 {node_id} 的数据库任务将通过外键约束自动删除')
            
    except Exception as e:
        logger.error(f'清除节点 {node_id} 任务时发生未知错误: {str(e)}')
        # 不抛出异常，让删除节点操作继续进行


def create_node_tasks(node_id, cron_expression, node_name, min_delay, max_delay):
    """为节点创建多个定时任务"""
    try:
        logger.info(f'解析节点 {node_name} 的cron表达式: {cron_expression}')
        
        # 直接解析cron字符串
        cron_parts = cron_expression.strip().split()
        if len(cron_parts) != 5:
            logger.error(f'无效的cron表达式: {cron_expression}')
            return
        
        minute_part, hour_part, _, _, _ = cron_parts
        
        # 解析小时值
        if hour_part == '*':
            hours = list(range(24))
            logger.info(f'小时字段为通配符*, 使用0-23所有小时')
        else:
            hours = []
            for part in hour_part.split(','):
                try:
                    hours.append(int(part))
                except ValueError as e:
                    logger.error(f'转换小时部分 {part} 失败: {e}')
            logger.info(f'解析得到的小时值: {hours}')
        
        # 解析分钟值
        if minute_part == '*':
            minutes = list(range(60))
            logger.info(f'分钟字段为通配符*, 使用0-59所有分钟')
        else:
            minutes = []
            for part in minute_part.split(','):
                try:
                    minutes.append(int(part))
                except ValueError as e:
                    logger.error(f'转换分钟部分 {part} 失败: {e}')
            logger.info(f'解析得到的分钟值: {minutes}')
        
        # 确保小时和分钟值在有效范围内
        hours = [h for h in hours if 0 <= h <= 23]
        minutes = [m for m in minutes if 0 <= m <= 59]
        logger.info(f'过滤后的小时值: {hours}, 过滤后的分钟值: {minutes}')
            
        # 为每个时间点创建未来3天的任务
        task_count = 0
        for day_offset in range(3):  # 创建未来3天的任务
            for hour in hours:
                for minute in minutes:
                    # 生成随机延迟 (分钟)
                    delay = random.randint(min_delay, max_delay)
                    
                    # 计算任务执行时间
                    now = datetime.now()
                    execution_time = datetime(now.year, now.month, now.day, hour, minute)
                    
                    # 设置为未来第N天
                    execution_time += timedelta(days=day_offset)
                    
                    # 如果今天的执行时间已过，则设置为明天
                    if execution_time < now:
                        execution_time += timedelta(days=1)
                    
                    # 添加延迟
                    execution_time += timedelta(minutes=delay)
                    
                    # 创建任务
                    task = Task(
                        task_type='node_job',
                        node_id=node_id,
                        status='pending',
                        priority=1,
                        execution_time=execution_time,
                        result=json.dumps({
                            'delay': delay
                        })
                    )
                    db.session.add(task)
                    task_count += 1
                    logger.info(f'为节点 {node_name} 创建任务，执行时间: {execution_time}, 延迟: {delay}分钟')
        
        db.session.commit()
        logger.info(f'已为节点 {node_name} 创建 {task_count} 个任务')
    except Exception as e:
        logger.error(f'为节点 {node_name} 创建任务失败: {str(e)}')



def update_node_task(node_id, new_cron_expression, node_name, min_delay, max_delay):
    """更新节点的定时任务"""
    if new_cron_expression:
        # 清除旧任务
        clear_node_tasks(node_id)
        # 创建新任务
        create_node_tasks(node_id, new_cron_expression, node_name, min_delay, max_delay)
    else:
        # 如果移除了cron表达式，删除任务
        clear_node_tasks(node_id)



# 注意：这个函数现在可能不再需要，因为我们改为通过任务表下发任务
# 但为了兼容性保留

def trigger_node_job(node_id):
    """定时任务执行函数 - 触发节点运行"""
    logger.warning('trigger_node_job 函数已弃用，请使用任务表机制')
    return



# 用于跟踪已发送离线推送的节点，避免重复推送
offline_notification_sent = set()

def check_node_offline_status():
    """检查节点离线状态并触发推送"""
    global app_instance, offline_notification_sent
    with app_instance.app_context():
        try:
            from .models import BotNode
            from .push import trigger_push_notification
            from datetime import datetime, timezone
            
            now = datetime.now(timezone.utc)
            offline_nodes = []
            
            # 查询所有在线状态的节点，只获取需要的字段
            online_nodes = BotNode.query.filter_by(status=1).with_entities(
                BotNode.id, BotNode.node_name, BotNode.ip_address, 
                BotNode.last_seen, BotNode.heartbeat_timeout
            ).all()
            
            for node_tuple in online_nodes:
                node_id, node_name, ip_address, last_seen, heartbeat_timeout = node_tuple
                
                if not last_seen:
                    # 如果节点从未签到过，跳过
                    continue
                
                # 计算心跳超时时间
                timeout_seconds = heartbeat_timeout or 600  # 默认10分钟
                
                # 确保时间对象都是timezone-aware
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                
                # 计算时间差
                time_diff = (now - last_seen).total_seconds()
                
                # 如果超过心跳超时时间，标记为离线
                if time_diff > timeout_seconds:
                    logger.info(f'节点 {node_name} 心跳超时，标记为离线 (超时: {time_diff:.0f}秒)')
                    
                    # 更新节点状态为离线
                    node = BotNode.query.get(node_id)
                    if node:
                        node.status = 0
                        node.activity_status = 'Offline'
                        node.status_updated_at = now
                    
                    offline_nodes.append({
                        'node_name': node_name,
                        'ip_address': ip_address,
                        'timeout_seconds': timeout_seconds,
                        'last_seen': last_seen
                    })
            
            # 提交数据库更改
            if offline_nodes:
                db.session.commit()
                logger.info(f'检测到 {len(offline_nodes)} 个节点离线')
                
                # 为每个离线节点发送推送通知（避免重复推送）
                for node_info in offline_nodes:
                    node_key = f"offline_{node_info['node_name']}"
                    
                    # 检查是否已经发送过离线推送
                    if node_key not in offline_notification_sent:
                        try:
                            push_title = f"🔴 {node_info['node_name']} 节点离线"
                            push_content = f"📱 节点: {node_info['node_name']}\n"
                            push_content += f"🌐 IP地址: {node_info['ip_address'] or '未知'}\n"
                            push_content += f"💓 最后心跳: {node_info['last_seen'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                            push_content += f"⏱️ 超时时间: {node_info['timeout_seconds']}秒\n"
                            push_content += f"❌ 状态: 离线"
                            
                            trigger_push_notification('node_offline', push_title, push_content)
                            offline_notification_sent.add(node_key)
                            logger.info(f'已发送节点离线推送: {node_info["node_name"]}')
                        except Exception as push_error:
                            logger.error(f'发送节点离线推送失败: {push_error}')
                    else:
                        logger.debug(f'节点 {node_info["node_name"]} 离线推送已发送过，跳过')
            else:
                logger.debug('所有节点都在线')
                
            # 清理已重新上线的节点的离线推送记录
            # 查询所有离线状态的节点
            offline_nodes_in_db = BotNode.query.filter_by(status=0).all()
            for node in offline_nodes_in_db:
                node_key = f"offline_{node.node_name}"
                if node_key in offline_notification_sent:
                    # 如果节点重新上线，移除离线推送记录
                    if node.last_seen:
                        last_seen = node.last_seen
                        if last_seen.tzinfo is None:
                            last_seen = last_seen.replace(tzinfo=timezone.utc)
                        
                        time_diff = (now - last_seen).total_seconds()
                        timeout_seconds = node.heartbeat_timeout or 600
                        
                        # 如果节点在超时时间内有新的心跳，说明重新上线了
                        if time_diff <= timeout_seconds:
                            offline_notification_sent.discard(node_key)
                            logger.info(f'节点 {node.node_name} 重新上线，清除离线推送记录')
                
        except Exception as e:
            logger.error(f'检查节点离线状态时出错: {e}')
            db.session.rollback()

def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info('调度器已关闭')


def scan_task_table():
    """扫描任务表，推送待下发任务到节点"""
    global app_instance
    with app_instance.app_context():
        try:
            # 查询所有待下发的任务（排除已完成、失败和已下发的任务）
            pending_tasks = Task.query.filter(
                Task.status.in_(['pending'])
            ).all()
            logger.info(f'找到 {len(pending_tasks)} 个待下发任务')

            for task in pending_tasks:
                # 直接使用任务的execution_time字段
                execution_time = task.execution_time
                
                # 检查是否到了执行时间
                if datetime.now() < execution_time:
                    continue
                
                # 检查节点是否存在且在线
                node = BotNode.query.get(task.node_id)
                if not node:
                    logger.error(f'任务 {task.id} 对应的节点不存在，更新任务状态为失败')
                    task.status = 'failed'
                    task.error_message = '节点不存在'
                    db.session.commit()
                    continue

                if node.status != 1:
                    logger.warning(f'任务 {task.id} 对应的节点 {node.node_name} 不在线，跳过')
                    continue

                # 检查是否有启用状态的账户
                from .models import BotAccount
                enabled_accounts = BotAccount.query.filter_by(assigned_node_id=node.id, is_enabled=True).all()
                if not enabled_accounts:
                    logger.warning(f'节点 {node.node_name} 没有启用的账户，跳过任务 {task.id}')
                    task.status = 'failed'
                    task.error_message = '节点没有启用的账户'
                    db.session.commit()
                    continue

                # 使用数据库锁防止重复处理
                # 先尝试更新任务状态，如果更新失败说明已被其他进程处理
                try:
                    # 使用原子更新操作，确保只有一个进程能成功更新
                    updated_rows = Task.query.filter(
                        Task.id == task.id,
                        Task.status == 'pending'  # 只更新状态为pending的任务
                    ).update({
                        'status': 'issued',
                        'started_at': datetime.now(timezone.utc)
                    })
                    
                    if updated_rows == 0:
                        logger.warning(f'任务 {task.id} 已被其他进程处理，跳过')
                        continue
                    
                    db.session.commit()
                    logger.info(f'任务 {task.id} 状态已更新为已下发')
                except Exception as e:
                    logger.error(f'更新任务 {task.id} 状态失败: {e}')
                    db.session.rollback()
                    continue

                # 推送任务到节点
                logger.info(f'任务 {task.id} 已下发到节点 {node.node_name}，执行时间: {execution_time}')
                
                # 注意：任务开始推送已移至websocket_events.py的task_status_update中
                # 当节点上报status='executing'时才发送推送，避免下发就推送的问题
                
                # 准备任务数据
                task_data = {
                    'task_id': task.id,
                    'task_type': task.task_type,
                    'params': {}
                }
                
                # 将任务设置为节点命令
                node.command = 'RUN_TASKS'
                node.command_status = 'pending'
                node.command_data = json.dumps(task_data)
                db.session.commit()
                logger.info(f'已为节点 {node.node_name} 设置任务命令')
                
                # 通过WebSocket发送任务到节点
                try:
                    from . import websocket_events
                    success = websocket_events.send_task_to_node(node.id, 'RUN_TASKS', task_data)
                    if success:
                        logger.debug(f'已通过WebSocket向节点 {node.node_name} 发送任务 {task.id}')
                    else:
                        logger.warning(f'WebSocket发送任务失败，节点 {node.node_name} 可能不在线')
                except Exception as ws_error:
                    logger.error(f'WebSocket发送任务时出错: {ws_error}')
                    # 继续执行，不阻止任务处理
                
        except Exception as e:
            logger.error(f'扫描任务表失败: {str(e)}')


def reset_node_tasks(node_id):
    """重置节点的运行中任务为待下发状态"""
    with app_instance.app_context():
        try:
            node = BotNode.query.get(node_id)
            if not node:
                logger.error(f'未找到节点 ID: {node_id}')
                return

            # 查询节点的所有已下发和运行中的任务
            running_tasks = Task.query.filter(
                Task.node_id == node_id,
                Task.status.in_(['issued', 'running'])
            ).all()

            for task in running_tasks:
                # 重置为待下发状态
                task.status = 'pending'
                task.error_message = '节点状态变为running，任务重置'
                db.session.commit()
                logger.info(f'已重置节点 {node.node_name} 的任务 {task.id} 为待下发状态')

        except Exception as e:
            logger.error(f'重置节点任务失败: {str(e)}')


def recreate_daily_tasks():
    """每日重新创建所有节点的定时任务"""
    global app_instance
    with app_instance.app_context():
        try:
            logger.info('开始执行每日任务重建...')
            
            # 清除所有过期任务
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            
            expired_tasks = Task.query.filter(Task.execution_time < yesterday).all()
            for task in expired_tasks:
                db.session.delete(task)
            
            if expired_tasks:
                db.session.commit()
                logger.info(f'已清除 {len(expired_tasks)} 个过期任务')
            
            # 重新加载所有节点的任务
            load_all_node_tasks()
            logger.info('每日任务重建完成')
            
        except Exception as e:
            logger.error(f'每日任务重建失败: {str(e)}')


def cleanup_old_logs():
    """清理2天前的日志"""
    global app_instance
    with app_instance.app_context():
        try:
            from .models import NodeLog
            from sqlalchemy import text
            
            # 执行数据库清理函数
            result = db.session.execute(text('SELECT cleanup_old_logs()'))
            deleted_count = result.scalar()
            
            logger.info(f'日志清理完成，删除了 {deleted_count} 条过期日志')
            
        except Exception as e:
            logger.error(f'日志清理失败: {str(e)}')