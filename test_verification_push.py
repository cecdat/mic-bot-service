#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码推送功能测试脚本
测试验证码提醒推送功能是否正常工作
"""

import requests
import subprocess
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"
NODE_TOKEN = "d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077"

def test_verification_push():
    """测试验证码推送功能"""
    print("🔔 测试验证码推送功能")
    print("="*50)
    
    # 1. 检查推送配置
    print("1. 检查推送配置")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/push_configs")
        if response.status_code == 200:
            configs = response.json()
            print(f"✅ 找到 {len(configs)} 个推送配置")
            
            # 检查是否有启用验证码推送的配置
            verification_configs = [c for c in configs if c.get('notify_on_verification_code')]
            if verification_configs:
                print(f"✅ 找到 {len(verification_configs)} 个启用验证码推送的配置")
                for config in verification_configs:
                    print(f"   - {config['url']}")
            else:
                print("⚠️  没有找到启用验证码推送的配置")
                print("   请在推送配置页面启用'验证码提醒'选项")
        else:
            print(f"❌ 获取推送配置失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查推送配置异常: {e}")
    
    # 2. 测试验证码请求（会触发推送）
    print("\n2. 测试验证码请求（触发推送）")
    try:
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/request",
            json={"email": "test@example.com"},
            headers={
                "Authorization": f"Bearer {NODE_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                verification_id = data.get('verification_id')
                print(f"✅ 验证码请求创建成功，ID: {verification_id}")
                print("📱 如果配置了验证码推送，应该会收到推送通知")
            else:
                print(f"❌ 验证码请求失败: {data.get('message')}")
        else:
            print(f"❌ 验证码请求HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 测试验证码请求异常: {e}")
    
    # 3. 检查数据库中的验证码记录
    print("\n3. 检查验证码记录")
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT id, email, status, created_at FROM verification_codes ORDER BY id DESC LIMIT 3;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 数据库查询成功")
            print(result.stdout)
        else:
            print("❌ 数据库查询失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 检查验证码记录异常: {e}")

def show_push_config_guide():
    """显示推送配置指南"""
    print("\n" + "="*60)
    print("📋 验证码推送配置指南")
    print("="*60)
    print("要启用验证码推送功能，请按以下步骤操作:")
    print()
    print("1. 打开Service端管理界面")
    print("   http://localhost:2002")
    print()
    print("2. 登录后点击左侧导航栏的'推送配置'")
    print()
    print("3. 添加或编辑推送配置:")
    print("   - 输入Bark URL (例如: https://api.day.app/YOUR_KEY/)")
    print("   - 启用'验证码提醒'开关")
    print("   - 保存配置")
    print()
    print("4. 推送通知内容包含:")
    print("   - 标题: 验证码请求 - [节点名称]")
    print("   - 内容: 账户邮箱、辅助邮箱、节点名称、时间")
    print()
    print("5. 测试推送功能:")
    print("   - 让Node端执行需要验证码的登录任务")
    print("   - 检查是否收到推送通知")
    print()
    print("🔔 推送通知示例:")
    print("标题: 验证码请求 - localhost")
    print("内容:")
    print("账户: hehaipi@outlook.com")
    print("辅助邮箱: hehaipi@qq.com")
    print("节点: localhost")
    print("时间: 2025-01-19 16:30:00")
    print("请及时处理验证码")

def main():
    print("🔔 验证码推送功能测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_verification_push()
    show_push_config_guide()
    
    print("\n" + "="*60)
    print("🎯 测试完成")
    print("请按照上述指南配置验证码推送功能")
    print("="*60)

if __name__ == "__main__":
    main()
