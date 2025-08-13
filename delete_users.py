#!/usr/bin/env python3
# 此脚本应在Docker容器内运行，或确保能访问到MySQL数据库
from project.db import db
from project.models import WebUser
from flask import Flask
import os

# 创建Flask应用实例
app = Flask(__name__)

# 尝试使用环境变量或默认值连接数据库
# 本地测试时，可能需要修改为实际的数据库连接信息
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+mysqlconnector://user:password@127.0.0.1:3306/rewards_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

try:
    with app.app_context():
        # 删除所有用户数据
        users_deleted = WebUser.query.delete()
        db.session.commit()
        print(f'已删除 {users_deleted} 个用户记录')
        
        # 检查是否还有其他表的数据
        from project.models import BotNode, BotAccount, Account, PushConfig
        
        bot_nodes_count = BotNode.query.count()
        bot_accounts_count = BotAccount.query.count()
        accounts_count = Account.query.count()
        push_configs_count = PushConfig.query.count()
        
        print(f'保留的其他数据：')
        print(f'- BotNode: {bot_nodes_count} 条')
        print(f'- BotAccount: {bot_accounts_count} 条')
        print(f'- Account: {accounts_count} 条')
        print(f'- PushConfig: {push_configs_count} 条')
except Exception as e:
    print(f'连接数据库失败: {str(e)}')
    print('请确保MySQL服务器正在运行，并且连接信息正确。')
    print('如果是在Docker外部运行此脚本，可能需要修改数据库连接URL中的主机名为127.0.0.1，并确保数据库端口已映射到主机。')