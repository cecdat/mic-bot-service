#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端积分页面测试脚本
"""

import requests
import json

SERVICE_BASE_URL = "http://localhost:2002"

def test_mobile_points_page():
    """测试移动端积分页面访问"""
    print("📱 测试移动端积分页面访问")
    print("="*60)
    
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/mobile_points")
        if response.status_code == 200:
            print("✅ 移动端积分页面访问成功")
            print(f"   页面大小: {len(response.content)} 字节")
        else:
            print(f"❌ 移动端积分页面访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 移动端积分页面访问异常: {str(e)}")
        return False
    
    return True

def test_mobile_api():
    """测试移动端API"""
    print("\n🔒 测试移动端API")
    print("="*60)
    
    # 测试直接访问API
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/mobile/get_points")
        if response.status_code == 200:
            print("✅ API访问成功")
            data = response.json()
            print(f"   返回账户数量: {len(data)}")
        else:
            print(f"❌ API访问返回错误状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ API访问异常: {str(e)}")

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 移动端积分页面使用指南")
    print("="*60)
    print("1. 页面访问:")
    print(f"   完整地址: {SERVICE_BASE_URL}/mobile_points")
    print(f"   简短地址: {SERVICE_BASE_URL}/m")
    print("   特点: 完全免登录，无需Token认证")
    
    print("\n2. 使用方式:")
    print("   - 直接打开页面即可查看所有账户积分")
    print("   - 页面会自动刷新数据")
    print("   - 支持手动刷新")

def main():
    """主测试函数"""
    print("🚀 开始测试移动端积分页面功能")
    print("="*60)
    
    test_mobile_points_page()
    test_mobile_api()
    show_usage_guide()

if __name__ == "__main__":
    main()
