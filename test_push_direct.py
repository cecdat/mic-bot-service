#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_push_notification():
    """直接测试推送通知"""
    print("📱 直接测试推送通知...")
    
    try:
        from project.push import trigger_push_notification
        import time
        
        # 直接调用推送函数
        trigger_push_notification(
            'verification_code',
            "测试验证码推送",
            f"这是一个测试推送消息\n时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n节点: localhost\n账户: test@example.com"
        )
        
        print("✅ 推送通知已发送")
        
    except Exception as e:
        print(f"❌ 推送通知失败: {e}")
        import traceback
        traceback.print_exc()

def test_bark_notification():
    """直接测试Bark推送"""
    print("\n🔔 直接测试Bark推送...")
    
    try:
        from project.push import send_bark_notification
        
        # 测试Bark推送
        test_url = "https://push.2020310.xyz/3S7MQPCaQGuh8aKkcwjcGg/"
        title = "测试Bark推送"
        body = "这是一个测试Bark推送消息"
        
        send_bark_notification(test_url, title, body)
        print("✅ Bark推送已发送")
        
    except Exception as e:
        print(f"❌ Bark推送失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 开始直接测试推送功能")
    print("=" * 50)
    
    # 测试推送通知
    test_push_notification()
    
    # 测试Bark推送
    test_bark_notification()
    
    print("\n" + "=" * 50)
    print("📋 测试完成")

if __name__ == "__main__":
    main()
