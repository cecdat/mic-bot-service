#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试推送通知函数
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.push import trigger_push_notification

def test_push_direct():
    """直接测试推送通知函数"""
    print("🔔 直接测试推送通知函数")
    print("="*50)
    
    try:
        title = "测试推送通知"
        body = "这是一个测试推送通知\n时间: 2025-08-19 16:52:00"
        
        print("调用推送通知函数...")
        trigger_push_notification('verification_code', title, body)
        print("推送通知函数调用完成")
        
    except Exception as e:
        print(f"❌ 推送通知测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_push_direct()
