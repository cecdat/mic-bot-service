#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试节点脚本
"""

import requests
import json

def create_test_node():
    """创建测试节点"""
    print("=== 创建测试节点 ===")
    
    # 首先登录获取session
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        # 登录
        print("尝试登录...")
        login_response = session.post(
            "http://localhost:2002/web_api/login",
            json=login_data
        )
        
        if login_response.status_code == 200:
            print("✅ 登录成功")
            
            # 创建测试节点
            test_node_data = {
                "node_name": "测试节点",
                "cron_schedule": "10 9,13,19 * * *",
                "min_sleep_minutes": 5,
                "max_sleep_minutes": 20,
                "clusters": 1,
                "search_delay_min": "30s",
                "search_delay_max": "2min"
            }
            
            print("创建测试节点...")
            create_response = session.post(
                "http://localhost:2002/web_api/nodes",
                json=test_node_data
            )
            
            print(f"创建响应: {create_response.status_code} - {create_response.text}")
            
            if create_response.status_code == 200:
                result = create_response.json()
                print(f"✅ 测试节点创建成功: {result}")
                
                # 获取节点列表验证
                nodes_response = session.get("http://localhost:2002/web_api/nodes")
                if nodes_response.status_code == 200:
                    nodes = nodes_response.json()
                    print(f"✅ 现在有 {len(nodes)} 个节点")
                    
                    if nodes:
                        test_node = nodes[0]
                        print(f"测试节点: ID={test_node['id']}, 名称={test_node['node_name']}")
                
            else:
                print(f"❌ 创建测试节点失败")
                
        else:
            print(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
            
    except Exception as e:
        print(f"❌ 创建测试节点时出错: {e}")

if __name__ == "__main__":
    create_test_node()
