from functools import wraps
from flask import request, jsonify, g, session, redirect, url_for
from werkzeug.security import check_password_hash
from .models import BotNode, WebUser

def check_bot_token(token):
    """验证 mic-bot 提供的 API Token"""
    if not token: return False
    nodes = BotNode.query.all()
    for node in nodes:
        if check_password_hash(node.api_token_hash, token):
            g.node = node
            return True
    return False

def bot_api_required(f):
    """保护 mic-bot API 的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not token or not check_bot_token(token):
            return jsonify({"status": "error", "message": "Invalid or missing API Token"}), 401
        
        return f(*args, **kwargs)
    return decorated

def web_login_required(f):
    """保护网页和网页API的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # 如果是API请求，返回401 JSON错误；如果是页面请求，则重定向
            if request.path.startswith('/web_api/'):
                return jsonify(status='error', message='Authentication required'), 401
            return redirect(url_for('frontend.login'))
        
        g.user = WebUser.query.get(session['user_id'])
        return f(*args, **kwargs)
    return decorated_function
