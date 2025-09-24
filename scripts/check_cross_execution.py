#!/usr/bin/env python3
"""
检查交叉执行配置的简化脚本
"""

import os
import sys
import psycopg2
from datetime import datetime

def check_database_direct():
    """直接检查数据库配置"""
    print("🔍 直接检查数据库配置...")
    
    try:
        # 数据库连接参数 - 请根据实际情况修改
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'mic_bot_service',
            'user': 'mic_bot_user',
            'password': 'mic_bot_password'
        }
        
        # 连接数据库
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查表结构
        print("\n📋 检查表结构...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'bot_nodes' 
            AND column_name = 'search_cross_execution'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ search_cross_execution 字段存在:")
            print(f"   - 字段名: {result[0]}")
            print(f"   - 数据类型: {result[1]}")
            print(f"   - 可空: {result[2]}")
            print(f"   - 默认值: {result[3]}")
        else:
            print("❌ search_cross_execution 字段不存在")
            return False
        
        # 查询所有节点的交叉执行配置
        print("\n📊 查询节点配置...")
        cursor.execute("""
            SELECT id, name, search_cross_execution, status, last_checkin
            FROM bot_nodes
            ORDER BY id
        """)
        
        nodes = cursor.fetchall()
        
        if not nodes:
            print("❌ 没有找到任何节点")
            return False
        
        print(f"📋 找到 {len(nodes)} 个节点:")
        
        for node in nodes:
            node_id, name, cross_exec, status, last_checkin = node
            print(f"\n🔹 节点: {name} (ID: {node_id})")
            print(f"   - 交叉执行: {cross_exec}")
            print(f"   - 状态: {status}")
            print(f"   - 最后签到: {last_checkin}")
            
            if cross_exec is True:
                print("   ✅ 交叉执行已启用")
            elif cross_exec is False:
                print("   ❌ 交叉执行未启用")
            else:
                print(f"   ⚠️ 交叉执行配置异常: {cross_exec}")
        
        # 检查数据库版本
        print("\n📋 检查数据库版本...")
        cursor.execute("SELECT version FROM db_version WHERE id = 1")
        version_result = cursor.fetchone()
        
        if version_result:
            print(f"✅ 数据库版本: {version_result[0]}")
        else:
            print("❌ 无法获取数据库版本")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n🔧 请检查数据库连接参数:")
        print("   - 主机地址")
        print("   - 端口号")
        print("   - 数据库名")
        print("   - 用户名和密码")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def check_docker_compose():
    """检查 Docker Compose 配置"""
    print("\n🔍 检查 Docker Compose 配置...")
    
    compose_file = os.path.join(os.path.dirname(__file__), '..', 'docker-compose.yaml')
    
    if os.path.exists(compose_file):
        print("✅ 找到 docker-compose.yaml 文件")
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查数据库配置
        if 'POSTGRES_DB' in content:
            print("✅ 找到数据库配置")
        else:
            print("❌ 缺少数据库配置")
            
    else:
        print("❌ 找不到 docker-compose.yaml 文件")

def main():
    """主函数"""
    print("="*60)
    print("🔍 交叉执行配置检查工具")
    print("="*60)
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查 Docker Compose 配置
    check_docker_compose()
    
    # 检查数据库配置
    db_ok = check_database_direct()
    
    print("\n" + "="*60)
    print("📋 检查结果和建议:")
    print("="*60)
    
    if db_ok:
        print("✅ 数据库配置检查完成")
        print("\n🔧 如果交叉执行仍然不工作，请检查:")
        print("1. mic-bot-service 是否已重启")
        print("2. mic-bot-node 是否已重启")
        print("3. 节点管理页面的交叉运行开关是否已开启")
        print("4. 节点启动日志中的配置加载信息")
    else:
        print("❌ 数据库配置有问题")
        print("\n🔧 请检查:")
        print("1. 数据库连接参数是否正确")
        print("2. 数据库服务是否正在运行")
        print("3. search_cross_execution 字段是否存在")
        print("4. 数据库升级脚本是否已执行")

if __name__ == "__main__":
    main()
