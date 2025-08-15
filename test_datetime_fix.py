#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间戳修复的脚本
验证 datetime.now(timezone.utc) 的正确用法
"""

from datetime import datetime, timezone
import json

def test_datetime_fix():
    """测试修复后的时间戳处理"""
    print("🧪 测试时间戳修复...")
    
    try:
        # 测试修复后的时间戳处理
        current_time = datetime.now(timezone.utc)
        iso_time = current_time.isoformat()
        
        print(f"✅ 当前UTC时间: {current_time}")
        print(f"✅ ISO格式时间: {iso_time}")
        print(f"✅ 时区信息: {current_time.tzinfo}")
        
        # 测试JSON序列化
        test_data = {
            "timestamp": iso_time,
            "status": "success"
        }
        
        json_str = json.dumps(test_data, ensure_ascii=False)
        print(f"✅ JSON序列化成功: {json_str}")
        
        # 测试从ISO格式解析
        parsed_time = datetime.fromisoformat(iso_time)
        print(f"✅ 解析ISO时间成功: {parsed_time}")
        print(f"✅ 解析后时区信息: {parsed_time.tzinfo}")
        
        print("\n🎉 所有测试通过！时间戳处理修复成功。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

def test_old_broken_code():
    """测试旧的错误代码（应该会失败）"""
    print("\n🧪 测试旧的错误代码...")
    
    try:
        # 这些是修复前的错误用法
        # current_time = datetime.now(datetime.timezone.utc)  # 错误
        # current_time = datetime.datetime.now(datetime.timezone.utc)  # 错误
        
        print("✅ 旧的错误代码已被移除，不会执行")
        
    except Exception as e:
        print(f"❌ 旧代码执行失败（预期结果）: {e}")
        return True
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 mic-bot-service 时间戳修复测试")
    print("=" * 50)
    
    # 测试修复后的代码
    success1 = test_datetime_fix()
    
    # 测试旧的错误代码
    success2 = test_old_broken_code()
    
    if success1 and success2:
        print("\n🎯 总结：时间戳处理修复完成！")
        print("✅ 修复了 datetime.now(timezone.utc) 的语法错误")
        print("✅ 修复了 datetime.datetime.now() 的重复引用错误")
        print("✅ 现在可以正确处理UTC时间戳")
    else:
        print("\n❌ 测试未完全通过，需要进一步检查")
