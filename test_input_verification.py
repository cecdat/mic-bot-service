#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试验证码输入功能
"""

import requests
import json

SERVICE_BASE_URL = "http://localhost:2002"

def test_verification_input():
    """测试验证码输入功能"""
    print("🧪 测试验证码输入功能")
    print("="*50)
    
    # 首先检查数据库中的验证码记录
    print("\n1. 检查数据库中的验证码记录")
    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT id, email, status, created_at, expires_at FROM verification_codes ORDER BY id DESC LIMIT 3;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 数据库查询成功")
            print(result.stdout)
        else:
            print("❌ 数据库查询失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 数据库查询异常: {e}")
    
    # 测试验证码输入API（需要登录，所以会返回401）
    print("\n2. 测试验证码输入API（未登录状态）")
    try:
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/input/2",
            json={"code": "123456"},
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ API需要认证（正常）")
        elif response.status_code == 200:
            print("✅ 验证码输入成功")
            print(f"响应: {response.json()}")
        else:
            print(f"⚠️  其他状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n" + "="*50)
    print("🎯 测试完成")
    print("="*50)
    print("说明:")
    print("1. 验证码输入API需要登录才能访问")
    print("2. 在浏览器中登录后可以正常输入验证码")
    print("3. 修复了时区问题，现在应该不会出现500错误")

if __name__ == "__main__":
    test_verification_input()
