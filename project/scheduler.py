from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .db import db
from .models import BotNode
import logging
from datetime import datetime

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
    
    # 启动调度器
    scheduler.start()
    logger.info('调度器已启动')


def load_all_node_tasks():
    """加载所有节点的定时任务"""
    nodes = BotNode.query.all()
    for node in nodes:
        if node.cron_schedule:
            add_node_task(node.id, node.cron_schedule, node.node_name)
        else:
            logger.info(f'节点 {node.node_name} 没有设置cron调度，跳过')


def add_node_task(node_id, cron_expression, node_name):
    """为节点添加定时任务"""
    # 先移除可能存在的同名任务
    job_id = f'node_{node_id}_task'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f'已移除节点 {node_name} 的旧任务')
    
    try:
        # 创建Cron触发器
        trigger = CronTrigger.from_crontab(cron_expression)
        
        # 添加任务
        scheduler.add_job(
            func=trigger_node_job,
            trigger=trigger,
            args=[node_id],
            id=job_id,
            name=f'节点 {node_name} 定时任务',
            replace_existing=True
        )
        logger.info(f'已添加节点 {node_name} 的定时任务，Cron表达式: {cron_expression}')
    except Exception as e:
        logger.error(f'添加节点 {node_name} 的定时任务失败: {str(e)}')


def update_node_task(node_id, new_cron_expression, node_name):
    """更新节点的定时任务"""
    if new_cron_expression:
        add_node_task(node_id, new_cron_expression, node_name)
    else:
        # 如果移除了cron表达式，删除任务
        job_id = f'node_{node_id}_task'
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f'已删除节点 {node_name} 的定时任务')


def trigger_node_job(node_id):
    """定时任务执行函数 - 触发节点运行"""
    global app_instance
    with app_instance.app_context():
        try:
            node = BotNode.query.get(node_id)
            if not node:
                logger.error(f'未找到节点 ID: {node_id}')
                return

            # 检查节点状态
            if node.status != 1:
                logger.warning(f'节点 {node.node_name} 不在线，无法触发任务')
                return

            if node.activity_status != 'Idle':
                logger.warning(f'节点 {node.node_name} 正忙 ({node.activity_status})，无法触发任务')
                return
            
            # 设置节点命令
            node.command = 'RUN_TASKS'
            db.session.commit()
            logger.info(f'已向节点 {node.node_name} 发送触发指令')
        except Exception as e:
            db.session.rollback()
            logger.error(f'触发节点 {node_id} 任务失败: {str(e)}')


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info('调度器已关闭')
        scheduler = None