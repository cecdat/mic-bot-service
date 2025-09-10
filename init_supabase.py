#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 数据库初始化脚本
用于在 Supabase 中创建必要的表结构和数据
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Supabase 连接信息
SUPABASE_URL = "svicxyubtwdisddxsoqh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2aWN4eXVidHdkaXNkZHhzb3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzQzNzIsImV4cCI6MjA3MzA1MDM3Mn0.il8strW1UlV47xl9bAlAoizjjiuOHhc8oSNbACpJ90Q"

def connect_to_supabase():
    """连接到 Supabase 数据库"""
    try:
        conn = psycopg2.connect(
            host=SUPABASE_URL,
            port=5432,
            database="postgres",
            user="postgres",
            password=SUPABASE_KEY
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ 连接 Supabase 失败: {e}")
        return None

def execute_sql_file(conn, sql_file_path):
    """执行 SQL 文件"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        cursor.execute(sql_content)
        cursor.close()
        print(f"✅ 成功执行 {sql_file_path}")
        return True
    except Exception as e:
        print(f"❌ 执行 {sql_file_path} 失败: {e}")
        return False

def check_table_exists(conn, table_name):
    """检查表是否存在"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'mic_bot' 
                AND table_name = %s
            );
        """, (table_name,))
        exists = cursor.fetchone()[0]
        cursor.close()
        return exists
    except Exception as e:
        print(f"❌ 检查表 {table_name} 失败: {e}")
        return False

def create_schema(conn):
    """创建 mic_bot 模式"""
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE SCHEMA IF NOT EXISTS mic_bot;")
        cursor.execute("SET search_path TO mic_bot, public;")
        cursor.close()
        print("✅ 成功创建 mic_bot 模式")
        return True
    except Exception as e:
        print(f"❌ 创建模式失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始初始化 Supabase 数据库...")
    
    # 连接数据库
    conn = connect_to_supabase()
    if not conn:
        return
    
    print("✅ 成功连接到 Supabase")
    
    # 创建 mic_bot 模式
    if not create_schema(conn):
        return
    
    # 检查是否已经初始化
    if check_table_exists(conn, 'db_version'):
        print("📊 数据库已初始化，检查版本...")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;")
            version = cursor.fetchone()
            if version:
                print(f"📈 当前数据库版本: {version[0]}")
            cursor.close()
        except Exception as e:
            print(f"⚠️ 检查版本失败: {e}")
    else:
        print("📝 数据库未初始化，开始创建表结构...")
        
        # 执行 base.sql
        sql_file = os.path.join(os.path.dirname(__file__), 'sql', 'base.sql')
        if os.path.exists(sql_file):
            if execute_sql_file(conn, sql_file):
                print("✅ 数据库表结构创建完成")
            else:
                print("❌ 数据库表结构创建失败")
                return
        else:
            print(f"❌ 找不到 SQL 文件: {sql_file}")
            return
    
    # 检查关键表
    tables_to_check = [
        'web_users', 'bot_nodes', 'bot_accounts', 'accounts', 
        'tasks', 'push_configs', 'verification_codes', 'user_agents',
        'node_logs', 'account_points_history'
    ]
    
    print("\n📋 检查表结构...")
    for table in tables_to_check:
        if check_table_exists(conn, table):
            print(f"✅ {table} 表存在")
        else:
            print(f"❌ {table} 表不存在")
    
    # 创建默认管理员用户
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM web_users;")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("\n👤 创建默认管理员用户...")
            cursor.execute("""
                INSERT INTO web_users (username, password_hash, status) 
                VALUES ('admin', 'admin123', 1);
            """)
            print("✅ 默认管理员用户创建完成 (用户名: admin, 密码: admin123)")
        else:
            print(f"👤 已存在 {user_count} 个用户")
        
        cursor.close()
    except Exception as e:
        print(f"⚠️ 创建默认用户失败: {e}")
    
    conn.close()
    print("\n🎉 Supabase 数据库初始化完成！")

if __name__ == '__main__':
    main()
