#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试验证码API
"""

import requests
import json
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"
NODE_TOKEN = "d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077"

def test_verification_api():
    """测试验证码API"""
    print("🔧 测试验证码API")
    print("="*50)
    
    # 测试验证码请求
    print("1. 测试验证码请求")
    try:
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/request",
            json={"email": "test_debug@example.com"},
            headers={
                "Authorization": f"Bearer {NODE_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 验证码请求成功: {result}")
            
            # 检查验证码记录
            verification_id = result.get('verification_id')
            if verification_id:
                print(f"验证码ID: {verification_id}")
                
                # 测试检查验证码状态
                print("\n2. 测试检查验证码状态")
                check_response = requests.get(
                    f"{SERVICE_BASE_URL}/web_api/verification/check/{verification_id}",
                    headers={
                        "Authorization": f"Bearer {NODE_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"检查状态码: {check_response.status_code}")
                if check_response.status_code == 200:
                    check_result = check_response.json()
                    print(f"✅ 检查验证码状态成功: {check_result}")
                else:
                    print(f"❌ 检查验证码状态失败: {check_response.text}")
        else:
            print(f"❌ 验证码请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试验证码API异常: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔧 验证码API测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_verification_api()
    
    print("\n" + "="*60)
    print("🎯 测试完成")
    print("请检查Service端日志以查看推送通知是否发送")
    print("="*60)

if __name__ == "__main__":
    main()
