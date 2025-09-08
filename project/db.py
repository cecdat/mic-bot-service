from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
import click

db = SQLAlchemy()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """清除现有数据并创建新表。"""
    # 在这里导入模型以确保它们被注册到 SQLAlchemy
    from . import models
    db.create_all()
    click.echo('Initialized the database.')

def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)
