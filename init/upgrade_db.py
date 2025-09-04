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

def split_sql_statements(sql_content):
    """智能分割SQL语句，处理dollar-quoted strings"""
    statements = []
    current_statement = ""
    in_dollar_quote = False
    dollar_tag = ""
    i = 0
    
    while i < len(sql_content):
        char = sql_content[i]
        
        if not in_dollar_quote:
            # 不在dollar-quoted string中
            if char == '$':
                # 检查是否是dollar-quoted string的开始
                j = i + 1
                tag = ""
                while j < len(sql_content) and sql_content[j] != '$':
                    tag += sql_content[j]
                    j += 1
                
                if j < len(sql_content) and sql_content[j] == '$':
                    # 找到完整的dollar tag
                    dollar_tag = '$' + tag + '$'
                    in_dollar_quote = True
                    current_statement += sql_content[i:j+1]
                    i = j + 1
                    continue
            
            elif char == ';':
                # 普通分号，结束语句
                current_statement += char
                statement = current_statement.strip()
                # 过滤空语句和纯注释
                if statement and not statement.startswith('--') and not statement.isspace():
                    statements.append(statement)
                current_statement = ""
                i += 1
                continue
        
        else:
            # 在dollar-quoted string中
            if sql_content[i:i+len(dollar_tag)] == dollar_tag:
                # 找到dollar-quoted string的结束
                in_dollar_quote = False
                current_statement += dollar_tag
                i += len(dollar_tag)
                continue
        
        current_statement += char
        i += 1
    
    # 添加最后一个语句
    statement = current_statement.strip()
    if statement and not statement.startswith('--') and not statement.isspace():
        statements.append(statement)
    
    return statements

def execute_sql_script(script_path):
    """执行SQL脚本文件"""
    with get_app().app_context():
        try:
            # 读取SQL脚本
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # 分割SQL语句（处理dollar-quoted strings）
            sql_statements = split_sql_statements(sql_script)

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
    with get_app().app_context():
        try:
            # 检查当前数据库版本
            current_version = "0.0"
            try:
                result = db.session.execute("SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1").fetchone()
                if result:
                    current_version = result[0]
                click.echo(f'当前数据库版本: {current_version}')
            except Exception as e:
                click.echo(f'无法获取当前版本: {e}')
                click.echo('将执行所有升级脚本')
            
            if version == 'latest':
                # 查找所有升级脚本
                sql_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sql')
                upgrade_scripts = []
                
                if os.path.exists(sql_dir):
                    for filename in os.listdir(sql_dir):
                        if filename.startswith('upgrade_db_v') and filename.endswith('.sql'):
                            # 提取版本号
                            version_match = filename.replace('upgrade_db_v', '').replace('.sql', '')
                            upgrade_scripts.append((filename, version_match))
                
                # 按版本号排序
                upgrade_scripts.sort(key=lambda x: x[1])
                
                # 只执行比当前版本更新的脚本
                executed_scripts = []
                for script_file, script_version in upgrade_scripts:
                    if script_version > current_version:
                        script_path = os.path.join(sql_dir, script_file)
                        click.echo(f'执行升级脚本: {script_file} (版本 {script_version})')
                        
                        success, message = execute_sql_script(script_path)
                        if success:
                            click.echo(f'✓ {script_file} 执行成功')
                            executed_scripts.append(script_file)
                        else:
                            click.echo(f'✗ {script_file} 执行失败: {message}')
                            return
                    else:
                        click.echo(f'跳过已执行的升级脚本: {script_file} (版本 {script_version})')
                
                if executed_scripts:
                    click.echo(f'成功执行了 {len(executed_scripts)} 个升级脚本')
                else:
                    click.echo('没有需要执行的升级脚本')
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
                    
        except Exception as e:
            click.echo(f'升级过程中发生错误: {e}')

if __name__ == '__main__':
    with get_app().app_context():
        upgrade_db_command()

# 注册命令到Flask CLI
def init_app(app):
    app.cli.add_command(upgrade_db_command)