from project import create_app
from project import db
from project.models import *

app = create_app()
with app.app_context():
    db.create_all()
    print('数据库初始化成功')