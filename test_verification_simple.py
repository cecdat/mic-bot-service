#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单验证码API测试脚本
"""

import requests
import json
import time
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"

def test_api_endpoints():
    """测试验证码相关的API端点"""
    print("🧪 测试验证码API端点")
    print("="*50)
    
    # 测试1: 验证码列表接口（需要登录）
    print("\n1. 测试验证码列表接口")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/verification/list")
        print(f"状态码: {response.status_code}")
        if response.status_code == 401:
            print("✅ 接口存在且需要认证（正常）")
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试2: 验证码页面接口
    print("\n2. 测试验证码页面接口")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/verification")
        print(f"状态码: {response.status_code}")
        if response.status_code == 302:
            print("✅ 页面重定向到登录（正常）")
        elif response.status_code == 200:
            print("✅ 页面可以访问")
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试3: 检查Service端状态
    print("\n3. 检查Service端状态")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/")
        print(f"状态码: {response.status_code}")
        if response.status_code == 302:
            print("✅ Service端正常运行，重定向到登录")
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*50)
    print("🗄️  测试数据库连接")
    print("="*50)
    
    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT COUNT(*) FROM verification_codes;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 数据库连接正常")
            print(f"验证码表记录数: {result.stdout.strip()}")
        else:
            print("❌ 数据库连接失败")
            print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"❌ 数据库测试异常: {e}")

def main():
    print("🧪 验证码系统测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_api_endpoints()
    test_database_connection()
    
    print("\n" + "="*50)
    print("🎯 测试完成")
    print("="*50)
    print("提示:")
    print("1. 确保Service端正在运行: docker-compose up -d")
    print("2. 确保Node端正在运行")
    print("3. 在Service端验证码管理页面可以查看验证码")
    print("4. Node端等待验证码时间已修改为300秒")
    print("5. Node端日志会显示倒计时: 等待验证码输入...300s")

if __name__ == "__main__":
    main()
