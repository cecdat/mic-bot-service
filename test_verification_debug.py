#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码调试脚本
检查验证码记录和API状态
"""

import requests
import subprocess
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"
NODE_TOKEN = "d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077"

def check_verification_records():
    """检查数据库中的验证码记录"""
    print("🔍 检查数据库中的验证码记录")
    print("="*50)
    
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT id, node_id, email, status, created_at, expires_at FROM verification_codes ORDER BY id DESC;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 数据库查询成功")
            print(result.stdout)
        else:
            print("❌ 数据库查询失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 数据库查询异常: {e}")

def test_verification_api():
    """测试验证码API"""
    print("\n🧪 测试验证码API")
    print("="*50)
    
    # 测试ID为3的验证码（Node端正在请求的）
    print("1. 测试ID为3的验证码检查")
    try:
        response = requests.get(
            f"{SERVICE_BASE_URL}/web_api/verification/check/3",
            headers={
                "Authorization": f"Bearer {NODE_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 测试ID为4的验证码（数据库中存在的）
    print("\n2. 测试ID为4的验证码检查")
    try:
        response = requests.get(
            f"{SERVICE_BASE_URL}/web_api/verification/check/4",
            headers={
                "Authorization": f"Bearer {NODE_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_verification_request():
    """测试创建验证码请求"""
    print("\n🧪 测试创建验证码请求")
    print("="*50)
    
    try:
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/request",
            json={"email": "hehaipi@qq.com"},
            headers={
                "Authorization": f"Bearer {NODE_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def check_node_logs():
    """检查Node端日志"""
    print("\n📋 检查Node端日志")
    print("="*50)
    
    try:
        result = subprocess.run([
            "docker-compose", "-f", "../mic-bot-node/compose.yaml", "logs", "--tail", "10"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Node端日志获取成功")
            print(result.stdout)
        else:
            print("❌ Node端日志获取失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Node端日志获取异常: {e}")

def main():
    print("🔧 验证码调试工具")
    print("="*60)
    print(f"调试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_verification_records()
    test_verification_api()
    test_verification_request()
    check_node_logs()
    
    print("\n" + "="*60)
    print("🎯 调试完成")
    print("="*60)

if __name__ == "__main__":
    main()
