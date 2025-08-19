#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

# 配置
SERVICE_BASE_URL = "http://localhost:2002"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def login():
    """登录获取session"""
    session = requests.Session()
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    response = session.post(f"{SERVICE_BASE_URL}/web_api/login", json=login_data)
    if response.status_code == 200:
        print("✅ 登录成功")
        return session
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return None

def check_push_configs(session):
    """检查推送配置"""
    print("\n🔍 检查推送配置...")
    
    response = session.get(f"{SERVICE_BASE_URL}/web_api/push_configs")
    if response.status_code == 200:
        configs = response.json()
        print(f"✅ 获取到 {len(configs)} 个推送配置")
        
        for i, config in enumerate(configs, 1):
            print(f"\n配置 {i}:")
            print(f"  URL: {config.get('url', 'N/A')}")
            print(f"  节点上线: {config.get('notify_on_node_online', False)}")
            print(f"  节点离线: {config.get('notify_on_node_offline', False)}")
            print(f"  账户异常: {config.get('notify_on_account_error', False)}")
            print(f"  验证码提醒: {config.get('notify_on_verification_code', False)}")
            
            # 检查是否有验证码推送配置
            if config.get('notify_on_verification_code'):
                print("  ✅ 验证码推送已启用")
            else:
                print("  ❌ 验证码推送未启用")
        
        return configs
    else:
        print(f"❌ 获取推送配置失败: {response.status_code}")
        return []

def test_verification_push_trigger(session):
    """测试验证码推送触发"""
    print("\n🧪 测试验证码推送触发...")
    
    # 模拟验证码请求
    test_data = {
        "email": "test@example.com"
    }
    
    # 使用一个测试token（需要替换为实际的token）
    headers = {
        "Authorization": "Bearer d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077"
    }
    
    response = requests.post(
        f"{SERVICE_BASE_URL}/web_api/verification/request",
        json=test_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 验证码请求成功: {result}")
        return result.get('verification_id')
    else:
        print(f"❌ 验证码请求失败: {response.status_code} - {response.text}")
        return None

def check_database_push_configs():
    """直接检查数据库中的推送配置"""
    print("\n🗄️ 检查数据库中的推送配置...")
    
    import subprocess
    
    try:
        # 查询推送配置
        result = subprocess.run([
            "docker", "exec", "postgres-db-service", "psql", 
            "-U", "user", "-d", "rewards_db",
            "-c", "SELECT id, url, notify_on_verification_code, status FROM push_configs;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 数据库查询成功:")
            print(result.stdout)
        else:
            print(f"❌ 数据库查询失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 数据库查询异常: {e}")

def test_push_notification_direct():
    """直接测试推送通知"""
    print("\n📱 直接测试推送通知...")
    
    try:
        from project.push import trigger_push_notification
        
        # 直接调用推送函数
        trigger_push_notification(
            'verification_code',
            "测试验证码推送",
            "这是一个测试推送消息\n时间: " + time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        print("✅ 推送通知已发送")
        
    except Exception as e:
        print(f"❌ 推送通知失败: {e}")

def main():
    print("🚀 开始检查推送管理模块")
    print("=" * 50)
    
    # 登录
    session = login()
    if not session:
        return
    
    # 检查推送配置
    configs = check_push_configs(session)
    
    # 检查数据库
    check_database_push_configs()
    
    # 测试验证码推送触发
    verification_id = test_verification_push_trigger(session)
    
    # 直接测试推送
    test_push_notification_direct()
    
    print("\n" + "=" * 50)
    print("📋 检查结果总结:")
    
    if configs:
        verification_enabled = any(config.get('notify_on_verification_code') for config in configs)
        if verification_enabled:
            print("✅ 验证码推送配置已启用")
        else:
            print("❌ 验证码推送配置未启用")
            print("💡 请在推送配置页面启用验证码提醒开关")
    else:
        print("❌ 没有找到推送配置")
        print("💡 请在推送配置页面添加Bark URL")
    
    if verification_id:
        print("✅ 验证码推送触发测试成功")
    else:
        print("❌ 验证码推送触发测试失败")

if __name__ == "__main__":
    main()
