#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动验证码流程测试
指导用户完成真实的验证码流程测试
"""

import requests
import json
import subprocess
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"

def test_verification_page_display():
    """测试验证码管理页面显示"""
    print("🧪 验证码管理页面显示测试")
    print("="*50)
    
    # 检查数据库中的验证码记录
    print("\n1. 检查数据库中的验证码记录")
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT vc.id, vc.email, vc.status, vc.created_at, ba.auxiliary_email, bn.node_name FROM verification_codes vc LEFT JOIN bot_accounts ba ON vc.email = ba.email LEFT JOIN bot_nodes bn ON vc.node_id = bn.id ORDER BY vc.id DESC LIMIT 3;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 数据库查询成功")
            print(result.stdout)
        else:
            print("❌ 数据库查询失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 数据库查询异常: {e}")
    
    # 测试验证码管理页面访问
    print("\n2. 测试验证码管理页面访问")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/verification")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 验证码管理页面可以正常访问")
            if "主账户" in response.text:
                print("✅ 页面显示'主账户'标签（修复成功）")
            else:
                print("⚠️  页面可能未显示'主账户'标签")
        elif response.status_code == 302:
            print("✅ 页面重定向到登录（正常）")
        else:
            print(f"⚠️  其他状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n" + "="*50)
    print("🎯 显示测试完成")
    print("="*50)

def show_manual_test_guide():
    """显示手动测试指南"""
    print("\n" + "="*60)
    print("📋 手动验证码流程测试指南")
    print("="*60)
    print("请按以下步骤完成真实的验证码流程测试:")
    print()
    
    print("🔧 准备工作:")
    print("1. 确保Service端正在运行:")
    print("   docker-compose up -d")
    print()
    print("2. 确保Node端正在运行:")
    print("   cd ../mic-bot-node")
    print("   docker-compose up -d")
    print()
    print("3. 检查账户配置:")
    print("   在Service端账户管理页面确认测试账户已配置辅助邮箱")
    print()
    
    print("🚀 测试流程:")
    print("步骤1: 触发验证码请求")
    print("   - 让Node端执行需要验证码的登录任务")
    print("   - 确保Node端配置了正确的辅助邮箱")
    print("   - Node端会自动调用Service端API创建验证码请求")
    print()
    
    print("步骤2: 查看验证码管理页面")
    print("   - 打开浏览器访问: http://localhost:2002")
    print("   - 登录Service端管理界面")
    print("   - 点击左侧导航栏的'验证码管理'")
    print("   - 查看是否有新的验证码请求")
    print("   - 确认显示信息正确:")
    print("     * 主账户: [主账户邮箱]")
    print("     * 节点: [节点名称]")
    print("     * 辅助邮箱: [辅助邮箱地址]")
    print("     * 创建时间: [时间]")
    print("     * 过期时间: [时间]")
    print("     * 剩余时间: [倒计时]")
    print()
    
    print("步骤3: 输入验证码")
    print("   - 在验证码管理页面点击'输入验证码'按钮")
    print("   - 在弹出的对话框中输入6位数字验证码")
    print("   - 点击确认提交")
    print("   - 验证码状态应该变为'已完成'")
    print()
    
    print("步骤4: 验证Node端接收")
    print("   - 查看Node端日志:")
    print("     cd ../mic-bot-node")
    print("     docker-compose logs -f")
    print("   - 应该看到以下日志:")
    print("     * '成功获取验证码: [验证码]'")
    print("     * '已填入验证码: [验证码]'")
    print("     * 继续执行后续流程")
    print()
    
    print("步骤5: 验证流程完成")
    print("   - Node端应该成功完成验证码验证")
    print("   - 继续执行登录或其他任务")
    print("   - Service端验证码记录状态为'completed'")
    print()
    
    print("🔍 验证要点:")
    print("✅ 验证码管理页面显示'主账户'而不是'账户'")
    print("✅ 显示正确的辅助邮箱信息")
    print("✅ 倒计时功能正常工作")
    print("✅ 输入验证码后Node端能收到")
    print("✅ 整个流程无错误完成")
    print()
    
    print("🐛 故障排除:")
    print("如果遇到问题，请检查:")
    print("1. Service端和Node端是否都正常运行")
    print("2. 账户是否配置了正确的辅助邮箱")
    print("3. Node端API配置是否正确")
    print("4. 网络连接是否正常")
    print("5. 查看Service端和Node端日志")
    print()

def check_current_status():
    """检查当前状态"""
    print("\n" + "="*50)
    print("📊 当前系统状态检查")
    print("="*50)
    
    # 检查Service端状态
    print("\n1. Service端状态:")
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/")
        print(f"   状态码: {response.status_code}")
        if response.status_code in [200, 302]:
            print("   ✅ Service端正常运行")
        else:
            print("   ❌ Service端可能有问题")
    except Exception as e:
        print(f"   ❌ Service端连接失败: {e}")
    
    # 检查数据库连接
    print("\n2. 数据库状态:")
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db", 
            "psql", "-U", "user", "-d", "rewards_db", 
            "-c", "SELECT COUNT(*) FROM verification_codes;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ 数据库连接正常")
            print(f"   验证码记录数: {result.stdout.strip()}")
        else:
            print("   ❌ 数据库连接失败")
    except Exception as e:
        print(f"   ❌ 数据库检查异常: {e}")
    
    # 检查Node端状态
    print("\n3. Node端状态:")
    try:
        result = subprocess.run([
            "docker-compose", "-f", "../mic-bot-node/compose.yaml", "ps"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ Node端容器状态正常")
        else:
            print("   ❌ Node端可能未运行")
    except Exception as e:
        print(f"   ❌ Node端检查异常: {e}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    print("🧪 验证码流程手动测试工具")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_verification_page_display()
    check_current_status()
    show_manual_test_guide()
    
    print("\n" + "="*60)
    print("🎯 测试工具运行完成")
    print("请按照上述指南进行手动测试")
    print("="*60)
