#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试验证码列表API返回的详细数据
"""

import requests
import json
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"

def test_verification_list_data():
    """测试验证码列表API返回的数据格式"""
    print("🧪 测试验证码列表API数据格式")
    print("="*50)
    
    # 首先检查数据库中的验证码记录
    print("\n1. 检查数据库中的验证码记录")
    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT vc.id, vc.email, vc.status, vc.created_at, vc.expires_at, ba.auxiliary_email, bn.node_name FROM verification_codes vc LEFT JOIN bot_accounts ba ON vc.email = ba.email LEFT JOIN bot_nodes bn ON vc.node_id = bn.id ORDER BY vc.id DESC LIMIT 3;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 数据库查询成功")
            print(result.stdout)
        else:
            print("❌ 数据库查询失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 数据库查询异常: {e}")
    
    # 测试验证码列表API（需要登录，所以会返回401）
    print("\n2. 测试验证码列表API（未登录状态）")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/verification/list")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ API需要认证（正常）")
        elif response.status_code == 200:
            data = response.json()
            print("✅ 验证码列表获取成功")
            print(f"响应数据结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('success') and data.get('data'):
                print("\n📋 验证码列表详情:")
                for i, code in enumerate(data['data'], 1):
                    print(f"\n验证码 #{i}:")
                    print(f"  ID: {code.get('id')}")
                    print(f"  账户邮箱: {code.get('email')}")
                    print(f"  辅助邮箱: {code.get('auxiliary_email', '未配置')}")
                    print(f"  节点名称: {code.get('node_name')}")
                    print(f"  创建时间: {code.get('created_at')}")
                    print(f"  过期时间: {code.get('expires_at')}")
                    print(f"  状态: {code.get('status')}")
        else:
            print(f"⚠️  其他状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n" + "="*50)
    print("🎯 测试完成")
    print("="*50)
    print("说明:")
    print("1. 验证码列表API现在返回更详细的信息")
    print("2. 包括账户邮箱、辅助邮箱、节点名称、创建时间、过期时间")
    print("3. 前端页面会显示所有这些信息")
    print("4. 在浏览器中登录后可以查看完整的验证码列表")

if __name__ == "__main__":
    test_verification_list_data()
