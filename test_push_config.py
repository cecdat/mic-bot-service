#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送配置API测试脚本
测试推送配置的增删改查功能
"""

import requests
import json
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"

def test_push_config_api():
    """测试推送配置API"""
    print("🔧 测试推送配置API")
    print("="*50)
    
    # 1. 获取当前配置
    print("1. 获取当前推送配置")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/push_configs")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            configs = response.json()
            print(f"✅ 找到 {len(configs)} 个配置")
            for config in configs:
                print(f"   ID: {config['id']}, URL: {config['url']}")
                print(f"   节点上线: {config.get('notify_on_node_online', False)}")
                print(f"   节点离线: {config.get('notify_on_node_offline', False)}")
                print(f"   账户异常: {config.get('notify_on_account_error', False)}")
                print(f"   验证码提醒: {config.get('notify_on_verification_code', False)}")
        else:
            print(f"❌ 获取配置失败: {response.text}")
    except Exception as e:
        print(f"❌ 获取配置异常: {e}")
    
    # 2. 测试添加新配置
    print("\n2. 测试添加新配置")
    try:
        new_config = {
            "url": "https://api.day.app/test_key/",
            "notify_on_node_online": True,
            "notify_on_node_offline": False,
            "notify_on_account_error": True,
            "notify_on_verification_code": True
        }
        
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/push_configs",
            json=new_config,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 添加配置结果: {result}")
        else:
            print(f"❌ 添加配置失败: {response.text}")
    except Exception as e:
        print(f"❌ 添加配置异常: {e}")
    
    # 3. 再次获取配置验证
    print("\n3. 验证配置是否添加成功")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/push_configs")
        if response.status_code == 200:
            configs = response.json()
            print(f"✅ 现在有 {len(configs)} 个配置")
            for config in configs:
                print(f"   ID: {config['id']}, URL: {config['url']}")
                print(f"   验证码提醒: {config.get('notify_on_verification_code', False)}")
    except Exception as e:
        print(f"❌ 验证配置异常: {e}")

def test_verification_push_trigger():
    """测试验证码推送触发"""
    print("\n🔔 测试验证码推送触发")
    print("="*50)
    
    try:
        # 模拟Node端请求验证码
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/request",
            json={"email": "test_push@example.com"},
            headers={
                "Authorization": "Bearer d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077",
                "Content-Type": "application/json"
            }
        )
        
        print(f"验证码请求状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 验证码请求成功: {result}")
            print("📱 如果配置了验证码推送，应该会收到推送通知")
        else:
            print(f"❌ 验证码请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 验证码推送测试异常: {e}")

def main():
    print("🔧 推送配置API测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_push_config_api()
    test_verification_push_trigger()
    
    print("\n" + "="*60)
    print("🎯 测试完成")
    print("请检查Service端日志以查看推送通知是否发送")
    print("="*60)

if __name__ == "__main__":
    main()
