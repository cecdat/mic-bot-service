from project import create_app
from project.db import db
from project.models import WebUser
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 查找admin用户
    admin_user = WebUser.query.filter_by(username='admin').first()
    if admin_user:
        # 更新密码
        admin_user.password_hash = generate_password_hash('new_password')
        db.session.commit()
        print('管理员密码已重置为: new_password')
    else:
        # 创建新用户
        new_user = WebUser(username='admin', password_hash=generate_password_hash('new_password'))
        db.session.add(new_user)
        db.session.commit()
        print('管理员用户创建成功，密码为: new_password')