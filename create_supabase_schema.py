#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 Supabase mic_bot 模式脚本
专门用于在 Supabase 中创建 mic_bot 模式
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

def create_mic_bot_schema(conn):
    """创建 mic_bot 模式"""
    try:
        cursor = conn.cursor()
        
        # 创建 mic_bot 模式
        cursor.execute("CREATE SCHEMA IF NOT EXISTS mic_bot;")
        print("✅ 成功创建 mic_bot 模式")
        
        # 设置搜索路径
        cursor.execute("SET search_path TO mic_bot, public;")
        print("✅ 设置搜索路径为 mic_bot, public")
        
        # 授予权限
        cursor.execute("GRANT USAGE ON SCHEMA mic_bot TO postgres;")
        cursor.execute("GRANT CREATE ON SCHEMA mic_bot TO postgres;")
        print("✅ 授予权限给 postgres 用户")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ 创建 mic_bot 模式失败: {e}")
        return False

def verify_schema(conn):
    """验证模式是否创建成功"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'mic_bot';
        """)
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print("✅ mic_bot 模式验证成功")
            return True
        else:
            print("❌ mic_bot 模式验证失败")
            return False
    except Exception as e:
        print(f"❌ 验证模式失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始创建 Supabase mic_bot 模式...")
    
    # 连接数据库
    conn = connect_to_supabase()
    if not conn:
        return
    
    print("✅ 成功连接到 Supabase")
    
    # 创建 mic_bot 模式
    if create_mic_bot_schema(conn):
        print("✅ mic_bot 模式创建完成")
        
        # 验证模式
        if verify_schema(conn):
            print("🎉 mic_bot 模式创建和验证成功！")
            print("\n📝 现在可以运行以下命令初始化数据库：")
            print("   python init_supabase.py")
        else:
            print("❌ 模式验证失败")
    else:
        print("❌ 模式创建失败")
    
    conn.close()

if __name__ == '__main__':
    main()
