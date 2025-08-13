from .db import db

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
    command = db.Column(db.String(50), nullable=True)
    command_status = db.Column(db.String(50), nullable=True, default=None)  # pending, received, executed
    last_seen = db.Column(db.String(255))
    heartbeat_timeout = db.Column(db.Integer, default=600)
    ip_address = db.Column(db.String(45))
    cron_schedule = db.Column(db.String(255), default='10 9,13,19 * * *')
    min_sleep_minutes = db.Column(db.Integer, default=5)
    max_sleep_minutes = db.Column(db.Integer, default=20)
    clusters = db.Column(db.Integer, default=1)
    search_delay_min = db.Column(db.String(10), default='30s')
    search_delay_max = db.Column(db.String(10), default='2min')
    accounts = db.relationship('BotAccount', backref='node', lazy='dynamic')

class BotAccount(db.Model):
    __tablename__ = 'bot_accounts'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))
    proxy = db.Column(db.Text)
    user_agents = db.Column(db.Text)
    hot_search_endpoints = db.Column(db.Text)
    assigned_node_id = db.Column(db.Integer, db.ForeignKey('bot_nodes.id'))
    status = db.Column(db.Integer, default=1)
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
    last_updated = db.Column(db.String(255))
    node_name = db.Column(db.String(255))
    status_details = db.Column(db.Text)

class PushConfig(db.Model):
    __tablename__ = 'push_configs'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, nullable=False)
    notify_on_node_online = db.Column(db.Boolean, default=False)
    notify_on_node_offline = db.Column(db.Boolean, default=False)
    notify_on_account_error = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=1)