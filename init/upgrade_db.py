import os
import click
from project import db

app = None

def get_app():
    global app
    if app is None:
        from project import create_app
        app = create_app()
    return app

def execute_sql_script(script_path):
    """执行SQL脚本文件"""
    with get_app().app_context():
        try:
            # 读取SQL脚本
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # 分割SQL语句（简单分割，实际项目中可能需要更复杂的处理）
            sql_statements = sql_script.split(';')

            # 执行每条SQL语句
            for statement in sql_statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    db.session.execute(statement)

            db.session.commit()
            return True, "SQL脚本执行成功"
        except Exception as e:
            db.session.rollback()
            return False, f"SQL脚本执行失败: {str(e)}"

@click.command('upgrade-db')
@click.option('--version', default='latest', help='要升级到的版本，默认为最新版本')
def upgrade_db_command(version):
    """升级数据库结构"""
    if version == 'latest':
        # 查找最新的升级脚本
        sql_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sql')
        upgrade_scripts = [f for f in os.listdir(sql_dir) if f.startswith('upgrade_db_v') and f.endswith('.sql')]
        if not upgrade_scripts:
            click.echo('没有找到升级脚本')
            return

        # 按版本号排序
        upgrade_scripts.sort(reverse=True)
        latest_script = upgrade_scripts[0]
        script_path = os.path.join(sql_dir, latest_script)
        click.echo(f'执行最新升级脚本: {latest_script}')
    else:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sql', f'upgrade_db_v{version}.sql')
        if not os.path.exists(script_path):
            click.echo(f'未找到版本 {version} 的升级脚本')
            return
        click.echo(f'执行升级脚本: upgrade_db_v{version}.sql')

    success, message = execute_sql_script(script_path)
    if success:
        click.echo(message)
    else:
        click.echo(message)

if __name__ == '__main__':
    with get_app().app_context():
        upgrade_db_command()

# 注册命令到Flask CLI
def init_app(app):
    app.cli.add_command(upgrade_db_command)