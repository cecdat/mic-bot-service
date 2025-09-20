import os
from project import create_app
from flask_socketio import SocketIO

# 设置环境变量确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 应用工厂创建应用实例
print("🚀 正在启动 Mic-Bot Service...")
app = create_app()

# 初始化SocketIO
# 根据环境变量选择async_mode
import os
async_mode = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading')
print(f"🔌 正在初始化 SocketIO (模式: {async_mode})...")
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode=async_mode,
    max_http_buffer_size=100000,  # 减少HTTP缓冲区大小到100KB
    ping_timeout=60,  # ping超时时间1分钟
    ping_interval=30,  # ping间隔30秒
    logger=False,  # 禁用Socket.IO日志
    engineio_logger=False,  # 禁用Engine.IO日志
    always_connect=False,  # 不总是连接
    transports=['polling', 'websocket'],  # 明确指定传输方式
    allow_upgrades=True,  # 允许升级到WebSocket
    compression_threshold=1024,  # 压缩阈值1KB
    max_payload_size=500000,  # 减少最大载荷大小到500KB
    cookie=False,  # 禁用cookie
    manage_session=False,  # 禁用会话管理
    close_timeout=10,  # 连接关闭超时时间
    disconnect_timeout=5  # 断开连接超时时间
)
print("✅ SocketIO 初始化完成")

# 将socketio实例添加到应用上下文
app.socketio = socketio

# 注册WebSocket事件处理器
print("📡 正在注册 WebSocket 事件处理器...")
from project import websocket_events
websocket_events.register_websocket_events(socketio)
print("✅ WebSocket 事件处理器注册完成")

if __name__ == '__main__':
    # 只在开发环境直接运行
    import os
    if os.environ.get('FLASK_ENV') != 'production':
        # 开发环境
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    else:
        # 生产环境由gunicorn处理，这里不运行
        print("生产环境由gunicorn启动，跳过直接运行")
