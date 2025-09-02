#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送功能诊断脚本
用于排查推送不工作的问题
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

def check_service_status():
    """检查服务状态"""
    print("=== 检查服务状态 ===")
    
    try:
        response = requests.get("http://localhost:2002/", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正在运行")
            return True
        else:
            print(f"⚠️  服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return False

def check_push_configs():
    """检查推送配置"""
    print("\n=== 检查推送配置 ===")
    
    try:
        response = requests.get("http://localhost:2002/web_api/push_configs")
        
        if response.status_code == 200:
            configs = response.json()
            print(f"✅ 找到 {len(configs)} 个推送配置:")
            
            if not configs:
                print("⚠️  没有配置任何推送URL")
                return False
            
            for config in configs:
                print(f"  - ID: {config.get('id')}")
                print(f"    URL: {config.get('url')}")
                print(f"    状态: {config.get('status')}")
                print(f"    节点上线: {config.get('notify_on_node_online')}")
                print(f"    节点离线: {config.get('notify_on_node_offline')}")
                print(f"    账户异常: {config.get('notify_on_account_error')}")
                print(f"    验证码提醒: {config.get('notify_on_verification_code')}")
                print()
            
            return True
        else:
            print(f"❌ 获取推送配置失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 检查推送配置时出错: {e}")
        return False

def test_push_notification():
    """测试推送通知"""
    print("\n=== 测试推送通知 ===")
    
    test_cases = [
        {
            "event_type": "node_online",
            "title": "节点上线测试",
            "body": f"测试节点已上线 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        },
        {
            "event_type": "account_error",
            "title": "账户异常测试", 
            "body": f"测试账户出现异常 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        },
        {
            "event_type": "verification_code",
            "title": "验证码提醒测试",
            "body": f"需要输入验证码 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['event_type']} 事件...")
        
        try:
            response = requests.post(
                "http://localhost:2002/bot_api/test_push",
                json=test_case,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API调用成功: {result}")
            else:
                print(f"❌ API调用失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 测试时出错: {e}")

def check_database_connection():
    """检查数据库连接"""
    print("\n=== 检查数据库连接 ===")
    
    try:
        # 尝试连接数据库
        from project.db import db
        from project.models import PushConfig
        
        # 查询推送配置数量
        count = PushConfig.query.count()
        print(f"✅ 数据库连接正常，推送配置数量: {count}")
        
        # 查询启用的推送配置
        active_configs = PushConfig.query.filter_by(status=1).all()
        print(f"✅ 启用的推送配置数量: {len(active_configs)}")
        
        for config in active_configs:
            print(f"  - URL: {config.url}")
            print(f"    订阅事件: ", end="")
            events = []
            if config.notify_on_node_online:
                events.append("节点上线")
            if config.notify_on_node_offline:
                events.append("节点离线")
            if config.notify_on_account_error:
                events.append("账户异常")
            if config.notify_on_verification_code:
                events.append("验证码提醒")
            print(", ".join(events) if events else "无")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def check_bark_url_format():
    """检查Bark URL格式"""
    print("\n=== 检查Bark URL格式 ===")
    
    try:
        response = requests.get("http://localhost:2002/web_api/push_configs")
        
        if response.status_code == 200:
            configs = response.json()
            
            for config in configs:
                url = config.get('url', '')
                print(f"检查URL: {url}")
                
                if not url:
                    print("  ❌ URL为空")
                    continue
                
                if not url.startswith(('https://api.day.app/', 'http://api.day.app/')):
                    print("  ❌ 不是有效的Bark URL格式")
                    continue
                
                if not url.endswith('/'):
                    print("  ⚠️  URL应该以斜杠结尾")
                
                print("  ✅ URL格式正确")
                
                # 测试URL可访问性
                try:
                    test_url = f"{url.rstrip('/')}/测试/测试内容"
                    response = requests.get(test_url, timeout=5)
                    print(f"  ✅ URL可访问，响应状态: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ URL不可访问: {e}")
        
    except Exception as e:
        print(f"❌ 检查URL格式时出错: {e}")

def check_logs():
    """检查日志"""
    print("\n=== 检查推送相关日志 ===")
    
    try:
        # 这里可以添加检查应用日志的逻辑
        print("请检查应用日志中是否有推送相关的错误信息")
        print("常见问题:")
        print("1. 数据库连接失败")
        print("2. 推送配置查询失败")
        print("3. Bark URL格式错误")
        print("4. 网络连接问题")
        print("5. Bark服务不可用")
        
    except Exception as e:
        print(f"❌ 检查日志时出错: {e}")

def main():
    """主函数"""
    print("推送功能诊断开始...")
    print("=" * 50)
    
    # 检查服务状态
    if not check_service_status():
        print("\n❌ 服务未运行，请先启动服务")
        print("启动命令: docker-compose up -d")
        return
    
    # 检查数据库连接
    if not check_database_connection():
        print("\n❌ 数据库连接失败")
        return
    
    # 检查推送配置
    if not check_push_configs():
        print("\n❌ 没有配置推送URL")
        print("请在网页界面添加推送配置")
        return
    
    # 检查Bark URL格式
    check_bark_url_format()
    
    # 测试推送通知
    test_push_notification()
    
    # 检查日志
    check_logs()
    
    print("\n" + "=" * 50)
    print("诊断完成!")
    print("\n如果推送仍然不工作，请检查:")
    print("1. Bark应用是否正确安装和配置")
    print("2. Bark URL是否正确")
    print("3. 网络连接是否正常")
    print("4. 应用日志中的错误信息")

if __name__ == "__main__":
    main()
