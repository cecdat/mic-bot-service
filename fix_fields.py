#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 数据库连接配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/rewards_db')

def fix_missing_fields():
    """手动添加缺失的字段"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("开始检查并添加缺失的字段...")
        
        # 检查字段是否存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'push_configs' 
            AND column_name IN ('notify_on_task_start', 'notify_on_task_finish')
            ORDER BY column_name;
        """)
        
        existing_fields = [row[0] for row in cursor.fetchall()]
        print(f"已存在的字段: {existing_fields}")
        
        # 添加缺失的字段
        if 'notify_on_task_start' not in existing_fields:
            print("添加字段 notify_on_task_start...")
            cursor.execute("ALTER TABLE push_configs ADD COLUMN notify_on_task_start BOOLEAN DEFAULT FALSE;")
            print("✓ 字段 notify_on_task_start 添加成功")
        else:
            print("✓ 字段 notify_on_task_start 已存在")
            
        if 'notify_on_task_finish' not in existing_fields:
            print("添加字段 notify_on_task_finish...")
            cursor.execute("ALTER TABLE push_configs ADD COLUMN notify_on_task_finish BOOLEAN DEFAULT FALSE;")
            print("✓ 字段 notify_on_task_finish 添加成功")
        else:
            print("✓ 字段 notify_on_task_finish 已存在")
        
        # 验证字段是否添加成功
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'push_configs' 
            AND column_name IN ('notify_on_task_start', 'notify_on_task_finish')
            ORDER BY column_name;
        """)
        
        final_fields = [row[0] for row in cursor.fetchall()]
        print(f"最终字段列表: {final_fields}")
        
        cursor.close()
        conn.close()
        print("✅ 字段修复完成")
        
    except Exception as e:
        print(f"❌ 字段修复失败: {e}")

if __name__ == '__main__':
    fix_missing_fields()
