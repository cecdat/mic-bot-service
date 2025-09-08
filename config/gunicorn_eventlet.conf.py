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
loglevel = "warning"  # 减少日志级别
access_log_format = '%(h)s %(t)s "%(r)s" %(s)s %(b)s'  # 简化日志格式

# 进程命名
proc_name = 'mic-bot-service'

# 服务器钩子
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    # 在worker进程中执行monkey patching
    import eventlet
    eventlet.monkey_patch()
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
