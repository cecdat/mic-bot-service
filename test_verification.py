#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码流程测试脚本
"""

import requests
import json
import time
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"
NODE_TOKEN = "test_token_123"  # 这个token需要与数据库中的hash匹配
TEST_EMAIL = "test@example.com"

def test_verification_flow():
    print("🚀 开始测试验证码流程")
    
    # 步骤1: 创建验证码请求
    print("\n步骤1: 创建验证码请求")
    create_url = f"{SERVICE_BASE_URL}/web_api/verification/request"
    create_data = {"email": TEST_EMAIL}
    create_headers = {
        "Authorization": f"Bearer {NODE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        create_response = requests.post(create_url, json=create_data, headers=create_headers)
        print(f"状态码: {create_response.status_code}")
        print(f"响应: {create_response.json()}")
        
        if create_response.status_code == 200:
            verification_id = create_response.json().get('verification_id')
            print(f"✅ 验证码请求创建成功，ID: {verification_id}")
            
            # 步骤2: 检查验证码状态
            print("\n步骤2: 检查验证码状态")
            check_url = f"{SERVICE_BASE_URL}/web_api/verification/check/{verification_id}"
            check_response = requests.get(check_url, headers=create_headers)
            print(f"状态码: {check_response.status_code}")
            print(f"响应: {check_response.json()}")
            
            # 步骤3: 模拟等待验证码
            print("\n步骤3: 模拟等待验证码（30秒）")
            start_time = time.time()
            while time.time() - start_time < 30:
                elapsed = int(time.time() - start_time)
                remaining = 30 - elapsed
                print(f"⏳ 等待验证码输入...{remaining}s")
                
                check_response = requests.get(check_url, headers=create_headers)
                if check_response.status_code == 200:
                    result = check_response.json()
                    if result.get('status') == 'completed':
                        print(f"✅ 收到验证码: {result.get('code')}")
                        break
                
                time.sleep(3)
            
        else:
            print("❌ 创建验证码请求失败")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_verification_flow()
