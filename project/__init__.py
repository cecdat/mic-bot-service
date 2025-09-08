from flask import Flask
import os
from . import scheduler
import atexit

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-should-be-changed'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'postgresql+psycopg2://user:password@db:5432/rewards_db?client_encoding=utf8'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # 配置日志系统
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.logging_config import setup_logging, log_system_info, cleanup_old_logs
    setup_logging(app)
    log_system_info(app.logger)
    
    # 清理旧日志文件
    cleanup_old_logs(os.path.join(app.instance_path, 'logs'))

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 初始化数据库
    from . import db
    db.init_app(app)

    # 注册蓝图
    from . import api_bot
    app.register_blueprint(api_bot.bp)
    
    from . import api_web
    app.register_blueprint(api_web.bp)
    
    from . import api_verification
    app.register_blueprint(api_verification.bp)
    
    from . import api_user_agents
    app.register_blueprint(api_user_agents.bp)
    
    from . import api_push
    app.register_blueprint(api_push.bp)

    from . import frontend
    app.register_blueprint(frontend.bp)
    
    # 注册命令行工具
    from . import commands
    app.cli.add_command(commands.add_user_command)

    # 初始化调度器
    scheduler.init_scheduler(app)
    
    # 确保在应用退出时关闭调度器
    atexit.register(scheduler.shutdown_scheduler)
    
    return app
