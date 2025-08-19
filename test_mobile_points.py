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
    
    # 测试无Token访问
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/mobile/get_points")
        if response.status_code == 401:
            print("✅ 无Token访问正确返回401")
        else:
            print(f"❌ 无Token访问返回错误状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 无Token访问异常: {str(e)}")
    
    # 测试无效Token访问
    try:
        headers = {'Authorization': 'Bearer invalid_token'}
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/mobile/get_points", headers=headers)
        if response.status_code == 401:
            print("✅ 无效Token访问正确返回401")
        else:
            print(f"❌ 无效Token访问返回错误状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 无效Token访问异常: {str(e)}")

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 移动端积分页面使用指南")
    print("="*60)
    print("1. 页面访问:")
    print(f"   URL: {SERVICE_BASE_URL}/mobile_points")
    print("   特点: 免登录，基于Token认证")
    
    print("\n2. 获取访问Token:")
    print("   在service端节点管理页面查看节点的Token")
    print("   或者在数据库中查询:")
    print("   SELECT node_name, token FROM bot_nodes;")
    
    print("\n3. 使用方式:")
    print("   - 打开移动端积分页面")
    print("   - 输入节点的Token")
    print("   - 查看该节点下所有账户的积分情况")

def main():
    """主测试函数"""
    print("🚀 开始测试移动端积分页面功能")
    print("="*60)
    
    test_mobile_points_page()
    test_mobile_api()
    show_usage_guide()

if __name__ == "__main__":
    main()
