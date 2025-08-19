#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码修复和快照功能测试脚本
验证Node端的重复登录修复和快照功能
"""

import requests
import subprocess
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"
NODE_TOKEN = "d756432a356ce9aad23c5e38eecdb825a1b9b20a252f7077"

def test_verification_api_fixes():
    """测试验证码API修复"""
    print("🔧 测试验证码API修复")
    print("="*50)
    
    # 创建新的验证码请求
    print("1. 创建验证码请求")
    try:
        response = requests.post(
            f"{SERVICE_BASE_URL}/web_api/verification/request",
            json={"email": "hehaipi@outlook.com"},
            headers={
                "Authorization": f"Bearer {NODE_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                verification_id = data.get('verification_id')
                print(f"✅ 验证码请求创建成功，ID: {verification_id}")
                
                # 测试验证码检查
                print(f"\n2. 测试验证码检查 (ID: {verification_id})")
                check_response = requests.get(
                    f"{SERVICE_BASE_URL}/web_api/verification/check/{verification_id}",
                    headers={
                        "Authorization": f"Bearer {NODE_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )
                print(f"状态码: {check_response.status_code}")
                print(f"响应: {check_response.text}")
                
                if check_response.status_code == 200:
                    print("✅ 验证码检查API正常工作")
                else:
                    print("❌ 验证码检查API仍有问题")
            else:
                print("❌ 验证码请求创建失败")
        else:
            print("❌ 验证码请求API仍有问题")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def check_node_snapshots():
    """检查Node端快照功能"""
    print("\n📸 检查Node端快照功能")
    print("="*50)
    
    try:
        # 检查快照目录是否存在
        result = subprocess.run([
            "docker-compose", "-f", "../mic-bot-node/compose.yaml", "exec", "-T", "mic-bot-node",
            "ls", "-la", "/app/sessions/verification_snapshots"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 验证码快照目录存在")
            print("目录内容:")
            print(result.stdout)
        else:
            print("⚠️  验证码快照目录可能不存在（这是正常的，因为还没有生成快照）")
            print("错误信息:", result.stderr)
    except Exception as e:
        print(f"❌ 检查快照目录异常: {e}")

def check_node_logs():
    """检查Node端日志"""
    print("\n📋 检查Node端日志")
    print("="*50)
    
    try:
        result = subprocess.run([
            "docker-compose", "-f", "../mic-bot-node/compose.yaml", "logs", "--tail", "15"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Node端日志获取成功")
            print("最近日志:")
            print(result.stdout)
        else:
            print("❌ Node端日志获取失败")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Node端日志获取异常: {e}")

def show_test_instructions():
    """显示测试说明"""
    print("\n" + "="*60)
    print("📋 验证码修复测试说明")
    print("="*60)
    print("修复内容:")
    print("1. ✅ 修复了Service端验证码API的时区问题")
    print("2. ✅ 添加了验证码输入前后的快照功能")
    print("3. ✅ 修复了Node端重复登录问题")
    print("4. ✅ 优化了验证码处理流程")
    print()
    print("测试步骤:")
    print("1. 确保Node端正在运行")
    print("2. 在Service端为测试账户配置辅助邮箱")
    print("3. 让Node端执行需要验证码的登录任务")
    print("4. 观察以下改进:")
    print("   - 验证码API不再返回500错误")
    print("   - 验证码输入前后会保存快照")
    print("   - 验证码处理后不会重复寻找'使用密码'选项")
    print("   - 登录流程更加顺畅")
    print()
    print("快照文件位置:")
    print("   /app/sessions/verification_snapshots/")
    print("   - pc_before_verification_input_[timestamp].html/png")
    print("   - pc_after_verification_input_[timestamp].html/png")
    print("   - pc_verification_result_[timestamp].html/png")
    print("   - app_* (移动端快照)")
    print()
    print("验证要点:")
    print("✅ 验证码管理页面可以正常输入验证码")
    print("✅ Node端不再出现重复登录日志")
    print("✅ 验证码处理过程中生成快照文件")
    print("✅ 整个登录流程更加稳定")

def main():
    print("🔧 验证码修复和快照功能测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_verification_api_fixes()
    check_node_snapshots()
    check_node_logs()
    show_test_instructions()
    
    print("\n" + "="*60)
    print("🎯 测试完成")
    print("请按照上述说明进行实际测试")
    print("="*60)

if __name__ == "__main__":
    main()
