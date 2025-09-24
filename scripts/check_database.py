#!/usr/bin/env python3
"""
检查数据库状态脚本
用于诊断 search_cross_execution 字段问题
"""

import sys
import os
sys.path.append('/app')

from project import create_app, db
from project.models import BotNode
from sqlalchemy import text

def check_database():
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表结构
            print("🔍 检查 bot_nodes 表结构...")
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'bot_nodes' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("📋 bot_nodes 表字段:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # 检查 search_cross_execution 字段是否存在
            print("\n🔍 检查 search_cross_execution 字段...")
            has_field = any(col[0] == 'search_cross_execution' for col in columns)
            if has_field:
                print("✅ search_cross_execution 字段存在")
            else:
                print("❌ search_cross_execution 字段不存在")
            
            # 检查数据库版本
            print("\n🔍 检查数据库版本...")
            try:
                result = db.session.execute(text("SELECT version FROM db_version WHERE id = 1"))
                version = result.fetchone()
                if version:
                    print(f"📊 当前数据库版本: {version[0]}")
                else:
                    print("❌ 无法获取数据库版本")
            except Exception as e:
                print(f"❌ 检查数据库版本失败: {e}")
            
            # 测试查询节点
            print("\n🔍 测试查询节点...")
            try:
                nodes = BotNode.query.limit(1).all()
                if nodes:
                    node = nodes[0]
                    print(f"📋 测试节点: {node.node_name}")
                    print(f"  - search_cross_execution: {getattr(node, 'search_cross_execution', 'NOT_FOUND')}")
                else:
                    print("ℹ️ 没有找到节点")
            except Exception as e:
                print(f"❌ 查询节点失败: {e}")
                
        except Exception as e:
            print(f"❌ 检查数据库失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_database()
