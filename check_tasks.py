#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timezone

# 添加项目根目录到Python路径
sys.path.insert(0, '/app')

# 数据库连接配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/rewards_db')

def check_tasks():
    """检查定时任务状态"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("=== 定时任务状态检查 ===")
        
        # 检查任务表
        cursor.execute("""
            SELECT 
                id, 
                task_type, 
                node_id, 
                status, 
                execution_time, 
                created_at,
                started_at,
                completed_at
            FROM tasks 
            ORDER BY execution_time DESC 
            LIMIT 20;
        """)
        
        tasks = cursor.fetchall()
        print(f"\n任务表中有 {len(tasks)} 个任务（最近20个）:")
        for task in tasks:
            print(f"  ID: {task[0]}, 类型: {task[1]}, 节点ID: {task[2]}, 状态: {task[3]}")
            print(f"    执行时间: {task[4]}, 创建时间: {task[5]}")
            if task[6]:
                print(f"    开始时间: {task[6]}")
            if task[7]:
                print(f"    完成时间: {task[7]}")
            print()
        
        # 检查节点状态
        cursor.execute("""
            SELECT 
                id, 
                node_name, 
                status, 
                activity_status, 
                cron_schedule,
                command,
                command_status
            FROM bot_nodes 
            ORDER BY id;
        """)
        
        nodes = cursor.fetchall()
        print(f"\n节点状态 ({len(nodes)} 个节点):")
        for node in nodes:
            print(f"  ID: {node[0]}, 名称: {node[1]}, 状态: {node[2]}, 活动状态: {node[3]}")
            print(f"    Cron: {node[4]}, 命令: {node[5]}, 命令状态: {node[6]}")
            print()
        
        # 检查待执行任务
        now = datetime.now(timezone.utc)
        cursor.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE status = 'pending' AND execution_time <= %s;
        """, (now,))
        
        pending_count = cursor.fetchone()[0]
        print(f"\n当前时间: {now}")
        print(f"应该执行但未执行的任务数量: {pending_count}")
        
        # 检查最近的任务执行情况
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM tasks 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY status
            ORDER BY count DESC;
        """)
        
        recent_tasks = cursor.fetchall()
        print(f"\n最近24小时任务状态统计:")
        for status, count in recent_tasks:
            print(f"  {status}: {count} 个")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == '__main__':
    check_tasks()
