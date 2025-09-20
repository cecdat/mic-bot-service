# Gunicorn配置文件 - 支持WebSocket的eventlet版本
import multiprocessing

# 服务器套接字
bind = "0.0.0.0:5000"
backlog = 2048

# Worker进程
workers = 1  # eventlet建议使用1个worker
worker_class = "eventlet"
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # 禁用preload避免monkey patching问题

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"  # 改为info级别以显示更多日志
access_log_format = '%(h)s %(t)s "%(r)s" %(s)s %(b)s'  # 简化日志格式

# 进程命名
proc_name = 'mic-bot-service'

# 服务器钩子
def when_ready(server):
    print("🚀 Mic-Bot Service 服务器已准备就绪，正在启动工作进程...")
    server.log.info("🚀 Mic-Bot Service 服务器已准备就绪，正在启动工作进程...")

def worker_int(worker):
    print("⚠️ 工作进程收到 INT 或 QUIT 信号")
    worker.log.info("⚠️ 工作进程收到 INT 或 QUIT 信号")

def pre_fork(server, worker):
    # 在worker进程中执行monkey patching
    import eventlet
    eventlet.monkey_patch()
    print(f"🔧 正在启动工作进程 (PID: {worker.pid})...")
    server.log.info("🔧 正在启动工作进程 (PID: %s)...", worker.pid)

def post_fork(server, worker):
    print(f"✅ 工作进程启动成功 (PID: {worker.pid})")
    print("🌐 Mic-Bot Service 已启动，监听端口 5000")
    print("📊 WebSocket 支持已启用")
    print("🎯 服务已就绪，等待连接...")
    server.log.info("✅ 工作进程启动成功 (PID: %s)", worker.pid)
    server.log.info("🌐 Mic-Bot Service 已启动，监听端口 5000")
    server.log.info("📊 WebSocket 支持已启用")
    server.log.info("🎯 服务已就绪，等待连接...")
