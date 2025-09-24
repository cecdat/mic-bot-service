#!/usr/bin/env python3
"""
交叉执行配置调试脚本
用于检查交叉执行配置在各个层级的传递情况
"""

import os
import sys
import json
import requests
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

try:
    from models import db, BotNode
    from app import create_app
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在 mic-bot-service 项目根目录下运行此脚本")
    sys.exit(1)

def check_database_config():
    """检查数据库中的交叉执行配置"""
    print("🔍 检查数据库配置...")
    
    app = create_app()
    with app.app_context():
        try:
            # 查询所有节点
            nodes = BotNode.query.all()
            
            if not nodes:
                print("❌ 数据库中没有找到任何节点")
                return False
            
            print(f"📊 找到 {len(nodes)} 个节点:")
            
            for node in nodes:
                print(f"\n📋 节点: {node.name} (ID: {node.id})")
                print(f"   - 交叉执行配置: {getattr(node, 'search_cross_execution', '字段不存在')}")
                print(f"   - 节点状态: {node.status}")
                print(f"   - 最后签到: {node.last_checkin}")
                
                # 检查字段是否存在
                if hasattr(node, 'search_cross_execution'):
                    print(f"   ✅ search_cross_execution 字段存在")
                else:
                    print(f"   ❌ search_cross_execution 字段不存在")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
            return False

def check_api_config():
    """检查API接口返回的配置"""
    print("\n🔍 检查API接口配置...")
    
    try:
        # 这里需要根据实际情况调整API地址
        base_url = "http://localhost:5000"  # 或者您的实际服务地址
        
        # 检查节点配置API
        api_url = f"{base_url}/bot_api/config"
        
        print(f"📡 请求API: {api_url}")
        
        # 这里需要实际的API token，您需要替换
        headers = {
            'Authorization': 'Bearer YOUR_API_TOKEN',  # 需要替换为实际的token
            'Content-Type': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            config_data = response.json()
            print("✅ API响应成功")
            print(f"📋 配置数据: {json.dumps(config_data, indent=2, ensure_ascii=False)}")
            
            # 检查交叉执行配置
            if 'search_cross_execution' in config_data:
                print(f"✅ 交叉执行配置: {config_data['search_cross_execution']}")
            else:
                print("❌ API响应中缺少 search_cross_execution 配置")
                
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求异常: {e}")
    except Exception as e:
        print(f"❌ API检查失败: {e}")

def check_frontend_config():
    """检查前端配置"""
    print("\n🔍 检查前端配置...")
    
    try:
        # 检查节点管理页面配置
        nodes_html_path = os.path.join(os.path.dirname(__file__), '..', 'project', 'templates', 'nodes.html')
        
        if os.path.exists(nodes_html_path):
            with open(nodes_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查交叉执行相关配置
            if 'search_cross_execution' in content:
                print("✅ 前端模板包含 search_cross_execution 配置")
            else:
                print("❌ 前端模板缺少 search_cross_execution 配置")
                
            if '交叉运行' in content:
                print("✅ 前端模板包含交叉运行UI")
            else:
                print("❌ 前端模板缺少交叉运行UI")
        else:
            print("❌ 找不到前端模板文件")
            
    except Exception as e:
        print(f"❌ 前端配置检查失败: {e}")

def check_node_logs():
    """检查节点日志中的配置信息"""
    print("\n🔍 检查节点配置日志...")
    
    print("📋 请检查以下日志信息:")
    print("1. 节点启动时的配置加载日志")
    print("2. 查找包含 '交叉执行配置' 的日志行")
    print("3. 查找包含 'search_cross_execution' 的日志行")
    print("4. 查找包含 '配置未启用交叉执行' 的日志行")
    
    print("\n🔍 预期的日志格式:")
    print("✅ 正确配置: '🔄 交叉执行配置: 已启用'")
    print("❌ 错误配置: '🔄 交叉执行配置: 未启用' 或 '配置未启用交叉执行'")

def generate_debug_report():
    """生成调试报告"""
    print("\n" + "="*60)
    print("🔍 交叉执行配置调试报告")
    print("="*60)
    print(f"⏰ 调试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查各个层级
    db_ok = check_database_config()
    check_api_config()
    check_frontend_config()
    check_node_logs()
    
    print("\n" + "="*60)
    print("📋 调试建议:")
    print("="*60)
    
    if not db_ok:
        print("1. ❌ 数据库配置有问题，请检查:")
        print("   - 数据库表结构是否正确")
        print("   - search_cross_execution 字段是否存在")
        print("   - 节点配置是否正确设置")
    
    print("2. 🔍 手动检查步骤:")
    print("   - 登录 mic-bot-service 管理界面")
    print("   - 进入节点管理页面")
    print("   - 检查 '交叉运行' 开关是否已开启")
    print("   - 保存配置后重启节点")
    
    print("3. 📊 验证配置传递:")
    print("   - 检查节点启动日志")
    print("   - 查找 '交叉执行配置' 相关日志")
    print("   - 确认配置值是否正确传递")
    
    print("4. 🔧 如果配置仍然无效:")
    print("   - 检查 mic-bot-service 是否重启")
    print("   - 检查 mic-bot-node 是否重启")
    print("   - 检查数据库连接是否正常")

if __name__ == "__main__":
    generate_debug_report()
