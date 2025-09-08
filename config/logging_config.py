"""
日志配置文件
统一管理应用日志输出，控制日志大小和级别
"""
import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    """配置应用日志"""
    
    # 创建logs目录
    log_dir = os.path.join(app.instance_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志级别
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器 - 只显示WARNING及以上级别
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 - 轮转日志，每个文件最大10MB，保留5个文件
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志文件 - 只记录ERROR及以上级别
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'error.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # 特定模块的日志级别控制
    module_loggers = {
        'werkzeug': logging.WARNING,  # Flask开发服务器日志
        'urllib3': logging.WARNING,   # HTTP请求日志
        'requests': logging.WARNING,  # 请求库日志
        'psutil': logging.WARNING,    # 系统监控日志
        'apscheduler': logging.WARNING,  # 调度器日志
        'eventlet': logging.WARNING,  # WebSocket日志
        'socketio': logging.WARNING,  # SocketIO日志
    }
    
    for module, level in module_loggers.items():
        logging.getLogger(module).setLevel(level)
    
    # 应用特定日志记录器
    app_logger = logging.getLogger('mic-bot-service')
    app_logger.setLevel(logging.INFO)
    
    # 数据库升级日志记录器
    db_logger = logging.getLogger('database_upgrader')
    db_logger.setLevel(logging.INFO)
    
    # 推送服务日志记录器
    push_logger = logging.getLogger('push_service')
    push_logger.setLevel(logging.INFO)
    
    app.logger.info(f"日志系统已初始化 - 级别: {log_level}")
    app.logger.info(f"日志文件目录: {log_dir}")
    
    return app_logger

def get_logger(name):
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)

def log_system_info(logger):
    """记录系统信息（仅在启动时记录一次）"""
    import psutil
    import platform
    
    logger.info("=" * 50)
    logger.info("系统信息:")
    logger.info(f"  操作系统: {platform.system()} {platform.release()}")
    logger.info(f"  Python版本: {platform.python_version()}")
    logger.info(f"  CPU核心数: {psutil.cpu_count()}")
    logger.info(f"  内存总量: {psutil.virtual_memory().total / (1024**3):.1f}GB")
    logger.info(f"  磁盘总量: {psutil.disk_usage('/').total / (1024**3):.1f}GB")
    logger.info("=" * 50)

def cleanup_old_logs(log_dir, days=7):
    """清理超过指定天数的旧日志文件"""
    import glob
    import time
    
    logger = get_logger('mic-bot-service')
    
    try:
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        log_files = glob.glob(os.path.join(log_dir, "*.log*"))
        cleaned_count = 0
        
        for log_file in log_files:
            if os.path.getmtime(log_file) < cutoff_time:
                os.remove(log_file)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个旧日志文件")
            
    except Exception as e:
        logger.warning(f"清理旧日志文件失败: {e}")
