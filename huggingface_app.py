#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 部署入口文件
适配 Hugging Face 容器环境
"""

import os
import sys
from project import create_app
from flask_socketio import SocketIO

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['FLASK_ENV'] = 'production'

# Supabase 数据库配置
SUPABASE_URL = "https://svicxyubtwdisddxsoqh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2aWN4eXVidHdkaXNkZHhzb3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzQzNzIsImV4cCI6MjA3MzA1MDM3Mn0.il8strW1UlV47xl9bAlAoizjjiuOHhc8oSNbACpJ90Q"

# 设置数据库连接
# Supabase 连接字符串格式: postgresql://postgres:[password]@[host]:5432/postgres
# 使用 mic_bot 模式而不是默认的 public 模式
os.environ['DATABASE_URL'] = f"postgresql://postgres:{SUPABASE_KEY}@svicxyubtwdisddxsoqh.supabase.co:5432/postgres?options=-csearch_path=mic_bot"
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = SUPABASE_KEY
os.environ['POSTGRES_DB'] = 'postgres'
os.environ['POSTGRES_SCHEMA'] = 'mic_bot'

# 其他环境变量
os.environ['ENABLE_WEBSOCKET'] = 'true'
os.environ['SOCKETIO_ASYNC_MODE'] = 'eventlet'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['HOST_HOSTNAME'] = 'huggingface'

# 创建应用实例
app = create_app()

# 初始化SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    max_http_buffer_size=100000,
    ping_timeout=60,
    ping_interval=30,
    logger=False,
    engineio_logger=False,
    always_connect=False,
    transports=['polling', 'websocket'],
    allow_upgrades=True,
    compression_threshold=1024,
    max_payload_size=500000,
    cookie=False,
    manage_session=False,
    close_timeout=10,
    disconnect_timeout=5
)

# 将socketio实例添加到应用上下文
app.socketio = socketio

# 注册WebSocket事件处理器
from project import websocket_events
websocket_events.register_websocket_events(socketio)

# 数据库初始化
@app.before_first_request
def initialize_database():
    """初始化数据库表结构"""
    try:
        from project.db import db
        from project import models
        
        # 创建所有表
        db.create_all()
        print("✅ 数据库表结构初始化完成")
        
        # 检查是否需要执行基础SQL
        from project.models import db_version
        version_record = db_version.query.first()
        if not version_record:
            print("📝 执行基础数据库结构...")
            # 这里可以执行 base.sql 中的内容
            # 由于 Supabase 可能不支持某些 PostgreSQL 功能，我们使用 SQLAlchemy 创建表
            pass
        else:
            print(f"📊 当前数据库版本: {version_record.version}")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

if __name__ == '__main__':
    # Hugging Face 环境
    port = int(os.environ.get('PORT', 7860))
    host = '0.0.0.0'
    
    print(f"🚀 启动 mic-bot-service 在 {host}:{port}")
    print(f"📊 数据库连接: {os.environ.get('DATABASE_URL', 'Not set')}")
    
    socketio.run(app, host=host, port=port, debug=False)
