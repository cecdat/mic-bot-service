import os
from project import create_app
from flask_socketio import SocketIO

# 设置环境变量确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 应用工厂创建应用实例
app = create_app()

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 将socketio实例添加到应用上下文
app.socketio = socketio

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
