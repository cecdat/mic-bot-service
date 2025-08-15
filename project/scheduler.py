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
        
        # 添加任务表扫描定时任务 (每分钟执行一次)
        scheduler.add_job(
            func=scan_task_table,
            trigger='interval',
            minutes=1,
            id='task_scanner',
            name='任务表扫描器',
            replace_existing=True
        )
        logger.info('已添加任务表扫描定时任务')
    
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
    # 删除调度器中的任务
    job_id = f'node_{node_id}_task'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f'已移除节点 {node_id} 的调度任务')

    # 删除数据库中的任务
    tasks = Task.query.filter_by(node_id=node_id).all()
    for task in tasks:
        db.session.delete(task)
    db.session.commit()
    logger.info(f'已清除节点 {node_id} 的 {len(tasks)} 个任务')


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
            
        # 为每个时间点创建一个任务
        task_count = 0
        for hour in hours:
            for minute in minutes:
                # 生成随机延迟 (分钟)
                delay = random.randint(min_delay, max_delay)
                
                # 计算任务执行时间
                now = datetime.now()
                execution_time = datetime(now.year, now.month, now.day, hour, minute)
                
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
            # 查询所有待下发的任务
            pending_tasks = Task.query.filter_by(status='pending').all()
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

                # 更新任务状态为已下发
                task.status = 'issued'
                # 修复：使用正确的UTC时间
                task.started_at = datetime.now(timezone.utc)
                db.session.commit()

                # 推送任务到节点
                logger.info(f'任务 {task.id} 已下发到节点 {node.node_name}，执行时间: {execution_time}')
                
                # 准备任务数据
                task_data = {
                    'task_id': task.id,
                    'task_type': task.task_type,
                    'params': {}
                }
                
                # 将任务设置为节点命令
                node.command = 'RUN_TASK'
                node.command_status = 'pending'
                node.command_data = json.dumps(task_data)
                db.session.commit()
                logger.info(f'已为节点 {node.node_name} 设置任务命令')
                
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