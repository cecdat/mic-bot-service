#!/usr/bin/env python3
"""
数据库初始化脚本 - Python版本
替代有换行符问题的shell脚本
"""

import os
import sys
import time
import psycopg2
import subprocess
from datetime import datetime

def log_with_time(message):
    """带时间戳的日志函数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

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

def wait_for_database():
    """等待数据库服务就绪"""
    log_with_time("等待数据库服务就绪...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host='db',
                port=5432,
                user=os.getenv('POSTGRES_USER', 'user'),
                password=os.getenv('POSTGRES_PASSWORD', 'password'),
                database=os.getenv('POSTGRES_DB', 'rewards_db')
            )
            conn.close()
            log_with_time("数据库已就绪")
            return True
        except psycopg2.OperationalError:
            retry_count += 1
            log_with_time(f"数据库尚未就绪，等待5秒... (尝试 {retry_count}/{max_retries})")
            time.sleep(5)
    
    log_with_time("数据库连接超时")
    return False

def initialize_database():
    """初始化数据库"""
    try:
        log_with_time("开始初始化数据库...")
        
        # 检查数据库是否已初始化
        conn = psycopg2.connect(
            host='db',
            port=5432,
            user=os.getenv('POSTGRES_USER', 'user'),
            password=os.getenv('POSTGRES_PASSWORD', 'password'),
            database=os.getenv('POSTGRES_DB', 'rewards_db')
        )
        cursor = conn.cursor()
        
        # 检查是否存在bot_nodes表
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'bot_nodes'
            );
        """)
        
        if cursor.fetchone()[0]:
            log_with_time("数据库已初始化，跳过初始化步骤")
            cursor.close()
            conn.close()
            return True
        
        # 执行基础SQL脚本
        base_sql_path = '/app/sql/base.sql'
        if os.path.exists(base_sql_path):
            log_with_time("执行基础SQL脚本...")
            with open(base_sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 使用psycopg2的execute_values或直接执行整个脚本
            try:
                # 直接执行整个SQL脚本
                cursor.execute(sql_content)
                log_with_time("基础SQL脚本执行完成")
            except Exception as e:
                log_with_time(f"直接执行失败，尝试分割执行: {e}")
                # 如果直接执行失败，则分割执行
                sql_statements = split_sql_statements(sql_content)
                log_with_time(f"分割得到 {len(sql_statements)} 条SQL语句")
                
                for i, statement in enumerate(sql_statements):
                    statement = statement.strip()
                    if statement:
                        log_with_time(f"执行第 {i+1} 条SQL语句: {statement[:100]}...")
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            log_with_time(f"SQL语句执行失败: {e}")
                            log_with_time(f"失败的语句: {statement}")
                            raise
                    else:
                        log_with_time(f"跳过第 {i+1} 条空语句")
            
            conn.commit()
            log_with_time("基础SQL脚本执行完成")
        else:
            log_with_time("警告：未找到基础SQL脚本")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        log_with_time(f"数据库初始化失败: {e}")
        return False

def upgrade_database():
    """升级数据库"""
    try:
        log_with_time("开始数据库升级...")
        
        # 获取当前数据库版本
        conn = psycopg2.connect(
            host='db',
            port=5432,
            user=os.getenv('POSTGRES_USER', 'user'),
            password=os.getenv('POSTGRES_PASSWORD', 'password'),
            database=os.getenv('POSTGRES_DB', 'rewards_db')
        )
        cursor = conn.cursor()
        
        # 检查db_version表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'db_version'
            );
        """)
        
        if not cursor.fetchone()[0]:
            log_with_time("db_version表不存在，跳过升级")
            cursor.close()
            conn.close()
            return True
        
        # 确保db_version表的version字段有唯一约束
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints 
                WHERE table_name = 'db_version' 
                AND constraint_type = 'UNIQUE'
                AND constraint_name LIKE '%version%'
            );
        """)
        
        if not cursor.fetchone()[0]:
            log_with_time("为db_version表的version字段添加唯一约束...")
            
            # 先清理重复的版本记录，只保留最新的
            log_with_time("清理重复的版本记录...")
            cursor.execute("""
                DELETE FROM db_version 
                WHERE id NOT IN (
                    SELECT DISTINCT ON (version) id 
                    FROM db_version 
                    ORDER BY version, applied_at DESC
                );
            """)
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                log_with_time(f"删除了 {deleted_count} 条重复的版本记录")
            
            # 添加唯一约束
            cursor.execute("ALTER TABLE db_version ADD CONSTRAINT unique_version UNIQUE (version);")
            conn.commit()
            log_with_time("唯一约束添加成功")
        
        # 获取当前版本
        cursor.execute("SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;")
        result = cursor.fetchone()
        current_version = result[0] if result else "0.0"
        
        log_with_time(f"当前数据库版本: {current_version}")
        
        # 查找升级脚本
        sql_dir = '/app/sql'
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
        for script_file, version in upgrade_scripts:
            if version > current_version:
                script_path = os.path.join(sql_dir, script_file)
                log_with_time(f"执行升级脚本: {script_file} (版本 {version})")
                
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # 尝试直接执行整个SQL脚本
                try:
                    cursor.execute(sql_content)
                    log_with_time(f"升级脚本 {script_file} 执行完成")
                except Exception as e:
                    log_with_time(f"直接执行失败，尝试分割执行: {e}")
                    # 如果直接执行失败，则分割执行
                    sql_statements = split_sql_statements(sql_content)
                    for statement in sql_statements:
                        if statement.strip():
                            cursor.execute(statement)
                
                conn.commit()
                log_with_time(f"升级脚本 {script_file} 执行完成")
            else:
                log_with_time(f"跳过已执行的升级脚本: {script_file} (版本 {version})")
        
        cursor.close()
        conn.close()
        log_with_time("数据库升级完成")
        return True
        
    except Exception as e:
        log_with_time(f"数据库升级失败: {e}")
        return False

def start_flask_app():
    """启动Flask应用"""
    log_with_time("启动Flask应用...")
    try:
        # 使用sys.executable确保使用正确的Python解释器
        os.execv(sys.executable, [sys.executable, 'run.py'])
    except Exception as e:
        log_with_time(f"启动Flask应用失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    log_with_time("开始初始化 mic-bot-service...")
    
    # 等待数据库就绪
    if not wait_for_database():
        log_with_time("数据库连接失败，退出")
        sys.exit(1)
    
    # 初始化数据库
    if not initialize_database():
        log_with_time("数据库初始化失败，退出")
        sys.exit(1)
    
    # 升级数据库
    if not upgrade_database():
        log_with_time("数据库升级失败，退出")
        sys.exit(1)
    
    # 启动Flask应用
    start_flask_app()

if __name__ == "__main__":
    main()
