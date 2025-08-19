#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码推送功能测试脚本
测试验证码提醒推送功能是否正常工作
"""

import requests
import time

# 配置
SERVICE_BASE_URL = "http://localhost:2002"
NODE_TOKEN = "d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077"

def test_verification_request():
    """测试验证码请求并检查推送"""
    print("🧪 测试验证码请求...")
    
    # 模拟验证码请求
    test_data = {
        "email": "test@example.com"
    }
    
    headers = {
        "Authorization": f"Bearer {NODE_TOKEN}"
    }
    
    try:
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/request",
            json=test_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 验证码请求成功: {result}")
            verification_id = result.get('verification_id')
            
            if verification_id:
                print(f"📝 验证码ID: {verification_id}")
                return verification_id
            else:
                print("❌ 未获取到验证码ID")
                return None
        else:
            print(f"❌ 验证码请求失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 验证码请求异常: {e}")
        return None

def check_verification_status(verification_id):
    """检查验证码状态"""
    print(f"\n🔍 检查验证码状态 (ID: {verification_id})...")
    
    headers = {
        "Authorization": f"Bearer {NODE_TOKEN}"
    }
    
    try:
        response = requests.get(
            f"{SERVICE_BASE_URL}/web_api/verification/check/{verification_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 验证码状态: {result}")
            return result
        else:
            print(f"❌ 检查验证码状态失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 检查验证码状态异常: {e}")
        return None

def check_service_logs():
    """检查服务日志"""
    print("\n📋 检查服务日志...")
    
    import subprocess
    
    try:
        result = subprocess.run([
            "docker", "logs", "api", "--tail", "20"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 服务日志:")
            print(result.stdout)
        else:
            print(f"❌ 获取服务日志失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 检查服务日志异常: {e}")

def main():
    print("🚀 开始测试验证码推送功能")
    print("=" * 50)
    
    # 测试验证码请求
    verification_id = test_verification_request()
    
    if verification_id:
        # 等待一下让推送发送
        print("\n⏳ 等待推送发送...")
        time.sleep(2)
        
        # 检查验证码状态
        check_verification_status(verification_id)
        
        # 检查服务日志
        check_service_logs()
    
    print("\n" + "=" * 50)
    print("📋 测试完成")
    print("\n💡 如果推送没有收到，请检查:")
    print("1. 推送配置页面是否启用了验证码提醒")
    print("2. Bark URL是否正确")
    print("3. 网络连接是否正常")

if __name__ == "__main__":
    main()
