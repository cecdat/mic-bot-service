import os
import sys
import click
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 添加项目根目录到Python路径
sys.path.insert(0, '/app')

# 数据库连接配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/rewards_db')

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

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
    conn = get_db_connection()
    try:
        # 读取SQL脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 分割SQL语句（处理dollar-quoted strings）
        sql_statements = split_sql_statements(sql_script)

        # 执行每条SQL语句
        cursor = conn.cursor()
        for i, statement in enumerate(sql_statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    print(f"执行SQL语句 {i+1}: {statement[:100]}...")
                    cursor.execute(statement)
                    print(f"✓ SQL语句 {i+1} 执行成功")
                except Exception as e:
                    print(f"✗ SQL语句 {i+1} 执行失败: {e}")
                    print(f"失败的语句: {statement}")
                    cursor.close()
                    return False, f"SQL语句 {i+1} 执行失败: {str(e)}"

        cursor.close()
        return True, "SQL脚本执行成功"
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        return False, f"SQL脚本执行失败: {str(e)}"
    finally:
        conn.close()

def get_current_version():
    """获取当前数据库版本"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else "0.0"
    except Exception as e:
        print(f'无法获取当前版本: {e}')
        return "0.0"
    finally:
        conn.close()

def upgrade_database(version='latest'):
    """升级数据库结构"""
    try:
        # 检查当前数据库版本
        current_version = get_current_version()
        print(f'当前数据库版本: {current_version}')
        
        if version == 'latest':
            # 查找所有升级脚本
            sql_dir = '/app/sql'
            upgrade_scripts = []
            
            if os.path.exists(sql_dir):
                for filename in os.listdir(sql_dir):
                    if filename.startswith('upgrade_db_v') and filename.endswith('.sql'):
                        # 提取版本号
                        version_match = filename.replace('upgrade_db_v', '').replace('.sql', '')
                        upgrade_scripts.append((filename, version_match))
            
            # 按版本号排序（使用版本号比较）
            def version_key(version_tuple):
                version_str = version_tuple[1]
                try:
                    # 将版本号转换为元组进行比较，如 "2.9" -> (2, 9)
                    return tuple(map(int, version_str.split('.')))
                except ValueError:
                    # 如果版本号格式不正确，按字符串比较
                    return (0, 0)
            
            upgrade_scripts.sort(key=version_key)
            
            # 只执行比当前版本更新的脚本
            executed_scripts = []
            for script_file, script_version in upgrade_scripts:
                if version_key((script_file, script_version)) > version_key(('', current_version)):
                    script_path = os.path.join(sql_dir, script_file)
                    print(f'执行升级脚本: {script_file} (版本 {script_version})')
                    
                    success, message = execute_sql_script(script_path)
                    if success:
                        print(f'✓ {script_file} 执行成功')
                        executed_scripts.append(script_file)
                    else:
                        print(f'✗ {script_file} 执行失败: {message}')
                        return
                else:
                    print(f'跳过已执行的升级脚本: {script_file} (版本 {script_version})')
            
            if executed_scripts:
                print(f'成功执行了 {len(executed_scripts)} 个升级脚本')
            else:
                print('没有需要执行的升级脚本')
        else:
            script_path = f'/app/sql/upgrade_db_v{version}.sql'
            if not os.path.exists(script_path):
                print(f'未找到版本 {version} 的升级脚本')
                return
            print(f'执行升级脚本: upgrade_db_v{version}.sql')
            
            success, message = execute_sql_script(script_path)
            if success:
                print(message)
            else:
                print(message)
                    
    except Exception as e:
        print(f'升级过程中发生错误: {e}')

if __name__ == '__main__':
    upgrade_database()