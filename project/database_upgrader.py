#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库升级模块
独立处理数据库版本检测和升级逻辑
"""

import os
import sys
import psycopg2
import glob
import re
import logging
from datetime import datetime
from typing import List, Tuple, Optional

# 配置日志记录器
logger = logging.getLogger('database_upgrader')

class DatabaseUpgrader:
    """数据库升级器"""
    
    def __init__(self, database_url: str = None):
        """初始化数据库升级器"""
        self.database_url = database_url or os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/rewards_db')
        self.sql_dir = '/app/sql'
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        try:
            # 解析数据库URL
            if '://' in self.database_url:
                parts = self.database_url.split('://')[1]
                if '@' in parts:
                    user_pass, host_db = parts.split('@')
                    user, password = user_pass.split(':')
                    if ':' in host_db:
                        host, port_db = host_db.split(':')
                        port, database = port_db.split('/')
                    else:
                        host = host_db.split('/')[0]
                        port = '5432'
                        database = host_db.split('/')[1]
                else:
                    raise ValueError("Invalid database URL format")
            else:
                raise ValueError("Invalid database URL format")
            
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号，返回1表示version1>version2，-1表示version1<version2，0表示相等"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        try:
            v1_tuple = version_tuple(version1)
            v2_tuple = version_tuple(version2)
            
            if v1_tuple > v2_tuple:
                return 1
            elif v1_tuple < v2_tuple:
                return -1
            else:
                return 0
        except ValueError:
            # 如果版本号格式不正确，回退到字符串比较
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            else:
                return 0
    
    def get_current_version(self) -> str:
        """获取当前数据库版本"""
        try:
            # 检查db_version表是否存在
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'db_version'
                );
            """)
            
            if not self.cursor.fetchone()[0]:
                logger.info("db_version表不存在，当前版本为0.0")
                return "0.0"
            
            # 获取当前版本
            self.cursor.execute("SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;")
            result = self.cursor.fetchone()
            current_version = result[0] if result else "0.0"
            
            logger.info(f"当前数据库版本: {current_version}")
            return current_version
        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return "0.0"
    
    def find_upgrade_scripts(self) -> List[Tuple[str, str]]:
        """查找所有升级脚本"""
        upgrade_scripts = []
        
        if not os.path.exists(self.sql_dir):
            print(f"SQL目录不存在: {self.sql_dir}")
            return upgrade_scripts
        
        # 查找所有升级脚本
        pattern = os.path.join(self.sql_dir, 'upgrade_db_v*.sql')
        script_files = glob.glob(pattern)
        
        for script_file in script_files:
            filename = os.path.basename(script_file)
            # 提取版本号
            version_match = re.search(r'upgrade_db_v(\d+\.\d+)\.sql', filename)
            if version_match:
                version = version_match.group(1)
                upgrade_scripts.append((script_file, version))
        
        # 按版本号排序
        upgrade_scripts.sort(key=lambda x: x[1])
        return upgrade_scripts
    
    def execute_sql_file(self, file_path: str) -> bool:
        """执行SQL文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            statements = self.split_sql_statements(sql_content)
            
            for statement in statements:
                if statement.strip():
                    self.cursor.execute(statement)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"执行SQL文件失败: {e}")
            self.conn.rollback()
            return False
    
    def split_sql_statements(self, sql_content: str) -> List[str]:
        """智能分割SQL语句，处理dollar-quoted strings"""
        statements = []
        current_statement = ""
        in_dollar_quote = False
        dollar_tag = ""
        i = 0
        
        while i < len(sql_content):
            char = sql_content[i]
            
            if not in_dollar_quote:
                if char == '$':
                    # 检查是否是dollar-quoted string的开始
                    j = i + 1
                    while j < len(sql_content) and sql_content[j] != '$':
                        j += 1
                    if j < len(sql_content):
                        dollar_tag = sql_content[i:j+1]
                        in_dollar_quote = True
                        current_statement += char
                elif char == ';':
                    current_statement += char
                    if current_statement.strip():
                        statements.append(current_statement.strip())
                    current_statement = ""
                else:
                    current_statement += char
            else:
                current_statement += char
                if char == '$' and sql_content[i-len(dollar_tag)+1:i+1] == dollar_tag:
                    in_dollar_quote = False
                    dollar_tag = ""
            
            i += 1
        
        # 添加最后一个语句
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    def upgrade_database(self) -> bool:
        """升级数据库"""
        try:
            logger.info("开始数据库升级...")
            
            if not self.connect():
                logger.error("数据库连接失败")
                return False
            
            current_version = self.get_current_version()
            upgrade_scripts = self.find_upgrade_scripts()
            
            if not upgrade_scripts:
                logger.info("没有找到升级脚本")
                return True
            
            logger.info(f"找到 {len(upgrade_scripts)} 个升级脚本，当前版本: {current_version}")
            
            # 执行需要升级的脚本
            upgraded_count = 0
            for script_file, version in upgrade_scripts:
                if self.compare_versions(version, current_version) > 0:
                    logger.info(f"执行升级脚本: {os.path.basename(script_file)} (版本 {version})")
                    
                    if self.execute_sql_file(script_file):
                        logger.info(f"升级脚本 {os.path.basename(script_file)} 执行成功")
                        current_version = version
                        upgraded_count += 1
                    else:
                        logger.error(f"升级脚本 {os.path.basename(script_file)} 执行失败")
                        return False
                else:
                    logger.debug(f"跳过升级脚本: {os.path.basename(script_file)} (版本 {version}) - 已是最新版本")
            
            if upgraded_count > 0:
                logger.info(f"数据库升级完成！共执行了 {upgraded_count} 个升级脚本，当前版本: {current_version}")
            else:
                logger.info(f"数据库已是最新版本，无需升级，当前版本: {current_version}")
            
            return True
            
        except Exception as e:
            logger.error(f"数据库升级失败: {e}")
            return False
        finally:
            self.disconnect()
    
    def check_database_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            logger.info("开始数据库健康检查...")
            
            if not self.connect():
                logger.error("数据库连接失败")
                return False
            
            # 检查关键表是否存在
            critical_tables = ['db_version', 'bot_nodes', 'bot_accounts', 'accounts']
            
            for table in critical_tables:
                self.cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table,))
                
                exists = self.cursor.fetchone()[0]
                if not exists:
                    logger.error(f"关键表 {table} 不存在")
                    return False
            
            logger.info("数据库健康检查通过")
            return True
            
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """主函数"""
    logger.info("数据库升级模块启动")
    
    upgrader = DatabaseUpgrader()
    
    # 检查数据库健康状态
    if not upgrader.check_database_health():
        logger.error("数据库健康检查失败")
        sys.exit(1)
    
    # 执行数据库升级
    if not upgrader.upgrade_database():
        logger.error("数据库升级失败")
        sys.exit(1)
    
    logger.info("数据库升级完成")

if __name__ == '__main__':
    main()
