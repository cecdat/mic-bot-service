#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
积分计算测试脚本
测试桌面端和移动端积分计算的准确性
"""

import requests
import json
from datetime import datetime

SERVICE_BASE_URL = "http://localhost:2002"

def test_points_calculation():
    """测试积分计算逻辑"""
    print("🔢 测试积分计算逻辑")
    print("="*60)
    
    # 模拟积分计算场景
    scenarios = [
        {
            "name": "正常情况 - 桌面端和移动端都成功",
            "initial_points": 1000,
            "desktop_final": 1200,
            "mobile_final": 1350,
            "expected_desktop_gain": 200,
            "expected_mobile_gain": 150,
            "expected_total_gain": 350
        },
        {
            "name": "桌面端失败，移动端成功",
            "initial_points": 1000,
            "desktop_final": 1000,
            "mobile_final": 1150,
            "expected_desktop_gain": 0,
            "expected_mobile_gain": 150,
            "expected_total_gain": 150
        },
        {
            "name": "桌面端成功，移动端失败",
            "initial_points": 1000,
            "desktop_final": 1200,
            "mobile_final": 1200,
            "expected_desktop_gain": 200,
            "expected_mobile_gain": 0,
            "expected_total_gain": 200
        },
        {
            "name": "都失败",
            "initial_points": 1000,
            "desktop_final": 1000,
            "mobile_final": 1000,
            "expected_desktop_gain": 0,
            "expected_mobile_gain": 0,
            "expected_total_gain": 0
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 40)
        
        # 模拟计算过程
        initial_points = scenario['initial_points']
        desktop_final = scenario['desktop_final']
        mobile_final = scenario['mobile_final']
        
        # 桌面端收益计算
        desktop_gain = desktop_final - initial_points
        
        # 移动端收益计算（基于桌面端完成后的积分）
        mobile_gain = mobile_final - desktop_final
        
        # 总收益计算
        total_gain = mobile_final - initial_points
        
        print(f"初始积分: {initial_points}")
        print(f"桌面端最终积分: {desktop_final}")
        print(f"移动端最终积分: {mobile_final}")
        print(f"桌面端收益: {desktop_gain} (期望: {scenario['expected_desktop_gain']})")
        print(f"移动端收益: {mobile_gain} (期望: {scenario['expected_mobile_gain']})")
        print(f"总收益: {total_gain} (期望: {scenario['expected_total_gain']})")
        
        # 验证计算结果
        desktop_correct = desktop_gain == scenario['expected_desktop_gain']
        mobile_correct = mobile_gain == scenario['expected_mobile_gain']
        total_correct = total_gain == scenario['expected_total_gain']
        
        if desktop_correct and mobile_correct and total_correct:
            print("✅ 计算结果正确")
        else:
            print("❌ 计算结果错误")
            if not desktop_correct:
                print(f"   桌面端收益计算错误: 实际 {desktop_gain}, 期望 {scenario['expected_desktop_gain']}")
            if not mobile_correct:
                print(f"   移动端收益计算错误: 实际 {mobile_gain}, 期望 {scenario['expected_mobile_gain']}")
            if not total_correct:
                print(f"   总收益计算错误: 实际 {total_gain}, 期望 {scenario['expected_total_gain']}")

def test_database_points():
    """测试数据库中的积分数据"""
    print("\n" + "="*60)
    print("🗄️ 测试数据库中的积分数据")
    print("="*60)
    
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/web_api/get_points")
        if response.status_code == 200:
            accounts = response.json()
            print(f"✅ 获取到 {len(accounts)} 个账户的积分数据")
            
            for account in accounts[:5]:  # 只显示前5个账户
                email = account.get('email', '未知')
                total_points = account.get('total_points', 0)
                daily_gain = account.get('daily_gain', 0)
                desktop_gain = account.get('desktop_gain', 0)
                mobile_gain = account.get('mobile_gain', 0)
                last_updated = account.get('last_updated', '未知')
                
                print(f"\n账户: {email}")
                print(f"  总积分: {total_points}")
                print(f"  今日收益: {daily_gain}")
                print(f"  桌面端收益: {desktop_gain}")
                print(f"  移动端收益: {mobile_gain}")
                print(f"  最后更新: {last_updated}")
                
                # 验证积分计算的一致性
                calculated_total = desktop_gain + mobile_gain
                if daily_gain == calculated_total:
                    print("  ✅ 积分计算一致")
                else:
                    print(f"  ❌ 积分计算不一致: 今日收益 {daily_gain} != 桌面端 {desktop_gain} + 移动端 {mobile_gain} = {calculated_total}")
        else:
            print(f"❌ 获取积分数据失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试数据库积分数据异常: {e}")

def show_optimization_guide():
    """显示积分计算优化指南"""
    print("\n" + "="*60)
    print("📋 积分计算优化指南")
    print("="*60)
    print("优化后的积分计算逻辑:")
    print()
    print("1. 初始积分获取:")
    print("   - 在桌面端登录成功后获取初始积分")
    print("   - 保存到本地文件，避免重复获取")
    print()
    print("2. 桌面端收益计算:")
    print("   - 基于今日初始积分计算")
    print("   - 收益 = 桌面端完成后的积分 - 初始积分")
    print()
    print("3. 移动端收益计算:")
    print("   - 基于桌面端完成后的积分作为初始值")
    print("   - 收益 = 移动端完成后的积分 - 桌面端完成后的积分")
    print()
    print("4. 总收益计算:")
    print("   - 总收益 = 移动端完成后的积分 - 今日初始积分")
    print("   - 或者 = 桌面端收益 + 移动端收益")
    print()
    print("5. 优势:")
    print("   - 避免积分重复计算")
    print("   - 确保桌面端和移动端收益独立")
    print("   - 提供准确的收益统计")
    print()
    print("6. 日志输出:")
    print("   - 桌面端: 初始积分、最终积分、收益")
    print("   - 移动端: 初始积分(桌面端完成后的)、最终积分、收益")
    print("   - 总体: 初始积分、最终积分、总收益、各端收益")

def main():
    print("🔢 积分计算优化测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_points_calculation()
    test_database_points()
    show_optimization_guide()
    
    print("\n" + "="*60)
    print("🎯 测试完成")
    print("请检查Node端的积分计算逻辑是否按预期工作")
    print("="*60)

if __name__ == "__main__":
    main()
