from .db import db

from datetime import datetime, timezone, timedelta

class WebUser(db.Model):
    __tablename__ = 'web_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    status = db.Column(db.Integer, default=1)

class BotNode(db.Model):
    __tablename__ = 'bot_nodes'
    id = db.Column(db.Integer, primary_key=True)
    node_name = db.Column(db.String(255), unique=True, nullable=False)
    api_token_hash = db.Column(db.Text, nullable=False)
    status = db.Column(db.Integer, default=1)
    activity_status = db.Column(db.String(50), default='Idle')
    status_updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # 状态更新时间
    command = db.Column(db.String(50), nullable=True)
    command_status = db.Column(db.String(50), nullable=True, default=None)  # pending, received, executed
    command_data = db.Column(db.Text, nullable=True)  # 存储命令相关数据(JSON格式)
    last_seen = db.Column(db.DateTime)
    heartbeat_timeout = db.Column(db.Integer, default=600)
    ip_address = db.Column(db.String(45))
    cron_schedule = db.Column(db.String(255), default='10 9,13,19 * * *')
    min_sleep_minutes = db.Column(db.Integer, default=5)
    max_sleep_minutes = db.Column(db.Integer, default=20)
    clusters = db.Column(db.Integer, default=1)
    search_delay_min = db.Column(db.String(10), default='30s')
    search_delay_max = db.Column(db.String(10), default='2min')
    # 日志推送相关字段
    log_push_enabled = db.Column(db.Boolean, default=False)
    log_push_interval = db.Column(db.Integer, default=30)
    accounts = db.relationship('BotAccount', backref='node', lazy='dynamic')

class BotAccount(db.Model):
    __tablename__ = 'bot_accounts'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))
    auxiliary_email = db.Column(db.String(255))  # 辅助邮箱，用于接收验证码
    proxy = db.Column(db.Text)
    user_agents = db.Column(db.Text)
    hot_search_endpoints = db.Column(db.Text)
    assigned_node_id = db.Column(db.Integer, db.ForeignKey('bot_nodes.id'))
    status = db.Column(db.Integer, default=1)
    is_enabled = db.Column(db.Boolean, default=True)  # 账户启用状态，默认为True
    created_at = db.Column(db.DateTime, nullable=True, default=db.func.current_timestamp())  # 创建时间
    monitoring_data = db.relationship('Account', backref='bot_account', uselist=False, cascade="all, delete-orphan")

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    bot_account_id = db.Column(db.Integer, db.ForeignKey('bot_accounts.id'), unique=True, nullable=False)
    total_points = db.Column(db.Integer)
    daily_gain = db.Column(db.Integer)
    # [新增] 分别记录桌面和移动端收益
    desktop_gain = db.Column(db.Integer, default=0)
    mobile_gain = db.Column(db.Integer, default=0)
    # 修复：将last_updated改为Text类型以支持ISO格式时间戳
    last_updated = db.Column(db.Text)
    node_name = db.Column(db.String(255))
    status_details = db.Column(db.Text)

class AccountPointsHistory(db.Model):
    __tablename__ = 'account_points_history'
    id = db.Column(db.Integer, primary_key=True)
    bot_account_id = db.Column(db.Integer, db.ForeignKey('bot_accounts.id'), nullable=False)
    total_points = db.Column(db.Integer, nullable=False)
    daily_gain = db.Column(db.Integer, default=0)
    desktop_gain = db.Column(db.Integer, default=0)
    mobile_gain = db.Column(db.Integer, default=0)
    record_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    bot_account = db.relationship('BotAccount', backref='points_history')

class PushConfig(db.Model):
    __tablename__ = 'push_configs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='配置名称')
    channel = db.Column(db.String(50), nullable=False, comment='推送渠道')
    is_enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    config_data = db.Column(db.Text, comment='配置数据(JSON格式)')
    notify_on_node_online = db.Column(db.Boolean, default=False)
    notify_on_node_offline = db.Column(db.Boolean, default=False)
    notify_on_account_error = db.Column(db.Boolean, default=False)
    notify_on_verification_code = db.Column(db.Boolean, default=False)
    notify_on_task_completed = db.Column(db.Boolean, default=False)
    notify_on_system_alert = db.Column(db.Boolean, default=False)
    notify_on_task_start = db.Column(db.Boolean, default=False)
    notify_on_task_finish = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'channel': self.channel,
            'is_enabled': self.is_enabled,
            'config_data': json.loads(self.config_data) if self.config_data else {},
            'notify_on_node_online': self.notify_on_node_online,
            'notify_on_node_offline': self.notify_on_node_offline,
            'notify_on_account_error': self.notify_on_account_error,
            'notify_on_verification_code': self.notify_on_verification_code,
            'notify_on_task_completed': self.notify_on_task_completed,
            'notify_on_system_alert': self.notify_on_system_alert,
            'notify_on_task_start': self.notify_on_task_start,
            'notify_on_task_finish': self.notify_on_task_finish,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(50), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey('bot_nodes.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('bot_accounts.id'))
    status = db.Column(db.String(50), default='pending')  # pending(待下发), issued(已下发), running(运行中), completed(已完成), failed(失败)
    priority = db.Column(db.Integer, default=1)
    # 修复：使用正确的UTC时间默认值
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    execution_time = db.Column(db.DateTime)  # 执行时间 = 调度配置时间 + 随机延时
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    result = db.Column(db.Text)
    error_message = db.Column(db.Text)
    # 外键关系
    node = db.relationship('BotNode', backref=db.backref('tasks', lazy=True))
    account = db.relationship('BotAccount', backref=db.backref('tasks', lazy=True))

class NodeLog(db.Model):
    __tablename__ = 'node_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('bot_nodes.id'), nullable=False)
    node_name = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    level = db.Column(db.String(20), nullable=False)
    platform = db.Column(db.String(50))
    title = db.Column(db.String(255))
    message = db.Column(db.Text)
    pid = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    node = db.relationship('BotNode', backref='logs')


class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('bot_nodes.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)  # 主账户邮箱（正在执行登录的账户）
    auxiliary_email = db.Column(db.String(255), nullable=False)  # 辅助邮箱（用于接收验证码）
    code = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, expired
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.now() + timedelta(minutes=10))
    
    node = db.relationship('BotNode', backref='verification_codes')


class UserAgent(db.Model):
    __tablename__ = 'user_agents'
    id = db.Column(db.Integer, primary_key=True)
    desktop_ua = db.Column(db.Text, nullable=False)  # 桌面端User-Agent
    mobile_ua = db.Column(db.Text, nullable=False)   # 移动端User-Agent
    is_used = db.Column(db.Boolean, default=False)   # 是否已被使用
    used_by_account_id = db.Column(db.Integer, db.ForeignKey('bot_accounts.id'), nullable=True)  # 被哪个账户使用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    used_by_account = db.relationship('BotAccount', backref='user_agent', uselist=False)