#!/usr/bin/env python3
"""
修复 search_cross_execution 字段脚本
"""

import sys
import os
sys.path.append('/app')

from project import create_app, db
from sqlalchemy import text

def fix_search_cross_execution():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 检查 search_cross_execution 字段是否存在...")
            
            # 检查字段是否存在
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'bot_nodes' 
                    AND column_name = 'search_cross_execution'
                )
            """))
            
            field_exists = result.fetchone()[0]
            
            if field_exists:
                print("✅ search_cross_execution 字段已存在")
            else:
                print("❌ search_cross_execution 字段不存在，正在添加...")
                
                # 添加字段
                db.session.execute(text("""
                    ALTER TABLE bot_nodes 
                    ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE
                """))
                
                db.session.commit()
                print("✅ 成功添加 search_cross_execution 字段")
            
            # 更新数据库版本
            print("🔍 更新数据库版本...")
            db.session.execute(text("""
                UPDATE db_version SET version = '2.12' WHERE id = 1
            """))
            
            # 如果 db_version 表不存在，创建它
            db.session.execute(text("""
                INSERT INTO db_version (id, version, applied_at, description) 
                SELECT 1, '2.12', CURRENT_TIMESTAMP, 'Added search cross execution feature'
                WHERE NOT EXISTS (SELECT 1 FROM db_version WHERE id = 1)
            """))
            
            db.session.commit()
            print("✅ 数据库版本已更新到 2.12")
            
            # 验证修复结果
            print("🔍 验证修复结果...")
            result = db.session.execute(text("""
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'bot_nodes' 
                AND column_name = 'search_cross_execution'
            """))
            
            field_info = result.fetchone()
            if field_info:
                print(f"✅ 验证成功: {field_info[0]} ({field_info[1]}, default: {field_info[2]})")
            else:
                print("❌ 验证失败: 字段不存在")
                
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fix_search_cross_execution()
