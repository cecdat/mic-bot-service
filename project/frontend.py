from flask import Blueprint, flash, redirect, render_template, request, session, url_for, g, jsonify
from .models import WebUser
from werkzeug.security import check_password_hash, generate_password_hash
from .auth import web_login_required
from .db import db

bp = Blueprint('frontend', __name__, template_folder='templates', static_folder='static')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    # 检查是否已有用户注册
    if WebUser.query.first() is not None:
        flash('注册功能已关闭，已有用户存在。')
        return redirect(url_for('frontend.login'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        error = None

        if not username:
            error = '用户名不能为空。'
        elif not password:
            error = '密码不能为空。'
        elif password != confirm_password:
            error = '两次输入的密码不一致。'
        elif WebUser.query.filter_by(username=username).first() is not None:
            error = '用户名已存在。'

        if error is None:
            # 创建新用户
            new_user = WebUser(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录。')
            return redirect(url_for('frontend.login'))

        flash(error)
    return render_template('register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = WebUser.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password_hash, password):
            error = '无效的用户名或密码。'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('frontend.index'))
        
        flash(error)
    # 检查是否有用户存在
    web_users = WebUser.query.first() is not None
    return render_template('login.html', web_users=web_users)

@bp.route('/change_password', methods=('GET', 'POST'))
@web_login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        error = None

        # 验证原密码
        if not check_password_hash(g.user.password_hash, old_password):
            error = '原密码错误。'
        elif not new_password:
            error = '新密码不能为空。'
        elif new_password != confirm_new_password:
            error = '两次输入的新密码不一致。'

        if error is None:
            # 更新密码
            g.user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return jsonify({'success': True, 'message': '密码修改成功。'})
        return jsonify({'success': False, 'message': error})
    return render_template('change_password.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('frontend.login'))

@bp.route('/')
@web_login_required
def index():
    return render_template('index.html')

@bp.route('/manage')
@web_login_required
def manage():
    return render_template('manage.html')

@bp.route('/nodes')
@web_login_required
def nodes():
    return render_template('nodes.html')

# [核心修正] 添加 /push 路由
@bp.route('/push')
@web_login_required
def push():
    return render_template('push.html')

# 添加验证码管理路由
@bp.route('/verification')
@web_login_required
def verification():
    return render_template('verification.html')

# 添加User-Agent管理路由
@bp.route('/user_agents')
@web_login_required
def user_agents():
    return render_template('user_agents.html')

# 添加移动端积分页面路由
@bp.route('/mobile_points')
def mobile_points():
    return render_template('mobile_points.html')

# 添加简短的移动端积分页面路由
@bp.route('/m')
def mobile_points_short():
    return render_template('mobile_points.html')
