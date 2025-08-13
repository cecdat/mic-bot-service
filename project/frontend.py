from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import WebUser
from werkzeug.security import check_password_hash
from .auth import web_login_required

bp = Blueprint('frontend', __name__, template_folder='templates', static_folder='static')

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
    return render_template('login.html')

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
